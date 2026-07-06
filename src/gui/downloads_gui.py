"""
Downloads management page for Computer Lockdown admin dashboard.

Shows the download blocking configuration and review queue for
quarantined downloads.
"""

from __future__ import annotations

import logging
from typing import Any

import customtkinter as ctk

from .theme import Theme

logger = logging.getLogger(__name__)


class DownloadsManagerPage(ctk.CTkFrame):
    """Admin page for managing download blocking and reviewing quarantined files."""

    def __init__(self, parent: ctk.CTkFrame, config_manager: Any) -> None:
        super().__init__(parent, fg_color="transparent")
        self._config = config_manager
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Title
        ctk.CTkLabel(
            scroll, text="Download Blocking",
            font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            scroll,
            text="Quarantined downloads are held for review. Approve or deny each item.",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 16))

        # Block all toggle
        toggle_row = ctk.CTkFrame(scroll, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS)
        toggle_row.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            toggle_row, text="Block ALL downloads in locked mode",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left", padx=12, pady=10)
        block_all = self._config.get("download_blocking.block_all_in_locked_mode", True)
        self._block_all_var = ctk.StringVar(value="on" if block_all else "off")
        ctk.CTkSwitch(
            toggle_row, text="", variable=self._block_all_var,
            onvalue="on", offvalue="off",
            command=self._toggle_block_all,
        ).pack(side="right", padx=12, pady=10)

        # Review Queue
        ctk.CTkLabel(
            scroll, text="Review Queue",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        queue = self._config.get("download_blocking.review_queue", [])
        if not queue:
            ctk.CTkLabel(
                scroll, text="No quarantined downloads.",
                font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED,
            ).pack(anchor="w", pady=8)
        else:
            for i, entry in enumerate(queue):
                self._build_queue_row(scroll, i, entry)

        # Blocked extensions section
        ctk.CTkFrame(scroll, height=1, fg_color=Theme.BORDER).pack(fill="x", pady=16)
        ctk.CTkLabel(
            scroll, text="Blocked Extensions",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))
        exts = self._config.get("download_blocking.block_extensions", [])
        ext_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        ext_frame.pack(anchor="w")
        for ext in exts:
            ctk.CTkLabel(
                ext_frame, text=ext,
                font=Theme.FONT_SMALL, text_color=Theme.TEXT_PRIMARY,
                fg_color=Theme.BG_MEDIUM, corner_radius=6,
                padx=8, pady=2,
            ).pack(side="left", padx=(0, 4), pady=2)

    def _build_queue_row(self, parent, index, entry):
        row = ctk.CTkFrame(parent, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS)
        row.pack(fill="x", pady=(0, 4))

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, padx=12, pady=8)
        ctk.CTkLabel(
            info, text=entry.get("filename", "?"),
            font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=f"{entry.get('original_path', '')}  |  {entry.get('timestamp', '')}",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w")

        status = entry.get("status", "pending")
        btn_frame = ctk.CTkFrame(row, fg_color="transparent")
        btn_frame.pack(side="right", padx=12, pady=8)

        if status == "pending":
            ctk.CTkButton(
                btn_frame, text="Allow", width=60, height=28,
                font=Theme.FONT_SMALL,
                fg_color=Theme.ACCENT_SUCCESS, hover_color="#16a34a",
                text_color=Theme.TEXT_PRIMARY,
                command=lambda i=index: self._approve(i),
            ).pack(side="left", padx=(0, 4))
            ctk.CTkButton(
                btn_frame, text="Deny", width=60, height=28,
                font=Theme.FONT_SMALL,
                fg_color=Theme.ACCENT_DANGER, hover_color="#dc2626",
                text_color=Theme.TEXT_PRIMARY,
                command=lambda i=index: self._deny(i),
            ).pack(side="left")
        elif status == "approved":
            ctk.CTkLabel(
                btn_frame, text="Approved",
                font=Theme.FONT_SMALL, text_color=Theme.ACCENT_SUCCESS,
            ).pack()
        elif status == "denied":
            ctk.CTkLabel(
                btn_frame, text="Denied",
                font=Theme.FONT_SMALL, text_color=Theme.ACCENT_DANGER,
            ).pack()

    def _toggle_block_all(self):
        val = self._block_all_var.get() == "on"
        self._config.set("download_blocking.block_all_in_locked_mode", val)

    def _approve(self, index):
        queue = self._config.get("download_blocking.review_queue", [])
        if 0 <= index < len(queue):
            queue[index]["status"] = "approved"
            self._config.set("download_blocking.review_queue", queue)
            logger.info("Download approved: %s", queue[index].get("filename"))

    def _deny(self, index):
        queue = self._config.get("download_blocking.review_queue", [])
        if 0 <= index < len(queue):
            queue[index]["status"] = "denied"
            self._config.set("download_blocking.review_queue", queue)
            logger.info("Download denied: %s", queue[index].get("filename"))
