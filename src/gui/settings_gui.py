"""
Settings page for Computer Lockdown.

Contains sections for: password change, startup behaviour, download-blocking
extension management, system-policy toggles, and a reset-to-defaults action.
"""

from __future__ import annotations

import logging
from typing import Any

import customtkinter as ctk

from .theme import Theme

logger = logging.getLogger(__name__)

_APP_VERSION = "1.0.0"


class SettingsPage(ctk.CTkFrame):
    """Settings page.

    Parameters
    ----------
    parent:
        Parent widget.
    config_manager:
        A :class:`~src.utils.config.ConfigManager` instance.
    """

    def __init__(self, parent: ctk.CTkFrame, config_manager: Any) -> None:
        super().__init__(parent, fg_color="transparent")
        self._config = config_manager

        self.grid_columnconfigure(0, weight=1)

        self._build_header()

        # Scrollable body so everything fits regardless of screen height
        self._body = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
        )
        self._body.grid(row=1, column=0, sticky="nswe", padx=0, pady=0)
        self._body.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_password_section()
        self._create_startup_section()
        self._create_download_section()
        self._create_policy_section()
        self._create_about_section()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        ctk.CTkLabel(
            self,
            text="Settings",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=30, pady=(28, 16))

    # ------------------------------------------------------------------
    # Password section
    # ------------------------------------------------------------------

    def _create_password_section(self) -> None:
        card = self._section_card(self._body, "Change Admin Password")

        labels = ["Current password", "New password", "Confirm password"]
        self._pw_entries: list[ctk.CTkEntry] = []
        for idx, lbl in enumerate(labels):
            ctk.CTkLabel(
                card, text=lbl, font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_SECONDARY, anchor="w",
            ).pack(fill="x", padx=16, pady=(10 if idx == 0 else 4, 0))
            entry = ctk.CTkEntry(
                card,
                show="*",
                font=Theme.FONT_BODY,
                fg_color=Theme.BG_MEDIUM,
                border_color=Theme.BORDER,
                text_color=Theme.TEXT_PRIMARY,
                placeholder_text_color=Theme.TEXT_MUTED,
                corner_radius=8,
                height=Theme.INPUT_HEIGHT,
            )
            entry.pack(fill="x", padx=16, pady=(2, 0))
            self._pw_entries.append(entry)

        self._pw_status = ctk.CTkLabel(
            card, text="", font=Theme.FONT_SMALL,
            text_color=Theme.ACCENT_DANGER,
        )
        self._pw_status.pack(padx=16, pady=(4, 0))

        ctk.CTkButton(
            card,
            text="Update Password",
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT_PRIMARY,
            hover_color=Theme.ACCENT_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=8,
            height=Theme.BUTTON_HEIGHT,
            command=self.change_password,
        ).pack(padx=16, pady=(8, 16))

    # ------------------------------------------------------------------
    # Startup section
    # ------------------------------------------------------------------

    def _create_startup_section(self) -> None:
        card = self._section_card(self._body, "Startup")

        run_on_start = self._config.get("startup.run_on_startup", True)
        self._run_startup_var = ctk.BooleanVar(value=run_on_start)
        self._toggle_row(
            card, "Run on Windows startup", self._run_startup_var,
            lambda: self._config.set("startup.run_on_startup", self._run_startup_var.get()),
        )

        start_locked = self._config.get("startup.start_locked", True)
        self._start_locked_var = ctk.BooleanVar(value=start_locked)
        self._toggle_row(
            card, "Start in locked mode", self._start_locked_var,
            lambda: self._config.set("startup.start_locked", self._start_locked_var.get()),
        )

    # ------------------------------------------------------------------
    # Download blocking section
    # ------------------------------------------------------------------

    def _create_download_section(self) -> None:
        card = self._section_card(self._body, "Download Blocking")

        ctk.CTkLabel(
            card,
            text="Blocked file extensions:",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=16, pady=(10, 4))

        # Extension tag display
        self._ext_tag_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._ext_tag_frame.pack(fill="x", padx=16, pady=(0, 8))
        self._refresh_ext_tags()

        # Add extension row
        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=16, pady=(0, 16))

        self._ext_entry = ctk.CTkEntry(
            add_row,
            placeholder_text=".zip",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            placeholder_text_color=Theme.TEXT_MUTED,
            corner_radius=8,
            height=Theme.INPUT_HEIGHT,
            width=120,
        )
        self._ext_entry.pack(side="left", padx=(0, 8))
        self._ext_entry.bind("<Return>", lambda _: self._add_extension())

        ctk.CTkButton(
            add_row,
            text="+ Add",
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT_PRIMARY,
            hover_color=Theme.ACCENT_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=8,
            height=Theme.BUTTON_HEIGHT,
            width=80,
            command=self._add_extension,
        ).pack(side="left")

    def _refresh_ext_tags(self) -> None:
        for w in self._ext_tag_frame.winfo_children():
            w.destroy()

        exts: list[str] = self._config.get("download_blocking.block_extensions", [])
        for ext in exts:
            tag = ctk.CTkFrame(
                self._ext_tag_frame,
                fg_color=Theme.BG_LIGHT,
                corner_radius=6,
            )
            tag.pack(side="left", padx=3, pady=3)
            ctk.CTkLabel(
                tag, text=ext, font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_PRIMARY,
            ).pack(side="left", padx=(8, 2), pady=4)
            ctk.CTkButton(
                tag,
                text="\u00d7",
                font=("Segoe UI", 12, "bold"),
                fg_color="transparent",
                hover_color=Theme.ACCENT_DANGER,
                text_color=Theme.TEXT_MUTED,
                width=20,
                height=20,
                corner_radius=4,
                command=lambda e=ext: self._remove_extension(e),
            ).pack(side="left", padx=(0, 4), pady=4)

    def _add_extension(self) -> None:
        raw = self._ext_entry.get().strip().lower()
        if not raw:
            return
        if not raw.startswith("."):
            raw = f".{raw}"
        exts: list[str] = list(self._config.get("download_blocking.block_extensions", []))
        if raw in exts:
            self._ext_entry.delete(0, "end")
            return
        exts.append(raw)
        self._config.set("download_blocking.block_extensions", exts)
        self._ext_entry.delete(0, "end")
        self._refresh_ext_tags()

    def _remove_extension(self, ext: str) -> None:
        exts = [e for e in self._config.get("download_blocking.block_extensions", []) if e != ext]
        self._config.set("download_blocking.block_extensions", exts)
        self._refresh_ext_tags()

    # ------------------------------------------------------------------
    # Policy section
    # ------------------------------------------------------------------

    def _create_policy_section(self) -> None:
        card = self._section_card(self._body, "System Policies")

        policies: list[tuple[str, str]] = [
            ("Block Task Manager", "policy.block_task_manager"),
            ("Block CMD / PowerShell", "policy.block_cmd"),
            ("Block Registry Editor", "policy.block_registry_editor"),
            ("Block Control Panel", "policy.block_control_panel"),
            ("Block Windows Settings", "policy.block_settings"),
        ]

        for label, cfg_key in policies:
            current = self._config.get(cfg_key, False)
            var = ctk.BooleanVar(value=current)
            self._toggle_row(
                card, label, var,
                lambda k=cfg_key, v=var: self._config.set(k, v.get()),
            )

    # ------------------------------------------------------------------
    # About + reset section
    # ------------------------------------------------------------------

    def _create_about_section(self) -> None:
        card = self._section_card(self._body, "About")

        info_lines = [
            f"Version:  {_APP_VERSION}",
            "Built with Python + CustomTkinter",
            "Designed for Windows 11",
        ]
        for line in info_lines:
            ctk.CTkLabel(
                card, text=line, font=Theme.FONT_BODY,
                text_color=Theme.TEXT_SECONDARY, anchor="w",
            ).pack(fill="x", padx=16, pady=2)

        ctk.CTkButton(
            card,
            text="Reset All Settings",
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT_DANGER,
            hover_color="#dc2626",
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=8,
            height=Theme.BUTTON_HEIGHT,
            command=self.reset_all,
        ).pack(padx=16, pady=(16, 16))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def change_password(self) -> None:
        """Validate and update the admin password."""
        current = self._pw_entries[0].get()
        new_pw = self._pw_entries[1].get()
        confirm = self._pw_entries[2].get()

        if not current or not new_pw or not confirm:
            self._pw_status.configure(
                text="All fields are required.", text_color=Theme.ACCENT_DANGER,
            )
            return

        # Verify current password
        try:
            from ..utils.crypto import verify_password

            stored_hash = self._config.get("admin_password_hash", "")
            if stored_hash and not verify_password(current, stored_hash):
                self._pw_status.configure(
                    text="Current password is incorrect.", text_color=Theme.ACCENT_DANGER,
                )
                return
        except ImportError:
            logger.warning("crypto module not available — skipping current-password check.")

        if new_pw != confirm:
            self._pw_status.configure(
                text="New passwords do not match.", text_color=Theme.ACCENT_DANGER,
            )
            return

        if len(new_pw) < 4:
            self._pw_status.configure(
                text="Password must be at least 4 characters.", text_color=Theme.ACCENT_DANGER,
            )
            return

        # Hash and save
        try:
            from ..utils.crypto import hash_password

            hashed = hash_password(new_pw)
            self._config.set("admin_password_hash", hashed)
            self._pw_status.configure(
                text="Password updated successfully.", text_color=Theme.ACCENT_SUCCESS,
            )
            for e in self._pw_entries:
                e.delete(0, "end")
            logger.info("Admin password changed.")
        except ImportError:
            self._pw_status.configure(
                text="Crypto module unavailable.", text_color=Theme.ACCENT_DANGER,
            )

    def reset_all(self) -> None:
        """Reset configuration to defaults after confirmation."""
        popup = ctk.CTkToplevel(self)
        popup.title("Confirm Reset")
        popup.geometry("380x180")
        popup.configure(fg_color=Theme.BG_DARKEST)
        popup.grab_set()

        ctk.CTkLabel(
            popup,
            text="Reset all settings to defaults?",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_PRIMARY,
        ).pack(padx=24, pady=(24, 8))

        ctk.CTkLabel(
            popup,
            text="This cannot be undone.  Your password will be cleared.",
            font=Theme.FONT_BODY,
            text_color=Theme.ACCENT_WARNING,
            wraplength=320,
        ).pack(padx=24, pady=(0, 16))

        btn_row = ctk.CTkFrame(popup, fg_color="transparent")
        btn_row.pack(pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text="Reset",
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT_DANGER,
            hover_color="#dc2626",
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=8,
            height=36,
            width=100,
            command=lambda: self._do_reset(popup),
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=8,
            height=36,
            width=100,
            command=popup.destroy,
        ).pack(side="left", padx=6)

    def _do_reset(self, popup: ctk.CTkToplevel) -> None:
        self._config.reset_to_defaults()
        popup.destroy()
        logger.info("All settings reset to defaults.")

    # ------------------------------------------------------------------
    # Reusable helpers
    # ------------------------------------------------------------------

    def _section_card(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        """Create a titled card container and pack it into *parent*."""
        ctk.CTkLabel(
            parent, text=title, font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).pack(fill="x", padx=30, pady=(20, 4))

        card = ctk.CTkFrame(
            parent, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS,
        )
        card.pack(fill="x", padx=24, pady=(0, 4))
        return card

    def _toggle_row(
        self,
        parent: ctk.CTkFrame,
        label: str,
        variable: ctk.BooleanVar,
        command: Any,
    ) -> None:
        """Add a label + switch row to *parent*."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=6)
        row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            row, text=label, font=Theme.FONT_BODY,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkSwitch(
            row,
            text="",
            variable=variable,
            onvalue=True,
            offvalue=False,
            fg_color=Theme.BG_LIGHT,
            progress_color=Theme.ACCENT_SUCCESS,
            button_color=Theme.TEXT_PRIMARY,
            button_hover_color=Theme.ACCENT_HOVER,
            command=command,
        ).grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------
    # Public alias
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data when the page is re-selected."""
        self._refresh_ext_tags()
