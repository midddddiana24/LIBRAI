"""Safe formatting helpers for API timestamps."""

from __future__ import annotations

from datetime import datetime


def format_date(value, fallback: str = "—") -> str:
    if not value:
        return fallback
    raw = str(value)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%b %d, %Y")
    except ValueError:
        return raw[:10] or fallback
