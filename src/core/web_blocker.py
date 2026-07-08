"""
Website blocking via the Windows hosts file for Computer Lockdown.

Adds entries that redirect blocked domains to ``127.0.0.1``, effectively
preventing the browser from reaching them.  Entries are demarcated with
unique markers so they can be cleanly inserted and removed without
disturbing the user's original hosts file content.
"""

import logging
import platform
import subprocess
from pathlib import Path
from typing import Optional

from ..utils.subprocess_helper import run_hidden

from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


class WebBlocker:
    """Blocks websites by modifying the Windows hosts file.

    Blocked entries are wrapped between ``BLOCK_MARKER_START`` and
    ``BLOCK_MARKER_END`` so that they can be surgically removed later
    without affecting any pre-existing hosts-file content.
    """

    HOSTS_PATH: str = r"C:\Windows\System32\drivers\etc\hosts"
    BLOCK_MARKER_START: str = "# === COMPUTER LOCKDOWN START ==="
    BLOCK_MARKER_END: str = "# === COMPUTER LOCKDOWN END ==="

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config: ConfigManager = config_manager

        # On non-Windows platforms use a local temp file for development.
        if platform.system() != "Windows":
            dev_path = (
                Path(__file__).resolve().parents[2] / "config" / "hosts_dev"
            )
            self._hosts_path: Path = dev_path
            logger.warning(
                "Non-Windows platform detected.  Using dev hosts file: %s",
                self._hosts_path,
            )
        else:
            self._hosts_path = Path(self.HOSTS_PATH)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def activate(self) -> None:
        """Write blocked sites to the hosts file and flush the DNS cache.

        * Reads the current hosts file.
        * Strips any previous Computer Lockdown block.
        * Appends the new block of ``127.0.0.1`` entries for every domain
          in the configured blocked-sites list.
        * Flushes the Windows DNS resolver cache.
        """
        if not self.config.get("web_blocking.enabled", True):
            logger.info("Web blocking is disabled in config — skipping activate.")
            return

        blocked_sites: list[str] = self.config.get("web_blocking.blocked_sites", [])
        if not blocked_sites:
            logger.info("No sites in the block list — nothing to do.")
            self.deactivate()  # Clean up any stale entries
            return

        # Read existing content (minus our old block).
        original = self._read_hosts_without_block()

        # Build the new block.
        lines: list[str] = [self.BLOCK_MARKER_START]
        for domain in blocked_sites:
            domain = domain.strip().lower()
            if not domain:
                continue
            lines.append(f"127.0.0.1 {domain}")
            # Also block the www variant if not already present.
            if not domain.startswith("www."):
                lines.append(f"127.0.0.1 www.{domain}")
        lines.append(self.BLOCK_MARKER_END)

        new_content = original.rstrip("\n") + "\n\n" + "\n".join(lines) + "\n"

        try:
            self._hosts_path.write_text(new_content, encoding="utf-8")
            logger.info("Hosts file updated with %d blocked domains.", len(blocked_sites))
        except PermissionError:
            logger.error(
                "Permission denied writing to hosts file.  "
                "Run as administrator to modify %s.",
                self._hosts_path,
            )
            return
        except OSError as exc:
            logger.error("Failed to write hosts file: %s", exc)
            return

        self._flush_dns()

    def deactivate(self) -> None:
        """Remove all Computer Lockdown entries from the hosts file."""
        original = self._read_hosts_without_block()
        try:
            self._hosts_path.write_text(original, encoding="utf-8")
            logger.info("Computer Lockdown entries removed from hosts file.")
        except PermissionError:
            logger.error(
                "Permission denied writing to hosts file.  "
                "Run as administrator."
            )
        except OSError as exc:
            logger.error("Failed to write hosts file: %s", exc)

        self._flush_dns()

    def add_site(self, domain: str) -> None:
        """Add a site to the block list and re-activate.

        Parameters
        ----------
        domain:
            The domain to block, e.g. ``"example.com"``.
        """
        domain = domain.strip().lower()
        if not domain:
            return

        blocked: list[str] = self.config.get("web_blocking.blocked_sites", [])
        if domain not in blocked:
            blocked.append(domain)
            self.config.set("web_blocking.blocked_sites", blocked)
            logger.info("Added %s to blocked sites.", domain)

        if self.config.get("web_blocking.enabled", True):
            self.activate()

    def remove_site(self, domain: str) -> None:
        """Remove a site from the block list and re-activate.

        Parameters
        ----------
        domain:
            The domain to unblock.
        """
        domain = domain.strip().lower()
        blocked: list[str] = self.config.get("web_blocking.blocked_sites", [])
        blocked = [d for d in blocked if d.lower() != domain]
        self.config.set("web_blocking.blocked_sites", blocked)
        logger.info("Removed %s from blocked sites.", domain)

        if self.config.get("web_blocking.enabled", True):
            self.activate()

    def get_blocked_sites(self) -> list[str]:
        """Return the current list of blocked sites from the configuration."""
        return list(self.config.get("web_blocking.blocked_sites", []))

    def is_active(self) -> bool:
        """Check if Computer Lockdown blocking entries exist in the hosts file.

        Returns
        -------
        bool
            ``True`` if the hosts file currently contains our marker block.
        """
        try:
            content = self._hosts_path.read_text(encoding="utf-8")
            return self.BLOCK_MARKER_START in content
        except OSError:
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_hosts_without_block(self) -> str:
        """Read the hosts file and strip out any existing Computer Lockdown
        block (everything between the markers, inclusive)."""
        try:
            content = self._hosts_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("Hosts file not found at %s — starting fresh.", self._hosts_path)
            return ""
        except OSError as exc:
            logger.error("Failed to read hosts file: %s", exc)
            return ""

        # Remove our block if present.
        result_lines: list[str] = []
        inside_block = False
        for line in content.splitlines(keepends=True):
            stripped = line.strip()
            if stripped == self.BLOCK_MARKER_START:
                inside_block = True
                continue
            if stripped == self.BLOCK_MARKER_END:
                inside_block = False
                continue
            if not inside_block:
                result_lines.append(line)

        return "".join(result_lines)

    @staticmethod
    def _flush_dns() -> None:
        """Flush the Windows DNS resolver cache.

        On non-Windows platforms this is a no-op with a debug log message.
        """
        if platform.system() != "Windows":
            logger.debug("DNS flush skipped — not on Windows.")
            return

        try:
            run_hidden(
                ["ipconfig", "/flushdns"],
                check=False,
            )
            logger.info("DNS cache flushed.")
        except FileNotFoundError:
            logger.warning("ipconfig not found — could not flush DNS.")
        except subprocess.TimeoutExpired:
            logger.warning("DNS flush timed out.")
        except OSError as exc:
            logger.warning("DNS flush failed: %s", exc)
