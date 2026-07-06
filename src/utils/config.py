"""
Configuration management for Computer Lockdown.

Handles loading, saving, and accessing application configuration stored as JSON.
Primary location: %PROGRAMDATA%/ComputerLockdown/config.json (Windows)
Fallback location: ./config/config.json (development)
"""

import copy
import hashlib
import hmac
import json
import logging
import os
import platform
import threading
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_HMAC_KEY = b"ComputerLockdown_ConfigIntegrity_v1"

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "admin_password_hash": "",
    "admin_mode": False,
    "app_whitelist": {
        "enabled": True,
        "allowed_apps": [
            {"name": "Google Chrome", "path": "chrome.exe"},
            {"name": "Microsoft Edge", "path": "msedge.exe"},
            {"name": "File Explorer", "path": "explorer.exe"},
        ],
        "allowed_services": [
            {"name": "Windows Defender", "path": "MsMpEng.exe", "parent_app": "System"},
            {"name": "Windows Update", "path": "wuauclt.exe", "parent_app": "System"},
        ],
        "auto_detect_dependencies": True,
    },
    "web_blocking": {
        "enabled": True,
        "mode": "blacklist",
        "blocked_sites": [],
        "allowed_sites": [],
    },
    "time_limits": {
        "enabled": True,
        "daily_limit_minutes": 120,
        "hard_cutoff": "20:30",
        "warning_minutes": 10,
        "schedule": {
            "monday": {"enabled": True, "start": "15:00", "end": "20:00"},
            "tuesday": {"enabled": True, "start": "15:00", "end": "20:00"},
            "wednesday": {"enabled": True, "start": "15:00", "end": "20:00"},
            "thursday": {"enabled": True, "start": "15:00", "end": "20:00"},
            "friday": {"enabled": True, "start": "15:00", "end": "21:00"},
            "saturday": {"enabled": True, "start": "10:00", "end": "21:00"},
            "sunday": {"enabled": True, "start": "10:00", "end": "20:00"},
        },
    },
    "download_blocking": {
        "enabled": True,
        "block_all_in_locked_mode": True,
        "block_extensions": [
            ".exe", ".msi", ".bat", ".cmd", ".ps1",
            ".vbs", ".js", ".wsf", ".scr",
        ],
        "review_queue": [],
        "quarantine_dir": "",
    },
    "network_rules": {
        "enabled": False,
        "allowed_lan_services": [],
        "allow_all_lan": False,
        "blocked_ports": [],
    },
    "policy": {
        "block_task_manager": True,
        "block_cmd": True,
        "block_registry_editor": True,
        "block_control_panel": False,
        "block_settings": False,
    },
    "startup": {
        "run_on_startup": True,
        "start_locked": True,
    },
    "usage_log": {
        "daily_usage_minutes": {},
        "last_reset_date": "",
    },
}


def _resolve_config_path() -> Path:
    """Return the path to the configuration file.

    On Windows the config lives under ``%PROGRAMDATA%/ComputerLockdown/``.
    On other platforms (or when ``%PROGRAMDATA%`` is not set) the function falls
    back to ``./config/config.json`` for local development.
    """
    if platform.system() == "Windows":
        programdata = os.environ.get("PROGRAMDATA")
        if programdata:
            return Path(programdata) / "ComputerLockdown" / "config.json"

    # Development fallback
    return Path(__file__).resolve().parents[2] / "config" / "config.json"


class ConfigManager:
    """Thread-safe JSON configuration manager.

    Usage::

        cfg = ConfigManager()
        cfg.load()

        enabled = cfg.get("app_whitelist.enabled")
        cfg.set("time_limits.daily_limit_minutes", 90)
        cfg.save()
    """

    def __init__(self, config_path: Optional[str | Path] = None) -> None:
        self._path: Path = Path(config_path) if config_path else _resolve_config_path()
        self._data: dict[str, Any] = copy.deepcopy(DEFAULT_CONFIG)
        self._lock: threading.RLock = threading.RLock()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        """Return the resolved config file path."""
        return self._path

    @property
    def data(self) -> dict[str, Any]:
        """Return a shallow reference to the internal config dict."""
        return self._data

    # ------------------------------------------------------------------
    # Core I/O
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load configuration from disk.

        If the file does not exist the default configuration is written out
        first so that subsequent calls always find a valid file.
        """
        with self._lock:
            if not self._path.exists():
                logger.info("Config file not found at %s — creating with defaults.", self._path)
                self._data = copy.deepcopy(DEFAULT_CONFIG)
                self._write_locked()
                return

            try:
                raw = self._path.read_text(encoding="utf-8")
                loaded = json.loads(raw)
                # Merge loaded values on top of defaults so new keys are
                # always present even if the file is from an older version.
                self._data = self._deep_merge(copy.deepcopy(DEFAULT_CONFIG), loaded)
                # HMAC verification
                sig_path = self._path.with_suffix(".sig")
                if sig_path.exists():
                    try:
                        stored_sig = sig_path.read_text(encoding="utf-8").strip()
                        computed_sig = hmac.new(_HMAC_KEY, raw.encode("utf-8"), hashlib.sha256).hexdigest()
                        if not hmac.compare_digest(stored_sig, computed_sig):
                            logger.warning(
                                "Config file integrity check FAILED — file may have been tampered with. "
                                "Reverting to defaults."
                            )
                            self._data = copy.deepcopy(DEFAULT_CONFIG)
                            self._write_locked()
                            return
                        logger.debug("Config integrity check passed.")
                    except OSError:
                        logger.debug("Could not read signature file.")
                else:
                    # No sig file yet (first run or upgrade) — write one
                    sig = hmac.new(_HMAC_KEY, raw.encode("utf-8"), hashlib.sha256).hexdigest()
                    try:
                        sig_path.write_text(sig, encoding="utf-8")
                    except OSError:
                        pass
                logger.info("Configuration loaded from %s", self._path)
            except (json.JSONDecodeError, OSError) as exc:
                logger.error("Failed to load config (%s) — using defaults.", exc)
                self._data = copy.deepcopy(DEFAULT_CONFIG)

    def save(self) -> None:
        """Persist the current configuration to disk (thread-safe)."""
        with self._lock:
            self._write_locked()

    def _write_locked(self) -> None:
        """Write ``self._data`` to disk.  Must be called while holding ``_lock``."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        json_content = json.dumps(self._data, indent=2, ensure_ascii=False) + "\n"
        tmp_path = self._path.with_suffix(".tmp")
        try:
            tmp_path.write_text(json_content, encoding="utf-8")
            tmp_path.replace(self._path)
            # Write HMAC signature
            sig = hmac.new(_HMAC_KEY, json_content.encode("utf-8"), hashlib.sha256).hexdigest()
            self._path.with_suffix(".sig").write_text(sig, encoding="utf-8")
            logger.debug("Configuration saved to %s", self._path)
        except OSError as exc:
            logger.error("Failed to save config: %s", exc)
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Accessors (dot-notation)
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value using dot-notation.

        Example::

            cfg.get("app_whitelist.enabled")       # True
            cfg.get("time_limits.schedule.monday")  # {"start": "15:00", ...}
        """
        with self._lock:
            return self._traverse(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value using dot-notation and persist to disk.

        Example::

            cfg.set("time_limits.daily_limit_minutes", 90)
        """
        with self._lock:
            parts = key.split(".")
            node = self._data
            for part in parts[:-1]:
                if part not in node or not isinstance(node[part], dict):
                    node[part] = {}
                node = node[part]
            node[parts[-1]] = value

        # Save outside the traversal lock to keep the critical section small
        self.save()

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset_to_defaults(self) -> None:
        """Replace the current configuration with ``DEFAULT_CONFIG`` and save."""
        with self._lock:
            self._data = copy.deepcopy(DEFAULT_CONFIG)
        self.save()
        logger.info("Configuration reset to defaults.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _traverse(self, key: str, default: Any = None) -> Any:
        """Walk ``self._data`` following *key* (dot-separated).  Must be called
        while holding ``_lock``."""
        node: Any = self._data
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Recursively merge *override* into *base* (mutates *base*)."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigManager._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
