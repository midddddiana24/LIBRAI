import re

from core.constants import Routes


def resolve_voice_command(text: str) -> dict:
    command = re.sub(r"\s+", " ", str(text or "").strip().lower())
    if not command:
        return {"action": "unknown", "message": "No voice command was detected."}
    if any(phrase in command for phrase in ("go home", "home page", "return home", "back home", "main menu", "start page")):
        return {"action": "navigate", "route": Routes.HOME, "message": "Opening the kiosk home page."}
    if any(phrase in command for phrase in ("borrow a book", "borrow book", "start borrowing", "i want to borrow", "i need to borrow", "can i borrow", "please borrow", "get a book")):
        return {"action": "navigate", "route": Routes.BORROW_SCAN_USER, "message": "Opening book borrowing."}
    if any(phrase in command for phrase in ("return a book", "return book", "start return", "i want to return", "give back a book")):
        return {"action": "navigate", "route": Routes.RETURN_SCAN_BOOK, "message": "Opening book returns."}
    if any(phrase in command for phrase in ("my account", "open account", "show account", "my loans", "my books")):
        return {"action": "navigate", "route": Routes.ACCOUNT, "message": "Opening your library account."}
    if any(phrase in command for phrase in ("reservations", "my reservations", "show reservations", "reservation queue")):
        return {"action": "navigate", "route": Routes.RESERVATIONS, "message": "Opening reservations."}
    if any(phrase in command for phrase in ("recommended books", "recommendations", "books for me")):
        return {"action": "navigate", "route": Routes.RECOMMENDATIONS, "message": "Opening recommendations."}
    if any(phrase in command for phrase in ("popular books", "most popular books")):
        return {"action": "navigate", "route": Routes.POPULAR_BOOKS, "message": "Opening popular books."}
    if any(phrase in command for phrase in ("new books", "new arrivals", "latest books")):
        return {"action": "navigate", "route": Routes.NEW_BOOKS, "message": "Opening new books."}
    if any(phrase in command for phrase in ("show available books", "show me books i can borrow", "available books", "books on shelf", "what books can i borrow")):
        return {"action": "search_available", "query": "", "message": "Showing available books."}
    if any(phrase in command for phrase in ("clear search", "clear the search", "remove search", "remove the search", "clear the filter", "remove the filter")):
        return {"action": "clear_search", "query": "", "message": "Clearing the catalog search."}
    if any(phrase in command for phrase in ("go back", "take me back", "back one page", "previous page", "previous screen")):
        return {"action": "back", "message": "Going back."}
    match = re.search(r"(?:search|find|look for|show me|i want|i need)\s+(?:some\s+|books?\s+about\s+|books?\s+on\s+|books?\s+)?(.+)", command)
    if match and match.group(1).strip():
        return {"action": "search", "query": match.group(1).strip(), "message": f"Searching for {match.group(1).strip()}."}
    return {"action": "ask", "query": text.strip(), "message": "I’ll ask LIBRAI Assistant about that."}
