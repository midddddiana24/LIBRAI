from __future__ import annotations
import re
from collections import Counter
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.ai.gemini_client import gemini_client
from backend.models.entities import AIInteraction, Book, BookCopy, Borrowing, CopyStatus, SearchHistory
from backend.services.serialization import book_dict
from backend.services import policy_service as policy


STOP = set("the a an i me want need show find some please recommend recommendations recommended book books about on for with to of only ones those them easier harder available all any can you do have what are is there my read reading may ba mga libro aklat tungkol sa para ang ng na ko ako mo puwede pwede bang po at atong gusto pahiram hanap maghanap ipakita mas madali mahirap lamang lang baguhan beginner intro introduction basic basics fundamentals intermediate practical advanced expert professional shelf borrow now help would like how learn learning include unavailable remove level filter kahit copies same topic iyon ganun something".split())
LEVEL_WORDS = {"beginner": {"beginner", "intro", "introduction", "basic", "basics", "fundamentals", "baguhan", "easier", "madali"}, "intermediate": {"intermediate", "practical"}, "advanced": {"advanced", "expert", "professional", "harder", "mahirap"}}
ALIASES = {"kasaysayan": "history", "agham": "science", "matematika": "mathematics", "romansa": "romance", "pagprograma": "programming"}
FOLLOW_UP = re.compile(r"\b(easier|harder|ones|those|them|same topic|available only|only available|include unavailable|remove level filter|all copies|mas madali|mas mahirap|iyon|ganun|lamang|lang)\b", re.I)


def parse_intent(query: str, context: dict | None = None) -> dict:
    lowered = query.lower().strip().rstrip(".!?")
    words = re.findall(r"[a-z0-9+#]+(?:[.-][a-z0-9]+)*", lowered)
    level = next((name for name, terms in LEVEL_WORDS.items() if terms.intersection(words)), None)
    tokens = list(dict.fromkeys(ALIASES.get(word, word) for word in words if word not in STOP))[:8]
    available = any(term in lowered for term in ("available", "on shelf", "borrow now", "puwedeng hiramin", "pwedeng hiramin"))
    follow_up = not tokens and bool(FOLLOW_UP.search(lowered) or (context and (available or level)))
    if follow_up and context:
        tokens = context.get("topics", [])
        level = level or context.get("level")
        available = available or context.get("available_only", False)
    if "remove level filter" in lowered:
        level = None
    if any(term in lowered for term in ("include unavailable", "all copies", "kahit unavailable")):
        available = False
    conversation = "greeting" if lowered in {"hello", "hello librai", "hi", "hi librai", "hey", "kumusta", "magandang umaga", "good morning", "good afternoon", "good evening"} else "thanks" if lowered in {"thanks", "thank you", "salamat"} else "help" if lowered in {"help", "what can you do", "how can you help"} else None
    return {"tokens": tokens, "topics": tokens, "level": level, "available_only": available, "conversation": conversation, "follow_up": follow_up}


def policy_answer(db: Session, query: str) -> str | None:
    q = query.lower()
    if re.search(r"how (?:do i|to|can i) (?:borrow|check out)|paano (?:ako )?(?:manghiram|humiram)", q):
        return "Choose Borrow a book, scan your approved library ID, scan the physical book QR, then review the details and confirm. Your receipt shows the due date."
    if re.search(r"how (?:do i|to|can i) return|paano (?:ako )?(?:ibalik|magsauli|isauli)", q):
        return "Choose Return a book, scan the book QR, review the active loan, then confirm the return. Your receipt shows any overdue fine."
    if re.search(r"how (?:do i|to|can i) (?:register|sign up)|paano (?:ako )?(?:magregister|magrehistro)", q):
        return "Choose Register on the home screen. Enter your details or scan your campus and library cards, review the fields, and submit for staff approval. Your library QR can be issued after approval; check with staff if it has not arrived."
    if q.strip().rstrip(".?!") in {"library rules", "library policy", "borrowing rules", "patakaran ng library", "patakaran ng aklatan"}:
        return f"Borrowing limit: {policy.borrowing_limit(db)} active loans. Loan period: {policy.borrowing_period_days(db)} days. Renewal limit: {policy.max_renewals(db)} time(s). Reservation pickup hold: {policy.reservation_hold_days(db)} day(s). Overdue fine: PHP {policy.overdue_fine_per_day_cents(db) / 100:.2f} per day per overdue loan. Ask about a rule for its conditions."
    # Policy facts bypass the language model so staff setting changes take effect immediately.
    if re.search(r"\b(renew|renewal|renewals|extend|palawig)\b", q):
        return f"You can renew up to {policy.max_renewals(db)} time(s), adding {policy.borrowing_period_days(db)} days per renewal. The loan must be active and not overdue, with no other member waiting for this title. Scan your ID in My account to renew."
    if re.search(r"\b(reserve|reservation|reservations|hold period|pickup|pick up|pareserba)\b", q):
        return f"When a reservation becomes ready, its pickup hold lasts {policy.reservation_hold_days(db)} day(s). Scan your ID to reserve an unavailable title or manage reservations in My account."
    if re.search(r"\b(limit|how many|ilang|gaano karami)\b", q) and not re.search(r"\b(days|araw)\b", q) and re.search(r"\b(borrow|books?|hiram|humiram|manghiram|libro|aklat)\b", q):
        return f"You may have up to {policy.borrowing_limit(db)} active loans. The loan period is {policy.borrowing_period_days(db)} days."
    if re.search(r"loan period|how long|how many days|ilang araw|gaano katagal|due date", q):
        return f"The loan period is {policy.borrowing_period_days(db)} days. Your exact due date appears in My account and on your borrowing receipt."
    if re.search(r"\b(fine|fines|penalty|penalties|multa|overdue|late return)\b", q):
        blocked = "Unpaid fines block new borrowing." if policy.block_borrow_with_unpaid_fines(db) else "Unpaid fines do not block new borrowing."
        overdue = "Overdue loans block new borrowing." if not policy.allow_overdue(db) else "Overdue loans do not block new borrowing."
        return f"The overdue fine is PHP {policy.overdue_fine_per_day_cents(db) / 100:.2f} per day per overdue loan. {blocked} {overdue} Check My account for your recorded balance."
    if re.search(r"library polic|library rules|opening hours|open on|closing|library hours|lost card|lost book|payment method|oras ng|patakaran", q):
        return "Please ask library staff about that policy. LIBRAI has no verified setting for it. I can explain borrowing limits, loan periods, renewals, reservations and overdue fines."
    return None


def candidates_for_query(db: Session, query: str, limit=12, user_id: int | None = None, context: dict | None = None) -> tuple[list[dict], dict]:
    intent = parse_intent(query, context)
    tokens = intent["tokens"]
    popularity = dict(db.execute(select(BookCopy.book_id, func.count(Borrowing.id)).select_from(BookCopy).outerjoin(Borrowing).group_by(BookCopy.book_id)).all())
    interests = set(db.scalars(select(Book.category_id).join(BookCopy).join(Borrowing).where(Borrowing.user_id == user_id)).all()) if user_id else set()
    scored = []
    for book in db.scalars(select(Book).where(Book.is_archived.is_(False))):
        fields = [(book.title, 7), (" ".join(book.subjects or []), 5), (" ".join(book.keywords or []), 4), (book.category.name if book.category else "", 4), (book.author, 2), (book.description or "", 1)]
        def matches(term, text):
            return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text.lower()) is not None
        score = sum(max((weight for text, weight in fields if matches(token, text)), default=0) for token in tokens)
        # Availability, popularity and history only break ties between relevant books.
        if tokens and not score:
            continue
        metadata = " ".join(text.lower() for text, _ in fields)
        if intent["level"] and not any(matches(word, metadata) for word in LEVEL_WORDS[intent["level"]] - {"easier", "harder", "madali", "mahirap"}):
            continue
        data = book_dict(db, book)
        if intent["available_only"] and not data["available_copies"]:
            continue
        score += (2 if book.category_id in interests else 0) + min(int(popularity.get(book.id, 0)), 5) * .25 + (2 if data["available_copies"] else 0)
        scored.append((score, data))
    return [b for _, b in sorted(scored, key=lambda item: (-item[0], item[1]["title"]))[:limit]], intent


def ai_search(db: Session, query: str, user_id=None, context: dict | None = None) -> dict:
    intent = parse_intent(query, context)
    answer = policy_answer(db, query)
    response_type = "policy" if answer else "catalog"
    books = []
    fallback = False
    next_context = context
    if not answer and intent["conversation"]:
        response_type = "conversation"
        answer = {"greeting": "Hello! I'm LIBRAI Assistant. I can find books and explain library borrowing policies.", "thanks": "You're welcome! Tell me what you would like to read next.", "help": "Ask for a topic, reading level, available copies, or the library's borrowing rules."}[intent["conversation"]]
    elif not answer:
        if intent["follow_up"] and not context and not intent["tokens"]:
            answer = "Which topic would you like? Search for a subject first, then ask for easier or available books."
        else:
            candidates, intent = candidates_for_query(db, query, user_id=user_id, context=context)
            next_context = {key: intent[key] for key in ("topics", "level", "available_only")}
            effective_query = " ".join(intent["topics"] + ([intent["level"]] if intent["level"] else []) + (["available only"] if intent["available_only"] else []))
            ranking = gemini_client.rank(effective_query or query, candidates) if candidates else None
            fallback = bool(candidates) and ranking is None
            by_id = {b["id"]: b for b in candidates}
            ids = list(dict.fromkeys(item.book_id for item in ranking.recommendations if item.book_id in by_id)) if ranking is not None else [b["id"] for b in candidates[:6]]
            # Never render unchecked model claims about titles, stock, shelves or suitability.
            books = [{**by_id[book_id], "why_match": "Matches catalog metadata" + (f"; tagged {intent['level']}" if intent["level"] else "") + "."} for book_id in ids[:6]]
            answer = f"Found {len(books)} matching catalog title(s). Availability and shelf locations are shown below." if books else "No matching catalog books were found. Try a different topic or remove a reading-level or availability filter."
    interaction = AIInteraction(user_id=user_id, question=query[:1000], response_summary=answer, fallback_used=fallback)
    db.add(interaction)
    if response_type == "catalog":
        db.add(SearchHistory(user_id=user_id, query=query[:500], search_type="ai", results_count=len(books)))
    db.flush()
    interaction_id = interaction.id
    db.commit()
    return {"query": query, "answer": answer, "message": answer, "books": books, "parsed_intent": intent, "context": next_context, "interaction_id": interaction_id, "ai_available": not fallback, "fallback_used": fallback, "response_type": response_type, "personalized": bool(user_id)}


def recommendations(db: Session, user_id=None, kind="personalized", limit=12) -> list[dict]:
    stmt=select(Book).where(Book.is_archived.is_(False),Book.copies.any(BookCopy.status==CopyStatus.AVAILABLE))
    if kind=="new": stmt=stmt.order_by(Book.created_at.desc())
    elif kind=="popular": stmt=stmt.outerjoin(BookCopy).outerjoin(Borrowing).group_by(Book.id).order_by(func.count(Borrowing.id).desc())
    elif user_id:
        category_ids=[x for x in db.scalars(select(Book.category_id).join(BookCopy).join(Borrowing).where(Borrowing.user_id==user_id)).all()]
        if category_ids:
            counts=Counter(category_ids); stmt=stmt.order_by((Book.category_id==counts.most_common(1)[0][0]).desc(),Book.title)
    return [book_dict(db,b) for b in db.scalars(stmt.limit(limit)).unique().all()]
