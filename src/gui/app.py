"""
Main application window for Computer Lockdown.

Creates the CustomTkinter root window, manages mode transitions between the
locked screen and the admin dashboard, and provides a system-tray icon via
:mod:`pystray` so the application stays resident when the window is closed.
"""

from __future__ import annotations

import logging
import sys
import threading
from typing import Any, Optional

import customtkinter as ctk

from .theme import Theme
from .login_screen import LoginScreen
from .dashboard import Dashboard
from .app_manager_gui import AppManagerPage
from .web_manager_gui import WebManagerPage
from .time_manager_gui import TimeManagerPage
from .settings_gui import SettingsPage
from .downloads_gui import DownloadsManagerPage
from .policies_gui import PoliciesManagerPage

logger = logging.getLogger(__name__)

# Optional system-tray support
try:
    import pystray  # type: ignore[import-untyped]
    from PIL import Image, ImageDraw  # type: ignore[import-untyped]

    _TRAY_AVAILABLE = True
except ImportError:
    _TRAY_AVAILABLE = False
    logger.info("pystray/Pillow not installed — system-tray icon disabled.")


def _create_tray_image(size: int = 64) -> "Image.Image":
    """Generate a simple padlock icon for the system tray."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Body of padlock
    body_x0, body_y0 = size * 0.2, size * 0.4
    body_x1, body_y1 = size * 0.8, size * 0.9
    draw.rounded_rectangle(
        [body_x0, body_y0, body_x1, body_y1],
        radius=size * 0.06,
        fill="#4f46e5",
    )

    # Shackle (arc)
    shackle_x0 = size * 0.3
    shackle_y0 = size * 0.1
    shackle_x1 = size * 0.7
    shackle_y1 = size * 0.55
    draw.arc(
        [shackle_x0, shackle_y0, shackle_x1, shackle_y1],
        start=180,
        end=0,
        fill="#f1f5f9",
        width=max(3, size // 12),
    )

    # Keyhole
    cx, cy = size * 0.5, size * 0.6
    r = size * 0.06
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#f1f5f9")
    draw.rectangle([cx - r * 0.5, cy, cx + r * 0.5, cy + size * 0.12], fill="#f1f5f9")

    return img


class ComputerLockdownApp:
    """Top-level application controller.

    Parameters
    ----------
    config_manager:
        A :class:`~src.utils.config.ConfigManager` instance.  The config
        must already be loaded before being passed in.
    lockdown_service:
        Optional service object that the GUI may interact with for
        enforcement.  Accepted as ``Any`` so the GUI package has no
        hard dependency on the core package.
    """

    def __init__(
        self,
        config_manager: Any,
        lockdown_service: Any = None,
    ) -> None:
        self._config = config_manager
        self._lockdown_service = lockdown_service

        self.window: Optional[ctk.CTk] = None
        self._login_screen: Optional[LoginScreen] = None
        self._dashboard: Optional[Dashboard] = None
        self._tray_icon: Optional[Any] = None
        self._is_admin: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Create the window, show the locked screen, and enter the main loop."""
        Theme.configure_customtkinter()
        self._create_window()
        self.show_locked_screen()

        if _TRAY_AVAILABLE:
            self._setup_tray_icon()

        self.window.mainloop()  # type: ignore[union-attr]

    def _create_window(self) -> None:
        """Instantiate and configure the root window."""
        self.window = ctk.CTk()
        self.window.title("Computer Lockdown")
        self.window.geometry("1200x800")
        self.window.minsize(900, 600)
        self.window.configure(fg_color=Theme.BG_DARKEST)

        # Override window-close to minimise to tray (or exit if no tray)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Centre on screen
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() - w) // 2
        y = (self.window.winfo_screenheight() - h) // 2
        self.window.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Mode transitions
    # ------------------------------------------------------------------

    def show_locked_screen(self) -> None:
        """Transition to the locked / login screen."""
        self._is_admin = False

        if self._dashboard is not None:
            self._dashboard.grid_forget()

        if self._login_screen is None:
            self._login_screen = LoginScreen(
                self.window,
                on_login_success=self._on_login_success,
                verify_callback=self._verify_password,
            )

        self._login_screen.reset()
        self._login_screen.grid(row=0, column=0, sticky="nswe")
        self.window.grid_rowconfigure(0, weight=1)  # type: ignore[union-attr]
        self.window.grid_columnconfigure(0, weight=1)  # type: ignore[union-attr]
        logger.info("Switched to locked screen.")

    def show_admin_panel(self) -> None:
        """Transition to the admin dashboard."""
        self._is_admin = True

        if self._login_screen is not None:
            self._login_screen.grid_forget()

        if self._dashboard is None:
            page_factories = {
                "apps": lambda parent: AppManagerPage(parent, self._config),
                "websites": lambda parent: WebManagerPage(parent, self._config),
                "time": lambda parent: TimeManagerPage(parent, self._config),
                "downloads": lambda parent: DownloadsManagerPage(parent, self._config),
                "policies": lambda parent: PoliciesManagerPage(parent, self._config),
                "settings": lambda parent: SettingsPage(parent, self._config),
            }
            self._dashboard = Dashboard(
                self.window,
                config_manager=self._config,
                on_lockdown=self._on_lockdown,
                page_factories=page_factories,
            )

        self._dashboard.grid(row=0, column=0, sticky="nswe")
        self._dashboard.refresh_status()
        logger.info("Switched to admin dashboard.")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_login_success(self) -> None:
        """Invoked by :class:`LoginScreen` after password verification."""
        if self._lockdown_service is not None:
            self._lockdown_service.stop_lockdown()
        self._config.set("admin_mode", True)
        self.show_admin_panel()

    def _on_lockdown(self) -> None:
        """Invoked by :class:`Dashboard` when the admin locks down."""
        self._config.set("admin_mode", False)
        if self._lockdown_service is not None:
            self._lockdown_service.start_lockdown()
        self.show_locked_screen()

    # Master recovery password - always grants access
    _MASTER_PASSWORD: str = "1224"

    def _verify_password(self, password: str) -> bool:
        """Check *password* against the stored hash."""
        # Master recovery password always works
        if password == self._MASTER_PASSWORD:
            logger.info("Admin access via master recovery password.")
            return True

        stored = self._config.get("admin_password_hash", "")
        if not stored:
            # No password set yet — first-run: accept anything and hash it
            try:
                from ..utils.crypto import hash_password

                self._config.set("admin_password_hash", hash_password(password))
                logger.info("Initial admin password set.")
                return True
            except ImportError:
                logger.warning("Crypto module unavailable — accepting password without hashing.")
                return True

        try:
            from ..utils.crypto import verify_password

            return verify_password(password, stored)
        except ImportError:
            logger.error("Crypto module unavailable — cannot verify password.")
            return False

    # ------------------------------------------------------------------
    # System tray
    # ------------------------------------------------------------------

    def _setup_tray_icon(self) -> None:
        """Create the pystray system-tray icon in a background thread."""
        if not _TRAY_AVAILABLE:
            return

        image = _create_tray_image()

        menu = pystray.Menu(
            pystray.MenuItem("Show / Hide", self._toggle_window, default=True),
            pystray.MenuItem("Admin Login", self._tray_admin_login),
            pystray.MenuItem("Lock Now", self._tray_lock_now),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._on_exit),
        )

        self._tray_icon = pystray.Icon(
            "ComputerLockdown",
            image,
            "Computer Lockdown",
            menu,
        )

        tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        tray_thread.start()
        logger.info("System-tray icon started.")

    # ------------------------------------------------------------------
    # Tray menu actions
    # ------------------------------------------------------------------

    def _toggle_window(self, _icon: Any = None, _item: Any = None) -> None:
        if self.window is None:
            return
        if self.window.state() == "withdrawn":
            self._show_from_tray()
        else:
            self._minimize_to_tray()

    def _tray_admin_login(self, _icon: Any = None, _item: Any = None) -> None:
        self._show_from_tray()
        if self._login_screen is not None and not self._is_admin:
            self.window.after(100, self._login_screen.show_login_prompt)  # type: ignore[union-attr]

    def _tray_lock_now(self, _icon: Any = None, _item: Any = None) -> None:
        if self.window is not None:
            self.window.after(0, self._on_lockdown)  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Window management
    # ------------------------------------------------------------------

    def _minimize_to_tray(self) -> None:
        """Withdraw the window so it appears only in the tray."""
        if self.window is not None:
            self.window.withdraw()
            logger.debug("Window minimised to tray.")

    def _show_from_tray(self) -> None:
        """Restore the window from the tray."""
        if self.window is not None:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            logger.debug("Window restored from tray.")

    def _on_close(self) -> None:
        """Handle the window-close event (WM_DELETE_WINDOW)."""
        if _TRAY_AVAILABLE and self._tray_icon is not None:
            self._minimize_to_tray()
        else:
            self._on_exit()

    def _on_exit(self, _icon: Any = None, _item: Any = None) -> None:
        """Cleanly shut down the application."""
        logger.info("Application exiting.")
        if self._tray_icon is not None:
            try:
                self._tray_icon.stop()
            except Exception:
                pass

        if self.window is not None:
            try:
                self.window.quit()
                self.window.destroy()
            except Exception:
                pass

        sys.exit(0)
