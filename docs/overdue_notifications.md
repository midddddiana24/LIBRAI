# Overdue borrowing reminders

Each ACTIVE or OVERDUE loan becomes eligible after its actual due_at passes. The API checks while awake every 30 seconds, queues up to 100 new reminders per cycle, and records one in-app notice plus one email for a member with a registered address. Notices appear in My account > Notifications and queued emails in Admin > Email deliveries. No daily repeats or automatic fine changes are introduced. Displayed deadlines use Philippine time (UTC+08:00).

Deduplication is durable: notifications link to the loan and a database index permits one OVERDUE_REMINDER per loan. PostgreSQL row locks coordinate multiple workers; SQLite requires one worker. Queue creation and its deduplication marker commit together. A failed transaction can be retried normally. Returned, future-due and exactly-at-due-time loans are excluded. Email delivery rechecks the current loan; stale reminders are withheld before transport and marked failed with an explanation.

## Deployment and delivery

1. Deploy the latest backend commit. The start command must run `alembic upgrade head` before Uvicorn. Migration `d3a9e6f120b4` adds a nullable loan link and an overdue-reminder index; it does not seed, replace or delete existing records.
2. `OVERDUE_NOTIFICATIONS_ENABLED=true` is the default. Set false to disable automatic reminder generation.
3. `EMAIL_AUTOSEND_ENABLED=false` keeps emails queued for staff review. Use Send now on an intended pending row for a controlled check. Set true only when the sender is working and staff intend the pending email backlog to be sent.
4. Actual sending uses the existing Gmail API or SMTP configuration. Valid configuration alone does not prove authorization, provider acceptance or inbox receipt.
5. Render Free sleep pauses the checks. The next awake cycle catches up; this is not an always-on or exact-time scheduler. The existing separate email worker sends queued notices but does not itself scan for overdue loans.

This backend feature works with the existing web and APK notification screens. It does not require another APK after 1.9.3. The QR download fix is separately documented in release_1.9.3.md.

## Verification

- Full backend regression run: 90 passed; one existing Starlette/httpx deprecation warning.
- Expanded overdue-specific suite: 10 passed, including deduplication, batch catch-up, deadline boundary, returned loans, missing email, rollback, stale-email suppression and automatic polling through a fake email transport.
- SQLite upgrade/downgrade test preserved existing notification rows and email queue links.
- PostgreSQL offline SQL generation verified the nullable link, foreign key and partial unique index. No production database was migrated manually during these checks.
- No real reminders were sent by the automated tests. Production polling may create real reminders once this feature is deployed. Inbox receipt and physical tablet acceptance remain separate checks.
