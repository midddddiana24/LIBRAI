# React migration feature and API matrix

This matrix records the new `web/` client against the existing FastAPI backend. The OpenAPI snapshot in `docs/openapi.json` was generated from `backend.main.app` on 2026-10-13. The backend has 50 route paths. Many endpoint responses lack explicit `response_model` definitions, so `web/src/api.ts` maintains response types checked against the actual handlers.

| Area | API used | New client | Remaining verification/work |
|---|---|---|---|
| Catalog search and detail | `GET /search/books`, `GET /books/{id}` | Kiosk search, detail, pagination | Live browser search and tablet layout |
| QR scanning | `POST /qr/verify-user`, `POST /qr/verify-book` | Native camera plugin; USB/manual fallback; one scan step at a time | Physical Android camera and permission check |
| Borrow | `POST /borrowings` | Sequential ID, book, review, receipt flow and duplicate-click guard | Real QR labels and concurrent tablets |
| Return | `GET /borrowings/active/by-copy/{id}`, `POST /returns` | Sequential book, review, receipt flow | Real book return and fine outcome |
| Account | `GET /borrowings`, `/reservations`, `/notifications`, `/fines` | Session-only account view | Tablet privacy and expired grant behavior |
| Renewal and reservation | `POST /borrowings/{id}/renew`, `POST/DELETE /reservations` | Account renewal/cancellation; detail reservation | Full policy conflict cases |
| Discovery and assistant | `POST /ai/recommend`, `/ai/search`, `/ai/feedback`, `/speech/transcribe` | Recommended/popular/new; assistant; reviewed English/Filipino voice commands, silence rejection, dictation, and device read-aloud | Real microphone and speech playback on Android tablet; recognition quality in the kiosk room |
| Staff login | `POST /auth/login`, `GET /auth/me`, `POST /auth/logout` | Browser login and memory-only token | Expiry and role checks in browser |
| Staff catalog | `GET/POST/PUT /books`, `GET/POST /books/{id}/copies`, QR endpoints | List, edit, copies, QR downloads | Covers, archiving, copy status, CSV import/export |
| Staff users | `GET/POST/PUT /users`, `GET /users/{id}/qr` | List, registration/edit, status, QR download | Photo upload and history detail |
| Staff operations | `GET /borrowings`, `/returns`, `/reservations`, `/fines`, `/audit-logs`, `/notifications/admin/email-deliveries` | Paginated tables; fine payment and reservation cancel | Rich filters and detail views |
| Reports and policies | `GET/POST /reports`, `GET/PUT /settings` | Preview/export and super-admin policy editing | Browser download and role checks |

The Flet client remains the fallback for workflows not yet listed as fully migrated. API authorization remains on the backend; kiosk QR grants do not authorize admin calls.
