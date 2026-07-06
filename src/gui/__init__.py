"""
GUI package for Computer Lockdown.

Re-exports the main classes so callers can do::

    from src.gui import ComputerLockdownApp, Theme
"""

from .theme import Theme
from .login_screen import LoginScreen
from .dashboard import Dashboard
from .app_manager_gui import AppManagerPage
from .web_manager_gui import WebManagerPage
from .time_manager_gui import TimeManagerPage
from .settings_gui import SettingsPage
from .downloads_gui import DownloadsManagerPage
from .policies_gui import PoliciesManagerPage
from .app import ComputerLockdownApp

__all__ = [
    "Theme",
    "LoginScreen",
    "Dashboard",
    "AppManagerPage",
    "WebManagerPage",
    "TimeManagerPage",
    "SettingsPage",
    "DownloadsManagerPage",
    "PoliciesManagerPage",
    "ComputerLockdownApp",
]
