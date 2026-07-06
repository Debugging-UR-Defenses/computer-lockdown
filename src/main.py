"""
Computer Lockdown - Parental Control Application for Windows 11
Main entry point.

Responsibilities:
    1. Enforce single-instance execution via a temp-file lock.
    2. Bootstrap logging (console + rotating log file).
    3. Load (or create) the application configuration.
    4. Optionally start lockdown immediately if configured.
    5. Launch the CustomTkinter GUI.
    6. Clean up on exit.
"""

import atexit
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging setup  (console handler first; file handler added after config load)
# ---------------------------------------------------------------------------

LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("ComputerLockdown")


# ---------------------------------------------------------------------------
# Single-instance lock
# ---------------------------------------------------------------------------

_LOCK_FILE_NAME: str = "computer_lockdown.lock"
_lock_file_handle: Optional[object] = None  # kept open for the process lifetime


def _acquire_instance_lock() -> bool:
    """Try to acquire a file-based lock to enforce single-instance execution.

    On **Windows** this uses :func:`msvcrt.locking` which fails immediately if
    another process already holds the lock.  On **POSIX** systems it falls back
    to :func:`fcntl.flock` with ``LOCK_EX | LOCK_NB``.

    Returns:
        ``True`` if the lock was acquired (we are the only instance).
        ``False`` if another instance is already running.
    """
    global _lock_file_handle

    lock_path: str = os.path.join(tempfile.gettempdir(), _LOCK_FILE_NAME)

    try:
        # Open (or create) the lock file in read/write mode.  We must NOT
        # truncate because another instance may be using it.
        _lock_file_handle = open(lock_path, "w")  # noqa: SIM115

        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(_lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(_lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

        # Write our PID for diagnostics.
        _lock_file_handle.write(str(os.getpid()))
        _lock_file_handle.flush()

        # Register cleanup so the lock is released on normal exit.
        atexit.register(_release_instance_lock)
        return True

    except (OSError, IOError):
        # Lock already held by another process.
        if _lock_file_handle is not None:
            _lock_file_handle.close()
            _lock_file_handle = None
        return False


def _release_instance_lock() -> None:
    """Release the instance lock file (called via :func:`atexit.register`)."""
    global _lock_file_handle

    if _lock_file_handle is None:
        return

    try:
        if sys.platform == "win32":
            import msvcrt

            try:
                msvcrt.locking(_lock_file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl

            try:
                fcntl.flock(_lock_file_handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass

        _lock_file_handle.close()
    except Exception:
        pass
    finally:
        _lock_file_handle = None

    # Best-effort removal of the lock file.
    lock_path: str = os.path.join(tempfile.gettempdir(), _LOCK_FILE_NAME)
    try:
        os.unlink(lock_path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# File-log bootstrap
# ---------------------------------------------------------------------------

def _attach_file_logger(log_dir: Path) -> None:
    """Add a :class:`logging.FileHandler` that writes to *log_dir*/lockdown.log.

    The directory is created if it does not exist.  A
    :class:`logging.handlers.RotatingFileHandler` is used so logs don't grow
    unbounded (max 2 MB, 3 backups).
    """
    from logging.handlers import RotatingFileHandler

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file: Path = log_dir / "lockdown.log"

    handler = RotatingFileHandler(
        str(log_file),
        maxBytes=2 * 1024 * 1024,  # 2 MB
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    logger.debug("File logging initialised: %s", log_file)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Application entry point.

    Steps:
        1. Acquire single-instance lock.
        2. Load configuration via :class:`ConfigManager`.
        3. Attach file-based log handler.
        4. Detect first-run (no admin password set).
        5. Create :class:`LockdownService` and optionally start it.
        6. Launch the CustomTkinter GUI.
        7. Clean up on exit.
    """

    # 1. Single-instance guard
    if not _acquire_instance_lock():
        logger.error(
            "Another instance of Computer Lockdown is already running. Exiting."
        )
        sys.exit(1)

    # 2. Load configuration
    from src.utils.config import ConfigManager
    from src.utils.crypto import is_password_set

    config = ConfigManager()
    config.load()

    # 3. Attach file logger (log next to config file)
    log_dir: Path = config.path.parent  # e.g. %APPDATA%/ComputerLockdown/
    _attach_file_logger(log_dir)

    logger.info("Computer Lockdown starting (PID %d)...", os.getpid())

    # 4. First-run detection
    first_run: bool = not is_password_set(config)
    if first_run:
        logger.info("First run detected - admin password setup will be required.")

    # 5. Initialise lockdown service
    from src.core.lockdown_service import LockdownService

    service = LockdownService(config)

    # Start lockdown immediately if configured and a password is set.
    if config.get("startup.start_locked") and not first_run:
        logger.info("Starting in locked mode (startup.start_locked is True).")
        service.start_lockdown()

    # 6. Launch GUI
    from src.gui.app import ComputerLockdownApp

    app = ComputerLockdownApp(config, service)

    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user (KeyboardInterrupt).")
    except Exception:
        logger.exception("Unhandled exception in main GUI loop.")
    finally:
        # 7. Cleanup
        service.stop_lockdown()
        logger.info("Computer Lockdown stopped.")


if __name__ == "__main__":
    main()
