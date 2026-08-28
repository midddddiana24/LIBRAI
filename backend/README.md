# LIBRAI Backend

FastAPI/SQLAlchemy backend and authoritative business-rule engine for LIBRAI.

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
$env:LIBRAI_SEED_ADMIN_PASSWORD="replace-with-a-secure-password"
python -m backend.scripts.seed
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

OpenAPI is available at `http://127.0.0.1:8000/docs`, health at `/health`, and the API root is `/api/v1`.

## Database

SQLite is the default local fallback. For PostgreSQL set, for example:

```text
DATABASE_URL=postgresql+psycopg://librai:password@localhost/librai
```

Always apply `alembic upgrade head`; production does not depend on `create_all`.

## Security model

- Admins authenticate with Argon2 password hashes and expiring HS256 access tokens.
- Logout persists token revocation.
- Admin endpoints enforce bearer authentication and role checks.
- QR codes contain opaque random tokens only.
- QR verification issues five-minute, resource-bound grants. Borrow, return, and reservation endpoints reject guessed IDs without the matching grant.
- Sensitive login/AI routes are rate-limited and request sizes are bounded.
- Gemini receives queries and catalog candidates only—never QR tokens, contacts, emails, or passwords.

## Business rules

Borrow and return services own availability, limits, overdue rules, due dates, reservation queues, notifications, and audit entries. Copy claiming uses an atomic conditional update, so only one concurrent kiosk can transition an available copy to borrowed.

Policy values are stored in `system_settings`: `BORROWING_LIMIT`, `BORROWING_PERIOD_DAYS`, `MAX_RENEWALS`, `ALLOW_BORROW_WITH_OVERDUE`, and `RESERVATION_HOLD_DAYS`.

## AI fallback

Set `GEMINI_API_KEY` to enable grounded Gemini reranking. Candidate books always come from the database and returned IDs are validated. Without a key, during rate limits, or on malformed responses, the deterministic catalog recommender remains operational and reports `fallback_used: true`.

To use Qwen through TokenRouter as the catalog-ranking provider, set
`TOKENROUTER_API_KEY`. It takes priority over Gemini for catalog ranking while
speech-to-text continues to use `GEMINI_API_KEY` and all library operations
remain backend-controlled. Never place either key in source code.

```text
TOKENROUTER_API_KEY=your-tokenrouter-key
TOKENROUTER_MODEL=qwen/qwen3.8-max-free
```

## Tests

```powershell
pytest -q
```

Tests use isolated SQLite databases and cover authentication, QR safety, borrowing policy failures, concurrent borrowing, returns, reservations, and Gemini fallback.
