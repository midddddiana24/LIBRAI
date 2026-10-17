from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from backend.ai.gemini_client import GeminiClient, GeminiRanking, gemini_client
from backend.models.entities import Book, BookCopy, Borrowing, Category, CopyStatus, SystemSetting
from backend.tests.conftest import qr_grants


def ask(client, query, **extra):
    response = client.post("/api/v1/ai/search", json={"query": query, **extra})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.mark.parametrize("query", ["beginner astronomy", "romance", "available quantum physics", "May libro ba tungkol sa romansa para sa baguhan?", "pyth"])
def test_unrelated_available_books_never_qualify(client, monkeypatch, query):
    monkeypatch.setattr(gemini_client, "rank", lambda *_: pytest.fail("No provider request for no candidates"))
    result = ask(client, query)
    assert result["books"] == [] and "No matching" in result["answer"]


def test_followups_keep_topic_filter_and_can_clear_filters(client, db_factory, monkeypatch):
    monkeypatch.setattr(gemini_client, "rank", lambda *_: None)
    first = ask(client, "May libro ba tungkol sa Python programming para sa baguhan?")
    assert first["books"][0]["id"] == 1
    second = ask(client, "Only available books", context=first["context"])
    assert second["context"] == {"topics": ["python", "programming"], "level": "beginner", "available_only": True}
    with db_factory() as db:
        for copy in db.query(BookCopy):
            copy.status = CopyStatus.BORROWED
        db.commit()
    assert not ask(client, "Show easier ones", context=second["context"])["books"]
    third = ask(client, "Include unavailable", context=second["context"])
    assert third["books"][0]["available_copies"] == 0
    assert third["context"]["topics"] == ["python", "programming"]
    assert not ask(client, "advanced Python")["books"]
    assert "Which topic" in ask(client, "Show easier ones")["answer"]
    assert ask(client, "romance", context=second["context"])["context"]["topics"] == ["romance"]


def test_policies_read_changed_staff_settings_without_ai(client, db_factory, monkeypatch):
    monkeypatch.setattr(gemini_client, "rank", lambda *_: pytest.fail("Policy must use actual settings"))
    with db_factory() as db:
        db.add_all([SystemSetting(key="BORROWING_LIMIT", value="5"), SystemSetting(key="BORROWING_PERIOD_DAYS", value="14"), SystemSetting(key="OVERDUE_FINE_PER_DAY_CENTS", value="125")])
        db.commit()
    assert "5 active loans" in ask(client, "Ilang libro ang puwedeng hiramin?")["answer"]
    assert "14 days" in ask(client, "How many days can I borrow a book?")["answer"]
    assert "PHP 1.25" in ask(client, "Magkano ang multa?")["answer"]
    assert "not overdue" in ask(client, "Can I renew?")["answer"]
    assert "not overdue" in ask(client, "How many times can I renew books?")["answer"]
    assert "pickup hold" in ask(client, "How many books can I reserve?")["answer"]
    assert "PHP 1.25" in ask(client, "library rules")["answer"]
    assert "2 day(s)" in ask(client, "reservation pickup")["answer"]
    assert "no verified setting" in ask(client, "What are the library hours?")["answer"]
    with db_factory() as db:
        db.query(SystemSetting).filter_by(key="BORROWING_LIMIT").one().value = "4"
        db.commit()
    assert "4 active loans" in ask(client, "How many books can I borrow?")["answer"]


def test_model_claims_cannot_replace_catalog_facts(client, monkeypatch):
    ranking = SimpleNamespace(message="Everything is free on shelf FAKE", recommendations=[SimpleNamespace(book_id=999, reason="invented"), SimpleNamespace(book_id=1, reason="free on FAKE"), SimpleNamespace(book_id=1, reason="duplicate")])
    monkeypatch.setattr(gemini_client, "rank", lambda *_: ranking)
    result = ask(client, "Python")
    assert len(result["books"]) == 1
    assert result["books"][0]["shelf_location"] == "CS-001"
    assert result["books"][0]["available_copies"] == 2
    assert "FAKE" not in str(result) and "invented" not in str(result)


def test_empty_model_result_does_not_turn_into_unrelated_fallback(client, monkeypatch):
    monkeypatch.setattr(gemini_client, "rank", lambda *_: GeminiRanking(message="none", recommendations=[]))
    result = ask(client, "Python")
    assert result["books"] == [] and result["fallback_used"] is False
    client_instance = GeminiClient()
    assert client_instance._validate_ids(GeminiRanking(message="none", recommendations=[]), [{"id": 1}]) is not None
    assert client_instance._validate_ids(GeminiRanking(message="bad", recommendations=[{"book_id": 999, "reason": "bad"}]), [{"id": 1}]) is None
    parsed = GeminiRanking(message="ok", recommendations=[{"book_id": 1, "reason": "a"}, {"book_id": 1, "reason": "b"}])
    assert len(client_instance._validate_ids(parsed, [{"id": 1}]).recommendations) == 1


def test_personalization_requires_grant_and_uses_history(client, db_factory):
    with db_factory() as db:
        category = Category(name="Art")
        book = Book(isbn="9780000000002", title="Aardvark Art", author="Another Author", shelf_location="ART-01", category=category)
        db.add(BookCopy(book=book, accession_number="ART-01", qr_token="art-test-qr-token", status=CopyStatus.AVAILABLE))
        db.add(Borrowing(user_id=1, book_copy_id=1, borrowed_at=datetime.now(timezone.utc), due_at=datetime.now(timezone.utc)))
        db.commit()
    for route, body in [("search", {"query": "Python"}), ("recommend", {"kind": "recommended"})]:
        assert client.post(f"/api/v1/ai/{route}", json={**body, "user_id": 1}).status_code == 401
    user, _ = qr_grants(client)
    grant = {"user_id": user["id"], "user_verification_token": user["verification_token"]}
    result = client.post("/api/v1/ai/recommend", json={"kind": "recommended", **grant})
    assert result.status_code == 200 and result.json()[0]["id"] == 1
    assert ask(client, "Python", **grant)["personalized"] is True
    assert ask(client, "Python")["personalized"] is False
    assert client.post("/api/v1/ai/search", json={"query": "Python", "context": {"topics": ["a" * 81]}}).status_code == 422


@pytest.mark.parametrize("query,expected", [
    ("How do I borrow a book?", "scan your approved library ID"),
    ("Paano manghiram?", "scan your approved library ID"),
    ("How do I return a book?", "confirm the return"),
    ("How do I register?", "staff approval"),
])
def test_chat_procedures_do_not_call_ranking(client, monkeypatch, query, expected):
    monkeypatch.setattr(gemini_client, "rank", lambda *_: pytest.fail("Procedure answers must not depend on model guesses"))
    result = ask(client, query)
    assert result["response_type"] == "policy" and expected in result["answer"]
    assert result["books"] == []
