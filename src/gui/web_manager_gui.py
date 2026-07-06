"""
Website blocking management page for Computer Lockdown.

Supports blacklist and whitelist modes with quick-add category presets
(Social Media, Gaming, Streaming, Adult Content).  Sites can be added
individually or removed from a scrollable list.
"""

from __future__ import annotations

import logging
from typing import Any

import customtkinter as ctk

from .theme import Theme

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Category presets
# ------------------------------------------------------------------

CATEGORY_PRESETS: dict[str, list[str]] = {
    "Social Media": [
        "facebook.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "tiktok.com",
        "snapchat.com",
        "reddit.com",
    ],
    "Gaming": [
        "store.steampowered.com",
        "epicgames.com",
        "roblox.com",
        "minecraft.net",
    ],
    "Streaming": [
        "twitch.tv",
        "youtube.com",
        "netflix.com",
        "disneyplus.com",
    ],
    "Adult Content": [
        # Placeholder — actual domains should be sourced from a curated
        # blocklist file or external API at deployment time.
    ],
}


class WebManagerPage(ctk.CTkFrame):
    """Website blocking management page.

    Parameters
    ----------
    parent:
        Parent widget (content area of the dashboard).
    config_manager:
        A :class:`~src.utils.config.ConfigManager` instance.
    """

    def __init__(self, parent: ctk.CTkFrame, config_manager: Any) -> None:
        super().__init__(parent, fg_color="transparent")
        self._config = config_manager

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # site list expands

        self._build_header()
        self._build_mode_toggle()
        self._build_add_bar()
        self._build_category_bar()
        self._build_site_list()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        ctk.CTkLabel(
            self,
            text="Website Manager",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=30, pady=(28, 2))
        ctk.CTkLabel(
            self,
            text="Block or allow websites by domain.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=30, pady=(0, 12))

    def _build_mode_toggle(self) -> None:
        """Blacklist / Whitelist segmented button + master enable switch."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="we", padx=24, pady=(0, 8))

        current_mode = self._config.get("web_blocking.mode", "blacklist")
        self._mode_var = ctk.StringVar(value=current_mode.capitalize())

        self._mode_seg = ctk.CTkSegmentedButton(
            bar,
            values=["Blacklist", "Whitelist"],
            variable=self._mode_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            selected_color=Theme.ACCENT_PRIMARY,
            selected_hover_color=Theme.ACCENT_HOVER,
            unselected_color=Theme.BG_MEDIUM,
            unselected_hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=8,
            command=self._on_mode_change,
        )
        self._mode_seg.pack(side="left", padx=(6, 16))

        enabled = self._config.get("web_blocking.enabled", True)
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
            command=lambda: self._config.set(
                "web_blocking.enabled", self._enabled_var.get()
            ),
        ).pack(side="right", padx=6)

    def _build_add_bar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="we", padx=24, pady=(0, 4))

        self._domain_entry = ctk.CTkEntry(
            bar,
            placeholder_text="example.com",
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            border_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            placeholder_text_color=Theme.TEXT_MUTED,
            corner_radius=8,
            height=Theme.INPUT_HEIGHT,
            width=300,
        )
        self._domain_entry.pack(side="left", padx=(6, 8))
        self._domain_entry.bind("<Return>", lambda _e: self.add_website())

        ctk.CTkButton(
            bar,
            text="+ Add Website",
            font=Theme.FONT_BODY,
            fg_color=Theme.ACCENT_PRIMARY,
            hover_color=Theme.ACCENT_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=8,
            height=Theme.BUTTON_HEIGHT,
            command=self.add_website,
        ).pack(side="left", padx=(0, 8))

    def _build_category_bar(self) -> None:
        """Quick-add category buttons."""
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="e", padx=24, pady=(0, 4))

        ctk.CTkLabel(
            bar,
            text="Quick-add:",
            font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED,
        ).pack(side="left", padx=(0, 6))

        for cat in CATEGORY_PRESETS:
            ctk.CTkButton(
                bar,
                text=cat,
                font=Theme.FONT_SMALL,
                fg_color=Theme.BG_MEDIUM,
                hover_color=Theme.BG_HOVER,
                text_color=Theme.TEXT_SECONDARY,
                corner_radius=6,
                height=28,
                width=100,
                command=lambda c=cat: self.add_category(c),
            ).pack(side="left", padx=3)

    def _build_site_list(self) -> None:
        self._list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=Theme.BG_DARK,
            corner_radius=Theme.CORNER_RADIUS,
        )
        self._list_frame.grid(row=4, column=0, sticky="nswe", padx=24, pady=(8, 24))
        self._list_frame.grid_columnconfigure(0, weight=1)
        self._refresh_site_list()

    # ------------------------------------------------------------------
    # Site list rendering
    # ------------------------------------------------------------------

    def _refresh_site_list(self) -> None:
        for widget in self._list_frame.winfo_children():
            widget.destroy()

        mode = self._current_mode()
        sites = self._get_sites(mode)

        header_text = "Blocked websites" if mode == "blacklist" else "Allowed websites"
        ctk.CTkLabel(
            self._list_frame,
            text=header_text,
            font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=12, pady=(8, 4))

        if not sites:
            ctk.CTkLabel(
                self._list_frame,
                text="No websites in the list.  Add one above.",
                font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED,
            ).pack(pady=20)
            return

        for idx, domain in enumerate(sites):
            self._make_site_row(idx, domain)

    def _make_site_row(self, idx: int, domain: str) -> None:
        row = ctk.CTkFrame(
            self._list_frame,
            fg_color=Theme.BG_MEDIUM if idx % 2 == 0 else "transparent",
            corner_radius=8,
        )
        row.pack(fill="x", padx=4, pady=2)
        row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            row,
            text=f"\U0001F310  {domain}",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=12, pady=10)

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
            command=lambda d=domain: self.remove_website(d),
        ).grid(row=0, column=1, padx=12, pady=6)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def add_website(self) -> None:
        """Add the domain from the entry field to the current list."""
        raw = self._domain_entry.get().strip().lower()
        if not raw:
            return

        # Normalise: strip scheme
        for prefix in ("https://", "http://", "www."):
            if raw.startswith(prefix):
                raw = raw[len(prefix):]
        domain = raw.rstrip("/")

        if not domain:
            return

        mode = self._current_mode()
        sites = list(self._get_sites(mode))
        if domain in sites:
            logger.info("Domain %s already in %s list.", domain, mode)
            self._domain_entry.delete(0, "end")
            return

        sites.append(domain)
        self._set_sites(mode, sites)
        self._domain_entry.delete(0, "end")
        logger.info("Added %s to %s list.", domain, mode)
        self._refresh_site_list()

    def remove_website(self, domain: str) -> None:
        """Remove *domain* from the current list."""
        mode = self._current_mode()
        sites = [s for s in self._get_sites(mode) if s != domain]
        self._set_sites(mode, sites)
        logger.info("Removed %s from %s list.", domain, mode)
        self._refresh_site_list()

    def toggle_mode(self) -> None:
        """Programmatically toggle between blacklist and whitelist."""
        new_mode = "whitelist" if self._current_mode() == "blacklist" else "blacklist"
        self._mode_var.set(new_mode.capitalize())
        self._on_mode_change(new_mode.capitalize())

    def add_category(self, category: str) -> None:
        """Quick-add all domains from a preset category."""
        domains = CATEGORY_PRESETS.get(category, [])
        if not domains:
            logger.info("Category '%s' has no preset domains.", category)
            return

        mode = self._current_mode()
        sites = list(self._get_sites(mode))
        added = 0
        for d in domains:
            if d not in sites:
                sites.append(d)
                added += 1
        if added:
            self._set_sites(mode, sites)
            logger.info("Added %d domains from category '%s'.", added, category)
            self._refresh_site_list()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current_mode(self) -> str:
        return self._mode_var.get().lower()

    def _get_sites(self, mode: str) -> list[str]:
        key = "web_blocking.blocked_sites" if mode == "blacklist" else "web_blocking.allowed_sites"
        return self._config.get(key, [])

    def _set_sites(self, mode: str, sites: list[str]) -> None:
        key = "web_blocking.blocked_sites" if mode == "blacklist" else "web_blocking.allowed_sites"
        self._config.set(key, sites)

    def _on_mode_change(self, value: str) -> None:
        mode = value.lower()
        self._config.set("web_blocking.mode", mode)
        self._refresh_site_list()

    # ------------------------------------------------------------------
    # Public alias
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Called when the page is re-selected in the sidebar."""
        self._refresh_site_list()
