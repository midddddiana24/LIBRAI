"""Reusable LIBRAI brand artwork."""

from __future__ import annotations

import flet as ft

from core.theme import Colors, Radius


LOGO_ASSET = "librai-logo.png"


def BrandLogo(
    width: int = 112,
    height: int | None = None,
    *,
    framed: bool = False,
) -> ft.Control:
    """Return the official supplied logo at a predictable size."""
    image = ft.Image(
        src=LOGO_ASSET,
        width=width,
        height=height or width,
        fit=ft.ImageFit.CONTAIN,
        gapless_playback=True,
        semantics_label="LIBRAI logo",
    )
    if not framed:
        return image
    return ft.Container(
        width=width,
        height=height or width,
        padding=6,
        bgcolor=Colors.SURFACE,
        border=ft.border.all(1, Colors.BORDER),
        border_radius=Radius.MD,
        alignment=ft.alignment.center,
        content=image,
    )
