"""
Application whitelist enforcement for Computer Lockdown.

Monitors running processes and terminates any that are not on the
configured whitelist or in the set of Windows-critical system processes.
"""

import logging
import os
import threading
import time
from datetime import datetime
from typing import Optional

from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System-critical processes that must NEVER be killed, regardless of the
# whitelist.  Compared case-insensitively against process executable names.
# ---------------------------------------------------------------------------
SYSTEM_CRITICAL_PROCESSES: set[str] = {
    "svchost.exe",
    "csrss.exe",
    "lsass.exe",
    "winlogon.exe",
    "services.exe",
    "smss.exe",
    "system",
    "system idle process",
    "dwm.exe",
    "sihost.exe",
    "taskhostw.exe",
    "runtimebroker.exe",
    "explorer.exe",
    "searchhost.exe",
    "startmenuexperiencehost.exe",
    "shellexperiencehost.exe",
    "ctfmon.exe",
    "fontdrvhost.exe",
    "dllhost.exe",
    "conhost.exe",
    "wmiprvse.exe",
    "wininit.exe",
    "lsaiso.exe",
    "securityhealthservice.exe",
    "msmpeng.exe",          # Windows Defender antimalware
    "nissrv.exe",           # Windows Defender network inspection
    "textinputhost.exe",
    "applicationframehost.exe",
    "lockapp.exe",
    "logonui.exe",
    "comppkgsrv.exe",
    "spoolsv.exe",
}

# Our own executable name(s) so we never kill ourselves.
_OWN_PROCESS_NAMES: set[str] = {
    "computerlockdown.exe",
    "computer-lockdown.exe",
    "computer_lockdown.exe",
    "python.exe",
    "pythonw.exe",
}

# ---------------------------------------------------------------------------
# Dangerous system tools that should be terminated even if whitelisted.
# A child could use these to bypass lockdown restrictions.
# ---------------------------------------------------------------------------
BLOCKED_SYSTEM_TOOLS: set[str] = {
    "powershell.exe",
    "powershell_ise.exe",
    "pwsh.exe",              # PowerShell Core
    "cmd.exe",
    "wt.exe",                # Windows Terminal
    "wscript.exe",           # Windows Script Host
    "cscript.exe",           # Command-line script host
    "mshta.exe",             # HTML Application host
    "certutil.exe",          # Can download files
    "bitsadmin.exe",         # Background transfer — downloads files
    "reg.exe",               # Command-line registry editor
    "regedit.exe",           # Registry editor
    "sc.exe",                # Service control
    "net.exe",               # Network commands
    "net1.exe",              # Network commands (alt)
    "wsl.exe",               # Windows Subsystem for Linux
    "bash.exe",              # WSL bash
    "ubuntu.exe",            # WSL Ubuntu
    "taskmgr.exe",           # Task Manager
    "taskkill.exe",          # Process killer
    "tskill.exe",            # Terminal Services process killer
    "mmc.exe",               # Management console
    "msconfig.exe",          # System config
    "eventvwr.exe",          # Event viewer
}

# ---------------------------------------------------------------------------
# Windows process helpers (ctypes / subprocess)
# ---------------------------------------------------------------------------

try:
    import ctypes
    import ctypes.wintypes

    _kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    _psapi = ctypes.windll.psapi  # type: ignore[attr-defined]

    # Constants
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    PROCESS_TERMINATE = 0x0001
    MAX_PATH = 260

    _WINDOWS_AVAILABLE = True
except (AttributeError, OSError):
    _WINDOWS_AVAILABLE = False
    logger.warning(
        "Windows APIs unavailable — AppMonitor will run in dry-run mode."
    )


def _enum_process_ids() -> list[int]:
    """Return a list of all running process IDs using the Windows PSAPI."""
    if not _WINDOWS_AVAILABLE:
        return []

    count = 1024
    while True:
        arr = (ctypes.wintypes.DWORD * count)()
        bytes_returned = ctypes.wintypes.DWORD()
        success = _psapi.EnumProcesses(
            ctypes.byref(arr),
            ctypes.sizeof(arr),
            ctypes.byref(bytes_returned),
        )
        if not success:
            logger.error("EnumProcesses failed.")
            return []

        num_pids = bytes_returned.value // ctypes.sizeof(ctypes.wintypes.DWORD)
        if num_pids < count:
            return list(arr[:num_pids])
        # Buffer was too small — double and retry.
        count *= 2


def _get_process_name(pid: int) -> Optional[str]:
    """Return the executable name for *pid*, or ``None`` on failure."""
    if not _WINDOWS_AVAILABLE:
        return None

    handle = _kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not handle:
        return None

    try:
        buf = (ctypes.c_char * MAX_PATH)()
        if _psapi.GetModuleBaseNameA(handle, None, ctypes.byref(buf), MAX_PATH):
            return buf.value.decode("utf-8", errors="replace")
        return None
    finally:
        _kernel32.CloseHandle(handle)


def _get_process_path(pid: int) -> Optional[str]:
    """Return the full image path for *pid*, or ``None`` on failure."""
    if not _WINDOWS_AVAILABLE:
        return None

    handle = _kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not handle:
        return None

    try:
        buf = (ctypes.c_char * MAX_PATH)()
        if _psapi.GetModuleFileNameExA(handle, None, ctypes.byref(buf), MAX_PATH):
            return buf.value.decode("utf-8", errors="replace")
        return None
    finally:
        _kernel32.CloseHandle(handle)


def _terminate_process(pid: int) -> bool:
    """Terminate a process by *pid*.  Returns ``True`` on success."""
    if not _WINDOWS_AVAILABLE:
        logger.warning("Dry-run: would terminate PID %d", pid)
        return False

    handle = _kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
    if not handle:
        logger.debug("Could not open PID %d for termination.", pid)
        return False

    try:
        result = _kernel32.TerminateProcess(handle, 1)
        if result:
            logger.info("Terminated PID %d.", pid)
            return True
        logger.warning("TerminateProcess failed for PID %d.", pid)
        return False
    finally:
        _kernel32.CloseHandle(handle)


# ---------------------------------------------------------------------------
# AppMonitor
# ---------------------------------------------------------------------------

class AppMonitor:
    """Monitors running processes and kills any not in the whitelist.

    The monitor runs a background thread that polls the process list every
    ``CHECK_INTERVAL`` seconds and terminates anything that is neither a
    system-critical process nor present on the user-configured whitelist.
    """

    CHECK_INTERVAL: float = 2.0  # seconds between scans

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config: ConfigManager = config_manager
        self.running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._kill_log: list[dict] = []  # Track what was killed
        self._lock: threading.Lock = threading.Lock()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start monitoring in a background thread.  Check every 2 seconds."""
        if self.running:
            logger.debug("AppMonitor already running.")
            return

        self.running = True
        self._thread = threading.Thread(
            target=self._monitor_loop,
            name="AppMonitor",
            daemon=True,
        )
        self._thread.start()
        logger.info("AppMonitor started.")

    def stop(self) -> None:
        """Stop monitoring."""
        self.running = False
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("AppMonitor stopped.")

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _monitor_loop(self) -> None:
        """Background thread entry point."""
        while self.running:
            try:
                if self.config.get("app_whitelist.enabled", True):
                    self.check_processes()
            except Exception:
                logger.exception("Error in AppMonitor loop.")
            time.sleep(self.CHECK_INTERVAL)

    def check_processes(self) -> None:
        """Check all running processes against the whitelist.

        Non-whitelisted processes are terminated and the event is logged.
        """
        pids = _enum_process_ids()
        own_pid = os.getpid()

        for pid in pids:
            if pid == 0 or pid == own_pid:
                continue

            proc_name = _get_process_name(pid)
            if proc_name is None:
                # Cannot read — probably a protected system process.  Skip.
                continue

            proc_path = _get_process_path(pid) or ""

            if not self.is_process_allowed(proc_name, proc_path):
                logger.info(
                    "Killing non-whitelisted process: %s (PID %d)", proc_name, pid
                )
                killed = _terminate_process(pid)
                if killed:
                    entry = {
                        "timestamp": datetime.now().isoformat(),
                        "process_name": proc_name,
                        "process_path": proc_path,
                        "pid": pid,
                    }
                    with self._lock:
                        self._kill_log.append(entry)
                        # Keep only the most recent 500 entries.
                        if len(self._kill_log) > 500:
                            self._kill_log = self._kill_log[-500:]

    def is_process_allowed(self, process_name: str, process_path: str) -> bool:
        """Check if a process is in the whitelist or is a system process.

        Parameters
        ----------
        process_name:
            Executable name, e.g. ``"chrome.exe"``.
        process_path:
            Full path to the executable, e.g. ``"C:\\Program Files\\...\\chrome.exe"``.

        Returns
        -------
        bool
            ``True`` if the process should be kept alive.
        """
        name_lower = process_name.lower()

        # Dangerous system tools are always blocked (unless in admin mode).
        if name_lower in BLOCKED_SYSTEM_TOOLS:
            if not self.config.get("admin_mode", False):
                return False

        # 1. Always allow system-critical processes.
        if name_lower in SYSTEM_CRITICAL_PROCESSES:
            return True

        # 2. Always allow our own process.
        if name_lower in _OWN_PROCESS_NAMES:
            return True

        # 3. Check the user-configured app whitelist.
        allowed_apps: list[dict] = self.config.get("app_whitelist.allowed_apps", [])
        for app_entry in allowed_apps:
            app_path: str = app_entry.get("path", "")
            # Simple exe-name match (case-insensitive).
            if app_path and app_path.lower() == name_lower:
                return True
            # Full path match — the whitelist might store a full path.
            if app_path and process_path:
                if os.path.normcase(app_path) == os.path.normcase(process_path):
                    return True
                # Check if the whitelist entry is just the filename portion
                # and it matches the basename of the running process path.
                if os.path.basename(process_path).lower() == app_path.lower():
                    return True

        # 4. Check the service whitelist.
        allowed_services: list[dict] = self.config.get("app_whitelist.allowed_services", [])
        for svc in allowed_services:
            svc_path: str = svc.get("path", "")
            if not svc_path:
                continue
            if name_lower == svc_path.lower():
                return True
            if process_path and svc_path.lower() in process_path.lower():
                return True

        return False

    # ------------------------------------------------------------------
    # Dependency detection
    # ------------------------------------------------------------------

    def detect_app_dependencies(self, app_path: str) -> list[dict]:
        """Scan running processes to find potential dependencies of an app.

        Looks for processes running from the same directory tree as the given app.
        Returns list of dicts with name, path, parent_app keys.
        """
        if not app_path:
            return []

        app_dir = os.path.dirname(app_path).lower()
        if not app_dir:
            return []

        dependencies = []
        pids = _enum_process_ids()
        own_pid = os.getpid()
        seen_names: set[str] = set()

        for pid in pids:
            if pid == 0 or pid == own_pid:
                continue
            proc_name = _get_process_name(pid)
            proc_path = _get_process_path(pid)
            if not proc_name or not proc_path:
                continue

            proc_name_lower = proc_name.lower()
            if proc_name_lower in seen_names:
                continue

            # Skip system processes and already-whitelisted apps
            if proc_name_lower in SYSTEM_CRITICAL_PROCESSES:
                continue
            if proc_name_lower in _OWN_PROCESS_NAMES:
                continue

            # Check if this process is in the same directory tree
            proc_dir = os.path.dirname(proc_path).lower()
            if proc_dir.startswith(app_dir) or app_dir.startswith(proc_dir):
                seen_names.add(proc_name_lower)
                app_name = os.path.basename(app_path)
                dependencies.append({
                    "name": proc_name.replace(".exe", ""),
                    "path": proc_name,
                    "parent_app": app_name.replace(".exe", ""),
                })

        return dependencies

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_kill_log(self) -> list[dict]:
        """Return a copy of recent kill-log entries.

        Each entry is a dict with keys ``timestamp``, ``process_name``,
        ``process_path``, and ``pid``.
        """
        with self._lock:
            return list(self._kill_log)
