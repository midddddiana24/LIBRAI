"""
LIBRAI – Design System
======================
Single source of truth for the entire frontend visual language.
School / academic library theme: calm, trustworthy, professional.

Palette: deep navy anchor + warm cream background + precise accent tones.
Typography: Inter-weight scale — the de-facto standard for modern software UI.
Every constant is named semantically so changing a value here propagates
everywhere with zero search-and-replace.
"""

from __future__ import annotations
import flet as ft

# Compatibility aliases for the existing LIBRAI components on Flet 0.86.
if not hasattr(ft.border, "all"):
    ft.border.all = ft.Border.all
if not hasattr(ft.border, "only"):
    ft.border.only = ft.Border.only
if not hasattr(ft.border_radius, "only"):
    ft.border_radius.only = ft.BorderRadius.only
if not hasattr(ft.border_radius, "all"):
    ft.border_radius.all = ft.BorderRadius.all
for _name, (_x, _y) in {"center": (0, 0), "center_left": (-1, 0), "center_right": (1, 0), "top_center": (0, -1)}.items():
    if not hasattr(ft.alignment, _name):
        setattr(ft.alignment, _name, ft.Alignment(_x, _y))
ft.padding.symmetric = ft.Padding.symmetric
ft.padding.only = ft.Padding.only
ft.padding.all = ft.Padding.all
ft.margin.symmetric = ft.Margin.symmetric
if not hasattr(ft, "ImageFit") and hasattr(ft, "BoxFit"):
    ft.ImageFit = ft.BoxFit

# ─────────────────────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────────────────────
class Colors:
    # ── Brand / Primary ────────────────────────────────────────
    PRIMARY        = "#0B3158"   # logo navy; trusted institutional anchor
    PRIMARY_DARK   = "#062542"   # deepest navy for admin navigation
    PRIMARY_LIGHT  = "#165D8E"   # interactive blue
    PRIMARY_MUTED  = "#EAF2F8"   # soft blue surface
    ON_PRIMARY     = "#FFFFFF"

    # ── Accent ─────────────────────────────────────────────────
    GOLD           = "#C9A84C"   # warm gold (school crest feel, highlights)
    GOLD_BG        = "#FDF6E3"
    BRAND_GREEN    = "#2F9E50"   # logo green; positive brand accent
    BRAND_GREEN_BG = "#EAF7EE"

    # ── Semantic status ────────────────────────────────────────
    SUCCESS        = "#1D7D4F"
    SUCCESS_BG     = "#E6F4ED"
    SUCCESS_MUTED  = "#D1EAD9"

    WARNING        = "#9A6100"
    WARNING_BG     = "#FEF6E4"

    ERROR          = "#C0392B"
    ERROR_BG       = "#FDECEA"

    INFO           = "#1A3C5E"
    INFO_BG        = "#EAF1F8"

    # ── Neutrals ───────────────────────────────────────────────
    BACKGROUND     = "#F4F7FA"   # cool off-white page canvas
    SURFACE        = "#FFFFFF"   # card / panel surface
    SURFACE_ALT    = "#F8FAFC"   # alternating table rows, subtle insets
    BORDER         = "#DCE5EC"   # hairline dividers
    BORDER_STRONG  = "#BAC8D4"   # focused fields, separators

    TEXT_PRIMARY   = "#111827"   # near-black body text
    TEXT_SECONDARY = "#4B5869"   # muted labels, captions
    TEXT_DISABLED  = "#9AA5B1"   # placeholder, hint
    TEXT_ON_DARK   = "#FFFFFF"

    # ── Sidebar specific ───────────────────────────────────────
    SIDEBAR_BG         = "#062542"
    SIDEBAR_SURFACE    = "#103A5E"
    SIDEBAR_ACTIVE     = "#0E3A61"
    SIDEBAR_ACTIVE_BAR = "#39A85A"   # logo-green active indicator
    SIDEBAR_TEXT       = "#C8D8E8"
    SIDEBAR_TEXT_MUTED = "#7B9BB8"
    SIDEBAR_DIVIDER    = "#1F3D5C"


# ─────────────────────────────────────────────────────────────
#  SPACING  (8-point grid)
# ─────────────────────────────────────────────────────────────
class Spacing:
    XS  =  4
    SM  =  8
    MD  = 16
    LG  = 24
    XL  = 32
    XXL = 48
    XXXL= 64


# ─────────────────────────────────────────────────────────────
#  BORDER RADIUS
# ─────────────────────────────────────────────────────────────
class Radius:
    XS   = 4
    SM   = 8
    MD   = 10
    LG   = 12
    XL   = 16
    PILL = 999


# ─────────────────────────────────────────────────────────────
#  ELEVATION / SHADOW PRESETS
# ─────────────────────────────────────────────────────────────
class Shadow:
    @staticmethod
    def xs() -> ft.BoxShadow:
        return ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.04, "#000"), offset=ft.Offset(0, 1))

    @staticmethod
    def sm() -> ft.BoxShadow:
        return ft.BoxShadow(blur_radius=18, color=ft.Colors.with_opacity(0.07, Colors.PRIMARY_DARK), offset=ft.Offset(0, 5))

    @staticmethod
    def md() -> ft.BoxShadow:
        return ft.BoxShadow(blur_radius=30, color=ft.Colors.with_opacity(0.10, Colors.PRIMARY_DARK), offset=ft.Offset(0, 9))

    @staticmethod
    def lg() -> ft.BoxShadow:
        return ft.BoxShadow(blur_radius=40, color=ft.Colors.with_opacity(0.12, "#000"), offset=ft.Offset(0, 12))


# ─────────────────────────────────────────────────────────────
#  TYPOGRAPHY HELPERS
# ─────────────────────────────────────────────────────────────
class T:
    """Semantic text style factory.  Call T.heading() etc. — each call
    returns a fresh TextStyle instance so shared references are safe."""

    @staticmethod
    def display(color: str = Colors.TEXT_PRIMARY) -> ft.TextStyle:
        return ft.TextStyle(size=36, weight=ft.FontWeight.W_800, color=color, letter_spacing=-0.5)

    @staticmethod
    def h1(color: str = Colors.TEXT_PRIMARY) -> ft.TextStyle:
        return ft.TextStyle(size=28, weight=ft.FontWeight.W_700, color=color, letter_spacing=-0.3)

    @staticmethod
    def h2(color: str = Colors.TEXT_PRIMARY) -> ft.TextStyle:
        return ft.TextStyle(size=22, weight=ft.FontWeight.W_700, color=color)

    @staticmethod
    def h3(color: str = Colors.TEXT_PRIMARY) -> ft.TextStyle:
        return ft.TextStyle(size=17, weight=ft.FontWeight.W_600, color=color)

    @staticmethod
    def body(color: str = Colors.TEXT_PRIMARY) -> ft.TextStyle:
        return ft.TextStyle(size=14, weight=ft.FontWeight.NORMAL, color=color)

    @staticmethod
    def small(color: str = Colors.TEXT_SECONDARY) -> ft.TextStyle:
        return ft.TextStyle(size=12, weight=ft.FontWeight.NORMAL, color=color)

    @staticmethod
    def label(color: str = Colors.TEXT_SECONDARY) -> ft.TextStyle:
        return ft.TextStyle(size=11, weight=ft.FontWeight.W_600, color=color, letter_spacing=0.4)

    @staticmethod
    def mono(color: str = Colors.TEXT_SECONDARY) -> ft.TextStyle:
        return ft.TextStyle(size=12, weight=ft.FontWeight.NORMAL, color=color, font_family="monospace")


# ─────────────────────────────────────────────────────────────
#  REUSABLE WIDGET FACTORIES
# ─────────────────────────────────────────────────────────────
def surface_card(
    content: ft.Control,
    padding: int | ft.Padding = Spacing.LG,
    radius: int = Radius.LG,
    shadow: ft.BoxShadow | None = None,
    bgcolor: str = Colors.SURFACE,
    border: bool = True,
    expand: bool | int = False,
    width: float | None = None,
) -> ft.Container:
    """Standard card container.  Consistent across kiosk and admin."""
    return ft.Container(
        expand=expand,
        width=width,
        bgcolor=bgcolor,
        border_radius=radius,
        border=ft.border.all(1, Colors.BORDER) if border else None,
        shadow=shadow or Shadow.sm(),
        padding=padding,
        content=content,
    )


def icon_badge(
    icon: str,
    color: str = Colors.PRIMARY,
    size: int = 20,
    badge_size: int = 44,
    radius: int = Radius.MD,
) -> ft.Container:
    """Tinted icon badge used on stat cards, action tiles, etc."""
    return ft.Container(
        width=badge_size,
        height=badge_size,
        border_radius=radius,
        bgcolor=ft.Colors.with_opacity(0.12, color),
        alignment=ft.alignment.center,
        content=ft.Icon(icon, size=size, color=color),
    )


def pill_badge(text: str, bg: str, fg: str) -> ft.Container:
    return ft.Container(
        bgcolor=bg,
        border_radius=Radius.PILL,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        content=ft.Text(text.replace("_", " ").title(), size=11, weight=ft.FontWeight.W_600, color=fg),
    )


def divider(margin_v: int = 0) -> ft.Container:
    return ft.Container(height=1, bgcolor=Colors.BORDER, margin=ft.margin.symmetric(vertical=margin_v))


# ─────────────────────────────────────────────────────────────
#  BUTTON STYLES
# ─────────────────────────────────────────────────────────────
def primary_button_style(height: int = 52) -> ft.ButtonStyle:
    """Touch-sized primary filled button (kiosk-safe 52px height)."""
    return ft.ButtonStyle(
        bgcolor=Colors.PRIMARY,
        color=Colors.ON_PRIMARY,
        padding=ft.padding.symmetric(horizontal=Spacing.XL, vertical=Spacing.MD),
        shape=ft.RoundedRectangleBorder(radius=Radius.MD),
        text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_600),
        elevation=0,
    )


def touch_button_style(
    bg_color: str = Colors.PRIMARY,
    fg_color: str = Colors.ON_PRIMARY,
    height: int = 52,
) -> ft.ButtonStyle:
    """Backwards-compatible kiosk action style with a large touch target.

    Borrow, return, and book-detail workflows share this helper. Keeping it
    in the design system prevents a visual refactor from breaking imports in
    completed kiosk features.
    """
    return ft.ButtonStyle(
        bgcolor=bg_color,
        color=fg_color,
        padding=ft.padding.symmetric(horizontal=Spacing.XL, vertical=Spacing.MD),
        shape=ft.RoundedRectangleBorder(radius=Radius.MD),
        text_style=ft.TextStyle(size=15, weight=ft.FontWeight.W_600),
        elevation=0,
    )


def secondary_button_style() -> ft.ButtonStyle:
    return ft.ButtonStyle(
        bgcolor=Colors.SURFACE,
        color=Colors.TEXT_PRIMARY,
        padding=ft.padding.symmetric(horizontal=Spacing.LG, vertical=Spacing.MD - 2),
        shape=ft.RoundedRectangleBorder(radius=Radius.MD),
        side=ft.BorderSide(1, Colors.BORDER_STRONG),
        text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500),
        elevation=0,
    )


# ─────────────────────────────────────────────────────────────
#  FLET THEME OBJECTS
# ─────────────────────────────────────────────────────────────
def _transitions_none() -> ft.PageTransitionsTheme:
    return ft.PageTransitionsTheme(
        android=ft.PageTransitionTheme.NONE,
        ios=ft.PageTransitionTheme.NONE,
        linux=ft.PageTransitionTheme.NONE,
        macos=ft.PageTransitionTheme.NONE,
        windows=ft.PageTransitionTheme.NONE,
    )


def build_theme() -> ft.Theme:
    """Kiosk theme — warm, spacious, touch-friendly."""
    return ft.Theme(
        color_scheme_seed=Colors.PRIMARY,
        color_scheme=ft.ColorScheme(
            primary=Colors.PRIMARY,
            on_primary=Colors.ON_PRIMARY,
            surface=Colors.SURFACE,
            error=Colors.ERROR,
        ),
        font_family="Segoe UI Variable, Segoe UI, Inter, Roboto, sans-serif",
        visual_density=ft.VisualDensity.COMFORTABLE,
        use_material3=True,
        page_transitions=_transitions_none(),
    )


def build_admin_theme() -> ft.Theme:
    """Admin theme — compact, information-dense, precise."""
    t = build_theme()
    _shape   = ft.RoundedRectangleBorder(radius=Radius.SM)
    _txt_btn = ft.TextStyle(size=13, weight=ft.FontWeight.W_600)

    t.filled_button_theme = ft.FilledButtonTheme(
        bgcolor=Colors.PRIMARY,
        foreground_color=Colors.ON_PRIMARY,
        elevation=0,
        padding=ft.padding.symmetric(horizontal=18, vertical=11),
        shape=_shape,
        text_style=_txt_btn,
        icon_size=17,
        minimum_size=ft.Size(0, 40),
        enable_feedback=False,
    )
    t.outlined_button_theme = ft.OutlinedButtonTheme(
        foreground_color=Colors.PRIMARY,
        elevation=0,
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        shape=_shape,
        border_side=ft.BorderSide(1.2, Colors.BORDER_STRONG),
        text_style=_txt_btn,
        icon_size=17,
        minimum_size=ft.Size(0, 40),
        enable_feedback=False,
    )
    t.text_button_theme = ft.TextButtonTheme(
        foreground_color=Colors.PRIMARY,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        shape=_shape,
        text_style=_txt_btn,
        enable_feedback=False,
    )
    t.data_table_theme = ft.DataTableTheme(
        heading_row_color=Colors.SURFACE_ALT,
        heading_row_height=44,
        data_row_min_height=52,
        data_row_max_height=60,
        horizontal_margin=20,
        column_spacing=28,
        divider_thickness=0.8,
        heading_text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_700,
                                        color=Colors.TEXT_SECONDARY, letter_spacing=0.3),
        data_text_style=ft.TextStyle(size=13, color=Colors.TEXT_PRIMARY),
    )
    t.dialog_theme = ft.DialogTheme(
        bgcolor=Colors.SURFACE,
        elevation=12,
        surface_tint_color=Colors.SURFACE,
        shape=ft.RoundedRectangleBorder(radius=Radius.LG),
        title_text_style=ft.TextStyle(size=20, weight=ft.FontWeight.W_700, color=Colors.TEXT_PRIMARY),
        actions_padding=ft.padding.only(left=24, right=24, bottom=20, top=8),
        barrier_color=ft.Colors.with_opacity(0.40, "#0F172A"),
    )
    t.splash_color    = ft.Colors.TRANSPARENT
    t.highlight_color = ft.Colors.TRANSPARENT
    return t
