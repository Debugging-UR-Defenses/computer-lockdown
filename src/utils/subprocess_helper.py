"""
Hidden subprocess execution for Computer Lockdown.

All subprocess calls should use ``run_hidden()`` instead of
``subprocess.run()`` to prevent CMD windows from flashing on Windows.
"""

import subprocess
import sys
from typing import Any


def _get_startupinfo() -> Any:
    """Return a STARTUPINFO that hides the console window on Windows."""
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        return si
    return None


def _get_creationflags() -> int:
    """Return creation flags that prevent a console window on Windows."""
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW
    return 0


def run_hidden(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
    """Run a subprocess with no visible console window.

    Drop-in replacement for ``subprocess.run()`` that automatically
    sets ``startupinfo`` and ``creationflags`` on Windows to hide
    the CMD window.
    """
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("timeout", 10)
    kwargs.setdefault("startupinfo", _get_startupinfo())
    kwargs.setdefault("creationflags", _get_creationflags())
    return subprocess.run(args, **kwargs)
