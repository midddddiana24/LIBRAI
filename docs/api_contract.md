# LIBRAI REST API Contract

Version: 1.0. Base path: `/api/v1`. Interactive schemas are also available from `/docs` and `/openapi.json`.

Successful endpoints return the documented resource directly for frontend compatibility. Errors use the appropriate HTTP status and include `detail`; domain conflicts additionally include `{success:false,error:{code,message}}`.

Common errors: `401` missing/expired/revoked credentials or QR grant, `403` insufficient role, `404` resource/QR not found, `409` business-rule conflict, `413` request too large, `422` schema validation, `429` rate limit, and `5xx` infrastructure failure.

## System and authentication

| Method | URL | Auth | Request → response | Rules/errors |
|---|---|---|---|---|
| GET | `/health`, `/api/v1/health` | Public | none → `{status,service,version}` | Checks database connectivity. |
| POST | `/auth/login` | Public | `{username,password}` → `{access_token,token_type,expires_at,user}` | Argon2 verification; `401`; audited and rate-limited. |
| GET | `/auth/me` | Admin | none → safe admin profile | Rejects expired/revoked/inactive accounts. |
| POST | `/auth/logout` | Admin | none → `{message}` | Persists JWT `jti` revocation and audits logout. |

## Student registration and ID-assisted input

`POST /registrations` is public and rate-limited. It accepts `student_id`, `first_name`, `last_name`, `course`, `year_level`, optional `library_card_number`, and optional contact fields. It creates a **PENDING** member and returns HTTP 202 with a generic acknowledgement only. Duplicate identifiers receive the same acknowledgement and never update an existing member. Extra fields are rejected; clients cannot request ACTIVE status or choose a QR token.

Staff use `GET /users?status=PENDING` to review requests and `PUT /users/{id}` with status ACTIVE to approve or INACTIVE to reject. These require admin authentication and are audited. Pending members cannot borrow, obtain a kiosk verification grant, or have a library QR issued. Campus student ID and library card number are separate identifiers; each has its own uniqueness constraint.

OCR is performed locally in the browser using self-hosted Tesseract assets. There is no ID-photo OCR API or photo upload in this registration flow. Only reviewed form fields are submitted. OCR output is an editable draft, not identity or enrollment verification. Existing signed LIBRAI QR borrowing remains authoritative.

## QR operations

Administrators can retrieve the current QR without invalidating it with
`GET /users/{id}/qr` and `GET /book-copies/{id}/qr`. The corresponding `POST`
routes intentionally rotate the opaque token and invalidate the old QR.
Both responses include a two-minute `download_url`. Opening
`GET /qr/download/{ticket}` downloads a non-cacheable PNG with a safe filename;
the signed ticket contains only the entity type and ID, never the raw QR token.
`POST /books/{id}/copies/qr-sheet` creates an A4 PDF label sheet for every
physical copy of a title and returns a five-minute signed download URL.

| Method | URL | Auth | Request → response | Rules/errors |
|---|---|---|---|---|
| POST | `/qr/verify-user` | Public | `{token}` or `{qr_token}` → safe user summary plus `verification_token` | No raw QR/contact/email returned. Grant expires in five minutes. |
| POST | `/qr/verify-book` | Public | token → copy/book summary plus `verification_token` | Grant binds to one physical copy. |
| POST | `/qr/decode-image` | Public | Multipart JPEG, PNG, or WebP QR photo → `{token}` | Decoded in memory, never stored, size-limited and rate-limited. |
| POST | `/users/{id}/qr` | Admin | none → `{user_id,qr_image}` | Rotates/invalidate previous opaque token; audited. |
| POST | `/book-copies/{id}/qr` | Admin | none → `{book_copy_id,qr_image}` | Rotates copy token; audited. |

## Users and books

`POST /books` accepts optional `initial_copy_count` from 0 through 100. The
title and initial physical copies are committed in one transaction; each copy
receives a unique accession number and opaque QR token.

Administrative user responses include editable name, course, year, email,
contact, and status fields. They never include QR tokens, PIN/password hashes,
or other credential material.

| Method | URL | Auth | Request → response | Rules/errors |
|---|---|---|---|---|
| GET/POST | `/users` | Admin | filters or user fields → paginated users / created user | Unique student ID/email; generated QR. |
| GET/PUT | `/users/{id}` | Admin | update fields → safe user summary | Status is ACTIVE, INACTIVE, or SUSPENDED. |
| GET/POST | `/categories` | GET public, POST admin | none or `{name,description?}` → categories | Category names are unique. |
| GET/POST | `/books` | GET public, POST admin | filters or book fields → paginated books / created book | Book title is separate from copies. |
| GET/PUT | `/books/{id}` | GET public, PUT admin | none/update → detailed book | Includes counts and similar catalog books. |
| POST | `/books/{id}/archive` | Admin | none → archived book | Available copies become archived. |
| GET/POST | `/books/{id}/copies` | Admin | none or `{quantity,accession_numbers?}` → physical copies | Unique accession and random QR per copy. |
| PUT | `/book-copies/{id}` | Admin | `{status}` → physical copy | Cannot bypass an active borrowing by manually changing BORROWED. |
| POST | `/books/{id}/cover` | Admin | multipart JPEG/PNG/WebP → `{book_id,cover_url}` | MIME, binary signature, and configured size are validated. |
| POST | `/borrowings/{id}/renew` | Verified kiosk user | `{user_id,user_verification_token}` → updated receipt | Rejects overdue/returned loans, policy-limit excess, and titles reserved by another user; audited. |
| POST | `/ai/feedback` | Optional verified kiosk user | `{interaction_id,helpful,reason?}` → acknowledgement | Feedback is tied to a real grounded AI interaction. |
| POST | `/users/{id}/photo` | Admin | multipart JPEG/PNG/WebP → safe user projection with `photo_url` | Image is resized, metadata-stripped, normalized to WebP, and audited. |
| GET | `/users/photo/{ticket}` | Signed ticket | none → private WebP image | Short-lived user-photo access; raw private storage paths are never returned. |

## Search and AI

| Method | URL | Auth | Request → response | Rules/errors |
|---|---|---|---|---|
| GET | `/search/books` | Public | `q,category,author,available_only,publication_year,offset,limit` → `{items,total}` | SQL metadata search; records meaningful query analytics. |
| POST | `/ai/search` | Public or user QR grant | `{query,user_id?,user_verification_token?,context?}` → `{query,answer,message,books,ai_available,fallback_used}` | A user ID requires its grant; database candidates first; Gemini only ranks supplied IDs. Returns bounded session context (topics, level, available_only); policy facts come from live admin settings. |
| POST | `/ai/recommend` | Public or user QR grant | `{user_id?,kind,user_verification_token?}` → book array | Deterministic history/category/popularity/availability ranking. |
| POST | `/speech/transcribe` | Public | multipart audio → `{text}` | Gemini transcription requires `GEMINI_API_KEY`; returns `503` without it, `502` if transcription fails, and rejects invalid or oversized uploads. No backend text-to-speech endpoint exists. |

## Borrowing and returns

Administrators may filter borrowing history by `user_id` directly. Kiosk
users requesting the same history must provide the matching short-lived user
QR verification grant.

Reservation creation rejects catalog titles with no non-archived physical
copies using `BOOK_HAS_NO_COPIES`. A kiosk user may cancel their own active or
ready reservation using the matching short-lived verification grant; an
administrator may cancel without that kiosk grant.

Kiosk users may retrieve and mark their own in-system notifications through
`GET /notifications` and `POST /notifications/{id}/read` using the matching
short-lived user verification grant. Administrators retain authenticated access.

| Method | URL | Auth | Request → response | Rules/errors |
|---|---|---|---|---|
| POST | `/borrowings` | User + book QR grants | `{user_id,book_copy_id,user_verification_token,book_verification_token,kiosk_id?}` → receipt | Atomic claim; validates status, overdue policy, limit, availability, queue, duplicate title. Conflict codes include `USER_INACTIVE`, `OVERDUE_RESTRICTION`, `BORROWING_LIMIT_REACHED`, `BOOK_COPY_UNAVAILABLE`, `RESERVED_FOR_ANOTHER_USER`, `DUPLICATE_ACTIVE_BORROWING`, `CONCURRENT_BORROW_CONFLICT`. |
| GET | `/borrowings` | Admin, or matching user QR grant | filters/pagination → `{items,total}` | Supports secure kiosk account history. |
| GET | `/borrowings/{id}` | Admin | none → receipt | `404`. |
| GET | `/borrowings/active/by-copy/{copy_id}` | Book QR grant | `book_verification_token` query → limited active transaction summary | Used before return; `404` if no active loan. |
| POST | `/returns` | Book QR grant | `{borrowing_id,book_verification_token}` → return receipt | Atomically closes loan, computes overdue state, advances reservation queue, notifies, audits. |
| GET | `/returns` | Admin | pagination → returned transactions | Read-only history. |

Due dates and statuses supplied by clients are ignored because those fields are not accepted.
Borrowing also rejects users with unpaid fines when
`BLOCK_BORROW_WITH_UNPAID_FINES=true`; the conflict code is
`UNPAID_FINE_RESTRICTION`. Return processing assesses configured overdue fines
before closing the transaction.

## Reservations and notifications

| Method | URL | Auth | Request → response | Rules/errors |
|---|---|---|---|---|
| GET | `/reservations` | QR grant for `user_id`, otherwise admin | query → `{items,total}` | Queue position is server-calculated. |
| POST | `/reservations` | User QR grant | `{user_id,book_id,user_verification_token}` → reservation | Rejects available books and duplicate active reservations. |
| DELETE | `/reservations/{id}` | Admin | none → cancelled status | Only ACTIVE/READY can cancel. |
| GET | `/notifications?user_id=` | Admin | none → notification array | In-system delivery foundation. |
| POST | `/notifications/{id}/read` | Admin | none → read status | `404`. |

## Fines and email delivery foundation

Overdue fines are assessed by the backend during return processing. The default
fine is PHP 5.00 per overdue day (`OVERDUE_FINE_PER_DAY_CENTS=500`), and
borrowing is blocked while unpaid fines exist when
`BLOCK_BORROW_WITH_UNPAID_FINES=true`. User-facing events create both an
in-system notification and a pending `email_deliveries` row when the user has an
email address; a later SMTP worker can send those queued emails.

| Method | URL | Auth | Request -> response | Rules/errors |
|---|---|---|---|---|
| GET | `/fines` | Admin, or matching user QR grant | `user_id,status,verification_token?` -> `{items,total}` | Kiosk users can only read their own fines with a matching grant. |
| POST | `/fines/{id}/pay` | Admin | `{note?}` -> paid fine | Only unpaid fines can be marked paid; audited and notifies the user. |

## Administration, settings, reports, audit

| Method | URL | Auth | Request → response | Rules/errors |
|---|---|---|---|---|
| GET | `/admin/dashboard` | Admin | none → KPIs plus chart datasets | Counts titles/copies separately and calculates current overdue items. |
| GET | `/reports` | Admin | `report_type`, optional `start_date`, `end_date` → preview | Preview capped at 100 rows and uses the same date filters as export. |
| POST | `/reports/export` | Admin | report type/date range/`pdf|csv|xlsx` → `{job_id,status,download_url}` | Backend generates artifact and audit entry. |
| GET | `/reports/{job_id}/download` | Admin | none → file | Authenticated download. |
| GET | `/reports/public-download/{ticket}` | Signed ticket | none → file | Browser download ticket expires after five minutes and disables caching. |
| GET | `/audit-logs` | Admin | action/pagination → `{items,total}` | Never includes password, token, PIN, or API secret data. |
| GET | `/settings` | SUPER_ADMIN | none → policies | Returns defaults merged with stored values. |
| PUT | `/settings` | SUPER_ADMIN | Object with one or more supported policy keys → policies | Validates every value before atomically saving the complete update. |
| PUT | `/settings/{key}` | SUPER_ADMIN | `{value}` → setting | Allowlisted policy keys only; audited. |

## Compatibility notes for the Flet client

The QR responses add `verification_token`. The updated frontend preserves it in structured session state and sends it only to borrow/return/reservation endpoints. The API continues returning both frontend-friendly aliases (`id`, `name`, `copy_id`, `available`) and explicit domain fields (`user_id`, `display_name`, `accession_number`, `availability`).


## Email delivery administration

- `POST /api/v1/users/{user_id}/email-qr`: staff only; active member with email required; queues the current library ID QR (202). It does not rotate the QR or send synchronously.
- `GET /api/v1/notifications/admin/email-status`: staff only; API-process configuration flags, no secrets and no connectivity claim. A separate worker may have its own configuration.
- `POST /api/v1/notifications/admin/email-deliveries/{delivery_id}/retry`: staff only; only FAILED rows can return to PENDING (202), other states return 409.
- Staff creation of ACTIVE accounts and PENDING-to-ACTIVE approval queue `LIBRARY_ID` notifications when email exists. Other edits do not resend. Pending public registration never emails a QR.
- See [Gmail setup and delivery semantics](gmail_notifications.md).

### Gmail API delivery

- `POST /api/v1/notifications/admin/email-deliveries/{delivery_id}/send`: staff only; requests background delivery of one PENDING email (202). Non-pending rows return 409; missing sender configuration returns 503. Refresh the delivery status to see the result.
- `EMAIL_TRANSPORT=gmail_api` selects HTTPS delivery using private `GMAIL_OAUTH_FILE`. No OAuth tokens or credentials are returned by API endpoints.
- `EMAIL_AUTOSEND_ENABLED` defaults false. When enabled, API lifespan polling processes up to five pending emails per cycle while the API is awake. Render sleep pauses polling; the Neon outbox persists.
- Email configuration status includes transport, email_configured and autosend_enabled. These describe configuration, not successful Gmail authorization or inbox receipt.

See [AI assistant behavior and verification](ai_assistant.md) for matching limits, session privacy, policy answers and physical voice acceptance checks.

### Conversational assistant (1.7.0)

`POST /api/v1/ai/search` accepts optional `history` with at most eight `{role: "user" | "assistant", content: string}` messages, each 1–2,500 characters. Only the current `query` (2–1,000 characters), bounded history and catalog context go to the conversation provider. History cannot grant authority. Supplying a `user_id` always requires a valid matching `user_verification_token`.

`response_type` distinguishes `conversation`, `clarify`, `catalog`, `policy`, and `account`. `language` is `en`, `fil` or `mixed` on new routed replies. Verified account replies may include `account.loans` (title, ISO due date, renewal eligibility/note) and `account.unpaid_fine_cents`. Client history excludes account replies. Policy values, library books and account records are server-derived; model plans cannot execute writes. Provider outage remains a normal reply with `fallback_used=true` for study questions, while local library lookups continue.
