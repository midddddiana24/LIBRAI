"""Structured in-memory UI state; authoritative rules stay on the API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass
class AppState:
    kiosk_user: dict[str, Any] | None = None
    scanned_book: dict[str, Any] | None = None
    active_borrowing: dict[str, Any] | None = None
    last_transaction: dict[str, Any] | None = None
    ai_messages: list[dict[str, Any]] = field(default_factory=list)
    admin_user: dict[str, Any] | None = None
    admin_token: str | None = None
    last_activity: datetime = field(default_factory=datetime.now)
    timeout_warning_shown: bool = False

    def touch(self) -> None:
        self.last_activity = datetime.now()
        self.timeout_warning_shown = False

    def clear_kiosk(self) -> None:
        self.kiosk_user = None
        self.scanned_book = None
        self.active_borrowing = None
        self.last_transaction = None
        self.ai_messages.clear()
        self.touch()


class _StateHost(Protocol):
    """A Flet Page (or test double) that can hold session state."""


def get_state(page: _StateHost) -> AppState:
    """Return UI state isolated to this Flet page/browser session."""
    current = getattr(page, "_librai_state", None)
    if current is None:
        current = AppState()
        setattr(page, "_librai_state", current)
    return current
