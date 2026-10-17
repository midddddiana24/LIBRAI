# Gmail SMTP alternative: school PC or paid worker

> Alternative guide: for the recommended free hosted Gmail API route, use [the main Gmail guide](gmail_notifications.md). For free SMTP, use a school PC; paid Render worker instructions below are optional.

## What is implemented locally

- Student kiosk registration stays **pending** until staff approve it.
- Staff approval, or staff creation of an active member, queues a welcome email if an email address was supplied.
- The worker attaches `library-id.png`, containing the member's current LIBRAI QR token. It uses the same token that the Borrow scanner verifies; the printed campus/library number is not a substitute for this QR.
- Staff can choose **Library users > Email QR** to resend an active member's ID. Confirm the email belongs to the member first. Saving unrelated edits does not resend it.
- **Email deliveries** shows pending, sent, or failed. Only failed messages can be retried. Retry queues work; it does not send from the admin browser.
- Borrow confirmations (including due date), returns, renewals, reservation creation/pickup availability, fine assessment and fine payment already queue notifications when a member has an email address.
- Scheduled due-soon/overdue reminders and password-reset emails are not implemented by this change. A due date in a borrow confirmation is not a scheduled reminder.

## 1. Choose SMTP-capable hosting

Your current Render Free API cannot send outbound traffic on ports 25, 465 or 587. Gmail SMTP needs 465 or 587. Adding a Gmail password to the Free service will not remove this restriction. [Render Free documentation](https://render.com/docs/free).

You selected hosting that allows SMTP. The least disruptive arrangement is:

1. Keep the existing Neon database and API URL.
2. Add a **paid Render Background Worker** for Gmail. The API may remain Free because only the worker opens the SMTP connection. Render workers poll continuously: [worker documentation](https://render.com/docs/background-workers).
3. If you also want an always-on API, change the existing API instance to a paid plan in its Render settings. Its URL and Neon database remain the same. This is a separate paid service.
4. Review the current charges in Render before creating or upgrading anything. No paid service has been created by these local changes. [Pricing](https://render.com/pricing).

Do not select the old paid database/disk Blueprint: this feature uses the existing Neon database and creates no new database or media disk.

## 2. Create the Gmail app password

1. Use a dedicated library Gmail account you control.
2. Enable Google **2-Step Verification**.
3. Open [Google App Passwords](https://myaccount.google.com/apppasswords) and create one named LIBRAI.
4. Save it directly in the worker's private Environment settings as `SMTP_PASSWORD`. Do not send it through chat, commit it, or use your normal Gmail password.
5. Some school accounts do not allow app passwords. Ask the school account administrator if the option is missing. [Google's instructions](https://support.google.com/accounts/answer/185833).

## 3. Deploy the application changes first

1. Publish the reviewed local registration/email code to `online-admin-postgres` before Render can build it. These instructions do not mean it has already been pushed.
2. Deploy the API from that branch using its existing build/start commands. Its start command must run `alembic upgrade head` before Uvicorn so the new library-card-number column exists. Keep the current `DATABASE_URL`, stable `SECRET_KEY`, AI key, storage and CORS settings.
3. Deploy the web kiosk/admin from the same branch. A new Android APK is separately required for kiosk registration on the installed app.
4. Check API `/health`: `status=healthy` and `database=connected`. Sign into `/admin` and verify the dashboard, users and pending queue load.
5. Review **Email deliveries** before enabling a worker. Existing pending messages will also be eligible for delivery. Do not start continuous delivery until staff approve that backlog.

## 4. Configure a controlled first email

Create or approve a test member with an inbox you own and permission to receive this test. Open **Email deliveries** and note that welcome email's numeric `id`. Do not use somebody else's inbox.

In Render choose **New > Background Worker**, repository LIBRAI, branch `online-admin-postgres`, root directory blank, Python runtime, Singapore region:

- Build command: `pip install -r requirements.txt`
- Initial start command: `python -m backend.scripts.email_worker --delivery-id 123 --watch`
- Replace `123` with the test delivery ID. This processes only that ID, then waits; it does not drain the old queue.
- Instance: a paid worker instance shown in Render; review its charges before creating it.

Set these environment variables in the worker only:

| Name | Value |
| --- | --- |
| `DATABASE_URL` | The same Neon PostgreSQL database as the API; paste privately |
| `LIBRAI_ENV` | `production` |
| `SECRET_KEY` | Same stable API secret; paste privately |
| `GEMINI_API_KEY` or `TOKENROUTER_API_KEY` | Same configured API provider key; current shared settings require one in production, although the email worker does not call AI |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USE_TLS` | `true` |
| `SMTP_USERNAME` | Your full library Gmail address |
| `SMTP_FROM` | The same library Gmail address |
| `SMTP_PASSWORD` | Google app password, entered privately without display spaces |

Port 587 uses verified STARTTLS. Port 465 is also supported with implicit TLS. [Google SMTP settings](https://support.google.com/mail/answer/7104828).

The API does not need the SMTP password if a separate worker sends mail. The staff-only `/api/v1/notifications/admin/email-status` endpoint reports API-process configuration only; it cannot establish worker connectivity or Gmail delivery.

## 5. Prove the first delivery

1. Worker logs should show `EMAIL_WORKER_PROCESSED 1`, followed by 0 while the selected ID is already sent.
2. In admin, refresh **Email deliveries**. The selected row should show `sent` and a sent timestamp. This means Gmail accepted it, not that it reached the inbox.
3. Check the test inbox and spam folder for **Your LIBRAI library ID** and `library-id.png`.
4. Open the attached QR on another screen and scan it in the kiosk. Confirm it identifies the expected test member. Stop before borrowing a real book unless that test transaction is intended.
5. If failed, inspect the redacted error. Authentication errors: check full Gmail username/app password. Network errors: check worker host/port and SMTP restrictions. Correct the settings, then use **Retry** on the failed row.
6. A QR email is withheld if the member is inactive/pending or their email changed before sending. Correct the account, then choose **Email QR** to queue a fresh message to the current address.
7. After staff review the existing pending backlog and the test succeeds, change the worker start command to `python -m backend.scripts.email_worker --watch` and redeploy the worker. Future queued notifications then send automatically, normally after its next 30-second poll.

## Local alternative / commands

For an SMTP-capable school PC, put the same private values in its ignored `.env`, with `DATABASE_URL` pointing to the intended deployed Neon database. Do not run against a different local database and expect the website's queue to be processed.

```powershell
.\.venv\Scripts\python.exe -m backend.scripts.email_worker --delivery-id 123
.\.venv\Scripts\python.exe -m backend.scripts.email_worker --watch
```

Run only one worker for SQLite. PostgreSQL workers lock each selected delivery until its result is committed. Failed deliveries need staff retry; the worker does not repeatedly retry a broken password. SMTP cannot guarantee exactly-once delivery if a process crashes after Gmail accepts a message but before the database commit. Rotating a member QR invalidates previously emailed images; resend the new ID afterward.

## Verified on 17 October 2026

- Live admin page HTTP 200; API health HTTP 200 with database connected (initial cold request timed out, retry succeeded).
- Live protected users/email-deliveries endpoints reject unauthenticated access with HTTP 401 and allow the configured kiosk CORS origin.
- Authenticated staff registration/approval and email queue controls are tested against an isolated local database; this does not prove a live staff password works.
- Worker tests use a simulated SMTP server, including a decodable QR attachment, revoked account/address checks, TLS, failure recording and staff retry. No Gmail inbox delivery or paid hosting activation was performed.
