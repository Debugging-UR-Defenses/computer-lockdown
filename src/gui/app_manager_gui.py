"""
Application whitelist management page for Computer Lockdown.

Displays the list of whitelisted applications with toggles and removal
buttons.  Supports adding apps via a file browser or by scanning currently
running processes for quick-add.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from tkinter import filedialog
from typing import Any, Optional

import customtkinter as ctk

from .theme import Theme

logger = logging.getLogger(__name__)


def _get_running_processes() -> list[dict[str, str]]:
    """Return a list of ``{"name": …, "path": …}`` for running processes.

    Uses :mod:`psutil` when available; falls back to an empty list.
    """
    try:
        import psutil  # type: ignore[import-untyped]

        seen: set[str] = set()
        result: list[dict[str, str]] = []
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                name = proc.info["name"] or ""
                exe = proc.info["exe"] or ""
                if name and name.lower() not in seen and exe:
                    seen.add(name.lower())
                    result.append({"name": name, "path": exe})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        result.sort(key=lambda p: p["name"].lower())
        return result
    except ImportError:
        logger.warning("psutil not installed — cannot scan running processes.")
        return []


class AppManagerPage(ctk.CTkFrame):
    """Application whitelist management page.

    Parameters
    ----------
    parent:
        The parent widget (content area of the dashboard).
    config_manager:
        A :class:`~src.utils.config.ConfigManager` instance.
    """

    def __init__(self, parent: ctk.CTkFrame, config_manager: Any) -> None:
        super().__init__(parent, fg_color="transparent")
        self._config = config_manager

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # list row expands

        self._build_header()
        self._build_toolbar()
        self._build_app_list()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        ctk.CTkLabel(
            self,
            text="Application Manager",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=30, pady=(28, 2))
        ctk.CTkLabel(
            self,
            text="Manage the whitelist of applications allowed to run.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=30, pady=(0, 16))

    def _build_toolbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="we", padx=24, pady=(0, 8))

        # Search / filter
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self.refresh_list())

        search = ctk.CTkEntry(
            bar,
            textvariable=self._search_var,
            placeholder_text="\U0001F50D  Search applications\u2026",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            placeholder_text_color=Theme.TEXT_MUTED,
            corner_radius=8,
            height=Theme.INPUT_HEIGHT,
            width=260,
        )
        search.pack(side="left", padx=(6, 12))

        # Buttons
        ctk.CTkButton(
            bar,
            text="+ Add Application",
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT_PRIMARY,
            hover_color=Theme.ACCENT_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=8,
            height=Theme.BUTTON_HEIGHT,
            command=self.add_application,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bar,
            text="\U0001F504  Scan Running",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=8,
            height=Theme.BUTTON_HEIGHT,
            command=self.scan_running,
        ).pack(side="left", padx=(0, 8))

        # Enable / disable master toggle
        enabled = self._config.get("app_whitelist.enabled", True)
        self._enabled_var = ctk.BooleanVar(value=enabled)
        ctk.CTkSwitch(
            bar,
            text="Enabled",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            variable=self._enabled_var,
            fg_color=Theme.BG_LIGHT,
            progress_color=Theme.ACCENT_SUCCESS,
            button_color=Theme.TEXT_PRIMARY,
            button_hover_color=Theme.ACCENT_HOVER,
            command=self._toggle_enabled,
        ).pack(side="right", padx=6)

    def _build_app_list(self) -> None:
        self._list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=Theme.BG_DARK,
            corner_radius=Theme.CORNER_RADIUS,
        )
        self._list_frame.grid(row=3, column=0, sticky="nswe", padx=24, pady=(0, 24))
        self._list_frame.grid_columnconfigure(0, weight=1)
        self.refresh_list()

    # ------------------------------------------------------------------
    # App list rendering
    # ------------------------------------------------------------------

    def refresh_list(self) -> None:
        """Rebuild the displayed list of whitelisted applications."""
        # Clear existing
        for widget in self._list_frame.winfo_children():
            widget.destroy()

        apps: list[dict[str, str]] = self._config.get(
            "app_whitelist.allowed_apps", []
        )
        query = self._search_var.get().strip().lower() if hasattr(self, "_search_var") else ""

        visible = [
            a for a in apps
            if not query or query in a.get("name", "").lower() or query in a.get("path", "").lower()
        ]

        if not visible:
            ctk.CTkLabel(
                self._list_frame,
                text="No applications found." if query else "Whitelist is empty.  Add an application above.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED,
            ).pack(pady=24)
            return

        for idx, app in enumerate(visible):
            self._make_app_row(idx, app)

    def _make_app_row(self, idx: int, app: dict[str, str]) -> None:
        row = ctk.CTkFrame(
            self._list_frame,
            fg_color=Theme.BG_MEDIUM if idx % 2 == 0 else "transparent",
            corner_radius=8,
        )
        row.pack(fill="x", padx=4, pady=2)
        row.grid_columnconfigure(1, weight=1)

        # App icon placeholder
        ctk.CTkLabel(
            row,
            text="\U0001F4E6",
            font=("Segoe UI Emoji", 18),
            width=36,
        ).grid(row=0, column=0, rowspan=2, padx=(12, 4), pady=8)

        # Name
        ctk.CTkLabel(
            row,
            text=app.get("name", "Unknown"),
            font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=4, pady=(8, 0))

        # Path
        ctk.CTkLabel(
            row,
            text=app.get("path", ""),
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="w", padx=4, pady=(0, 8))

        # Remove button
        ctk.CTkButton(
            row,
            text="\u2716",
            font=Theme.FONT_BODY,
            fg_color="transparent",
            hover_color=Theme.ACCENT_DANGER,
            text_color=Theme.TEXT_MUTED,
            width=32,
            height=32,
            corner_radius=6,
            command=lambda n=app.get("name", ""): self.remove_application(n),
        ).grid(row=0, column=2, rowspan=2, padx=12, pady=8)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def add_application(self) -> None:
        """Open a file dialog to add an executable to the whitelist."""
        filetypes = [("Executable files", "*.exe"), ("All files", "*.*")]
        path = filedialog.askopenfilename(
            title="Select Application",
            filetypes=filetypes,
        )
        if not path:
            return

        name = Path(path).stem.replace("_", " ").replace("-", " ").title()
        exe_name = Path(path).name

        apps: list[dict[str, str]] = list(
            self._config.get("app_whitelist.allowed_apps", [])
        )
        # Avoid duplicates
        if any(a.get("path", "").lower() == exe_name.lower() for a in apps):
            logger.info("Application %s already in whitelist.", exe_name)
            return

        apps.append({"name": name, "path": exe_name})
        self._config.set("app_whitelist.allowed_apps", apps)
        logger.info("Added %s (%s) to whitelist.", name, exe_name)
        self.refresh_list()

    def remove_application(self, app_name: str) -> None:
        """Remove *app_name* from the whitelist."""
        apps: list[dict[str, str]] = list(
            self._config.get("app_whitelist.allowed_apps", [])
        )
        apps = [a for a in apps if a.get("name") != app_name]
        self._config.set("app_whitelist.allowed_apps", apps)
        logger.info("Removed %s from whitelist.", app_name)
        self.refresh_list()

    def scan_running(self) -> None:
        """Show a popup window listing currently running processes for quick-add."""
        procs = _get_running_processes()
        if not procs:
            self._show_info_popup("No processes found (psutil may not be installed).")
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Running Processes")
        popup.geometry("520x480")
        popup.configure(fg_color=Theme.BG_DARKEST)
        popup.grab_set()

        ctk.CTkLabel(
            popup,
            text="Select processes to whitelist",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_PRIMARY,
        ).pack(padx=16, pady=(16, 8))

        scroll = ctk.CTkScrollableFrame(
            popup,
            fg_color=Theme.BG_DARK,
            corner_radius=Theme.CORNER_RADIUS,
        )
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        existing: set[str] = {
            a.get("path", "").lower()
            for a in self._config.get("app_whitelist.allowed_apps", [])
        }

        for proc in procs:
            exe_name = os.path.basename(proc["path"])
            already = exe_name.lower() in existing

            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=2)
            row.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row,
                text=proc["name"],
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_PRIMARY if not already else Theme.TEXT_MUTED,
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=8)

            ctk.CTkLabel(
                row,
                text=proc["path"],
                font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MUTED,
                anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=8, pady=(0, 4))

            if not already:
                ctk.CTkButton(
                    row,
                    text="+ Add",
                    font=Theme.FONT_SMALL,
                    fg_color=Theme.ACCENT_PRIMARY,
                    hover_color=Theme.ACCENT_HOVER,
                    text_color=Theme.TEXT_PRIMARY,
                    width=60,
                    height=28,
                    corner_radius=6,
                    command=lambda p=proc, r=row: self._quick_add(p, r, popup),
                ).grid(row=0, column=1, rowspan=2, padx=8, pady=4)
            else:
                ctk.CTkLabel(
                    row,
                    text="Added",
                    font=Theme.FONT_SMALL,
                    text_color=Theme.ACCENT_SUCCESS,
                ).grid(row=0, column=1, rowspan=2, padx=8)

        ctk.CTkButton(
            popup,
            text="Close",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_SECONDARY,
            corner_radius=8,
            height=Theme.BUTTON_HEIGHT,
            command=popup.destroy,
        ).pack(pady=(0, 16))

    def _quick_add(
        self,
        proc: dict[str, str],
        row: ctk.CTkFrame,
        popup: ctk.CTkToplevel,
    ) -> None:
        """Add a process from the scan popup and update the button."""
        exe_name = os.path.basename(proc["path"])
        apps: list[dict[str, str]] = list(
            self._config.get("app_whitelist.allowed_apps", [])
        )
        if not any(a.get("path", "").lower() == exe_name.lower() for a in apps):
            apps.append({"name": proc["name"], "path": exe_name})
            self._config.set("app_whitelist.allowed_apps", apps)
        self.refresh_list()

        # Update the row in the popup
        for widget in row.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.destroy()
        ctk.CTkLabel(
            row,
            text="Added",
            font=Theme.FONT_SMALL,
            text_color=Theme.ACCENT_SUCCESS,
        ).grid(row=0, column=1, rowspan=2, padx=8)

    def _toggle_enabled(self) -> None:
        self._config.set("app_whitelist.enabled", self._enabled_var.get())

    def _show_info_popup(self, message: str) -> None:
        popup = ctk.CTkToplevel(self)
        popup.title("Info")
        popup.geometry("360x150")
        popup.configure(fg_color=Theme.BG_DARKEST)
        popup.grab_set()
        ctk.CTkLabel(
            popup, text=message, font=Theme.FONT_BODY,
            text_color=Theme.TEXT_PRIMARY, wraplength=300,
        ).pack(expand=True, padx=24, pady=16)
        ctk.CTkButton(
            popup, text="OK", width=80, height=34, corner_radius=8,
            fg_color=Theme.ACCENT_PRIMARY, hover_color=Theme.ACCENT_HOVER,
            command=popup.destroy,
        ).pack(pady=(0, 16))

    # ------------------------------------------------------------------
    # Public alias used by Dashboard
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Called when the page is re-selected in the sidebar."""
        self.refresh_list()
