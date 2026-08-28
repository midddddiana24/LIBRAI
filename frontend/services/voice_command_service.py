import re

from core.constants import Routes


def resolve_voice_command(text: str) -> dict:
    command = re.sub(r"\s+", " ", str(text or "").strip().lower())
    if not command:
        return {"action": "unknown", "message": "No voice command was detected."}
    if any(phrase in command for phrase in ("go home", "home page", "return home", "back home", "main menu", "start page", "go to home", "take me home")):
        return {"action": "navigate", "route": Routes.HOME, "message": "Opening the kiosk home page.", "spoken_reply": "Okay, I got it. Opening the kiosk home page."}
    # Speech recognition often drops articles, changes "borrow" to
    # "barrow", or returns "take out" instead. Keep the intent broad but
    # require a book/lending phrase so ordinary catalog searches are not
    # redirected into a transaction.
    borrow_intent = re.search(r"\b(borrow|barrow|burrow|take out|get)\b.*\b(book|books|something|one)\b", command)
    if borrow_intent or any(phrase in command for phrase in ("start borrowing", "i want to borrow", "i need to borrow", "can i borrow", "please borrow")):
        return {"action": "navigate", "route": Routes.BORROW_SCAN_USER, "message": "Opening book borrowing.", "spoken_reply": "Okay, I got it. Let’s borrow a book."}
    return_intent = re.search(r"\b(return|give back|bring back)\b.*\b(book|books|one|it)\b", command)
    if return_intent or any(phrase in command for phrase in ("start return", "i want to return", "can i return", "return this book")):
        return {"action": "navigate", "route": Routes.RETURN_SCAN_BOOK, "message": "Opening book returns.", "spoken_reply": "Okay, I got it. Let’s return a book."}
    if any(phrase in command for phrase in ("my account", "open account", "show account", "my loans", "my books", "account page", "library account", "my borrowed books")):
        return {"action": "navigate", "route": Routes.ACCOUNT, "message": "Opening your library account."}
    if any(phrase in command for phrase in ("reservations", "my reservations", "show reservations", "reservation queue", "open reservations", "my reserved books")):
        return {"action": "navigate", "route": Routes.RESERVATIONS, "message": "Opening reservations."}
    if any(phrase in command for phrase in ("recommended books", "recommendations", "books for me", "recommend a book", "recommend something")):
        return {"action": "navigate", "route": Routes.RECOMMENDATIONS, "message": "Opening recommendations."}
    if any(phrase in command for phrase in ("popular books", "most popular books", "open popular", "what is popular", "trending books")):
        return {"action": "navigate", "route": Routes.POPULAR_BOOKS, "message": "Opening popular books."}
    if any(phrase in command for phrase in ("new books", "new arrivals", "latest books", "open new books", "newly added books", "recent books")):
        return {"action": "navigate", "route": Routes.NEW_BOOKS, "message": "Opening new books."}
    if any(phrase in command for phrase in ("show available books", "show me books i can borrow", "available books", "books on shelf", "what books can i borrow", "books available", "what can i borrow", "show books i can get", "what books can i get")):
        return {"action": "search_available", "query": "", "message": "Showing available books."}
    if any(phrase in command for phrase in ("find available", "search available", "available books about", "available books on")):
        query = re.sub(r"^(find|search) available (books? )?(about |on )?", "", command).strip()
        return {"action": "search_available", "query": query, "message": f"Showing available books for {query}." if query else "Showing available books."}
    if any(phrase in command for phrase in ("clear search", "clear the search", "remove search", "remove the search", "clear the filter", "remove the filter", "reset search", "start a new search")):
        return {"action": "clear_search", "query": "", "message": "Clearing the catalog search."}
    if any(phrase in command for phrase in ("go back", "take me back", "back one page", "previous page", "previous screen", "go to the previous page", "return to the previous page")):
        return {"action": "back", "message": "Going back."}
    match = re.search(r"(?:search|find|look for|show me|i want|i need)\s+(?:some\s+|books?\s+about\s+|books?\s+on\s+|books?\s+)?(.+)", command)
    if match and match.group(1).strip():
        return {"action": "search", "query": match.group(1).strip(), "message": f"Searching for {match.group(1).strip()}."}
    return {"action": "ask", "query": text.strip(), "message": "I’ll ask LIBRAI Assistant about that."}
