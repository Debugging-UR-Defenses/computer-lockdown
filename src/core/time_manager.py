"""
Time-limit and schedule enforcement for Computer Lockdown.

Tracks cumulative daily usage, compares it against the configured daily
limit, and checks whether the current wall-clock time falls inside the
allowed schedule window for today.  When limits are reached (or nearly
reached) the manager fires registered callbacks so the UI / service
layer can react (show warnings, lock the workstation, etc.).
"""

import logging
import platform
import threading
import time
from datetime import datetime, date
from typing import Callable, Optional

from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Windows workstation lock helper
# ---------------------------------------------------------------------------

_LOCK_WORKSTATION: Optional[Callable[[], bool]] = None

try:
    import ctypes
    _user32 = ctypes.windll.user32  # type: ignore[attr-defined]

    def _lock_workstation() -> bool:
        """Lock the Windows workstation via ``user32.LockWorkStation``."""
        result = _user32.LockWorkStation()
        if result:
            logger.info("Workstation locked successfully.")
        else:
            logger.warning("LockWorkStation call failed.")
        return bool(result)

    _LOCK_WORKSTATION = _lock_workstation

except (AttributeError, OSError):
    logger.warning(
        "Windows user32 unavailable — workstation lock will be a no-op."
    )

    def _lock_workstation_stub() -> bool:  # pragma: no cover
        logger.warning("Dry-run: would lock the workstation.")
        return False

    _LOCK_WORKSTATION = _lock_workstation_stub

# Day-name mapping (datetime.strftime('%A').lower() → config key)
_DAY_NAMES = [
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday",
]

# Warning is triggered when remaining time is at or below this threshold.
_WARNING_THRESHOLD_MINUTES: int = 10


class TimeManager:
    """Manages daily time limits and scheduled usage windows.

    The manager runs a background thread that wakes every
    ``CHECK_INTERVAL`` seconds.  On each tick it:

    1. Resets the daily usage counter if the date has changed.
    2. Increments the usage counter.
    3. Checks whether the current wall-clock time falls within the
       schedule window for today.
    4. Checks whether cumulative usage has exceeded the daily limit.
    5. Fires the ``"warning"`` or ``"lockout"`` callback as appropriate.
    """

    CHECK_INTERVAL: float = 30.0  # seconds between checks

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config: ConfigManager = config_manager
        self.running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._session_start: Optional[datetime] = None
        self._today_usage: int = 0  # minutes used today
        self._callbacks: dict[str, Optional[Callable]] = {
            "warning": None,
            "lockout": None,
        }
        self._last_check_date: Optional[date] = None
        self._lock: threading.Lock = threading.Lock()
        self._warning_fired: bool = False
        self._lockout_fired: bool = False

        # Restore persisted usage for today if available.
        self._restore_usage()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start time tracking in a background thread (30-second ticks)."""
        if self.running:
            logger.debug("TimeManager already running.")
            return

        self.running = True
        self._session_start = datetime.now()
        self._last_check_date = date.today()
        self._warning_fired = False
        self._lockout_fired = False
        self._thread = threading.Thread(
            target=self._tracking_loop,
            name="TimeManager",
            daemon=True,
        )
        self._thread.start()
        logger.info("TimeManager started.")

    def stop(self) -> None:
        """Stop time tracking and persist today's usage."""
        self.running = False
        self._persist_usage()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("TimeManager stopped.")

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _tracking_loop(self) -> None:
        """Background thread entry point."""
        while self.running:
            try:
                if self.config.get("time_limits.enabled", True):
                    self.check_time()
            except Exception:
                logger.exception("Error in TimeManager loop.")
            time.sleep(self.CHECK_INTERVAL)

    def check_time(self) -> None:
        """Evaluate the current time against the schedule and daily limit.

        * If the date has rolled over, the daily usage counter is reset.
        * If usage is within ``_WARNING_THRESHOLD_MINUTES`` of the limit
          the ``"warning"`` callback is fired.
        * If usage exceeds the limit **or** the current time is outside
          the allowed schedule, the ``"lockout"`` callback is fired.
        """
        now = datetime.now()
        today = now.date()

        with self._lock:
            # Date rollover — reset counters.
            if self._last_check_date is not None and today != self._last_check_date:
                logger.info("Date changed — resetting daily usage.")
                self.reset_daily_usage()
            self._last_check_date = today

            # Increment usage by roughly the check interval (in minutes).
            self._today_usage += max(1, int(self.CHECK_INTERVAL / 60))
            self._persist_usage()

        daily_limit: int = self.config.get("time_limits.daily_limit_minutes", 120)
        remaining = daily_limit - self._today_usage

        # --- Check 1: Outside allowed schedule? ---
        if not self.is_within_schedule():
            logger.info("Current time is outside the allowed schedule.")
            if not self._lockout_fired:
                self._lockout_fired = True
                self._fire_callback("lockout")
            return

        # --- Check 2: Daily limit exceeded? ---
        if remaining <= 0:
            logger.info("Daily time limit exceeded (%d min used).", self._today_usage)
            if not self._lockout_fired:
                self._lockout_fired = True
                self._fire_callback("lockout")
            return

        # --- Check 3: Approaching limit (warning)? ---
        if remaining <= _WARNING_THRESHOLD_MINUTES:
            logger.info("%d minute(s) remaining before daily limit.", remaining)
            if not self._warning_fired:
                self._warning_fired = True
                self._fire_callback("warning")

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------

    def get_remaining_time(self) -> int:
        """Return the remaining minutes for today (may be negative)."""
        daily_limit: int = self.config.get("time_limits.daily_limit_minutes", 120)
        return daily_limit - self._today_usage

    def get_today_usage(self) -> int:
        """Return minutes used today."""
        return self._today_usage

    def reset_daily_usage(self) -> None:
        """Reset the daily usage counter and associated flags."""
        with self._lock:
            self._today_usage = 0
            self._warning_fired = False
            self._lockout_fired = False
        self._persist_usage()
        logger.info("Daily usage counter reset.")

    def is_within_schedule(self) -> bool:
        """Check if the current wall-clock time is within today's allowed hours.

        Returns ``True`` if there is no schedule configured for today
        (i.e. unrestricted).
        """
        now = datetime.now()
        day_name = _DAY_NAMES[now.weekday()]

        schedule: Optional[dict] = self.config.get(
            f"time_limits.schedule.{day_name}"
        )
        if schedule is None:
            # No schedule for today → unrestricted.
            return True

        start_str: Optional[str] = schedule.get("start")
        end_str: Optional[str] = schedule.get("end")
        if not start_str or not end_str:
            return True

        try:
            start_time = datetime.strptime(start_str, "%H:%M").time()
            end_time = datetime.strptime(end_str, "%H:%M").time()
        except ValueError:
            logger.warning(
                "Invalid schedule format for %s: start=%r end=%r",
                day_name, start_str, end_str,
            )
            return True

        current_time = now.time()
        return start_time <= current_time <= end_time

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def set_warning_callback(self, callback: Callable) -> None:
        """Set the function to call when nearing the time limit."""
        self._callbacks["warning"] = callback

    def set_lockout_callback(self, callback: Callable) -> None:
        """Set the function to call when time is up / outside schedule."""
        self._callbacks["lockout"] = callback

    def on_lockout(self) -> None:
        """Default lockout handler: lock the Windows workstation.

        Can be overridden or replaced via ``set_lockout_callback``.
        """
        logger.info("Lockout triggered — locking workstation.")
        if _LOCK_WORKSTATION is not None:
            _LOCK_WORKSTATION()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fire_callback(self, name: str) -> None:
        """Fire a named callback, falling back to ``on_lockout`` for lockouts."""
        cb = self._callbacks.get(name)
        if cb is not None:
            try:
                cb()
            except Exception:
                logger.exception("Error in %s callback.", name)
        elif name == "lockout":
            self.on_lockout()

    def _persist_usage(self) -> None:
        """Save today's usage to config so it survives restarts."""
        today_str = date.today().isoformat()
        self.config.set("usage_log.daily_usage_minutes", {today_str: self._today_usage})
        self.config.set("usage_log.last_reset_date", today_str)

    def _restore_usage(self) -> None:
        """Restore persisted daily usage if it belongs to today."""
        today_str = date.today().isoformat()
        last_reset = self.config.get("usage_log.last_reset_date", "")
        if last_reset == today_str:
            usage_dict: dict = self.config.get("usage_log.daily_usage_minutes", {})
            self._today_usage = usage_dict.get(today_str, 0)
            logger.info("Restored today's usage: %d minutes.", self._today_usage)
        else:
            self._today_usage = 0
