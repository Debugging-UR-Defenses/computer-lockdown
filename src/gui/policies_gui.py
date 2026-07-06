"""
Security policies management page for Computer Lockdown admin dashboard.

Provides toggle switches for Windows security policies (Task Manager,
Command Prompt, Registry Editor, etc.) and network/LAN rules.
"""

from __future__ import annotations

import logging
from typing import Any

import customtkinter as ctk

from .theme import Theme

logger = logging.getLogger(__name__)


class PoliciesManagerPage(ctk.CTkFrame):
    """Admin page for managing security policies and network rules."""

    POLICIES = [
        ("block_task_manager", "Block Task Manager"),
        ("block_cmd", "Block Command Prompt"),
        ("block_registry_editor", "Block Registry Editor"),
        ("block_control_panel", "Block Control Panel"),
        ("block_settings", "Block Windows Settings"),
    ]

    def __init__(self, parent: ctk.CTkFrame, config_manager: Any) -> None:
        super().__init__(parent, fg_color="transparent")
        self._config = config_manager
        self._vars: dict[str, ctk.StringVar] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        ctk.CTkLabel(
            scroll, text="Security Policies",
            font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            scroll,
            text="Control which Windows system tools are restricted.",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_SECONDARY,
        ).pack(anchor="w", pady=(0, 16))

        for key, label in self.POLICIES:
            self._build_policy_row(scroll, key, label)

        # Network rules section
        ctk.CTkFrame(scroll, height=1, fg_color=Theme.BORDER).pack(fill="x", pady=16)
        ctk.CTkLabel(
            scroll, text="Network / LAN Rules",
            font=Theme.FONT_SUBHEADING, text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w", pady=(0, 8))

        net_row = ctk.CTkFrame(scroll, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS)
        net_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            net_row, text="Enable network rules",
            font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left", padx=12, pady=10)
        net_enabled = self._config.get("network_rules.enabled", False)
        self._net_var = ctk.StringVar(value="on" if net_enabled else "off")
        ctk.CTkSwitch(
            net_row, text="", variable=self._net_var,
            onvalue="on", offvalue="off",
            command=self._toggle_network,
        ).pack(side="right", padx=12, pady=10)

        services = self._config.get("network_rules.allowed_lan_services", [])
        for svc in services:
            self._build_service_row(scroll, svc)

    def _build_policy_row(self, parent, key, label):
        row = ctk.CTkFrame(parent, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS)
        row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            row, text=label,
            font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left", padx=12, pady=10)
        enabled = self._config.get(f"policy.{key}", False)
        var = ctk.StringVar(value="on" if enabled else "off")
        self._vars[key] = var
        ctk.CTkSwitch(
            row, text="", variable=var,
            onvalue="on", offvalue="off",
            command=lambda k=key: self._toggle_policy(k),
        ).pack(side="right", padx=12, pady=10)

    def _build_service_row(self, parent, svc):
        row = ctk.CTkFrame(parent, fg_color=Theme.BG_DARK, corner_radius=Theme.CORNER_RADIUS)
        row.pack(fill="x", pady=(0, 4))
        info = ctk.CTkFrame(row, fg_color="transparent")
        info.pack(side="left", padx=12, pady=8)
        ctk.CTkLabel(
            info, text=svc.get("name", ""),
            font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            info,
            text=f"{svc.get('protocol', 'tcp')}/{svc.get('port', '')} - {svc.get('description', '')}",
            font=Theme.FONT_SMALL, text_color=Theme.TEXT_MUTED,
        ).pack(anchor="w")

    def _toggle_policy(self, key):
        val = self._vars[key].get() == "on"
        self._config.set(f"policy.{key}", val)

    def _toggle_network(self):
        val = self._net_var.get() == "on"
        self._config.set("network_rules.enabled", val)
