"""Conversation routing around verified, read-only library queries."""
from datetime import datetime, timezone
import re
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from backend.ai.gemini_client import gemini_client
from backend.models.entities import AIInteraction, BookCopy, Borrowing, BorrowingStatus, Fine, FineStatus, Reservation, ReservationStatus, User
from backend.services import policy_service as policy
from backend.services.recommendation_service import ai_search, policy_answer


ACCOUNT = re.compile(r"\b(my (?:loans|borrowed|books|account|fines|balance|due)|what (?:did|have) i borrow|when (?:are|is) my|can i renew my|loans ko|hiniram ko|mga hiniram|libro ko|account ko|multa ko|due ko|aking (?:libro|account|utang)|renew (?:my|them|it)|renew ko)\b", re.I)
STUDY = re.compile(r"\b(explain|explanation|compare|difference|what is|what are|simpler|simply|research help|help with research|study plan|ipaliwanag|pagkakaiba|ano ang|mas simple|mas madaling intindihin)\b", re.I)


def language_of(query: str, history: list[dict]) -> str:
    # Used only for deterministic account/error messages; conversational language is model-selected.
    text = " ".join([m["content"] for m in history if m["role"] == "user"][-2:] + [query]).lower()
    if re.search(r"(?:in|use|speak) english", query, re.I):
        return "en"
    return "fil" if re.search(r"\b(filipino|tagalog|ano|paano|ilang|magkano|ipaliwanag|aking|hiniram|multa|salamat|ko|akin)\b", text) else "en"


def record_reply(db: Session, query: str, answer: str, response_type: str, user_id, context, *, fallback=False, language="en", account=None) -> dict:
    # Personal account details stay on the server/client path and out of provider/history payloads.
    row = AIInteraction(user_id=user_id, question=query[:1000], response_summary="Verified account summary." if response_type == "account" else answer, fallback_used=fallback)
    db.add(row); db.commit(); db.refresh(row)
    return {"query": query, "answer": answer, "message": answer, "books": [], "context": context,
            "interaction_id": row.id, "response_type": response_type, "fallback_used": fallback,
            "ai_available": not fallback, "personalized": bool(user_id), "language": language, "account": account}


def account_reply(db: Session, query: str, user_id, context, language: str) -> dict:
    fil = language != "en"
    user = db.get(User, user_id) if user_id else None
    if not user or user.status != "ACTIVE":
        answer = "I-scan muna ang approved library ID sa My account, pagkatapos bumalik sa chat para makita ang loans at due dates mo." if fil else "Scan your approved library ID in My account, then return to chat to see your loans, due dates and renewal options."
        return record_reply(db, query, answer, "account", None, context, language=language)
    loans = db.scalars(select(Borrowing).options(joinedload(Borrowing.book_copy).joinedload(BookCopy.book)).where(
        Borrowing.user_id == user_id, Borrowing.status.in_([BorrowingStatus.ACTIVE, BorrowingStatus.OVERDUE])).order_by(Borrowing.due_at)).unique().all()
    waiting = set(db.scalars(select(Reservation.book_id).where(Reservation.user_id != user_id,
        Reservation.status.in_([ReservationStatus.ACTIVE, ReservationStatus.READY]))).all())
    now = datetime.now(timezone.utc)
    limit = policy.max_renewals(db)
    items = []
    for loan in loans:
        due = loan.due_at if loan.due_at.tzinfo else loan.due_at.replace(tzinfo=timezone.utc)
        eligible = loan.status == BorrowingStatus.ACTIVE and due >= now and loan.renewal_count < limit and loan.book_copy.book_id not in waiting
        items.append({"book_title": loan.book_copy.book.title, "due_at": due.isoformat(), "can_renew": eligible,
                      "renewal_note": ("Maaaring i-renew sa My account; iche-check ulit bago ma-confirm." if fil else "Renew in My account; eligibility is checked again before confirmation.") if eligible else
                      ("Hindi puwedeng i-renew ngayon: overdue, naabot ang limit, o may naghihintay na reservation." if fil else "Cannot renew now: overdue, renewal limit reached, or another member has a waiting reservation.")})
    fine = db.scalar(select(func.coalesce(func.sum(Fine.amount_cents), 0)).where(Fine.user_id == user_id, Fine.status == FineStatus.UNPAID)) or 0
    answer = (f"May {len(items)} active loan(s) ka. Narito ang due dates at renewal options. Recorded unpaid fines: PHP {fine / 100:.2f}." if fil else
              f"You have {len(items)} active loan(s). Your due dates and renewal options are below. Recorded unpaid fines: PHP {fine / 100:.2f}.")
    return record_reply(db, query, answer, "account", user_id, context, language=language,
                        account={"loans": items, "unpaid_fine_cents": fine})


def localized_policy(db: Session, query: str, answer: str, language: str) -> str:
    if language == "en":
        return answer
    q = query.lower()
    if "no verified setting" in answer:
        return "Walang verified na impormasyon ang LIBRAI tungkol dito. Magtanong sa library staff. Maaari kitang tulungan sa borrowing limits, loan period, renewals, reservations at fines."
    if "Choose Register" in answer:
        return "Piliin ang Register sa Home. Ilagay ang details o i-scan ang campus at library cards, i-review, at isumite para sa staff approval. Pagkatapos ma-approve, maaaring ma-issue o ma-email ang library QR mo."
    if "Choose Borrow" in answer:
        return "Piliin ang Borrow a book, i-scan ang approved library ID at QR ng physical book, i-review ang details, at i-confirm. Nasa receipt ang due date."
    if "Choose Return" in answer:
        return "Piliin ang Return a book, i-scan ang book QR, i-review ang loan, at i-confirm. Makikita sa receipt kung may overdue fine."
    if "renew" in q or "palawig" in q:
        return f"Puwedeng mag-renew nang hanggang {policy.max_renewals(db)} beses; dagdag na {policy.borrowing_period_days(db)} araw bawat renewal. Dapat active at hindi overdue ang loan, at walang ibang member na naghihintay sa title. I-scan ang ID sa My account para mag-renew."
    if any(w in q for w in ("reserve", "reservation", "pickup", "pareserba")):
        return f"Kapag ready na ang reservation, may {policy.reservation_hold_days(db)} araw para kunin ito. Sa My account puwedeng mag-reserve ng unavailable title o tingnan ang reservations."
    if any(w in q for w in ("fine", "multa", "overdue", "penalty")):
        block = "Bawal muna ang bagong borrowing habang may unpaid fine." if policy.block_borrow_with_unpaid_fines(db) else "Hindi hinaharang ng unpaid fines ang bagong borrowing."
        overdue = "Bawal muna ang bagong borrowing habang may overdue loan." if not policy.allow_overdue(db) else "Pinapayagan ang borrowing kahit may overdue loan."
        return f"Ang overdue fine ay PHP {policy.overdue_fine_per_day_cents(db) / 100:.2f} bawat araw bawat overdue loan. {block} {overdue} Tingnan ang recorded balance sa My account."
    if any(w in q for w in ("how long", "how many days", "ilang araw", "gaano katagal", "loan period", "due date")):
        return f"Ang loan period ay {policy.borrowing_period_days(db)} araw. Makikita ang eksaktong due date ng loan mo sa My account at sa borrowing receipt."
    if any(w in q for w in ("library rules", "library policy", "borrowing rules", "patakaran")):
        return f"Hanggang {policy.borrowing_limit(db)} active loans sa loob ng {policy.borrowing_period_days(db)} araw. Hanggang {policy.max_renewals(db)} renewal(s); {policy.reservation_hold_days(db)} araw ang reservation pickup hold. Ang overdue fine ay PHP {policy.overdue_fine_per_day_cents(db) / 100:.2f} bawat araw bawat overdue loan. Magtanong tungkol sa isang rule para sa mga kondisyon nito."
    return f"Puwedeng humiram ng hanggang {policy.borrowing_limit(db)} libro sa isang pagkakataon, sa loob ng {policy.borrowing_period_days(db)} araw. Makikita ang eksaktong due date ng loan mo sa My account."


def chat_reply(db: Session, query: str, user_id=None, context=None, history: list[dict] | None = None) -> dict:
    history = history or []
    language = language_of(query, history)
    if ACCOUNT.search(query):
        return account_reply(db, query, user_id, context, language)
    direct_policy = policy_answer(db, query)
    # Known settings/procedures work even during an AI outage, without a model request.
    if direct_policy:
        answer = localized_policy(db, query, direct_policy, language)
        return record_reply(db, query, answer, "policy", user_id, context, language=language)
    if re.fullmatch(r"(?:i need research help|help with (?:my )?research|tulong sa research)[.!?]*", query.strip(), re.I):
        answer = "Ano ang research topic mo, at anong tulong ang kailangan mo?" if language != "en" else "What is your research topic, and what would you like help with?"
        return record_reply(db, query, answer, "clarify", user_id, context, language=language)
    plan = gemini_client.chat(query, history, context)
    if plan:
        language = plan.language
        if plan.intent == "account":
            return account_reply(db, query, user_id, context, language)
        if plan.intent == "policy":
            canonical = plan.query or query
            answer = policy_answer(db, canonical) or "Please ask library staff about that policy. LIBRAI has no verified setting for it."
            return record_reply(db, query, localized_policy(db, canonical, answer, language), "policy", user_id, context, language=language)
        if plan.intent in {"conversation", "clarify"}:
            answer = plan.answer.strip()
            if answer:
                return record_reply(db, query, answer, plan.intent, user_id, context, language=language)
        if plan.intent == "catalog":
            result = ai_search(db, plan.query.strip() or query, user_id, context)
            result.update(query=query, language=language)
            if language != "en":
                result["answer"] = result["message"] = (f"May {len(result['books'])} matching title(s) sa catalog. Narito ang availability at shelf locations." if result["books"] else "Walang matching libro sa catalog. Subukan ang ibang topic o alisin ang reading-level o availability filter.")
            return result
    if re.search(r"(?:research help|help with (?:my )?research|tulong sa research)\s*[.!?]*$", query, re.I):
        answer = "Ano ang research topic mo, at anong tulong ang kailangan mo?" if language != "en" else "What is your research topic, and what would you like help with?"
        return record_reply(db, query, answer, "clarify", user_id, context, language=language)
    if STUDY.search(query):
        answer = "Hindi available ang conversational AI ngayon. Subukan ulit; maaari ka pa ring maghanap ng libro o magtanong tungkol sa library rules." if language != "en" else "Conversational AI is unavailable right now. Please retry. Catalog search and verified library rules are still available."
        return record_reply(db, query, answer, "conversation", user_id, context, fallback=True, language=language)
    # Existing catalog matching remains available when the provider cannot respond.
    return ai_search(db, query, user_id, context)
