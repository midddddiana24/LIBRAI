from __future__ import annotations
import re
from collections import Counter
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from backend.ai.gemini_client import gemini_client
from backend.models.entities import AIInteraction, Book, BookCopy, Borrowing, CopyStatus, SearchHistory
from backend.services.catalog_service import search_books
from backend.services.serialization import book_dict


STOP={"the","a","an","i","me","want","need","show","book","books","about","for","with","to","of"}
LEVEL_WORDS={"beginner":{"beginner","intro","introduction","basic","fundamentals"},"intermediate":{"intermediate","practical"},"advanced":{"advanced","expert","professional"}}
GREETING_WORDS={"hello","hi","hey","hola","good morning","good afternoon","good evening"}
THANKS_WORDS={"thanks","thank you","thankyou"}


def parse_intent(query: str) -> dict:
    lowered=query.lower().strip();tokens=[x for x in re.findall(r"[a-z0-9+#.-]+",lowered) if x not in STOP]
    level=next((name for name,words in LEVEL_WORDS.items() if words.intersection(tokens)),None)
    conversation="greeting" if lowered in GREETING_WORDS or any(lowered.startswith(f"{word} ") for word in GREETING_WORDS if " " not in word) else "thanks" if lowered in THANKS_WORDS else "help" if lowered in {"help","what can you do","how can you help"} else None
    return {"tokens":tokens,"level":level,"available_only":any(phrase in lowered for phrase in ["available","on shelf","borrow now"]),"topics":tokens[:8],"conversation":conversation}


def candidates_for_query(db: Session, query: str, limit=12, user_id: int | None = None) -> tuple[list[dict],dict]:
    intent=parse_intent(query);tokens=intent["tokens"]
    popularity=dict(db.execute(select(BookCopy.book_id,func.count(Borrowing.id)).select_from(BookCopy).outerjoin(Borrowing).group_by(BookCopy.book_id)).all())
    interests=set(db.scalars(select(Book.category_id).join(BookCopy).join(Borrowing).where(Borrowing.user_id==user_id)).all()) if user_id else set()
    scored=[]
    for book in db.scalars(select(Book).where(Book.is_archived.is_(False))):
        data=book_dict(db,book)
        if intent["available_only"] and not data["available_copies"]:continue
        title=book.title.lower();category=book.category.name.lower() if book.category else "";keywords=" ".join(book.keywords or []).lower();subjects=" ".join(book.subjects or []).lower();description=(book.description or "").lower();author=book.author.lower()
        score=sum(7 if t in title else 5 if t in subjects else 4 if t in keywords else 4 if t in category else 2 if t in author else 1 if t in description else 0 for t in tokens)
        if intent["level"] and intent["level"] in " ".join([title,keywords,subjects,description]):score+=3
        if book.category_id in interests:score+=2
        score+=min(int(popularity.get(book.id,0)),5)*0.25
        if data["available_copies"]:score+=2
        if score:scored.append((score,data))
    candidates=[b for _,b in sorted(scored,key=lambda x:(-x[0],x[1]["title"]))[:limit]] or search_books(db,available_only=True,limit=limit)[0]
    return candidates,{"level":intent["level"],"available_only":intent["available_only"],"topics":tokens[:8]}


def ai_search(db: Session, query: str, user_id=None) -> dict:
    intent=parse_intent(query)
    if intent["conversation"]:
        answers={"greeting":"Hello! I’m LIBRAI Assistant. I can help you find books, check availability, and explain borrowing or reservations.","thanks":"You’re welcome! Tell me what you would like to read next.","help":"I can search the library catalog, recommend books by topic or level, and help you find available copies."}
        answer=answers[intent["conversation"]]
        interaction=AIInteraction(user_id=user_id,question=query[:1000],response_summary=answer,fallback_used=False);db.add(interaction);db.flush();db.commit()
        return {"query":query,"answer":answer,"message":answer,"books":[],"parsed_intent":intent,"interaction_id":interaction.id,"ai_available":True,"fallback_used":False,"response_type":"conversation"}
    candidates,_=candidates_for_query(db,query,user_id=user_id); ranking=gemini_client.rank(query,candidates); fallback=ranking is None
    if ranking:
        by_id={b["id"]:b for b in candidates}; books=[]
        for item in ranking.recommendations:
            if item.book_id in by_id: books.append({**by_id[item.book_id],"why_match":item.reason})
        answer=ranking.message
    else:
        books=[{**b,"why_match":"Matches catalog metadata and is ranked by the local recommendation engine."} for b in candidates[:6]]
        answer="I found matching books in the LIBRAI catalog." if books else "No matching catalog books were found."
    interaction=AIInteraction(user_id=user_id,question=query[:1000],response_summary=answer,fallback_used=fallback)
    db.add(SearchHistory(user_id=user_id,query=query[:500],search_type="ai",results_count=len(books)));db.add(interaction);db.flush();interaction_id=interaction.id;db.commit()
    return {"query":query,"answer":answer,"message":answer,"books":books,"parsed_intent":intent,"interaction_id":interaction_id,"ai_available":not fallback,"fallback_used":fallback,"response_type":"catalog"}


def recommendations(db: Session, user_id=None, kind="personalized", limit=12) -> list[dict]:
    stmt=select(Book).where(Book.is_archived.is_(False),Book.copies.any(BookCopy.status==CopyStatus.AVAILABLE))
    if kind=="new": stmt=stmt.order_by(Book.created_at.desc())
    elif kind=="popular": stmt=stmt.outerjoin(BookCopy).outerjoin(Borrowing).group_by(Book.id).order_by(func.count(Borrowing.id).desc())
    elif user_id:
        category_ids=[x for x in db.scalars(select(Book.category_id).join(BookCopy).join(Borrowing).where(Borrowing.user_id==user_id)).all()]
        if category_ids:
            counts=Counter(category_ids); stmt=stmt.order_by((Book.category_id==counts.most_common(1)[0][0]).desc(),Book.title)
    return [book_dict(db,b) for b in db.scalars(stmt.limit(limit)).unique().all()]
