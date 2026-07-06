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

    _SHAKE_DISTANCE: int = 10
    _SHAKE_STEPS: int = 6
    _SHAKE_DELAY_MS: int = 40

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        on_login_success: Callable[[], None],
        verify_callback: Optional[Callable[[str], bool]] = None,
    ) -> None:
        super().__init__(parent, fg_color=Theme.BG_DARKEST, corner_radius=0)

        self._on_login_success = on_login_success
        self._verify_callback = verify_callback

        # Internal state
        self._login_prompt_visible: bool = False

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble all widgets for the locked screen."""
        # Make frame fill its parent
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Centre container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0)
        self._container = container

        # -- Padlock icon --
        self._lock_icon = ctk.CTkLabel(
            container,
            text="\U0001F512",  # Padlock emoji
            font=("Segoe UI Emoji", 64),
            text_color=Theme.ACCENT_DANGER,
        )
        self._lock_icon.pack(pady=(0, 12))

        # -- Title --
        ctk.CTkLabel(
            container,
            text="Computer Lockdown",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
        ).pack(pady=(0, 4))

        # -- Status text --
        self._status_label = ctk.CTkLabel(
            container,
            text="System is locked",
            font=Theme.FONT_BODY,
            text_color=Theme.ACCENT_DANGER,
        )
        self._status_label.pack(pady=(0, 32))

        # -- Subtle glow line (decorative separator) --
        glow_frame = ctk.CTkFrame(
            container,
            height=2,
            width=220,
            fg_color=Theme.ACCENT_DANGER,
            corner_radius=1,
        )
        glow_frame.pack(pady=(0, 32))

        # -- Admin Login button --
        self._login_btn = ctk.CTkButton(
            container,
            text="Admin Login",
            font=Theme.FONT_SUBHEADING,
            fg_color=Theme.BG_MEDIUM,
            hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=Theme.CORNER_RADIUS,
            height=Theme.BUTTON_HEIGHT,
            width=220,
            command=self.show_login_prompt,
        )
        self._login_btn.pack(pady=(0, 8))

        # -- Login prompt frame (hidden initially) --
        self._prompt_frame = ctk.CTkFrame(container, fg_color="transparent")
        # NOT packed yet; shown via show_login_prompt()

        self._password_entry = ctk.CTkEntry(
            self._prompt_frame,
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
        self._password_entry.pack(pady=(12, 8))
        self._password_entry.bind("<Return>", lambda _e: self.verify_password())

        btn_row = ctk.CTkFrame(self._prompt_frame, fg_color="transparent")
        btn_row.pack(pady=(0, 4))

        self._submit_btn = ctk.CTkButton(
            btn_row,
            text="Unlock",
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT_PRIMARY,
            hover_color=Theme.ACCENT_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=Theme.CORNER_RADIUS,
            height=Theme.BUTTON_HEIGHT,
            width=120,
            command=self.verify_password,
        )
        self._submit_btn.grid(row=0, column=0, padx=(0, 6))

        self._cancel_btn = ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=Theme.CORNER_RADIUS,
            height=Theme.BUTTON_HEIGHT,
            width=120,
            command=self.reset,
        )
        self._cancel_btn.grid(row=0, column=1, padx=(6, 0))

        # -- Error label (hidden) --
        self._error_label = ctk.CTkLabel(
            self._prompt_frame,
            text="",
            font=Theme.FONT_SMALL,
            text_color=Theme.ACCENT_DANGER,
        )
        self._error_label.pack(pady=(4, 0))

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def show_login_prompt(self) -> None:
        """Reveal the password entry field and focus it."""
        if self._login_prompt_visible:
            return
        self._login_prompt_visible = True
        self._login_btn.pack_forget()
        self._prompt_frame.pack(pady=(0, 8))
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
        """Display *message* below the password field and shake the entry."""
        self._error_label.configure(text=message)
        self._shake(self._password_entry)

    def reset(self) -> None:
        """Clear the password field, hide the prompt, and show the login button."""
        self._password_entry.delete(0, "end")
        self._error_label.configure(text="")
        if self._login_prompt_visible:
            self._prompt_frame.pack_forget()
            self._login_btn.pack(pady=(0, 8))
            self._login_prompt_visible = False

    # ------------------------------------------------------------------
    # Animation helpers
    # ------------------------------------------------------------------

    def _shake(self, widget: ctk.CTkBaseClass, step: int = 0) -> None:
        """Horizontally shake *widget* to indicate an error."""
        if step >= self._SHAKE_STEPS:
            widget.place_configure(x=0)  # reset to origin
            return
        direction = 1 if step % 2 == 0 else -1
        dx = direction * self._SHAKE_DISTANCE
        # Use relative x offset by briefly switching to place manager
        try:
            widget.pack_info()
        except Exception:
            return  # widget not managed; bail
        # Simulate shake via padx manipulation
        pad = max(0, dx)
        widget.configure(padx=pad)
        self.after(
            self._SHAKE_DELAY_MS,
            lambda: self._shake(widget, step + 1),
        )
