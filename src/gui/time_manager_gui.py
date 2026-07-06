"""
Time limits management page for Computer Lockdown.

Provides a daily time-limit slider (0-480 min), per-day start/end schedule
pickers, a usage progress bar, and a remaining-time readout.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

import customtkinter as ctk

from .theme import Theme

logger = logging.getLogger(__name__)

_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_HOURS = [f"{h:02d}" for h in range(24)]
_MINUTES = [f"{m:02d}" for m in (0, 15, 30, 45)]


class TimeManagerPage(ctk.CTkFrame):
    """Time limits management page.

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
        # Let the schedule section expand vertically
        self.grid_rowconfigure(4, weight=1)

        self._build_header()
        self._create_usage_display()
        self._create_time_limit_section()
        self._create_schedule_section()
        self._build_save_bar()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="we", padx=24, pady=(28, 0))
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            hdr,
            text="Time Limits",
            font=Theme.FONT_TITLE,
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkLabel(
            hdr,
            text="Set daily usage limits and allowed hours per day of the week.",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 8))

        # Master toggle
        enabled = self._config.get("time_limits.enabled", True)
        self._enabled_var = ctk.BooleanVar(value=enabled)
        ctk.CTkSwitch(
            hdr,
            text="Enabled",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY,
            variable=self._enabled_var,
            fg_color=Theme.BG_LIGHT,
            progress_color=Theme.ACCENT_SUCCESS,
            button_color=Theme.TEXT_PRIMARY,
            button_hover_color=Theme.ACCENT_HOVER,
        ).grid(row=0, column=1, rowspan=2, sticky="e", padx=6)

    # ------------------------------------------------------------------
    # Usage display (progress bar + remaining time)
    # ------------------------------------------------------------------

    def _create_usage_display(self) -> None:
        card = ctk.CTkFrame(
            self, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS
        )
        card.grid(row=1, column=0, sticky="we", padx=24, pady=(12, 8))
        card.grid_columnconfigure(1, weight=1)

        # Time Used Today
        ctk.CTkLabel(
            card, text="Time Used Today", font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))

        limit = self._config.get("time_limits.daily_limit_minutes", 120)
        today = datetime.date.today().isoformat()
        used = self._config.get(f"usage_log.daily_usage_minutes.{today}", 0)
        remaining = max(0, limit - used)
        fraction = min(used / limit, 1.0) if limit > 0 else 0.0

        self._used_label = ctk.CTkLabel(
            card, text=self._fmt_minutes(used), font=Theme.FONT_BODY,
            text_color=Theme.ACCENT_WARNING, anchor="w",
        )
        self._used_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 2))

        self._progress = ctk.CTkProgressBar(
            card,
            width=400,
            height=14,
            corner_radius=7,
            fg_color=Theme.BG_LIGHT,
            progress_color=self._progress_colour(fraction),
        )
        self._progress.set(fraction)
        self._progress.grid(row=0, column=1, rowspan=2, sticky="we", padx=(8, 16), pady=14)

        # Time Remaining
        self._remaining_label = ctk.CTkLabel(
            card, text=f"Remaining: {self._fmt_minutes(remaining)}",
            font=Theme.FONT_BODY, text_color=Theme.ACCENT_SUCCESS, anchor="e",
        )
        self._remaining_label.grid(row=0, column=2, rowspan=2, sticky="e", padx=16, pady=14)

    # ------------------------------------------------------------------
    # Daily time limit slider
    # ------------------------------------------------------------------

    def _create_time_limit_section(self) -> None:
        card = ctk.CTkFrame(
            self, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS
        )
        card.grid(row=2, column=0, sticky="we", padx=24, pady=(8, 8))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Daily Time Limit", font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 2))

        current_limit = self._config.get("time_limits.daily_limit_minutes", 120)

        self._limit_label = ctk.CTkLabel(
            card, text=self._fmt_minutes(current_limit),
            font=Theme.FONT_HEADING, text_color=Theme.ACCENT_PRIMARY,
            anchor="e",
        )
        self._limit_label.grid(row=0, column=2, sticky="e", padx=16, pady=(14, 2))

        self._limit_slider = ctk.CTkSlider(
            card,
            from_=0,
            to=480,
            number_of_steps=32,  # 15-minute increments
            fg_color=Theme.BG_LIGHT,
            progress_color=Theme.ACCENT_PRIMARY,
            button_color=Theme.TEXT_PRIMARY,
            button_hover_color=Theme.ACCENT_HOVER,
            command=self._on_limit_change,
        )
        self._limit_slider.set(current_limit)
        self._limit_slider.grid(row=1, column=0, columnspan=3, sticky="we", padx=16, pady=(4, 16))

        # Min / max labels
        ctk.CTkLabel(
            card, text="0 min", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED, anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 10))
        ctk.CTkLabel(
            card, text="8 hours", font=Theme.FONT_SMALL,
            text_color=Theme.TEXT_MUTED, anchor="e",
        ).grid(row=2, column=2, sticky="e", padx=16, pady=(0, 10))

    # ------------------------------------------------------------------
    # Per-day schedule
    # ------------------------------------------------------------------

    def _create_schedule_section(self) -> None:
        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.grid(row=3, column=0, sticky="we", padx=24, pady=(8, 0))
        outer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            outer, text="Weekly Schedule", font=Theme.FONT_SUBHEADING,
            text_color=Theme.TEXT_PRIMARY, anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 6))

        card = ctk.CTkFrame(
            outer, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS,
        )
        card.grid(row=1, column=0, sticky="we")
        card.grid_columnconfigure(1, weight=1)

        # Column headers
        for ci, header in enumerate(["Day", "Start", "", "End"]):
            ctk.CTkLabel(
                card, text=header, font=Theme.FONT_SMALL,
                text_color=Theme.TEXT_MUTED,
            ).grid(row=0, column=ci, padx=12, pady=(10, 4))

        self._schedule_vars: dict[str, dict[str, list[ctk.StringVar]]] = {}

        for row_idx, (day_key, day_label) in enumerate(zip(_DAYS, _DAY_LABELS), start=1):
            sched = self._config.get(f"time_limits.schedule.{day_key}", {"start": "15:00", "end": "20:00"})
            start_h, start_m = sched["start"].split(":")
            end_h, end_m = sched["end"].split(":")

            ctk.CTkLabel(
                card, text=day_label, font=Theme.FONT_BODY,
                text_color=Theme.TEXT_PRIMARY, anchor="w",
            ).grid(row=row_idx, column=0, sticky="w", padx=16, pady=4)

            # Start time
            start_frame = ctk.CTkFrame(card, fg_color="transparent")
            start_frame.grid(row=row_idx, column=1, padx=4, pady=4)
            sh_var = ctk.StringVar(value=start_h)
            sm_var = ctk.StringVar(value=start_m)
            self._time_picker(start_frame, sh_var, sm_var)

            ctk.CTkLabel(
                card, text="\u2192", font=Theme.FONT_BODY,
                text_color=Theme.TEXT_MUTED,
            ).grid(row=row_idx, column=2, padx=4)

            # End time
            end_frame = ctk.CTkFrame(card, fg_color="transparent")
            end_frame.grid(row=row_idx, column=3, padx=4, pady=4)
            eh_var = ctk.StringVar(value=end_h)
            em_var = ctk.StringVar(value=end_m)
            self._time_picker(end_frame, eh_var, em_var)

            self._schedule_vars[day_key] = {
                "start": [sh_var, sm_var],
                "end": [eh_var, em_var],
            }

            # Separator
            if row_idx <= len(_DAYS):
                ctk.CTkFrame(card, height=1, fg_color=Theme.BORDER).grid(
                    row=row_idx, column=0, columnspan=4, sticky="we",
                    padx=12, pady=(0, 0),
                )

    def _time_picker(
        self, parent: ctk.CTkFrame, hour_var: ctk.StringVar, minute_var: ctk.StringVar
    ) -> None:
        """Create an HH:MM combo-box pair inside *parent*."""
        h_menu = ctk.CTkOptionMenu(
            parent,
            values=_HOURS,
            variable=hour_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            button_color=Theme.BG_LIGHT,
            button_hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_fg_color=Theme.BG_DARK,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            dropdown_hover_color=Theme.BG_HOVER,
            width=70,
            height=32,
            corner_radius=6,
        )
        h_menu.pack(side="left", padx=(0, 2))

        ctk.CTkLabel(parent, text=":", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED).pack(side="left")

        m_menu = ctk.CTkOptionMenu(
            parent,
            values=_MINUTES,
            variable=minute_var,
            font=Theme.FONT_BODY,
            fg_color=Theme.BG_MEDIUM,
            button_color=Theme.BG_LIGHT,
            button_hover_color=Theme.BG_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            dropdown_fg_color=Theme.BG_DARK,
            dropdown_text_color=Theme.TEXT_PRIMARY,
            dropdown_hover_color=Theme.BG_HOVER,
            width=70,
            height=32,
            corner_radius=6,
        )
        m_menu.pack(side="left", padx=(2, 0))

    # ------------------------------------------------------------------
    # Save bar
    # ------------------------------------------------------------------

    def _build_save_bar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=5, column=0, sticky="e", padx=24, pady=(12, 24))

        ctk.CTkButton(
            bar,
            text="Save Settings",
            font=Theme.FONT_SUBHEADING,
            fg_color=Theme.ACCENT_PRIMARY,
            hover_color=Theme.ACCENT_HOVER,
            text_color=Theme.TEXT_PRIMARY,
            corner_radius=8,
            height=Theme.BUTTON_HEIGHT,
            width=160,
            command=self.save_settings,
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def save_settings(self) -> None:
        """Persist current slider / schedule values to the config."""
        # Enabled toggle
        self._config.set("time_limits.enabled", self._enabled_var.get())

        # Daily limit (round to nearest 15)
        raw = int(self._limit_slider.get())
        rounded = round(raw / 15) * 15
        self._config.set("time_limits.daily_limit_minutes", rounded)

        # Per-day schedule
        for day_key, times in self._schedule_vars.items():
            start = f"{times['start'][0].get()}:{times['start'][1].get()}"
            end = f"{times['end'][0].get()}:{times['end'][1].get()}"
            self._config.set(f"time_limits.schedule.{day_key}", {"start": start, "end": end})

        logger.info("Time-limit settings saved.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fmt_minutes(minutes: int) -> str:
        h, m = divmod(int(minutes), 60)
        return f"{h}h {m:02d}m"

    @staticmethod
    def _progress_colour(fraction: float) -> str:
        if fraction < 0.5:
            return Theme.ACCENT_SUCCESS
        if fraction < 0.8:
            return Theme.ACCENT_WARNING
        return Theme.ACCENT_DANGER

    def _on_limit_change(self, value: float) -> None:
        rounded = round(value / 15) * 15
        self._limit_label.configure(text=self._fmt_minutes(int(rounded)))

    # ------------------------------------------------------------------
    # Public alias
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Reload data from config when page is re-selected."""
        limit = self._config.get("time_limits.daily_limit_minutes", 120)
        self._limit_slider.set(limit)
        self._limit_label.configure(text=self._fmt_minutes(limit))

        today = datetime.date.today().isoformat()
        used = self._config.get(f"usage_log.daily_usage_minutes.{today}", 0)
        remaining = max(0, limit - used)
        fraction = min(used / limit, 1.0) if limit > 0 else 0.0

        self._used_label.configure(text=self._fmt_minutes(used))
        self._progress.set(fraction)
        self._progress.configure(progress_color=self._progress_colour(fraction))
        self._remaining_label.configure(text=f"Remaining: {self._fmt_minutes(remaining)}")
