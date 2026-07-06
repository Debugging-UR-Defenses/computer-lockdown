"""
Windows Group Policy / Registry integration for Computer Lockdown.

Applies and removes security-related policies (e.g. disabling Task
Manager, Command Prompt, Registry Editor) by writing to the
``HKEY_CURRENT_USER`` registry hive.  All modifications are reversible
and tracked via the configuration.

On non-Windows platforms the module logs warnings and operates in
dry-run mode so that the rest of the application can be developed and
tested without a Windows machine.
"""

import logging
import platform
from typing import Any, Optional

from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# winreg import (Windows only)
# ---------------------------------------------------------------------------

_WINREG_AVAILABLE = False

try:
    import winreg  # type: ignore[import-not-found]
    _WINREG_AVAILABLE = True
except ImportError:
    logger.warning(
        "winreg unavailable — PolicyManager will operate in dry-run mode."
    )


# ---------------------------------------------------------------------------
# Policy definitions
# ---------------------------------------------------------------------------

# Each entry maps a friendly policy name to the registry path (relative
# to HKEY_CURRENT_USER), value name, and the DWORD value that enables the
# restriction.
POLICIES: dict[str, dict[str, Any]] = {
    "block_task_manager": {
        "path": r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
        "key": "DisableTaskMgr",
        "value": 1,
    },
    "block_cmd": {
        "path": r"Software\Policies\Microsoft\Windows\System",
        "key": "DisableCMD",
        "value": 1,
    },
    "block_registry_editor": {
        "path": r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
        "key": "DisableRegistryTools",
        "value": 1,
    },
    "block_control_panel": {
        "path": r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer",
        "key": "NoControlPanel",
        "value": 1,
    },
    "block_settings": {
        "path": r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer",
        "key": "NoControlPanel",
        "value": 1,
    },
}


# ---------------------------------------------------------------------------
# PolicyManager
# ---------------------------------------------------------------------------

class PolicyManager:
    """Manages Windows security policies via registry modifications.

    Only policies that are **enabled** in the configuration (under the
    ``policy`` key) are applied.  For example, if
    ``config.get("policy.block_task_manager")`` is ``True`` the
    ``DisableTaskMgr`` DWORD value will be written to
    ``HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System``.

    Policies are always written to ``HKEY_CURRENT_USER`` so that they
    affect only the target (child) user account.
    """

    # Expose the class-level policy definitions as an instance attribute
    # for convenience and testability.
    POLICIES = POLICIES

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config: ConfigManager = config_manager

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def apply_policies(self) -> None:
        """Apply all policies that are enabled in the configuration."""
        for policy_name in self.POLICIES:
            enabled: bool = self.config.get(f"policy.{policy_name}", False)
            if enabled:
                self.apply_policy(policy_name)
            else:
                # Ensure a disabled policy is not left lingering.
                self.remove_policy(policy_name)

    def remove_policies(self) -> None:
        """Remove **all** Computer Lockdown policies from the registry,
        regardless of their enabled state in the configuration."""
        for policy_name in self.POLICIES:
            self.remove_policy(policy_name)

    # ------------------------------------------------------------------
    # Single-policy operations
    # ------------------------------------------------------------------

    def apply_policy(self, policy_name: str) -> None:
        """Apply a single policy by writing its registry value.

        Parameters
        ----------
        policy_name:
            One of the keys in ``POLICIES``, e.g. ``"block_task_manager"``.
        """
        policy = self.POLICIES.get(policy_name)
        if policy is None:
            logger.warning("Unknown policy: %s", policy_name)
            return

        reg_path: str = policy["path"]
        reg_key: str = policy["key"]
        reg_value: int = policy["value"]

        if not _WINREG_AVAILABLE:
            logger.warning(
                "Dry-run: would set HKCU\\%s\\%s = %d (policy %s)",
                reg_path, reg_key, reg_value, policy_name,
            )
            return

        try:
            key_handle = winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER,
                reg_path,
                0,
                winreg.KEY_SET_VALUE,
            )
            with key_handle:
                winreg.SetValueEx(key_handle, reg_key, 0, winreg.REG_DWORD, reg_value)
            logger.info("Policy applied: %s (HKCU\\%s\\%s = %d)", policy_name, reg_path, reg_key, reg_value)
        except PermissionError:
            logger.error(
                "Permission denied setting registry value for policy %s. "
                "Run as administrator.", policy_name,
            )
        except OSError as exc:
            logger.error("Failed to apply policy %s: %s", policy_name, exc)

    def remove_policy(self, policy_name: str) -> None:
        """Remove a single policy by deleting its registry value.

        Parameters
        ----------
        policy_name:
            One of the keys in ``POLICIES``.
        """
        policy = self.POLICIES.get(policy_name)
        if policy is None:
            logger.warning("Unknown policy: %s", policy_name)
            return

        reg_path: str = policy["path"]
        reg_key: str = policy["key"]

        if not _WINREG_AVAILABLE:
            logger.warning(
                "Dry-run: would delete HKCU\\%s\\%s (policy %s)",
                reg_path, reg_key, policy_name,
            )
            return

        try:
            key_handle = winreg.OpenKeyEx(
                winreg.HKEY_CURRENT_USER,
                reg_path,
                0,
                winreg.KEY_SET_VALUE,
            )
            with key_handle:
                winreg.DeleteValue(key_handle, reg_key)
            logger.info("Policy removed: %s (deleted HKCU\\%s\\%s)", policy_name, reg_path, reg_key)
        except FileNotFoundError:
            # Value or key does not exist — nothing to remove.
            logger.debug("Policy %s was not applied (value not found).", policy_name)
        except PermissionError:
            logger.error(
                "Permission denied removing registry value for policy %s.", policy_name,
            )
        except OSError as exc:
            logger.error("Failed to remove policy %s: %s", policy_name, exc)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def is_policy_applied(self, policy_name: str) -> bool:
        """Check if a specific policy is currently applied in the registry.

        Parameters
        ----------
        policy_name:
            One of the keys in ``POLICIES``.

        Returns
        -------
        bool
            ``True`` if the registry value exists and matches the
            expected restriction value.
        """
        policy = self.POLICIES.get(policy_name)
        if policy is None:
            return False

        if not _WINREG_AVAILABLE:
            logger.debug(
                "Dry-run: cannot query registry for policy %s.", policy_name
            )
            return False

        reg_path: str = policy["path"]
        reg_key: str = policy["key"]
        expected: int = policy["value"]

        try:
            key_handle = winreg.OpenKeyEx(
                winreg.HKEY_CURRENT_USER,
                reg_path,
                0,
                winreg.KEY_READ,
            )
            with key_handle:
                value, reg_type = winreg.QueryValueEx(key_handle, reg_key)
                return value == expected
        except FileNotFoundError:
            return False
        except OSError:
            return False

    def get_policy_status(self) -> dict[str, bool]:
        """Return a dict mapping each policy name to its applied status.

        Example return value::

            {
                "block_task_manager": True,
                "block_cmd": False,
                "block_registry_editor": True,
                "block_control_panel": False,
                "block_settings": False,
            }
        """
        return {name: self.is_policy_applied(name) for name in self.POLICIES}
