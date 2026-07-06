"""
Admin dashboard for Computer Lockdown.

Provides a sidebar + content-area layout.  The sidebar contains navigation
buttons; the content area dynamically displays the selected page (home
overview, app manager, web manager, time limits, settings, etc.).
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Callable, Dict, Optional

import customtkinter as ctk

from .theme import Theme

logger = logging.getLogger(__name__)

# Navigation items: (label, icon, page_key)
_NAV_ITEMS: list[tuple[str, str, str]] = [
    ("\U0001F3E0  Dashboard", "\U0001F3E0", "home"),
    ("\U0001F4BB  Applications", "\U0001F4BB", "apps"),
    ("\U0001F310  Websites", "\U0001F310", "websites"),
    ("\u23F1  Time Limits", "\u23F1", "time"),
    ("\U0001F4E5  Downloads", "\U0001F4E5", "downloads"),
    ("\U0001F6E1  Policies", "\U0001F6E1", "policies"),
    ("\u2699  Settings", "\u2699", "settings"),
]


class Dashboard(ctk.CTkFrame):
    """Main admin dashboard shown after a successful login.

    Parameters
    ----------
    parent:
        The parent widget.
    config_manager:
        A :class:`~src.utils.config.ConfigManager` instance.
    on_lockdown:
        Callback invoked when the admin clicks the *Lock Down* button.
    page_factories:
        Optional mapping of ``page_key -> factory(parent) -> CTkFrame``.
        Allows the caller to inject actual management pages (app manager,
        web manager, etc.).  Pages not supplied get a placeholder.
    """

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        config_manager: Any,
        on_lockdown: Callable[[], None],
        page_factories: Optional[Dict[str, Callable[..., ctk.CTkFrame]]] = None,
    ) -> None:
        super().__init__(parent, fg_color=Theme.BG_DARKEST, corner_radius=0)

        self._config = config_manager
        self._on_lockdown = on_lockdown
        self._page_factories = page_factories or {}

        # Cache for lazily-created page frames keyed by page_key
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._active_page: Optional[str] = None
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        self._build_layout()
        self.show_page("home")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # content

        self._create_sidebar()
        self._create_content_area()

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------

    def _create_sidebar(self) -> None:
        """Build the fixed-width navigation sidebar."""
        sidebar = ctk.CTkFrame(
            self,
            width=Theme.SIDEBAR_WIDTH,
            fg_color=Theme.BG_DARK,
            corner_radius=0,
        )
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_propagate(False)

        # Logo / title
        title_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=(24, 8))

        ctk.CTkLabel(
            title_frame,
            text="\U0001F512 Computer",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            title_frame,
            text="    Lockdown",
            font=Theme.FONT_HEADING,
            text_color=Theme.ACCENT_PRIMARY,
            anchor="w",
        ).pack(fill="x")

        # Thin separator
        ctk.CTkFrame(sidebar, height=1, fg_color=Theme.BORDER).pack(
            fill="x", padx=16, pady=(16, 12)
        )

        # Navigation buttons
        for label, _icon, key in _NAV_ITEMS:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                font=Theme.FONT_BODY,
                fg_color="transparent",
                hover_color=Theme.BG_HOVER,
                text_color=Theme.TEXT_SECONDARY,
                anchor="w",
                height=40,
                corner_radius=8,
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._nav_buttons[key] = btn

        # Spacer
        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # Lock-down button at bottom of sidebar
        ctk.CTkButton(
            sidebar,
            text="\U0001F510  Lock Down",
            font=Theme.FONT_SUBHEADING,
            fg_color=Theme.ACCENT_DANGER,
            hover_color="#dc2626",
            text_color=Theme.TEXT_PRIMARY,
            height=44,
            corner_radius=Theme.CORNER_RADIUS,
            command=self._on_lockdown,
        ).pack(fill="x", padx=16, pady=(8, 24))

    # ------------------------------------------------------------------
    # Content area
    # ------------------------------------------------------------------

    def _create_content_area(self) -> None:
        """Create the right-hand content container."""
        self._content = ctk.CTkFrame(self, fg_color=Theme.BG_DARKEST, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nswe")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Page management
    # ------------------------------------------------------------------

    def show_page(self, page_name: str) -> None:
        """Switch the content area to *page_name*."""
        if page_name == self._active_page:
            return

        # Highlight the active nav button
        for key, btn in self._nav_buttons.items():
            if key == page_name:
                btn.configure(fg_color=Theme.BG_LIGHT, text_color=Theme.TEXT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=Theme.TEXT_SECONDARY)

        # Hide current page
        if self._active_page and self._active_page in self._pages:
            self._pages[self._active_page].grid_forget()

        # Lazily create the page frame
        if page_name not in self._pages:
            self._pages[page_name] = self._make_page(page_name)

        self._pages[page_name].grid(row=0, column=0, sticky="nswe")
        self._active_page = page_name

        # Refresh data if the page exposes a refresh method
        page = self._pages[page_name]
        if hasattr(page, "refresh") and callable(page.refresh):
            try:
                page.refresh()
            except Exception:
                logger.exception("Error refreshing page %s", page_name)

    def _make_page(self, key: str) -> ctk.CTkFrame:
        """Instantiate a page frame for the given key."""
        # Check if an external factory was injected
        if key in self._page_factories:
            return self._page_factories[key](self._content)

        # Built-in pages
        if key == "home":
            return self._build_home_page()
        if key == "downloads":
            return self._build_downloads_page()
        if key == "policies":
            return self._build_policies_page()

        # Fallback placeholder
        return self._build_placeholder_page(key)

    # ------------------------------------------------------------------
    # Home page
    # ------------------------------------------------------------------

    def _build_home_page(self) -> ctk.CTkFrame:
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)

        # -- Admin mode banner --
        banner = ctk.CTkFrame(page, fg_color=Theme.ACCENT_PRIMARY, corner_radius=Theme.CORNER_RADIUS)
        banner.grid(row=0, column=0, sticky="we", padx=24, pady=(24, 16))
        banner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            banner,
            text="\U0001F6E1  ADMIN MODE",
            font=Theme.FONT_HEADING,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(
            banner,
            text="You have full control.  Configure restrictions and lock when done.",
            font=Theme.FONT_SMALL,
            text_color="#c7d2fe",
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

        ctk.CTkButton(
            banner,
            text="Lock Down",
            font=Theme.FONT_SUBHEADING,
            fg_color=Theme.ACCENT_DANGER,
            hover_color="#dc2626",
            text_color=Theme.TEXT_PRIMARY,
            width=140,
            height=38,
            corner_radius=8,
            command=self._on_lockdown,
        ).grid(row=0, column=1, rowspan=2, padx=20, pady=16)

        # -- Status cards grid --
        cards_frame = ctk.CTkFrame(page, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="we", padx=24, pady=(0, 16))
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="card")

        card_data = self._get_status_card_data()
        self._status_card_labels: dict[str, ctk.CTkLabel] = {}
        for idx, (title, value, colour) in enumerate(card_data):
            card = self._make_status_card(cards_frame, title, value, colour)
            card.grid(row=0, column=idx, padx=6, pady=4, sticky="nswe")

        # -- Quick stats --
        stats_frame = ctk.CTkFrame(page, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS)
        stats_frame.grid(row=2, column=0, sticky="we", padx=24, pady=(0, 16))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="stat")

        stats = self._get_quick_stats()
        for idx, (label, val) in enumerate(stats):
            sf = ctk.CTkFrame(stats_frame, fg_color="transparent")
            sf.grid(row=0, column=idx, padx=16, pady=16)
            ctk.CTkLabel(sf, text=str(val), font=Theme.FONT_HEADING, text_color=Theme.ACCENT_PRIMARY).pack()
            ctk.CTkLabel(sf, text=label, font=Theme.FONT_SMALL, text_color=Theme.TEXT_SECONDARY).pack()

        # -- Recent activity log --
        log_label = ctk.CTkLabel(
            page, text="Recent Activity", font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        )
        log_label.grid(row=3, column=0, sticky="w", padx=30, pady=(0, 4))

        log_frame = ctk.CTkScrollableFrame(
            page,
            fg_color=Theme.BG_DARK,
            corner_radius=Theme.CORNER_RADIUS,
            height=200,
        )
        log_frame.grid(row=4, column=0, sticky="we", padx=24, pady=(0, 24))
        log_frame.grid_columnconfigure(0, weight=1)

        self._activity_log_frame = log_frame
        self._populate_activity_log(log_frame)

        # Expose a refresh helper on the page frame
        page.refresh = self._refresh_home  # type: ignore[attr-defined]
        return page

    # ------------------------------------------------------------------
    # Home page helpers
    # ------------------------------------------------------------------

    def _get_status_card_data(self) -> list[tuple[str, str, str]]:
        app_enabled = self._config.get("app_whitelist.enabled", False)
        web_enabled = self._config.get("web_blocking.enabled", False)
        time_enabled = self._config.get("time_limits.enabled", False)
        dl_exts = self._config.get("download_blocking.block_extensions", [])

        return [
            ("App Monitor", "ON" if app_enabled else "OFF",
             Theme.ACCENT_SUCCESS if app_enabled else Theme.TEXT_MUTED),
            ("Web Blocker", "ON" if web_enabled else "OFF",
             Theme.ACCENT_SUCCESS if web_enabled else Theme.TEXT_MUTED),
            ("Time Limits", self._format_time_remaining() if time_enabled else "OFF",
             Theme.ACCENT_WARNING if time_enabled else Theme.TEXT_MUTED),
            ("Downloads", f"{len(dl_exts)} blocked",
             Theme.ACCENT_PRIMARY),
        ]

    def _format_time_remaining(self) -> str:
        limit = self._config.get("time_limits.daily_limit_minutes", 0)
        today = datetime.date.today().isoformat()
        used = self._config.get(f"usage_log.daily_usage_minutes.{today}", 0)
        remaining = max(0, limit - used)
        hours, mins = divmod(remaining, 60)
        return f"{hours}h {mins}m"

    def _get_quick_stats(self) -> list[tuple[str, Any]]:
        apps = self._config.get("app_whitelist.allowed_apps", [])
        mode = self._config.get("web_blocking.mode", "blacklist")
        if mode == "blacklist":
            sites = self._config.get("web_blocking.blocked_sites", [])
        else:
            sites = self._config.get("web_blocking.allowed_sites", [])
        limit = self._config.get("time_limits.daily_limit_minutes", 0)
        hours, mins = divmod(limit, 60)

        return [
            ("Apps whitelisted", len(apps)),
            ("Sites in list", len(sites)),
            ("Daily limit", f"{hours}h {mins}m"),
        ]

    def _make_status_card(
        self,
        parent: ctk.CTkFrame,
        title: str,
        value: str,
        colour: str,
    ) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS)
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            card, text=title, font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))
        lbl = ctk.CTkLabel(
            card, text=value, font=Theme.FONT_HEADING,
            text_color=colour, anchor="w",
        )
        lbl.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 14))
        self._status_card_labels[title] = lbl
        return card

    def _populate_activity_log(self, frame: ctk.CTkScrollableFrame) -> None:
        """Fill the activity log with placeholder entries."""
        # In a real build this would pull from an event bus / database.
        entries = [
            ("No activity recorded yet.", Theme.TEXT_MUTED),
        ]
        for text, colour in entries:
            ctk.CTkLabel(
                frame,
                text=text,
                font=Theme.FONT_SMALL,
                text_color=colour,
                anchor="w",
            ).pack(fill="x", padx=12, pady=4)

    def _refresh_home(self) -> None:
        """Re-read config and update the home page cards & stats."""
        card_data = self._get_status_card_data()
        for title, value, colour in card_data:
            if title in self._status_card_labels:
                self._status_card_labels[title].configure(text=value, text_color=colour)

    # ------------------------------------------------------------------
    # Downloads page (lightweight built-in)
    # ------------------------------------------------------------------

    def _build_downloads_page(self) -> ctk.CTkFrame:
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            page, text="Download Blocking", font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=30, pady=(28, 4))
        ctk.CTkLabel(
            page, text="Manage blocked file extensions from the Settings page.",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=30, pady=(0, 16))

        exts_frame = ctk.CTkFrame(page, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS)
        exts_frame.grid(row=2, column=0, sticky="we", padx=24, pady=8)
        exts = self._config.get("download_blocking.block_extensions", [])
        text = ", ".join(exts) if exts else "None"
        ctk.CTkLabel(
            exts_frame, text=f"Blocked extensions:  {text}",
            font=Theme.FONT_MONO, text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).pack(padx=16, pady=16, fill="x")

        return page

    # ------------------------------------------------------------------
    # Policies page (lightweight built-in)
    # ------------------------------------------------------------------

    def _build_policies_page(self) -> ctk.CTkFrame:
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            page, text="System Policies", font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=30, pady=(28, 4))
        ctk.CTkLabel(
            page, text="Toggle system-level restrictions.  Changes apply immediately.",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY, anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=30, pady=(0, 20))

        policies: list[tuple[str, str]] = [
            ("Block Task Manager", "policy.block_task_manager"),
            ("Block CMD / PowerShell", "policy.block_cmd"),
            ("Block Registry Editor", "policy.block_registry_editor"),
            ("Block Control Panel", "policy.block_control_panel"),
            ("Block Windows Settings", "policy.block_settings"),
        ]

        card = ctk.CTkFrame(page, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS)
        card.grid(row=2, column=0, sticky="we", padx=24)
        card.grid_columnconfigure(0, weight=1)

        for idx, (label, cfg_key) in enumerate(policies):
            row_frame = ctk.CTkFrame(card, fg_color="transparent")
            row_frame.grid(row=idx, column=0, sticky="we", padx=16, pady=8)
            row_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row_frame, text=label, font=Theme.FONT_BODY,
                text_color=Theme.TEXT_PRIMARY, anchor="w",
            ).grid(row=0, column=0, sticky="w")

            current = self._config.get(cfg_key, False)
            var = ctk.BooleanVar(value=current)
            switch = ctk.CTkSwitch(
                row_frame,
                text="",
                variable=var,
                onvalue=True,
                offvalue=False,
                fg_color=Theme.BG_LIGHT,
                progress_color=Theme.ACCENT_SUCCESS,
                button_color=Theme.TEXT_PRIMARY,
                button_hover_color=Theme.ACCENT_HOVER,
                command=lambda k=cfg_key, v=var: self._config.set(k, v.get()),
            )
            switch.grid(row=0, column=1, sticky="e")

            # Separator between rows (except last)
            if idx < len(policies) - 1:
                ctk.CTkFrame(card, height=1, fg_color=Theme.BORDER).grid(
                    row=idx, column=0, sticky="we", padx=16, pady=(0, 0),
                )

        return page

    # ------------------------------------------------------------------
    # Placeholder page
    # ------------------------------------------------------------------

    def _build_placeholder_page(self, key: str) -> ctk.CTkFrame:
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(0, weight=1)
        ctk.CTkLabel(
            page,
            text=f"{key.title()} page",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_MUTED,
        ).grid(row=0, column=0)
        return page

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def refresh_status(self) -> None:
        """Refresh whichever page is currently active."""
        if self._active_page and self._active_page in self._pages:
            page = self._pages[self._active_page]
            if hasattr(page, "refresh") and callable(page.refresh):
                page.refresh()

    def show_home(self) -> None:
        """Convenience alias to switch to the dashboard home page."""
        self.show_page("home")
