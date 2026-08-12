# Operations

Create a local SQLite backup:

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.backup_sqlite
```

Run queued email delivery after configuring `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, and `SMTP_USE_TLS`:

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.email_worker
```

For PostgreSQL deployments, use `pg_dump` and verify a restore separately. The SQLite utility intentionally refuses non-SQLite databases.
