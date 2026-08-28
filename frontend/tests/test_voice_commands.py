from __future__ import annotations

from services.voice_command_service import resolve_voice_command


def test_common_borrow_phrases_open_borrow_flow():
    for phrase in ("I want to borrow a book", "I need to borrow a book", "Can I borrow something?", "Please borrow a book", "I want to barrow one"):
        assert resolve_voice_command(phrase)["action"] == "navigate"


def test_catalog_commands_are_resolved():
    assert resolve_voice_command("Show me books I can borrow")["action"] == "search_available"
    assert resolve_voice_command("Remove the search filter")["action"] == "clear_search"
    assert resolve_voice_command("Take me back")["action"] == "back"


def test_other_kiosk_navigation_commands_are_resolved():
    cases = {
        "Can I return this book?": "/return/scan-book",
        "Open my library account": "/account",
        "Show my reserved books": "/reservations",
        "Open popular books": "/popular",
        "Show new arrivals": "/new-books",
        "What books can I get?": "search_available",
        "Reset search": "clear_search",
        "Go to the previous page": "back",
    }
    for phrase, expected in cases.items():
        result = resolve_voice_command(phrase)
        assert result["route"] == expected if expected.startswith("/") else result["action"] == expected
