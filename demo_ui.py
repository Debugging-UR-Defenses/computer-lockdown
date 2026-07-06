"""
Computer Lockdown - UI Demo
Self-contained preview of the UI. No backend, no Windows APIs, no dependencies
beyond customtkinter. Run with: python demo_ui.py
"""

import customtkinter as ctk
import sys

# ── Theme ─────────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Use system-appropriate fonts
if sys.platform == "darwin":
    FONT_FAMILY = "SF Pro Display"
    FONT_MONO = "SF Mono"
    EMOJI_FONT = ("Apple Color Emoji", 56)
else:
    FONT_FAMILY = "Segoe UI"
    FONT_MONO = "Consolas"
    EMOJI_FONT = ("Segoe UI Emoji", 56)

BG_DARKEST  = "#0d0d0d"
BG_DARK     = "#1a1a2e"
BG_MEDIUM   = "#16213e"
BG_LIGHT    = "#1e2a4a"
BG_HOVER    = "#2a3a5c"

ACCENT      = "#4f46e5"
ACCENT_HVR  = "#6366f1"
SUCCESS     = "#22c55e"
WARNING     = "#f59e0b"
DANGER      = "#ef4444"

TEXT        = "#f1f5f9"
TEXT_SEC    = "#94a3b8"
TEXT_MUTED  = "#64748b"
BORDER      = "#2a2a4a"

FONT_TITLE  = (FONT_FAMILY, 24, "bold")
FONT_HEAD   = (FONT_FAMILY, 18, "bold")
FONT_SUB    = (FONT_FAMILY, 14, "bold")
FONT_BODY   = (FONT_FAMILY, 12)
FONT_SMALL  = (FONT_FAMILY, 10)
RADIUS      = 12


# ── Fake config for demo ─────────────────────────────────────────────────────

class DemoConfig:
    """Minimal config mock so UI pages can call .get() / .set()."""
    _data = {
        "admin_mode": False,
        "app_whitelist.enabled": True,
        "app_whitelist.allowed_apps": [
            {"name": "Google Chrome", "path": "C:\\Program Files\\Google\\Chrome\\chrome.exe"},
            {"name": "Microsoft Edge", "path": "C:\\Program Files\\Microsoft\\Edge\\msedge.exe"},
            {"name": "File Explorer", "path": "C:\\Windows\\explorer.exe"},
            {"name": "Notepad", "path": "C:\\Windows\\notepad.exe"},
            {"name": "Calculator", "path": "C:\\Windows\\calc.exe"},
            {"name": "Minecraft", "path": "C:\\Games\\Minecraft\\minecraft.exe"},
        ],
        "web_blocking.enabled": True,
        "web_blocking.mode": "blacklist",
        "web_blocking.blocked_sites": [
            "facebook.com", "instagram.com", "tiktok.com", "twitter.com",
            "reddit.com", "snapchat.com", "twitch.tv",
        ],
        "web_blocking.allowed_sites": [],
        "time_limits.enabled": True,
        "time_limits.daily_limit_minutes": 120,
        "time_limits.schedule.monday.start": "15:00",
        "time_limits.schedule.monday.end": "20:00",
        "time_limits.schedule.tuesday.start": "15:00",
        "time_limits.schedule.tuesday.end": "20:00",
        "time_limits.schedule.wednesday.start": "15:00",
        "time_limits.schedule.wednesday.end": "20:00",
        "time_limits.schedule.thursday.start": "15:00",
        "time_limits.schedule.thursday.end": "20:00",
        "time_limits.schedule.friday.start": "15:00",
        "time_limits.schedule.friday.end": "21:00",
        "time_limits.schedule.saturday.start": "10:00",
        "time_limits.schedule.saturday.end": "21:00",
        "time_limits.schedule.sunday.start": "10:00",
        "time_limits.schedule.sunday.end": "20:00",
        "download_blocking.enabled": True,
        "download_blocking.block_extensions": [
            ".exe", ".msi", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".wsf", ".scr"
        ],
        "time_limits.hard_cutoff": "20:30",
        "time_limits.warning_minutes": 10,
        "time_limits.schedule.monday.enabled": True,
        "time_limits.schedule.tuesday.enabled": True,
        "time_limits.schedule.wednesday.enabled": True,
        "time_limits.schedule.thursday.enabled": True,
        "time_limits.schedule.friday.enabled": True,
        "time_limits.schedule.saturday.enabled": True,
        "time_limits.schedule.sunday.enabled": True,
        "app_whitelist.allowed_services": [
            {"name": "Bamboo Connect", "path": "BambuConnect.exe", "parent_app": "Bambu Studio"},
            {"name": "Windows Defender", "path": "MsMpEng.exe", "parent_app": "System"},
            {"name": "Windows Update", "path": "wuauclt.exe", "parent_app": "System"},
        ],
        "app_whitelist.auto_detect_dependencies": True,
        "download_blocking.block_all_in_locked_mode": True,
        "download_blocking.review_queue": [
            {"filename": "setup_hack.exe", "original_path": "C:\\Users\\Kid\\Downloads\\setup_hack.exe", "quarantine_path": "C:\\quarantine\\setup_hack.exe", "timestamp": "2026-07-05T14:14:00", "extension": ".exe", "status": "pending"},
            {"filename": "free_vbucks.bat", "original_path": "C:\\Users\\Kid\\Downloads\\free_vbucks.bat", "quarantine_path": "C:\\quarantine\\free_vbucks.bat", "timestamp": "2026-07-05T13:02:00", "extension": ".bat", "status": "pending"},
            {"filename": "homework_template.docx", "original_path": "C:\\Users\\Kid\\Downloads\\homework_template.docx", "quarantine_path": "C:\\quarantine\\homework_template.docx", "timestamp": "2026-07-05T12:30:00", "extension": ".docx", "status": "pending"},
            {"filename": "mod_installer.msi", "original_path": "C:\\Users\\Kid\\Downloads\\mod_installer.msi", "quarantine_path": "", "timestamp": "2026-07-04T16:30:00", "extension": ".msi", "status": "denied"},
            {"filename": "school_project.pdf", "original_path": "C:\\Users\\Kid\\Downloads\\school_project.pdf", "quarantine_path": "", "timestamp": "2026-07-04T15:00:00", "extension": ".pdf", "status": "approved"},
        ],
        "network_rules.enabled": False,
        "network_rules.allowed_lan_services": [
            {"name": "Bamboo Connect LAN", "protocol": "tcp", "port": 8989, "description": "Bambu Studio printer communication"},
            {"name": "Local DNS", "protocol": "udp", "port": 53, "description": "DNS resolution"},
        ],
        "policy.block_task_manager": True,
        "policy.block_cmd": True,
        "policy.block_registry_editor": True,
        "policy.block_control_panel": False,
        "policy.block_settings": False,
    }

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value


config = DemoConfig()


# ── Locked Screen ─────────────────────────────────────────────────────────────

class LockedScreen(ctk.CTkFrame):
    def __init__(self, parent, on_unlock):
        super().__init__(parent, fg_color=BG_DARKEST, corner_radius=0)
        self._on_unlock = on_unlock

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        c = ctk.CTkFrame(self, fg_color="transparent")
        c.grid(row=0, column=0)

        # Padlock
        ctk.CTkLabel(c, text="\U0001F512", font=EMOJI_FONT, text_color=DANGER).pack(pady=(0, 12))

        # Title
        ctk.CTkLabel(c, text="Computer Lockdown", font=FONT_TITLE, text_color=TEXT).pack(pady=(0, 4))

        # Status
        ctk.CTkLabel(c, text="System is locked", font=FONT_BODY, text_color=DANGER).pack(pady=(0, 24))

        # Glow line
        ctk.CTkFrame(c, height=2, width=260, fg_color=DANGER, corner_radius=1).pack(pady=(0, 24))

        # Password entry (always visible)
        self._pw_entry = ctk.CTkEntry(
            c, placeholder_text="Enter admin password", show="*",
            font=FONT_BODY, fg_color=BG_MEDIUM, border_color=BORDER,
            text_color=TEXT, placeholder_text_color=TEXT_MUTED,
            corner_radius=RADIUS, height=40, width=260,
        )
        self._pw_entry.pack(pady=(0, 10))
        self._pw_entry.bind("<Return>", lambda _: self._try_unlock())

        # Unlock button
        ctk.CTkButton(
            c, text="Unlock", font=FONT_SUB,
            fg_color=ACCENT, hover_color=ACCENT_HVR, text_color=TEXT,
            corner_radius=RADIUS, height=40, width=260,
            command=self._try_unlock,
        ).pack(pady=(0, 6))

        # Error label
        self._err = ctk.CTkLabel(c, text="", font=FONT_SMALL, text_color=DANGER)
        self._err.pack(pady=(4, 0))

    def _try_unlock(self):
        pw = self._pw_entry.get().strip()
        if not pw:
            self._err.configure(text="Please enter a password.")
            return
        # Demo: any password works
        self._on_unlock()

    def reset(self):
        self._pw_entry.delete(0, "end")
        self._err.configure(text="")


# ── Admin Dashboard ───────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("\U0001F3E0  Dashboard", "home"),
    ("\U0001F4BB  Applications", "apps"),
    ("\U0001F310  Websites", "websites"),
    ("\u23F1  Time Limits", "time"),
    ("\U0001F4E5  Downloads", "downloads"),
    ("\U0001F6E1  Policies", "policies"),
    ("\u2699  Settings", "settings"),
]


class AdminDashboard(ctk.CTkFrame):
    def __init__(self, parent, on_lock):
        super().__init__(parent, fg_color=BG_DARKEST, corner_radius=0)
        self._on_lock = on_lock
        self._pages = {}
        self._active = None
        self._nav_btns = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._content = ctk.CTkFrame(self, fg_color=BG_DARKEST, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nswe")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self.show_page("home")

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=250, fg_color=BG_DARK, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nswe")
        sb.grid_propagate(False)

        tf = ctk.CTkFrame(sb, fg_color="transparent")
        tf.pack(fill="x", padx=16, pady=(24, 8))
        ctk.CTkLabel(tf, text="\U0001F512 Computer", font=FONT_HEAD, text_color=TEXT, anchor="w").pack(fill="x")
        ctk.CTkLabel(tf, text="    Lockdown", font=FONT_HEAD, text_color=ACCENT, anchor="w").pack(fill="x")

        ctk.CTkFrame(sb, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(16, 12))

        for label, key in NAV_ITEMS:
            btn = ctk.CTkButton(
                sb, text=label, font=FONT_BODY,
                fg_color="transparent", hover_color=BG_HOVER,
                text_color=TEXT_SEC, anchor="w", height=40, corner_radius=8,
                command=lambda k=key: self.show_page(k),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self._nav_btns[key] = btn

        ctk.CTkFrame(sb, fg_color="transparent").pack(fill="both", expand=True)

        ctk.CTkButton(
            sb, text="\U0001F510  Lock Down", font=FONT_SUB,
            fg_color=DANGER, hover_color="#dc2626", text_color=TEXT,
            height=44, corner_radius=RADIUS, command=self._on_lock,
        ).pack(fill="x", padx=16, pady=(8, 24))

    def show_page(self, key):
        if key == self._active:
            return
        for k, b in self._nav_btns.items():
            b.configure(
                fg_color=BG_LIGHT if k == key else "transparent",
                text_color=TEXT if k == key else TEXT_SEC,
            )
        if self._active and self._active in self._pages:
            self._pages[self._active].grid_forget()
        if key not in self._pages:
            self._pages[key] = self._make_page(key)
        self._pages[key].grid(row=0, column=0, sticky="nswe")
        self._active = key

    def _make_page(self, key):
        builders = {
            "home": self._home,
            "apps": self._apps,
            "websites": self._websites,
            "time": self._time,
            "downloads": self._downloads,
            "policies": self._policies,
            "settings": self._settings,
        }
        return builders.get(key, self._placeholder)(key)

    # ── Home ──────────────────────────────────────────────────────────────

    def _home(self, _key="home"):
        p = ctk.CTkFrame(self._content, fg_color="transparent")
        p.grid_columnconfigure(0, weight=1)

        # Banner
        banner = ctk.CTkFrame(p, fg_color=ACCENT, corner_radius=RADIUS)
        banner.grid(row=0, column=0, sticky="we", padx=24, pady=(24, 16))
        banner.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(banner, text="\U0001F6E1  ADMIN MODE", font=FONT_HEAD, text_color=TEXT, anchor="w").grid(
            row=0, column=0, sticky="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(banner, text="You have full control. Configure restrictions and lock when done.",
                     font=FONT_SMALL, text_color="#c7d2fe", anchor="w").grid(
            row=1, column=0, sticky="w", padx=20, pady=(0, 16))
        ctk.CTkButton(banner, text="Lock Down", font=FONT_SUB, fg_color=DANGER, hover_color="#dc2626",
                      text_color=TEXT, width=140, height=38, corner_radius=8,
                      command=self._on_lock).grid(row=0, column=1, rowspan=2, padx=20, pady=16)

        # Status cards
        cards = ctk.CTkFrame(p, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="we", padx=24, pady=(0, 16))
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1, uniform="card")

        card_data = [
            ("App Monitor", "ON", SUCCESS),
            ("Web Blocker", "ON", SUCCESS),
            ("Time Limits", "1h 42m", WARNING),
            ("Downloads", "9 blocked", ACCENT),
        ]
        for i, (title, val, color) in enumerate(card_data):
            c = ctk.CTkFrame(cards, fg_color=BG_DARK, corner_radius=RADIUS)
            c.grid(row=0, column=i, padx=6, pady=4, sticky="nswe")
            c.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(c, text=title, font=FONT_SMALL, text_color=TEXT_SEC, anchor="w").grid(
                row=0, column=0, sticky="w", padx=16, pady=(14, 2))
            ctk.CTkLabel(c, text=val, font=FONT_HEAD, text_color=color, anchor="w").grid(
                row=1, column=0, sticky="w", padx=16, pady=(0, 14))

        # Quick stats
        stats = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        stats.grid(row=2, column=0, sticky="we", padx=24, pady=(0, 16))
        stats.grid_columnconfigure((0, 1, 2), weight=1, uniform="stat")
        for i, (label, val) in enumerate([("Apps whitelisted", "6"), ("Sites blocked", "7"), ("Daily limit", "2h 0m")]):
            sf = ctk.CTkFrame(stats, fg_color="transparent")
            sf.grid(row=0, column=i, padx=16, pady=16)
            ctk.CTkLabel(sf, text=val, font=FONT_HEAD, text_color=ACCENT).pack()
            ctk.CTkLabel(sf, text=label, font=FONT_SMALL, text_color=TEXT_SEC).pack()

        # Activity log
        ctk.CTkLabel(p, text="Recent Activity", font=FONT_SUB, text_color=TEXT, anchor="w").grid(
            row=3, column=0, sticky="w", padx=30, pady=(0, 4))
        log = ctk.CTkScrollableFrame(p, fg_color=BG_DARK, corner_radius=RADIUS, height=160)
        log.grid(row=4, column=0, sticky="we", padx=24, pady=(0, 24))

        demo_log = [
            ("\u26D4  Blocked: discord.exe (not whitelisted)", DANGER),
            ("\u26D4  Blocked download: setup_hack.exe", DANGER),
            ("\u2705  Allowed: chrome.exe", SUCCESS),
            ("\u23F1  Time warning: 10 minutes remaining", WARNING),
            ("\u26D4  Blocked: cmd.exe (policy)", DANGER),
            ("\u2705  Allowed: explorer.exe", SUCCESS),
            ("\U0001F310  Blocked site: tiktok.com", DANGER),
            ("\u26D4  Blocked download: free_vbucks.bat", DANGER),
        ]
        for text, color in demo_log:
            ctk.CTkLabel(log, text=text, font=FONT_SMALL, text_color=color, anchor="w").pack(fill="x", padx=12, pady=3)

        return p

    # ── Applications ──────────────────────────────────────────────────────

    def _apps(self, _key="apps"):
        p = ctk.CTkScrollableFrame(self._content, fg_color="transparent")

        # Header
        hdr = ctk.CTkFrame(p, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(24, 4))
        ctk.CTkLabel(hdr, text="Application Whitelist", font=FONT_TITLE, text_color=TEXT, anchor="w").pack(
            fill="x")
        ctk.CTkLabel(hdr, text="Only these applications are allowed to run when locked.",
                     font=FONT_SMALL, text_color=TEXT_SEC, anchor="w").pack(fill="x", pady=(2, 0))

        # Toggle + buttons
        tb = ctk.CTkFrame(p, fg_color="transparent")
        tb.pack(fill="x", padx=24, pady=(12, 8))
        ctk.CTkLabel(tb, text="Enabled", font=FONT_BODY, text_color=TEXT_SEC).pack(side="left")
        sw = ctk.CTkSwitch(tb, text="", onvalue=True, offvalue=False, width=46)
        sw.select()
        sw.pack(side="left", padx=8)
        ctk.CTkButton(tb, text="+ Add Application", font=FONT_BODY, fg_color=ACCENT, hover_color=ACCENT_HVR,
                      text_color=TEXT, corner_radius=8, height=34, width=160).pack(side="right", padx=(8, 0))
        ctk.CTkButton(tb, text="Scan Running", font=FONT_BODY, fg_color=BG_MEDIUM, hover_color=BG_HOVER,
                      text_color=TEXT_SEC, corner_radius=8, height=34, width=130).pack(side="right")

        # Search
        ctk.CTkEntry(p, placeholder_text="Search applications...", font=FONT_BODY, fg_color=BG_MEDIUM,
                     border_color=BORDER, text_color=TEXT, placeholder_text_color=TEXT_MUTED,
                     corner_radius=8, height=36).pack(fill="x", padx=24, pady=(0, 8))

        # App list
        lst = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        lst.pack(fill="x", padx=24, pady=(0, 16))

        apps = config.get("app_whitelist.allowed_apps", [])
        for i, app in enumerate(apps):
            row = ctk.CTkFrame(lst, fg_color=BG_MEDIUM if i % 2 == 0 else "transparent", corner_radius=8)
            row.pack(fill="x", padx=4, pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=app["name"], font=FONT_BODY, text_color=TEXT, anchor="w").grid(
                row=0, column=0, sticky="w", padx=12, pady=(8, 1))
            ctk.CTkLabel(row, text=app["path"], font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w").grid(
                row=1, column=0, sticky="w", padx=12, pady=(0, 8))
            ctk.CTkButton(row, text="Remove", font=FONT_SMALL, fg_color=DANGER, hover_color="#dc2626",
                          text_color=TEXT, width=70, height=28, corner_radius=6).grid(
                row=0, column=1, rowspan=2, sticky="e", padx=12, pady=8)

        # ── Services Section ──────────────────────────────────────────────
        ctk.CTkFrame(p, height=1, fg_color=BORDER).pack(fill="x", padx=24, pady=(8, 16))

        svc_hdr = ctk.CTkFrame(p, fg_color="transparent")
        svc_hdr.pack(fill="x", padx=24, pady=(0, 4))
        ctk.CTkLabel(svc_hdr, text="Allowed Services & Background Processes", font=FONT_HEAD, text_color=TEXT,
                     anchor="w").pack(fill="x")
        ctk.CTkLabel(svc_hdr, text="These services are always allowed to run (e.g. printer communication, updaters).",
                     font=FONT_SMALL, text_color=TEXT_SEC, anchor="w").pack(fill="x", pady=(2, 0))

        svc_btns = ctk.CTkFrame(p, fg_color="transparent")
        svc_btns.pack(fill="x", padx=24, pady=(8, 8))
        ctk.CTkButton(svc_btns, text="+ Add Service", font=FONT_BODY, fg_color=ACCENT, hover_color=ACCENT_HVR,
                      text_color=TEXT, corner_radius=8, height=34, width=130).pack(side="left", padx=(0, 8))
        ctk.CTkButton(svc_btns, text="Auto-Detect", font=FONT_BODY, fg_color=BG_MEDIUM, hover_color=BG_HOVER,
                      text_color=TEXT_SEC, corner_radius=8, height=34, width=120).pack(side="left")

        svc_lst = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        svc_lst.pack(fill="x", padx=24, pady=(0, 24))

        services = config.get("app_whitelist.allowed_services", [])
        for i, svc in enumerate(services):
            row = ctk.CTkFrame(svc_lst, fg_color=BG_MEDIUM if i % 2 == 0 else "transparent", corner_radius=8)
            row.pack(fill="x", padx=4, pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=svc["name"], font=FONT_BODY, text_color=TEXT, anchor="w").grid(
                row=0, column=0, sticky="w", padx=12, pady=(8, 1))
            detail_text = f"{svc['path']}  \u2022  Parent: {svc['parent_app']}"
            ctk.CTkLabel(row, text=detail_text, font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w").grid(
                row=1, column=0, sticky="w", padx=12, pady=(0, 8))
            ctk.CTkButton(row, text="Remove", font=FONT_SMALL, fg_color=DANGER, hover_color="#dc2626",
                          text_color=TEXT, width=70, height=28, corner_radius=6).grid(
                row=0, column=1, rowspan=2, sticky="e", padx=12, pady=8)

        return p

    # ── Websites ──────────────────────────────────────────────────────────

    def _websites(self, _key="websites"):
        p = ctk.CTkFrame(self._content, fg_color="transparent")
        p.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(p, text="Website Blocking", font=FONT_TITLE, text_color=TEXT, anchor="w").grid(
            row=0, column=0, sticky="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(p, text="Block specific websites or allow only approved ones.",
                     font=FONT_SMALL, text_color=TEXT_SEC, anchor="w").grid(row=1, column=0, sticky="w", padx=24)

        # Mode toggle
        mode_row = ctk.CTkFrame(p, fg_color="transparent")
        mode_row.grid(row=2, column=0, sticky="we", padx=24, pady=(12, 8))
        ctk.CTkLabel(mode_row, text="Mode:", font=FONT_BODY, text_color=TEXT_SEC).pack(side="left")
        ctk.CTkSegmentedButton(mode_row, values=["Blacklist", "Whitelist"], font=FONT_BODY,
                               selected_color=ACCENT, selected_hover_color=ACCENT_HVR,
                               unselected_color=BG_MEDIUM, unselected_hover_color=BG_HOVER,
                               text_color=TEXT).pack(side="left", padx=12)
        ctk.CTkSwitch(mode_row, text="Enabled", font=FONT_BODY, text_color=TEXT_SEC).pack(side="right")

        # Add site
        add_row = ctk.CTkFrame(p, fg_color="transparent")
        add_row.grid(row=3, column=0, sticky="we", padx=24, pady=(0, 8))
        add_row.grid_columnconfigure(0, weight=1)
        ctk.CTkEntry(add_row, placeholder_text="Enter website domain (e.g. youtube.com)", font=FONT_BODY,
                     fg_color=BG_MEDIUM, border_color=BORDER, text_color=TEXT,
                     placeholder_text_color=TEXT_MUTED, corner_radius=8, height=36).grid(
            row=0, column=0, sticky="we", padx=(0, 8))
        ctk.CTkButton(add_row, text="+ Add", font=FONT_BODY, fg_color=ACCENT, hover_color=ACCENT_HVR,
                      text_color=TEXT, corner_radius=8, height=36, width=80).grid(row=0, column=1)

        # Quick-add categories
        cat_row = ctk.CTkFrame(p, fg_color="transparent")
        cat_row.grid(row=4, column=0, sticky="we", padx=24, pady=(0, 12))
        ctk.CTkLabel(cat_row, text="Quick add:", font=FONT_SMALL, text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))
        for cat in ["Social Media", "Gaming", "Streaming", "Adult Content"]:
            ctk.CTkButton(cat_row, text=cat, font=FONT_SMALL, fg_color=BG_MEDIUM, hover_color=BG_HOVER,
                          text_color=TEXT_SEC, corner_radius=6, height=28, width=100).pack(side="left", padx=3)

        # Site list
        lst = ctk.CTkScrollableFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        lst.grid(row=5, column=0, sticky="nswe", padx=24, pady=(0, 24))
        p.grid_rowconfigure(5, weight=1)

        sites = config.get("web_blocking.blocked_sites", [])
        for site in sites:
            row = ctk.CTkFrame(lst, fg_color="transparent", corner_radius=8)
            row.pack(fill="x", padx=4, pady=2)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=f"\U0001F6AB  {site}", font=FONT_BODY, text_color=TEXT, anchor="w").grid(
                row=0, column=0, sticky="w", padx=12, pady=8)
            ctk.CTkButton(row, text="X", font=FONT_SMALL, fg_color=DANGER, hover_color="#dc2626",
                          text_color=TEXT, width=32, height=28, corner_radius=6).grid(
                row=0, column=1, sticky="e", padx=12, pady=8)

        return p

    # ── Time Limits ───────────────────────────────────────────────────────

    def _time(self, _key="time"):
        p = ctk.CTkScrollableFrame(self._content, fg_color="transparent")

        ctk.CTkLabel(p, text="Time Limits", font=FONT_TITLE, text_color=TEXT, anchor="w").pack(
            fill="x", padx=24, pady=(24, 4))
        ctk.CTkLabel(p, text="Set daily usage limits and allowed hours per day.",
                     font=FONT_SMALL, text_color=TEXT_SEC, anchor="w").pack(fill="x", padx=24)

        # Daily limit slider
        lim_frame = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        lim_frame.pack(fill="x", padx=24, pady=(16, 12))
        lim_frame.grid_columnconfigure(0, weight=1)

        lim_hdr = ctk.CTkFrame(lim_frame, fg_color="transparent")
        lim_hdr.grid(row=0, column=0, sticky="we", padx=16, pady=(14, 4))
        lim_hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lim_hdr, text="Daily Time Limit", font=FONT_SUB, text_color=TEXT, anchor="w").grid(
            row=0, column=0, sticky="w")
        self._limit_label = ctk.CTkLabel(lim_hdr, text="2h 0m", font=FONT_SUB, text_color=ACCENT, anchor="e")
        self._limit_label.grid(row=0, column=1, sticky="e")

        self._limit_slider = ctk.CTkSlider(
            lim_frame, from_=0, to=480, number_of_steps=32,
            fg_color=BG_MEDIUM, progress_color=ACCENT, button_color=ACCENT_HVR,
            button_hover_color=TEXT, width=400,
            command=self._on_slider,
        )
        self._limit_slider.set(120)
        self._limit_slider.grid(row=1, column=0, sticky="we", padx=16, pady=(0, 14))

        # Usage progress
        usage_frame = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        usage_frame.pack(fill="x", padx=24, pady=(0, 12))
        usage_frame.grid_columnconfigure(0, weight=1)

        uf_hdr = ctk.CTkFrame(usage_frame, fg_color="transparent")
        uf_hdr.grid(row=0, column=0, sticky="we", padx=16, pady=(14, 6))
        uf_hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(uf_hdr, text="Today's Usage", font=FONT_SUB, text_color=TEXT, anchor="w").grid(
            row=0, column=0, sticky="w")
        ctk.CTkLabel(uf_hdr, text="18m / 2h 0m", font=FONT_BODY, text_color=TEXT_SEC, anchor="e").grid(
            row=0, column=1, sticky="e")

        prog = ctk.CTkProgressBar(usage_frame, progress_color=SUCCESS, fg_color=BG_MEDIUM, height=12,
                                  corner_radius=6)
        prog.set(18 / 120)  # ~15%
        prog.grid(row=1, column=0, sticky="we", padx=16, pady=(0, 6))
        ctk.CTkLabel(usage_frame, text="1h 42m remaining", font=FONT_SMALL, text_color=SUCCESS, anchor="w").grid(
            row=2, column=0, sticky="w", padx=16, pady=(0, 14))

        # Hard Cutoff Time
        cutoff_frame = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        cutoff_frame.pack(fill="x", padx=24, pady=(0, 12))

        cutoff_hdr = ctk.CTkFrame(cutoff_frame, fg_color="transparent")
        cutoff_hdr.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(cutoff_hdr, text="Hard Cutoff Time", font=FONT_SUB, text_color=TEXT, anchor="w").pack(
            side="left")

        cutoff_row = ctk.CTkFrame(cutoff_frame, fg_color="transparent")
        cutoff_row.pack(fill="x", padx=16, pady=(0, 4))

        hours = [str(h).zfill(2) for h in range(24)]
        minutes = [str(m).zfill(2) for m in range(0, 60, 5)]

        ctk.CTkLabel(cutoff_row, text="Hour:", font=FONT_BODY, text_color=TEXT_SEC).pack(side="left", padx=(0, 4))
        hour_menu = ctk.CTkOptionMenu(cutoff_row, values=hours, font=FONT_BODY,
                                      fg_color=BG_MEDIUM, button_color=BG_HOVER, button_hover_color=ACCENT,
                                      text_color=TEXT, width=70, height=32, corner_radius=8)
        hour_menu.set("20")
        hour_menu.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(cutoff_row, text="Minute:", font=FONT_BODY, text_color=TEXT_SEC).pack(side="left", padx=(0, 4))
        min_menu = ctk.CTkOptionMenu(cutoff_row, values=minutes, font=FONT_BODY,
                                     fg_color=BG_MEDIUM, button_color=BG_HOVER, button_hover_color=ACCENT,
                                     text_color=TEXT, width=70, height=32, corner_radius=8)
        min_menu.set("30")
        min_menu.pack(side="left")

        ctk.CTkLabel(cutoff_frame, text="Computer locks at this time regardless of remaining usage.",
                     font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w").pack(fill="x", padx=16, pady=(0, 14))

        # Weekly schedule
        sched = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        sched.pack(fill="x", padx=24, pady=(0, 24))
        sched.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(sched, text="Weekly Schedule", font=FONT_SUB, text_color=TEXT, anchor="w").grid(
            row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(14, 8))

        days = [("Mon", "monday", "15:00", "20:00"), ("Tue", "tuesday", "15:00", "20:00"),
                ("Wed", "wednesday", "15:00", "20:00"), ("Thu", "thursday", "15:00", "20:00"),
                ("Fri", "friday", "15:00", "21:00"), ("Sat", "saturday", "10:00", "21:00"),
                ("Sun", "sunday", "10:00", "20:00")]
        self._day_time_labels = []
        for i, (day_short, day_full, start, end) in enumerate(days):
            r = i + 1
            enabled = config.get(f"time_limits.schedule.{day_full}.enabled", True)

            sw = ctk.CTkSwitch(sched, text="", width=46, onvalue=True, offvalue=False)
            if enabled:
                sw.select()
            sw.grid(row=r, column=0, padx=(16, 4), pady=3)

            day_label = ctk.CTkLabel(sched, text=day_short, font=FONT_BODY,
                                     text_color=TEXT if enabled else TEXT_MUTED, width=40)
            day_label.grid(row=r, column=1, padx=(0, 8), pady=3)

            time_label = ctk.CTkLabel(sched, text=f"{start}  -  {end}", font=(FONT_MONO, 12),
                                      text_color=ACCENT if enabled else TEXT_MUTED)
            time_label.grid(row=r, column=2, sticky="w", padx=8, pady=3)

            self._day_time_labels.append((sw, day_label, time_label))

            # Bind toggle to dim/undim the row
            def _make_toggle(s=sw, dl=day_label, tl=time_label):
                def _toggle():
                    on = s.get()
                    dl.configure(text_color=TEXT if on else TEXT_MUTED)
                    tl.configure(text_color=ACCENT if on else TEXT_MUTED)
                return _toggle
            sw.configure(command=_make_toggle())

        ctk.CTkFrame(sched, height=0).grid(row=len(days) + 1, column=0, pady=(0, 14))

        return p

    def _on_slider(self, val):
        mins = int(val)
        h, m = divmod(mins, 60)
        self._limit_label.configure(text=f"{h}h {m}m")

    # ── Downloads ─────────────────────────────────────────────────────────

    def _downloads(self, _key="downloads"):
        p = ctk.CTkScrollableFrame(self._content, fg_color="transparent")

        ctk.CTkLabel(p, text="Download Blocking", font=FONT_TITLE, text_color=TEXT, anchor="w").pack(
            fill="x", padx=24, pady=(24, 4))
        ctk.CTkLabel(p, text="All downloads are quarantined in locked mode. Review and approve or deny them here.",
                     font=FONT_SMALL, text_color=TEXT_SEC, anchor="w").pack(fill="x", padx=24)

        # Block-all toggle
        toggle_row = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        toggle_row.pack(fill="x", padx=24, pady=(16, 12))
        toggle_inner = ctk.CTkFrame(toggle_row, fg_color="transparent")
        toggle_inner.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(toggle_inner, text="Block ALL downloads in locked mode", font=FONT_BODY,
                     text_color=TEXT).pack(side="left")
        block_sw = ctk.CTkSwitch(toggle_inner, text="", width=46, onvalue=True, offvalue=False)
        if config.get("download_blocking.block_all_in_locked_mode", True):
            block_sw.select()
        block_sw.pack(side="right")

        # Review Queue
        ctk.CTkLabel(p, text="Review Queue", font=FONT_HEAD, text_color=TEXT, anchor="w").pack(
            fill="x", padx=24, pady=(8, 8))

        queue = config.get("download_blocking.review_queue", [])
        queue_frame = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        queue_frame.pack(fill="x", padx=24, pady=(0, 16))

        for i, item in enumerate(queue):
            row = ctk.CTkFrame(queue_frame, fg_color=BG_MEDIUM if i % 2 == 0 else "transparent", corner_radius=8)
            row.pack(fill="x", padx=4, pady=2)
            row.grid_columnconfigure(1, weight=1)

            # Filename
            ctk.CTkLabel(row, text=item["filename"], font=FONT_BODY, text_color=TEXT, anchor="w").grid(
                row=0, column=0, sticky="w", padx=12, pady=(8, 1))

            # Original path + timestamp (muted)
            ts_display = item["timestamp"].replace("T", " ")[:-3]  # e.g. "2026-07-05 14:14"
            detail = f"{item['original_path']}  \u2022  {ts_display}"
            ctk.CTkLabel(row, text=detail, font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w").grid(
                row=1, column=0, sticky="w", padx=12, pady=(0, 8))

            # Status / action buttons
            status = item["status"]
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=1, rowspan=2, sticky="e", padx=12, pady=8)

            if status == "pending":
                ctk.CTkButton(btn_frame, text="Allow", font=FONT_SMALL, fg_color=SUCCESS,
                              hover_color="#16a34a", text_color=TEXT, width=60, height=28,
                              corner_radius=6).pack(side="left", padx=(0, 4))
                ctk.CTkButton(btn_frame, text="Deny", font=FONT_SMALL, fg_color=DANGER,
                              hover_color="#dc2626", text_color=TEXT, width=60, height=28,
                              corner_radius=6).pack(side="left")
            elif status == "approved":
                ctk.CTkLabel(btn_frame, text="\u2705 Approved", font=FONT_SMALL,
                             text_color=SUCCESS).pack(side="left")
            elif status == "denied":
                ctk.CTkLabel(btn_frame, text="\u26D4 Denied", font=FONT_SMALL,
                             text_color=DANGER).pack(side="left")

        # Blocked Extensions (secondary / collapsible-style section)
        ctk.CTkFrame(p, height=1, fg_color=BORDER).pack(fill="x", padx=24, pady=(8, 12))

        ext_hdr = ctk.CTkFrame(p, fg_color="transparent")
        ext_hdr.pack(fill="x", padx=24, pady=(0, 4))
        ctk.CTkLabel(ext_hdr, text="Blocked Extensions", font=FONT_SUB, text_color=TEXT_SEC,
                     anchor="w").pack(side="left")
        ctk.CTkLabel(ext_hdr, text="(always blocked regardless of review queue)", font=FONT_SMALL,
                     text_color=TEXT_MUTED).pack(side="left", padx=(8, 0))

        ext_frame = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        ext_frame.pack(fill="x", padx=24, pady=(0, 24))

        tags = ctk.CTkFrame(ext_frame, fg_color="transparent")
        tags.pack(fill="x", padx=16, pady=14)
        exts = config.get("download_blocking.block_extensions", [])
        for ext in exts:
            tag = ctk.CTkFrame(tags, fg_color=DANGER, corner_radius=6)
            tag.pack(side="left", padx=3, pady=3)
            ctk.CTkLabel(tag, text=ext, font=FONT_SMALL, text_color=TEXT).pack(side="left", padx=(8, 4), pady=4)
            ctk.CTkLabel(tag, text="x", font=FONT_SMALL, text_color="#fca5a5").pack(side="left", padx=(0, 8), pady=4)

        return p

    # ── Policies ──────────────────────────────────────────────────────────

    def _policies(self, _key="policies"):
        p = ctk.CTkScrollableFrame(self._content, fg_color="transparent")

        ctk.CTkLabel(p, text="Security Policies", font=FONT_TITLE, text_color=TEXT, anchor="w").pack(
            fill="x", padx=24, pady=(24, 4))
        ctk.CTkLabel(p, text="Windows Group Policy restrictions applied when locked.",
                     font=FONT_SMALL, text_color=TEXT_SEC, anchor="w").pack(fill="x", padx=24)

        policies_frame = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        policies_frame.pack(fill="x", padx=24, pady=(16, 16))

        policies = [
            ("Block Task Manager", "Prevents opening Task Manager (Ctrl+Shift+Esc)", True),
            ("Block Command Prompt", "Prevents opening CMD and PowerShell", True),
            ("Block Registry Editor", "Prevents opening regedit", True),
            ("Block Control Panel", "Prevents opening Control Panel", False),
            ("Block Windows Settings", "Prevents opening Windows Settings app", False),
        ]
        for i, (name, desc, default) in enumerate(policies):
            row = ctk.CTkFrame(policies_frame, fg_color=BG_MEDIUM if i % 2 == 0 else "transparent", corner_radius=8)
            row.pack(fill="x", padx=8, pady=2)
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=name, font=FONT_BODY, text_color=TEXT, anchor="w").grid(
                row=0, column=0, sticky="w", padx=16, pady=(10, 1))
            ctk.CTkLabel(row, text=desc, font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w").grid(
                row=1, column=0, sticky="w", padx=16, pady=(0, 10))
            sw = ctk.CTkSwitch(row, text="", width=46, onvalue=True, offvalue=False)
            if default:
                sw.select()
            sw.grid(row=0, column=1, rowspan=2, sticky="e", padx=16, pady=10)

        # ── Network / LAN Rules ───────────────────────────────────────────
        ctk.CTkFrame(p, height=1, fg_color=BORDER).pack(fill="x", padx=24, pady=(8, 16))

        ctk.CTkLabel(p, text="Network / LAN Rules", font=FONT_HEAD, text_color=TEXT, anchor="w").pack(
            fill="x", padx=24, pady=(0, 4))
        ctk.CTkLabel(p, text="Control which network services are allowed through the firewall when locked.",
                     font=FONT_SMALL, text_color=TEXT_SEC, anchor="w").pack(fill="x", padx=24, pady=(0, 8))

        # Enable toggle
        net_toggle = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        net_toggle.pack(fill="x", padx=24, pady=(0, 12))
        net_inner = ctk.CTkFrame(net_toggle, fg_color="transparent")
        net_inner.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(net_inner, text="Enable network rules", font=FONT_BODY, text_color=TEXT).pack(side="left")
        net_sw = ctk.CTkSwitch(net_inner, text="", width=46, onvalue=True, offvalue=False)
        if config.get("network_rules.enabled", False):
            net_sw.select()
        net_sw.pack(side="right")

        # Allowed LAN services
        svc_btn_row = ctk.CTkFrame(p, fg_color="transparent")
        svc_btn_row.pack(fill="x", padx=24, pady=(0, 8))
        ctk.CTkLabel(svc_btn_row, text="Allowed LAN Services", font=FONT_SUB, text_color=TEXT,
                     anchor="w").pack(side="left")
        ctk.CTkButton(svc_btn_row, text="+ Add Service", font=FONT_SMALL, fg_color=ACCENT,
                      hover_color=ACCENT_HVR, text_color=TEXT, corner_radius=8, height=30,
                      width=110).pack(side="right")

        lan_frame = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        lan_frame.pack(fill="x", padx=24, pady=(0, 24))

        lan_services = config.get("network_rules.allowed_lan_services", [])
        for i, svc in enumerate(lan_services):
            row = ctk.CTkFrame(lan_frame, fg_color=BG_MEDIUM if i % 2 == 0 else "transparent", corner_radius=8)
            row.pack(fill="x", padx=4, pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=svc["name"], font=FONT_BODY, text_color=TEXT, anchor="w").grid(
                row=0, column=0, sticky="w", padx=12, pady=(8, 1))
            detail = f"{svc['protocol'].upper()}/{svc['port']}  \u2022  {svc['description']}"
            ctk.CTkLabel(row, text=detail, font=FONT_SMALL, text_color=TEXT_MUTED, anchor="w").grid(
                row=1, column=0, sticky="w", padx=12, pady=(0, 8))
            ctk.CTkButton(row, text="Remove", font=FONT_SMALL, fg_color=DANGER, hover_color="#dc2626",
                          text_color=TEXT, width=70, height=28, corner_radius=6).grid(
                row=0, column=1, rowspan=2, sticky="e", padx=12, pady=8)

        return p

    # ── Settings ──────────────────────────────────────────────────────────

    def _settings(self, _key="settings"):
        p = ctk.CTkScrollableFrame(self._content, fg_color="transparent")

        ctk.CTkLabel(p, text="Settings", font=FONT_TITLE, text_color=TEXT, anchor="w").pack(
            fill="x", padx=24, pady=(24, 16))

        # Password section
        pw = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        pw.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(pw, text="Change Admin Password", font=FONT_SUB, text_color=TEXT, anchor="w").pack(
            fill="x", padx=16, pady=(14, 8))
        for ph in ["Current password", "New password", "Confirm new password"]:
            ctk.CTkEntry(pw, placeholder_text=ph, show="*", font=FONT_BODY, fg_color=BG_MEDIUM,
                         border_color=BORDER, text_color=TEXT, placeholder_text_color=TEXT_MUTED,
                         corner_radius=8, height=36, width=300).pack(padx=16, pady=3)
        ctk.CTkButton(pw, text="Update Password", font=FONT_BODY, fg_color=ACCENT, hover_color=ACCENT_HVR,
                      text_color=TEXT, corner_radius=8, height=36, width=160).pack(padx=16, pady=(8, 14))

        # Startup
        st = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        st.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(st, text="Startup", font=FONT_SUB, text_color=TEXT, anchor="w").pack(
            fill="x", padx=16, pady=(14, 8))
        for label, default in [("Run on Windows startup", True), ("Start in locked mode", True)]:
            r = ctk.CTkFrame(st, fg_color="transparent")
            r.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(r, text=label, font=FONT_BODY, text_color=TEXT_SEC).pack(side="left")
            sw = ctk.CTkSwitch(r, text="", width=46)
            if default:
                sw.select()
            sw.pack(side="right")
        ctk.CTkFrame(st, height=8, fg_color="transparent").pack()

        # About
        ab = ctk.CTkFrame(p, fg_color=BG_DARK, corner_radius=RADIUS)
        ab.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(ab, text="About", font=FONT_SUB, text_color=TEXT, anchor="w").pack(
            fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(ab, text="Computer Lockdown v1.0.0", font=FONT_BODY, text_color=TEXT_SEC).pack(
            padx=16, pady=(0, 4))
        ctk.CTkLabel(ab, text="Parental control for Windows 11", font=FONT_SMALL, text_color=TEXT_MUTED).pack(
            padx=16, pady=(0, 14))

        # Reset
        ctk.CTkButton(p, text="Reset All Settings", font=FONT_BODY, fg_color=DANGER, hover_color="#dc2626",
                      text_color=TEXT, corner_radius=8, height=40, width=200).pack(padx=24, pady=(8, 24))

        return p

    # ── Placeholder ───────────────────────────────────────────────────────

    def _placeholder(self, key):
        p = ctk.CTkFrame(self._content, fg_color="transparent")
        p.grid_rowconfigure(0, weight=1)
        p.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(p, text=f"{key.title()} page", font=FONT_HEAD, text_color=TEXT_MUTED).grid(
            row=0, column=0)
        return p

    def refresh_status(self):
        pass


# ── Main App ──────────────────────────────────────────────────────────────────

class DemoApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Computer Lockdown - UI Demo")
        self.window.geometry("1200x800")
        self.window.minsize(900, 600)
        self.window.configure(fg_color=BG_DARKEST)

        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        self.locked = LockedScreen(self.window, on_unlock=self._unlock)
        self.dashboard = AdminDashboard(self.window, on_lock=self._lock)

        self._lock()

        # Centre window
        self.window.update_idletasks()
        w, h = self.window.winfo_width(), self.window.winfo_height()
        x = (self.window.winfo_screenwidth() - w) // 2
        y = (self.window.winfo_screenheight() - h) // 2
        self.window.geometry(f"+{x}+{y}")

    def _unlock(self):
        self.locked.grid_forget()
        self.dashboard.grid(row=0, column=0, sticky="nswe")

    def _lock(self):
        self.dashboard.grid_forget()
        self.locked.reset()
        self.locked.grid(row=0, column=0, sticky="nswe")

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    DemoApp().run()
