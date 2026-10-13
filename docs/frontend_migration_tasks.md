# LIBRAI frontend migration tasks

## Target and working assumptions

Build a downloadable **Android tablet kiosk app** and a **browser-based admin site** in TypeScript and React. Both call the existing Python FastAPI service; the server and its database remain the source of truth. The kiosk needs a network connection for transactions. Package the kiosk with Capacitor after its browser version works. The user confirmed Android tablet as the first kiosk target.

This is the release checklist. Keep the current Flet client usable until the replacement passes the release checks.

## Current implementation status

The first React/TypeScript client and Capacitor Android project are in `web/`. The API snapshot is in `docs/openapi.json`, and `docs/frontend_feature_matrix.md` lists migrated and remaining workflows. The backend suite passes 23 tests. TypeScript build and lint pass. Android debug compilation passed, and a browser-to-API borrow/return smoke test passed with isolated local data. Physical-device validation remains open. The public hosting candidate and deployment instructions are in `render.production.yaml` and `docs/public_hosting.md`; no production server or database was changed.

## 1. Confirm the deployment target

- [ ] Record Android version, tablet screen size, camera or USB scanner model, and number of kiosks.
- [ ] Decide whether kiosks use a school LAN or the internet; choose the backend HTTPS hostname and who maintains it.
- [ ] Decide whether an offline catalog is needed. Borrowing, returns, and reservations must remain online unless a separate synchronization design is approved.
- [ ] List staff roles and the admin devices/browsers to support.

**Check:** A one-page deployment specification names the kiosk hardware, server address, expected connection, and supported admin browsers.

## 2. Record current behavior and API contracts

- [ ] Inventory every kiosk and admin route in `frontend/core/routes.py`, including search, account, QR borrow/return, reservations, AI, catalog management, users, fines, reports, and settings.
- [ ] Generate the current OpenAPI schema from `/openapi.json` and compare it with `docs/api_contract.md`; treat running backend behavior as authoritative when they differ.
- [ ] Map each existing `frontend/services/` call to its FastAPI route, required authentication, request body, response, and error states.
- [ ] Capture baseline backend tests and a manual walkthrough of the current Flet flows.

**Check:** A feature/API matrix shows how each existing screen will be replaced; known contract gaps are logged before UI work.

## 3. Prepare the shared backend for multiple devices

- [ ] Deploy one reachable FastAPI instance with HTTPS and a stable hostname. Configure explicit browser origins in CORS.
- [ ] Move the hosted database from the local SQLite fallback to persistent PostgreSQL; run Alembic migrations and verify a backup/restore.
- [ ] Put uploaded covers, private user photos, generated reports, and QR downloads on storage that survives server restarts, or document and implement a suitable persistent-volume setup.
- [ ] Set production secrets, allowed origins, health checks, logging, and the email worker configuration as needed.
- [ ] Verify two kiosks cannot borrow the same copy concurrently and that clients receive a clear conflict response.

**Check:** Two separate computers can reach `/health` and `/api/v1`; data and uploaded media survive a server restart; concurrent-borrow test passes.

## 4. Create the TypeScript frontend foundation

- [ ] Create separate `kiosk` and `admin` React applications (or routes with separate builds) and a shared typed API client/design package.
- [ ] Generate or maintain TypeScript API types from the verified OpenAPI contract.
- [ ] Implement environment-based API URL configuration, request timeouts, consistent error messages, and an explicit disconnected state.
- [ ] Keep credentials, AI provider keys, and library rules on the backend. Keep admin authentication separate from kiosk QR grants.
- [ ] Add basic accessibility and touch targets appropriate to the kiosk screen.

**Check:** Both apps load, call `/health`, and show a useful message when the server is unavailable.

## 5. Deliver one complete kiosk transaction first

- [ ] Build catalog search and book details using live `GET /search/books` and `GET /books/{id}` results.
- [ ] Scan QR codes with the kiosk's own camera or USB scanner; send opaque values to `POST /qr/verify-user` and `POST /qr/verify-book`.
- [ ] Keep the returned verification grants only for the active kiosk session. Clear them after completion, timeout, or explicit end-session.
- [ ] Implement borrow confirmation with `POST /borrowings`; show the server's due date and handle 401, 409, 429, and network errors.
- [ ] Prevent duplicate submission while the request is in flight.

**Check:** On the target kiosk hardware, a real scan and borrow updates the shared database and appears in the current admin view. A second kiosk sees the new availability. Invalid/expired QR and competing borrow attempts fail cleanly.

## 6. Finish kiosk feature parity

- [ ] Add return (`GET /borrowings/active/by-copy/{copy_id}` and `POST /returns`) and verify its receipt.
- [ ] Add account, loan history, renewals, reservations, notifications, fines, recommendations, and AI search as supported by the verified API.
- [ ] Rebuild privacy timeout, end-session behavior, loading/empty states, and recovery after a dropped connection.
- [ ] Validate camera and microphone behavior on the actual kiosk hardware; offer the existing manual QR fallback only where permitted for operations.

**Check:** The feature/API matrix from step 2 is complete, and user data disappears when a kiosk session ends or times out.

## 7. Build the admin web interface

- [ ] Implement login, `/auth/me`, logout, role-aware navigation, and session-expiry handling.
- [ ] Migrate dashboard, catalog/copies/QR labels, users, borrowing and return history, reservations, fines, reports, audit logs, and settings.
- [ ] Preserve backend permission checks; hiding an admin control in React is not authorization.
- [ ] Verify an admin edit made in the browser appears on a kiosk after refresh or refetch.

**Check:** A staff member can complete each existing admin workflow from a supported browser, and a kiosk QR grant cannot access admin endpoints.

## 8. Package and deploy

- [ ] Package the tested kiosk React build with Capacitor for Android, configure orientation, camera permission, server URL, and device kiosk/lock-task policy.
- [ ] Produce a signed APK or AAB for the intended distribution method. Keep the signing key outside this repository.
- [ ] Deploy the admin site over HTTPS with its production API URL and exact CORS origin.
- [ ] Write install, update, backup, and recovery instructions for school staff.

**Check:** Install on a clean target Android tablet, scan with its real camera/scanner, complete a transaction, and view it from the admin site on another device.

## 9. Release gate and cutover

- [ ] Run backend tests, frontend checks, and end-to-end checks for borrow, return, reservations, admin edits, login expiry, QR expiry, concurrent requests, and outages.
- [ ] Test with the expected number of simultaneous kiosks and confirm persistence after a backend restart.
- [ ] Have library staff perform a supervised pilot and record defects.
- [ ] Keep the Flet version available for rollback until the pilot passes; then switch kiosks to the packaged app.

**Check:** Staff sign off on the pilot, the installer and admin URL are documented, and rollback instructions have been exercised.

## Suggested implementation order

1. Steps 1–3: confirm the hardware and make the shared backend durable.
2. Steps 4–5: build and prove the first complete kiosk borrow flow.
3. Steps 6–7: reach kiosk and admin feature parity.
4. Steps 8–9: package, pilot, and switch over.

Do not treat a browser demo as proof that the camera, scanner, installer, or physical kiosk works; those need checks on the actual devices.
