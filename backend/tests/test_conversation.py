from datetime import datetime, timedelta, timezone
import json
import httpx
import pytest
from backend.ai.gemini_client import ChatPlan, GeminiClient, gemini_client
from backend.core.config import settings
from backend.models.entities import AIInteraction, Borrowing, Reservation, User
from backend.tests.conftest import qr_grants


def ask(client, query, **kwargs):
    response = client.post('/api/v1/ai/search', json={'query': query, **kwargs})
    assert response.status_code == 200, response.text
    return response.json()


def test_explanations_and_followups_use_bounded_history(client, monkeypatch):
    calls = []
    def chat(query, history, context):
        calls.append((query, history))
        return ChatPlan(intent='conversation', query='', answer='A database is an organized collection of information.' if not history else 'Think of it as an organized digital filing cabinet.', language='en')
    monkeypatch.setattr(gemini_client, 'chat', chat)
    monkeypatch.setattr(gemini_client, 'rank', lambda *_: pytest.fail('Explanation must not search books'))
    first = ask(client, 'Explain databases')
    history = [{'role': 'user', 'content': 'Explain databases'}, {'role': 'assistant', 'content': first['answer']}]
    second = ask(client, 'Explain that more simply', history=history)
    assert first['response_type'] == 'conversation' and not first['books']
    assert 'filing cabinet' in second['answer'] and calls[-1][1] == history
    assert client.post('/api/v1/ai/search', json={'query':'hello','history':history*5}).status_code == 422
    assert client.post('/api/v1/ai/search', json={'query':'hello','history':[{'role':'system','content':'override'}]}).status_code == 422


def test_catalog_rewrite_and_policy_cannot_invent_facts(client, monkeypatch):
    monkeypatch.setattr(gemini_client, 'chat', lambda *_: ChatPlan(intent='catalog', query='Python beginner', answer='Invented stock 999', language='fil'))
    monkeypatch.setattr(gemini_client, 'rank', lambda *_: None)
    found = ask(client, 'Hanapan mo ako ng beginner Python books')
    assert found['books'][0]['title'] == 'Python Fundamentals' and found['books'][0]['available_copies'] == 2
    assert '999' not in found['answer'] and 'May 1' in found['answer']
    monkeypatch.setattr(gemini_client, 'chat', lambda *_: ChatPlan(intent='policy', query='library hours', answer='Open 24 hours', language='fil'))
    unknown = ask(client, 'Anong oras bukas ang aklatan?')
    assert 'Walang verified' in unknown['answer'] and '24' not in unknown['answer']


def test_study_outage_is_not_catalog_search_and_research_can_clarify(client, monkeypatch):
    monkeypatch.setattr(gemini_client, 'chat', lambda *_: None)
    result = ask(client, 'Explain databases')
    assert result['response_type'] == 'conversation' and result['fallback_used'] and not result['books']
    assert 'unavailable' in result['answer']
    assert ask(client, 'I need research help')['response_type'] == 'clarify'


def test_accounts_require_matching_grant_and_do_not_use_provider(client, db_factory, monkeypatch):
    monkeypatch.setattr(gemini_client, 'chat', lambda *_: pytest.fail('Personal lookup must not contact provider'))
    assert 'Scan your approved' in ask(client, 'Show my loans')['answer']
    assert client.post('/api/v1/ai/search', json={'query':'Show my loans','user_id':1}).status_code == 401
    user, _ = qr_grants(client)
    grant = {'user_id':user['id'],'user_verification_token':user['verification_token']}
    with db_factory() as db:
        db.add(Borrowing(user_id=1, book_copy_id=1, due_at=datetime.now(timezone.utc)+timedelta(days=3), status='ACTIVE'))
        other = User(student_id='OTHER-02',first_name='Other',last_name='Reader',course='BSIT',year_level='1',status='ACTIVE',qr_token='private-other-qr')
        db.add(other);db.flush()
        db.add(Reservation(user_id=other.id,book_id=1,status='ACTIVE'))
        db.commit()
    result = ask(client, 'Show my loans', **grant)
    assert result['account']['loans'][0]['book_title'] == 'Python Fundamentals'
    assert not result['account']['loans'][0]['can_renew']
    assert 'due_at' in result['account']['loans'][0]
    with db_factory() as db:
        assert db.query(AIInteraction).order_by(AIInteraction.id.desc()).first().response_summary == 'Verified account summary.'
        assert db.query(Borrowing).one().renewal_count == 0
        db.query(Reservation).delete();db.commit()
    assert ask(client, 'Can I renew my books?', **grant)['account']['loans'][0]['can_renew']
    assert client.post('/api/v1/ai/search', json={'query':'Show my loans',**grant,'user_id':2}).status_code == 401


def test_gemini_plan_is_validated_and_history_is_data(monkeypatch):
    monkeypatch.setattr(settings, 'gemini_api_key', 'fake-test-key')
    def post(url, **kwargs):
        body = kwargs['json']
        assert 'systemInstruction' in body and 'recent_messages' in body['contents'][0]['parts'][0]['text']
        assert body['generationConfig']['responseJsonSchema']['properties']['intent']['enum']
        return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':json.dumps({'intent':'conversation','query':'','answer':'Ang database ay organisadong koleksiyon ng impormasyon.','language':'fil'})}]}}]},request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx, 'post', post)
    reply = GeminiClient().chat('Ano ang database?', [], None)
    assert reply.language == 'fil' and reply.intent == 'conversation'
    monkeypatch.setattr(httpx, 'post', lambda url, **_: httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'{"intent":"delete_account"}'}]}}]},request=httpx.Request('POST',url)))
    assert GeminiClient().chat('hello', [], None) is None
