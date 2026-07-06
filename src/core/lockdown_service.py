"""
Main coordinator service for Computer Lockdown.

``LockdownService`` owns instances of every enforcement component and
provides a single entry-point for activating, deactivating, and
querying the lockdown state.  It also handles the admin-mode workflow
(password verification, temporary suspension of restrictions).
"""

import logging
from typing import Callable, Optional

from ..utils.config import ConfigManager
from ..utils.crypto import verify_password
from .app_monitor import AppMonitor
from .web_blocker import WebBlocker
from .time_manager import TimeManager
from .download_blocker import DownloadBlocker
from .policy_manager import PolicyManager

logger = logging.getLogger(__name__)


class LockdownService:
    """Main service that coordinates all lockdown components.

    Typical lifecycle::

        cfg = ConfigManager()
        cfg.load()
        svc = LockdownService(cfg)
        svc.start_lockdown()
        ...
        if svc.enter_admin_mode("s3cret"):
            # All restrictions temporarily lifted.
            ...
            svc.exit_admin_mode()
        ...
        svc.stop_lockdown()
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config: ConfigManager = config_manager

        # Enforcement components
        self.app_monitor: AppMonitor = AppMonitor(config_manager)
        self.web_blocker: WebBlocker = WebBlocker(config_manager)
        self.time_manager: TimeManager = TimeManager(config_manager)
        self.download_blocker: DownloadBlocker = DownloadBlocker(config_manager)
        self.policy_manager: PolicyManager = PolicyManager(config_manager)

        self._admin_mode: bool = False
        self._status_callbacks: list[Callable] = []

    # ------------------------------------------------------------------
    # Lockdown lifecycle
    # ------------------------------------------------------------------

    def start_lockdown(self) -> None:
        """Activate all enabled lockdown features.

        Components that are individually disabled in the configuration
        will skip their activation logic internally but are still
        started so they can react if later enabled.
        """
        logger.info("Starting lockdown...")
        self._admin_mode = False
        self.config.set("admin_mode", False)

        # App whitelist enforcement
        if self.config.get("app_whitelist.enabled", True):
            self.app_monitor.start()
            logger.info("  App monitor: ACTIVE")
        else:
            logger.info("  App monitor: disabled in config")

        # Website blocking
        if self.config.get("web_blocking.enabled", True):
            self.web_blocker.activate()
            logger.info("  Web blocker: ACTIVE")
        else:
            logger.info("  Web blocker: disabled in config")

        # Time limits
        if self.config.get("time_limits.enabled", True):
            self.time_manager.start()
            logger.info("  Time manager: ACTIVE")
        else:
            logger.info("  Time manager: disabled in config")

        # Download blocking
        if self.config.get("download_blocking.enabled", True):
            self.download_blocker.start()
            logger.info("  Download blocker: ACTIVE")
        else:
            logger.info("  Download blocker: disabled in config")

        # Registry policies
        self.policy_manager.apply_policies()
        logger.info("  Policy manager: policies applied")

        self._notify_status_change()
        logger.info("Lockdown started.")

    def stop_lockdown(self) -> None:
        """Deactivate all lockdown features.

        This is called when entering admin mode or during application
        shutdown.  All monitors are stopped, hosts-file entries are
        removed, and registry policies are reverted.
        """
        logger.info("Stopping lockdown...")

        self.app_monitor.stop()
        self.web_blocker.deactivate()
        self.time_manager.stop()
        self.download_blocker.stop()
        self.policy_manager.remove_policies()

        self._notify_status_change()
        logger.info("Lockdown stopped.")

    # ------------------------------------------------------------------
    # Admin mode
    # ------------------------------------------------------------------

    def enter_admin_mode(self, password: str) -> bool:
        """Verify the supplied password and enter admin mode if correct.

        In admin mode **all** restrictions are temporarily suspended so
        that a parent / administrator can change settings.

        Parameters
        ----------
        password:
            The plain-text password to verify against the stored hash.

        Returns
        -------
        bool
            ``True`` if the password matched and admin mode is now
            active.
        """
        stored_hash: str = self.config.get("admin_password_hash", "")
        if not stored_hash:
            logger.warning(
                "No admin password hash configured — "
                "refusing admin mode for security."
            )
            return False

        if not verify_password(password, stored_hash):
            logger.warning("Admin mode: incorrect password.")
            return False

        logger.info("Admin mode: password accepted — suspending lockdown.")
        self.stop_lockdown()
        self._admin_mode = True
        self.config.set("admin_mode", True)
        self._notify_status_change()
        return True

    def exit_admin_mode(self) -> None:
        """Exit admin mode and re-engage all lockdown features."""
        logger.info("Exiting admin mode — re-engaging lockdown.")
        self._admin_mode = False
        self.config.set("admin_mode", False)
        self.start_lockdown()

    def is_admin_mode(self) -> bool:
        """Return ``True`` if the service is currently in admin mode."""
        return self._admin_mode

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, dict[str, bool]]:
        """Return a status dict for every component.

        Returns
        -------
        dict
            Mapping of ``component_name`` to
            ``{"enabled": bool, "active": bool}``.

        Example::

            {
                "app_monitor":      {"enabled": True,  "active": True},
                "web_blocker":      {"enabled": True,  "active": True},
                "time_manager":     {"enabled": True,  "active": False},
                "download_blocker": {"enabled": False, "active": False},
                "policy_manager":   {"enabled": True,  "active": True},
            }
        """
        policy_status = self.policy_manager.get_policy_status()
        any_policy_enabled = any(
            self.config.get(f"policy.{p}", False) for p in self.policy_manager.POLICIES
        )
        any_policy_active = any(policy_status.values())

        return {
            "app_monitor": {
                "enabled": self.config.get("app_whitelist.enabled", False),
                "active": self.app_monitor.running,
            },
            "web_blocker": {
                "enabled": self.config.get("web_blocking.enabled", False),
                "active": self.web_blocker.is_active(),
            },
            "time_manager": {
                "enabled": self.config.get("time_limits.enabled", False),
                "active": self.time_manager.running,
            },
            "download_blocker": {
                "enabled": self.config.get("download_blocking.enabled", False),
                "active": self.download_blocker.running,
            },
            "policy_manager": {
                "enabled": any_policy_enabled,
                "active": any_policy_active,
            },
        }

    def add_status_callback(self, callback: Callable) -> None:
        """Register a callback that will be invoked on status changes.

        The callback receives no arguments; call ``get_status()``
        inside it to inspect the new state.
        """
        if callback not in self._status_callbacks:
            self._status_callbacks.append(callback)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _notify_status_change(self) -> None:
        """Invoke all registered status-change callbacks."""
        for cb in self._status_callbacks:
            try:
                cb()
            except Exception:
                logger.exception("Error in status callback.")


