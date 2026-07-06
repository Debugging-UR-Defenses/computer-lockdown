"""
Download and installation blocking for Computer Lockdown.

Monitors common download locations (Downloads, Desktop, Documents) for
newly-created files.  When ``download_blocking.block_all_in_locked_mode``
is enabled (the default), **all** new files are quarantined and placed
into a review queue.  Otherwise only files whose extensions appear on
the configured block list are quarantined (legacy behaviour).

Quarantined files are moved to a dedicated quarantine directory and can
be approved (restored to original location) or denied (permanently
deleted) via the review queue API.

If the ``watchdog`` library is available the module uses efficient
filesystem event notifications; otherwise it falls back to a simple
polling strategy that scans every 5 seconds.
"""

import logging
import os
import platform
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Attempt to import watchdog for efficient filesystem watching.
# ---------------------------------------------------------------------------

_WATCHDOG_AVAILABLE = False

try:
    from watchdog.observers import Observer  # type: ignore[import-untyped]
    from watchdog.events import (  # type: ignore[import-untyped]
        FileSystemEventHandler,
        FileCreatedEvent,
    )
    _WATCHDOG_AVAILABLE = True
except ImportError:
    logger.info(
        "watchdog library not installed — DownloadBlocker will use polling."
    )


# ---------------------------------------------------------------------------
# Resolve common user directories
# ---------------------------------------------------------------------------

def _get_watched_directories() -> list[Path]:
    """Return a list of directories to monitor for new downloads.

    On Windows this uses the well-known shell folder paths.  On other
    platforms it falls back to ``~/Downloads``, ``~/Desktop``, and
    ``~/Documents``.
    """
    home = Path.home()
    candidates = [
        home / "Downloads",
        home / "Desktop",
        home / "Documents",
    ]

    # On Windows, try to pick up the actual known-folder locations from
    # environment variables (they may differ from the English defaults).
    if platform.system() == "Windows":
        user_profile = os.environ.get("USERPROFILE", "")
        if user_profile:
            candidates = [
                Path(user_profile) / "Downloads",
                Path(user_profile) / "Desktop",
                Path(user_profile) / "Documents",
            ]

    return [d for d in candidates if d.is_dir()]


# ---------------------------------------------------------------------------
# Watchdog handler (used when library is available)
# ---------------------------------------------------------------------------

if _WATCHDOG_AVAILABLE:
    class _NewFileHandler(FileSystemEventHandler):
        """Watchdog handler that delegates to ``DownloadBlocker.on_file_created``."""

        def __init__(self, blocker: "DownloadBlocker") -> None:
            super().__init__()
            self._blocker = blocker

        def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
            if event.is_directory:
                return
            self._blocker.on_file_created(event.src_path)


# ---------------------------------------------------------------------------
# DownloadBlocker
# ---------------------------------------------------------------------------

class DownloadBlocker:
    """Monitors filesystem for new downloads and blocks/quarantines files.

    When ``download_blocking.block_all_in_locked_mode`` is ``True`` (the
    default) every new file detected in the watched directories is moved
    to the quarantine directory and added to the review queue.

    When it is ``False``, only files whose extensions appear on the block
    list (``download_blocking.block_extensions``) are quarantined (legacy
    behaviour).

    Quarantined files can be approved or denied via ``approve_download``
    and ``deny_download``.
    """

    POLL_INTERVAL: float = 5.0  # seconds (used when watchdog is unavailable)

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config: ConfigManager = config_manager
        self.running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._watchers: list = []  # watchdog Observer instances (if used)
        self._blocked_log: list[dict] = []
        self._lock: threading.Lock = threading.Lock()
        # Snapshot for poll-based watching: {dir_path: set_of_filenames}
        self._snapshots: dict[str, set[str]] = {}

        # Quarantine directory
        self._quarantine_dir = self._get_quarantine_dir()

    # ------------------------------------------------------------------
    # Quarantine directory
    # ------------------------------------------------------------------

    def _get_quarantine_dir(self) -> Path:
        """Get or create the quarantine directory."""
        configured = self.config.get("download_blocking.quarantine_dir", "")
        if configured:
            qdir = Path(configured)
        elif platform.system() == "Windows":
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                qdir = Path(appdata) / "ComputerLockdown" / "quarantine"
            else:
                qdir = Path("quarantine")
        else:
            qdir = Path("quarantine")

        qdir.mkdir(parents=True, exist_ok=True)
        return qdir

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start monitoring Downloads, Desktop, and Documents folders.

        Uses ``watchdog`` if available; otherwise polls every 5 seconds.
        """
        if self.running:
            logger.debug("DownloadBlocker already running.")
            return

        if not self.config.get("download_blocking.enabled", True):
            logger.info("Download blocking is disabled in config.")
            return

        self.running = True
        dirs = _get_watched_directories()
        if not dirs:
            logger.warning("No watched directories found — DownloadBlocker idle.")
            return

        if _WATCHDOG_AVAILABLE:
            self._start_watchdog(dirs)
        else:
            self._start_polling(dirs)

        logger.info(
            "DownloadBlocker started — monitoring: %s",
            ", ".join(str(d) for d in dirs),
        )

    def stop(self) -> None:
        """Stop monitoring."""
        self.running = False

        # Stop watchdog observers.
        for observer in self._watchers:
            try:
                observer.stop()
                observer.join(timeout=5.0)
            except Exception:
                logger.exception("Error stopping watchdog observer.")
        self._watchers.clear()

        # Stop poll thread.
        if self._thread is not None:
            self._thread.join(timeout=10.0)
            self._thread = None

        logger.info("DownloadBlocker stopped.")

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def on_file_created(self, file_path: str) -> None:
        """Handle a new file detection.

        If ``block_all_in_locked_mode`` is ``True``: quarantine **any** new
        file.  Otherwise only block files with blocked extensions (legacy
        behaviour).

        Parameters
        ----------
        file_path:
            Absolute path to the newly created file.
        """
        path = Path(file_path)

        if path.is_dir():
            return

        # Skip temporary/partial download files
        if path.suffix.lower() in ('.crdownload', '.part', '.partial', '.tmp', '.temp'):
            return

        block_all = self.config.get("download_blocking.block_all_in_locked_mode", True)
        ext = path.suffix.lower()

        if block_all:
            # Block ALL downloads in locked mode
            self._quarantine_file(path)
        elif ext and self.is_extension_blocked(ext):
            # Legacy: only block specific extensions
            self._quarantine_file(path)

    def _quarantine_file(self, path: Path) -> None:
        """Move a file to quarantine and add to review queue."""
        logger.info("Quarantining file: %s", path)

        quarantine_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{path.name}"
        quarantine_path = self._quarantine_dir / quarantine_name

        try:
            time.sleep(0.5)  # Wait for download to complete
            if path.exists():
                shutil.move(str(path), str(quarantine_path))
                logger.info("File quarantined: %s -> %s", path, quarantine_path)
            else:
                logger.debug("File already gone: %s", path)
                return
        except (PermissionError, OSError) as exc:
            logger.warning("Could not quarantine %s: %s", path, exc)
            # Fall back to deletion
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            quarantine_path = None

        entry = {
            "filename": path.name,
            "original_path": str(path),
            "quarantine_path": str(quarantine_path) if quarantine_path else "",
            "timestamp": datetime.now().isoformat(),
            "extension": path.suffix.lower(),
            "status": "pending",
        }

        with self._lock:
            self._blocked_log.append(entry)
            if len(self._blocked_log) > 500:
                self._blocked_log = self._blocked_log[-500:]

        # Also persist to config review queue
        queue = self.config.get("download_blocking.review_queue", [])
        queue.append(entry)
        # Keep only last 100 in persistent queue
        if len(queue) > 100:
            queue = queue[-100:]
        self.config.set("download_blocking.review_queue", queue)

        self._notify_user(path.name)

    # ------------------------------------------------------------------
    # Review queue — approve / deny
    # ------------------------------------------------------------------

    def approve_download(self, index: int) -> bool:
        """Approve a quarantined download, restoring it to its original location.

        Args:
            index: Index into the review queue.

        Returns:
            True if the file was successfully restored.
        """
        queue = self.config.get("download_blocking.review_queue", [])
        if index < 0 or index >= len(queue):
            return False

        entry = queue[index]
        if entry.get("status") != "pending":
            return False

        quarantine_path = entry.get("quarantine_path", "")
        original_path = entry.get("original_path", "")

        if quarantine_path and original_path and Path(quarantine_path).exists():
            try:
                # Make sure original directory exists
                Path(original_path).parent.mkdir(parents=True, exist_ok=True)
                shutil.move(quarantine_path, original_path)
                entry["status"] = "approved"
                queue[index] = entry
                self.config.set("download_blocking.review_queue", queue)
                logger.info("Download approved: %s", entry.get("filename"))
                return True
            except (OSError, PermissionError) as exc:
                logger.warning("Failed to restore %s: %s", entry.get("filename"), exc)
                return False

        return False

    def deny_download(self, index: int) -> bool:
        """Deny a quarantined download, permanently deleting it.

        Args:
            index: Index into the review queue.

        Returns:
            True if the file was successfully deleted.
        """
        queue = self.config.get("download_blocking.review_queue", [])
        if index < 0 or index >= len(queue):
            return False

        entry = queue[index]
        if entry.get("status") != "pending":
            return False

        quarantine_path = entry.get("quarantine_path", "")

        if quarantine_path:
            try:
                Path(quarantine_path).unlink(missing_ok=True)
            except OSError:
                pass

        entry["status"] = "denied"
        queue[index] = entry
        self.config.set("download_blocking.review_queue", queue)
        logger.info("Download denied: %s", entry.get("filename"))
        return True

    def get_review_queue(self) -> list[dict]:
        """Return the current review queue from config."""
        return self.config.get("download_blocking.review_queue", [])

    def clear_resolved(self) -> None:
        """Remove approved and denied entries from the review queue."""
        queue = self.config.get("download_blocking.review_queue", [])
        queue = [e for e in queue if e.get("status") == "pending"]
        self.config.set("download_blocking.review_queue", queue)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_blocked_log(self) -> list[dict]:
        """Return a copy of the blocked-download log.

        Each entry is a dict with keys ``timestamp``, ``file_path``,
        ``extension``, and ``deleted``.
        """
        with self._lock:
            return list(self._blocked_log)

    def is_extension_blocked(self, ext: str) -> bool:
        """Check if a file extension is on the block list.

        Parameters
        ----------
        ext:
            Extension string including the leading dot, e.g. ``".exe"``.
        """
        blocked: list[str] = self.config.get(
            "download_blocking.block_extensions", []
        )
        return ext.lower() in {e.lower() for e in blocked}

    # ------------------------------------------------------------------
    # Watchdog-based watching
    # ------------------------------------------------------------------

    def _start_watchdog(self, dirs: list[Path]) -> None:
        """Create and start a ``watchdog.Observer`` for each directory."""
        handler = _NewFileHandler(self)  # type: ignore[used-before-def]
        for directory in dirs:
            observer = Observer()
            observer.schedule(handler, str(directory), recursive=False)
            observer.daemon = True
            observer.start()
            self._watchers.append(observer)
            logger.debug("Watchdog observer started for %s", directory)

    # ------------------------------------------------------------------
    # Poll-based watching (fallback)
    # ------------------------------------------------------------------

    def _start_polling(self, dirs: list[Path]) -> None:
        """Take an initial snapshot and launch the polling thread."""
        for directory in dirs:
            try:
                self._snapshots[str(directory)] = {
                    f.name for f in directory.iterdir() if f.is_file()
                }
            except OSError:
                self._snapshots[str(directory)] = set()

        self._thread = threading.Thread(
            target=self._poll_loop,
            args=(dirs,),
            name="DownloadBlockerPoll",
            daemon=True,
        )
        self._thread.start()

    def _poll_loop(self, dirs: list[Path]) -> None:
        """Periodically scan watched directories for new files."""
        while self.running:
            time.sleep(self.POLL_INTERVAL)
            if not self.running:
                break

            for directory in dirs:
                dir_key = str(directory)
                try:
                    current = {f.name for f in directory.iterdir() if f.is_file()}
                except OSError:
                    continue

                previous = self._snapshots.get(dir_key, set())
                new_files = current - previous
                self._snapshots[dir_key] = current

                for filename in new_files:
                    file_path = directory / filename
                    self.on_file_created(str(file_path))

    # ------------------------------------------------------------------
    # Notification helper
    # ------------------------------------------------------------------

    @staticmethod
    def _notify_user(filename: str) -> None:
        """Try to show a toast notification about the blocked download.

        This is best-effort; failures are silently logged.
        """
        if platform.system() != "Windows":
            logger.debug("Notification skipped — not on Windows.")
            return

        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                0,
                f"The file \"{filename}\" was blocked and quarantined by Computer Lockdown.",
                "Computer Lockdown — Download Quarantined",
                0x00000040,  # MB_ICONINFORMATION
            )
        except Exception:
            logger.debug("Could not display user notification.", exc_info=True)
