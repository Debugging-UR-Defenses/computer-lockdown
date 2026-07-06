"""
Locked-mode login screen for Computer Lockdown.

Displays a padlock icon and status text when the system is locked.  An
"Admin Login" button reveals a PIN / password entry field.  On successful
verification the *on_login_success* callback is invoked to transition to
the admin dashboard.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

import customtkinter as ctk

from .theme import Theme

logger = logging.getLogger(__name__)


class LoginScreen(ctk.CTkFrame):
    """Full-size overlay frame shown while the application is in locked mode.

    Parameters
    ----------
    parent:
        The parent widget (typically the main application window).
    on_login_success:
        A callable invoked (with no arguments) when the admin password is
        verified successfully.
    verify_callback:
        A callable that receives the entered password string and returns
        ``True`` when valid.  If *None*, every attempt is rejected.
    """

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        on_login_success: Callable[[], None],
        verify_callback: Optional[Callable[[str], bool]] = None,
    ) -> None:
        super().__init__(parent, fg_color=Theme.BG_DARKEST, corner_radius=0)

        self._on_login_success = on_login_success
        self._verify_callback = verify_callback

            self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble all widgets for the locked screen."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0)

        # -- Padlock icon --
        ctk.CTkLabel(
            container,
            text="\U0001F512",
            font=("Segoe UI Emoji", 64),
            text_color=Theme.ACCENT_DANGER,
        ).pack(pady=(0, 12))

        # -- Title --
        ctk.CTkLabel(
            container,
            text="Computer Lockdown",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
        ).pack(pady=(0, 4))

        # -- Status text --
        ctk.CTkLabel(
            container,
            text="System is locked",
            font=Theme.FONT_BODY,
            text_color=Theme.ACCENT_DANGER,
        ).pack(pady=(0, 24))

        # -- Decorative separator --
        ctk.CTkFrame(
            container,
            height=2,
            width=260,
            fg_color=Theme.ACCENT_DANGER,
            corner_radius=1,
        ).pack(pady=(0, 24))

        # -- Password entry (always visible) --
        self._password_entry = ctk.CTkEntry(
            container,
            placeholder_text="Enter admin password",
            show="*",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            placeholder_text_color=Theme.TEXT_MUTED,
            corner_radius=Theme.CORNER_RADIUS,
            height=Theme.INPUT_HEIGHT,
            width=260,
        )
        self._password_entry.pack(pady=(0, 10))
        self._password_entry.bind("<Return>", lambda _e: self.verify_password())

        # -- Unlock button --
        ctk.CTkButton(
            container,
            text="Unlock",
            font=Theme.FONT_SUBHEADING,
            fg_color=Theme.ACCENT_PRIMARY,
            hover_color=Theme.ACCENT_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.CORNER_RADIUS,
            height=Theme.BUTTON_HEIGHT,
            width=260,
            command=self.verify_password,
        ).pack(pady=(0, 6))

        # -- Error label --
        self._error_label = ctk.CTkLabel(
            container,
            text="",
            font=Theme.FONT_SMALL,
            text_color=Theme.ACCENT_DANGER,
        )
        self._error_label.pack(pady=(4, 0))

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def show_login_prompt(self) -> None:
        """Focus the password entry. Kept for API compatibility."""
        self._password_entry.focus_set()

    def verify_password(self) -> None:
        """Check the entered password; invoke callback on success."""
        password = self._password_entry.get().strip()
        if not password:
            self.show_error("Please enter a password.")
            return

        if self._verify_callback is not None and self._verify_callback(password):
            logger.info("Admin login successful.")
            self._error_label.configure(text="")
            self._on_login_success()
        else:
            logger.warning("Admin login failed — wrong password.")
            self.show_error("Incorrect password.")

    def show_error(self, message: str) -> None:
        """Display *message* below the password field."""
        self._error_label.configure(text=message)

    def reset(self) -> None:
        """Clear the password field and error message."""
        self._password_entry.delete(0, "end")
        self._error_label.configure(text="")


