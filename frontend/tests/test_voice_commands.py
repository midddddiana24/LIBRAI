from __future__ import annotations

from services.voice_command_service import resolve_voice_command


def test_common_borrow_phrases_open_borrow_flow():
    for phrase in ("I need to borrow a book", "Can I borrow something?", "Please borrow a book"):
        assert resolve_voice_command(phrase)["action"] == "navigate"


def test_catalog_commands_are_resolved():
    assert resolve_voice_command("Show me books I can borrow")["action"] == "search_available"
    assert resolve_voice_command("Remove the search filter")["action"] == "clear_search"
    assert resolve_voice_command("Take me back")["action"] == "back"

