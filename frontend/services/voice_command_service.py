import re

from core.constants import Routes


def resolve_voice_command(text: str) -> dict:
    command = re.sub(r"\s+", " ", str(text or "").strip().lower())
    if not command:
        return {"action": "unknown", "message": "No voice command was detected."}
    if any(phrase in command for phrase in ("go home", "home page", "return home", "back home")):
        return {"action": "navigate", "route": Routes.HOME, "message": "Opening the kiosk home page."}
    if any(phrase in command for phrase in ("borrow a book", "borrow book", "start borrowing")):
        return {"action": "navigate", "route": Routes.BORROW_SCAN_USER, "message": "Opening book borrowing."}
    if any(phrase in command for phrase in ("return a book", "return book", "start return")):
        return {"action": "navigate", "route": Routes.RETURN_SCAN_BOOK, "message": "Opening book returns."}
    if any(phrase in command for phrase in ("my account", "open account", "show account")):
        return {"action": "navigate", "route": Routes.ACCOUNT, "message": "Opening your library account."}
    if any(phrase in command for phrase in ("reservations", "my reservations", "show reservations")):
        return {"action": "navigate", "route": Routes.RESERVATIONS, "message": "Opening reservations."}
    if any(phrase in command for phrase in ("recommended books", "recommendations", "books for me")):
        return {"action": "navigate", "route": Routes.RECOMMENDATIONS, "message": "Opening recommendations."}
    if any(phrase in command for phrase in ("popular books", "most popular books")):
        return {"action": "navigate", "route": Routes.POPULAR_BOOKS, "message": "Opening popular books."}
    if any(phrase in command for phrase in ("new books", "new arrivals", "latest books")):
        return {"action": "navigate", "route": Routes.NEW_BOOKS, "message": "Opening new books."}
    match = re.search(r"(?:search|find|look for|show me)\s+(?:books?\s+)?(.+)", command)
    if match and match.group(1).strip():
        return {"action": "search", "query": match.group(1).strip(), "message": f"Searching for {match.group(1).strip()}."}
    return {"action": "ask", "query": text.strip(), "message": "I’ll ask LIBRAI Assistant about that."}
