"""
Dark modern theme configuration for Computer Lockdown.

Discord/Spotify-inspired dark palette with indigo accents, designed for
CustomTkinter widgets.  Import the :class:`Theme` class and reference its
class-level constants wherever colours, fonts, or dimensions are needed.
"""

from __future__ import annotations


class Theme:
    """Centralised design tokens for the entire application UI."""

    # ------------------------------------------------------------------
    # Background colours (darkest -> lightest)
    # ------------------------------------------------------------------
    BG_DARKEST: str = "#0d0d0d"       # Deepest background / window bg
    BG_DARK: str = "#1a1a2e"          # Main panel background
    BG_MEDIUM: str = "#16213e"        # Card / inner-panel background
    BG_LIGHT: str = "#1e2a4a"         # Lighter panels, hover states
    BG_HOVER: str = "#2a3a5c"         # Hover state for interactive items

    # ------------------------------------------------------------------
    # Accent colours
    # ------------------------------------------------------------------
    ACCENT_PRIMARY: str = "#4f46e5"   # Primary accent (indigo)
    ACCENT_HOVER: str = "#6366f1"     # Hover accent
    ACCENT_SUCCESS: str = "#22c55e"   # Green for success / enabled
    ACCENT_WARNING: str = "#f59e0b"   # Amber for warnings
    ACCENT_DANGER: str = "#ef4444"    # Red for danger / disabled / locked

    # ------------------------------------------------------------------
    # Text colours
    # ------------------------------------------------------------------
    TEXT_PRIMARY: str = "#f1f5f9"     # Main text (near-white)
    TEXT_SECONDARY: str = "#94a3b8"   # Secondary / muted text
    TEXT_MUTED: str = "#64748b"       # Very muted / placeholder text

    # ------------------------------------------------------------------
    # Border colours
    # ------------------------------------------------------------------
    BORDER: str = "#2a2a4a"
    BORDER_LIGHT: str = "#3a3a5a"

    # ------------------------------------------------------------------
    # Fonts (tuples accepted by CustomTkinter / Tkinter)
    # ------------------------------------------------------------------
    FONT_FAMILY: str = "Segoe UI"     # Windows system font
    FONT_TITLE: tuple[str, int, str] = ("Segoe UI", 24, "bold")
    FONT_HEADING: tuple[str, int, str] = ("Segoe UI", 18, "bold")
    FONT_SUBHEADING: tuple[str, int, str] = ("Segoe UI", 14, "bold")
    FONT_BODY: tuple[str, int] = ("Segoe UI", 12)
    FONT_SMALL: tuple[str, int] = ("Segoe UI", 10)
    FONT_MONO: tuple[str, int] = ("Consolas", 11)

    # ------------------------------------------------------------------
    # Dimensions
    # ------------------------------------------------------------------
    CORNER_RADIUS: int = 12
    BUTTON_HEIGHT: int = 40
    INPUT_HEIGHT: int = 40
    SIDEBAR_WIDTH: int = 250

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def configure_customtkinter() -> None:
        """Apply global appearance settings to CustomTkinter."""
        import customtkinter as ctk

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
