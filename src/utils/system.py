"""
System utilities for Computer Lockdown.

Provides helpers for process management, privilege checks, Windows startup
registration, and workstation locking.  All Windows-specific calls are guarded
so the module can be imported on non-Windows platforms (macOS / Linux) during
development — missing functionality logs a warning instead of crashing.
"""

import logging
import os
import platform
import subprocess
import sys
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

_IS_WINDOWS: bool = platform.system() == "Windows"

if _IS_WINDOWS:
    import ctypes
    import ctypes.wintypes

    try:
        import winreg  # noqa: F401 — used in startup helpers
    except ImportError:
        winreg = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Public API — platform info
# ---------------------------------------------------------------------------

def is_windows() -> bool:
    """Return ``True`` when running on a Windows operating system."""
    return _IS_WINDOWS


def get_system_drive() -> str:
    """Return the system drive letter (e.g. ``C:\\\\``).

    Falls back to ``C:\\\\`` when the ``SystemDrive`` environment variable is
    not set.
    """
    if _IS_WINDOWS:
        return os.environ.get("SystemDrive", "C:") + "\\"
    logger.warning("get_system_drive() called on non-Windows platform.")
    return "/"


def get_hosts_file_path() -> str:
    """Return the full path to the system ``hosts`` file."""
    if _IS_WINDOWS:
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        return os.path.join(system_root, "System32", "drivers", "etc", "hosts")
    # macOS / Linux
    return "/etc/hosts"


# ---------------------------------------------------------------------------
# Privilege management
# ---------------------------------------------------------------------------

def is_admin() -> bool:
    """Return ``True`` if the current process has administrator / root privileges."""
    if _IS_WINDOWS:
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
        except Exception:
            return False
    # Unix-like
    return os.getuid() == 0


def request_admin() -> None:
    """Re-launch the current script with elevated (UAC) privileges.

    On Windows this uses ``ShellExecuteW`` with the *runas* verb.  The current
    process continues running after the call — the caller should typically exit
    after invoking this function.

    On non-Windows platforms a warning is logged and nothing happens.
    """
    if not _IS_WINDOWS:
        logger.warning("request_admin() is only supported on Windows.")
        return

    script = os.path.abspath(sys.argv[0])
    params = " ".join(f'"{a}"' for a in sys.argv[1:])
    executable = sys.executable

    logger.info("Requesting UAC elevation for: %s %s %s", executable, script, params)

    try:
        ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None,       # hwnd
            "runas",    # operation
            executable, # file
            f'"{script}" {params}',  # parameters
            None,       # directory
            1,          # SW_SHOWNORMAL
        )
    except Exception as exc:
        logger.error("Failed to request admin privileges: %s", exc)


# ---------------------------------------------------------------------------
# Process management
# ---------------------------------------------------------------------------

def get_running_processes() -> list[dict[str, Any]]:
    """Return a list of currently running processes.

    Each entry is a dict with keys ``pid`` (int), ``name`` (str), and
    ``exe`` (str — full path when available, otherwise empty string).

    Uses :mod:`psutil` when available; otherwise falls back to
    ``tasklist.exe`` on Windows.
    """
    # Try psutil first (cross-platform, richer info)
    try:
        import psutil  # type: ignore[import-untyped]

        result: list[dict[str, Any]] = []
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                info = proc.info  # type: ignore[attr-defined]
                result.append({
                    "pid": info.get("pid", 0),
                    "name": info.get("name", ""),
                    "exe": info.get("exe", "") or "",
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return result
    except ImportError:
        pass

    # Fallback: tasklist on Windows
    if _IS_WINDOWS:
        return _tasklist_fallback()

    logger.warning("get_running_processes() has limited support on non-Windows without psutil.")
    return []


def _tasklist_fallback() -> list[dict[str, Any]]:
    """Parse ``tasklist /FO CSV`` output into a process list."""
    try:
        output = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"],
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if _IS_WINDOWS else 0,  # type: ignore[attr-defined]
        )
        result: list[dict[str, Any]] = []
        for line in output.strip().splitlines():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 2:
                try:
                    pid = int(parts[1])
                except ValueError:
                    pid = 0
                result.append({"pid": pid, "name": parts[0], "exe": ""})
        return result
    except Exception as exc:
        logger.error("tasklist fallback failed: %s", exc)
        return []


def kill_process(pid: int) -> None:
    """Terminate the process with the given *pid*.

    Uses :mod:`psutil` when available for a graceful kill, otherwise falls
    back to ``taskkill`` on Windows or ``os.kill`` on Unix.
    """
    try:
        import psutil  # type: ignore[import-untyped]

        proc = psutil.Process(pid)
        proc.terminate()
        logger.info("Terminated process %d (%s) via psutil.", pid, proc.name())
        return
    except ImportError:
        pass
    except Exception as exc:
        logger.error("psutil failed to kill PID %d: %s", pid, exc)
        # Fall through to OS-level fallback

    if _IS_WINDOWS:
        try:
            subprocess.check_call(
                ["taskkill", "/F", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
            )
            logger.info("Killed process %d via taskkill.", pid)
        except Exception as exc:
            logger.error("taskkill failed for PID %d: %s", pid, exc)
    else:
        import signal

        try:
            os.kill(pid, signal.SIGTERM)
            logger.info("Sent SIGTERM to process %d.", pid)
        except ProcessLookupError:
            logger.warning("Process %d does not exist.", pid)
        except PermissionError:
            logger.error("Permission denied when killing process %d.", pid)


# ---------------------------------------------------------------------------
# Windows startup registration
# ---------------------------------------------------------------------------

_STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_STARTUP_VALUE_NAME = "ComputerLockdown"


def add_to_startup(app_path: str) -> None:
    """Register *app_path* to run at Windows logon via the registry.

    Writes to ``HKCU\\...\\Run`` so admin rights are **not** required.
    """
    if not _IS_WINDOWS:
        logger.warning("add_to_startup() is only supported on Windows.")
        return

    if winreg is None:
        logger.error("winreg module is not available.")
        return

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _STARTUP_REG_KEY,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, _STARTUP_VALUE_NAME, 0, winreg.REG_SZ, f'"{app_path}"')
        winreg.CloseKey(key)
        logger.info("Added to startup: %s", app_path)
    except Exception as exc:
        logger.error("Failed to add to startup: %s", exc)


def remove_from_startup() -> None:
    """Remove the Computer Lockdown entry from Windows startup."""
    if not _IS_WINDOWS:
        logger.warning("remove_from_startup() is only supported on Windows.")
        return

    if winreg is None:
        logger.error("winreg module is not available.")
        return

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _STARTUP_REG_KEY,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, _STARTUP_VALUE_NAME)
        winreg.CloseKey(key)
        logger.info("Removed from startup.")
    except FileNotFoundError:
        logger.debug("Startup entry did not exist — nothing to remove.")
    except Exception as exc:
        logger.error("Failed to remove from startup: %s", exc)


# ---------------------------------------------------------------------------
# Workstation control
# ---------------------------------------------------------------------------

def lock_workstation() -> None:
    """Lock the Windows workstation (show the lock screen).

    Calls ``user32.LockWorkStation`` via :mod:`ctypes`.
    """
    if not _IS_WINDOWS:
        logger.warning("lock_workstation() is only supported on Windows.")
        return

    try:
        ctypes.windll.user32.LockWorkStation()  # type: ignore[attr-defined]
        logger.info("Workstation locked.")
    except Exception as exc:
        logger.error("Failed to lock workstation: %s", exc)


def log_off_user() -> None:
    """Log off the current Windows user.

    Uses ``ExitWindowsEx`` with ``EWX_LOGOFF`` (0x00) via :mod:`ctypes`.
    """
    if not _IS_WINDOWS:
        logger.warning("log_off_user() is only supported on Windows.")
        return

    EWX_LOGOFF = 0x00000000

    try:
        success = ctypes.windll.user32.ExitWindowsEx(  # type: ignore[attr-defined]
            EWX_LOGOFF, 0x0
        )
        if success:
            logger.info("User log-off initiated.")
        else:
            logger.error("ExitWindowsEx returned failure.")
    except Exception as exc:
        logger.error("Failed to log off user: %s", exc)
