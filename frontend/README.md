# LIBRAI Frontend

Flet-based kiosk and administrative interface for the LIBRAI smart library system. The frontend consumes the FastAPI backend and never implements authoritative borrowing, return, QR, fine, authentication, or AI rules locally.

## Install and run

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r frontend\requirements.txt
Copy-Item frontend\.env.example frontend\.env
python frontend\app.py
```

For browser mode, use `flet run --web frontend/app.py`.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `LIBRAI_API_BASE_URL` | `http://127.0.0.1:8000/api/v1` | FastAPI REST root |
| `LIBRAI_SCHOOL_NAME` | `Your School Name` | Institution name shown on the kiosk home page |
| `LIBRAI_LIBRARY_NAME` | `School Learning Resource Center` | Library name shown in kiosk/admin headers |
| `LIBRAI_API_TIMEOUT_SECONDS` | `10` | API timeout |
| `LIBRAI_USE_MOCK_FALLBACK` | `false` | Optional clearly marked demo data when an endpoint is unavailable |
| `LIBRAI_WINDOW_WIDTH` / `HEIGHT` | `1366` / `768` | Desktop kiosk window |
| `LIBRAI_FULLSCREEN` | `false` | Fullscreen kiosk mode |
| `LIBRAI_CAMERA_INDEX` | `0` | Local laptop/USB camera used for QR scanning |
| `LIBRAI_FRONTEND_UPLOAD_DIRECTORY` | `generated/frontend_uploads` | Temporary staging directory for browser-selected images |

Mock fallback is disabled by default so a backend outage cannot be mistaken for
real catalog data during production or capstone demonstrations.

## Interface design

The shared interface uses an institutional school-library system: restrained
navy and green accents, neutral surfaces, consistent spacing, touch-friendly
kiosk controls, and compact administrative controls. The admin sidebar becomes
a menu below 1050 px, while content is constrained to readable maximum widths.
Set the school and library names in `frontend/.env`; no page-specific edits are
needed for institutional branding.

## Structure

- `app.py`: application entry point and privacy timeout
- `core/`: configuration, route constants, state, theme, router
- `components/`: reusable cards, search, scanner, states, shells, and admin navigation
- `services/`: the only modules allowed to perform API requests
- `kiosk/`: catalog, assistant, account, reservation, borrow, and return flows
- `admin/`: login, dashboard, management, reports, audit, and settings views

## Available pages

Kiosk: home, search/filtering, book details, recommendations, popular books, new arrivals, AI assistant, account, reservations, five-step borrowing, and three-step return.

Kiosk catalog search loads live categories, supports sorting and pagination,
and distinguishes unavailable titles from catalog records with no physical
copies. Private QR sessions include loan history, due dates, reservations,
secure cancellation, persistent end-session access, and AI conversation state.
Eligible active loans can be renewed from My Account. Renewal limits, overdue
rules, and reservation conflicts are enforced by the backend and recorded in
an immutable renewal history.

Admin: login; operations-focused dashboard; catalog editing and archiving; physical-copy creation, status, and QR replacement; library-user registration, editing, account status, history, and QR replacement; borrowing, return, reservation, report, audit-log, and policy views.
The dashboard also highlights repeated searches with no results, Gemini
fallback rate, user helpfulness feedback, and daily renewal activity.

Administrators can upload JPEG, PNG, or WebP book covers and user profile
photos from the create/edit forms. Images are validated, resized, metadata is
removed, and files are normalized to WebP. Book covers are public catalog
media; user photos remain private and use short-lived signed display URLs.

Administrative QR tools can download a single PNG or generate an A4 PDF label
sheet for every copy of a title. Report previews use live API rows, and exports
use short-lived signed browser downloads. Admin headers cache and display the
backend connection state for quick operational diagnosis.

## Mock/demo behavior

When `LIBRAI_USE_MOCK_FALLBACK=true`, network/server failures fall back to small demo responses in service modules. Validation, authentication, and permission failures never fall back. Enter `demo-user-token` or `demo-book-token` in QR screens; these are sent to the backend first and are not treated as trusted QR data by the UI.

## Integration notes

- Laptop camera QR scanning uses OpenCV inside the local Python frontend. In Borrow Book, Return Book, or My Account, select **Start laptop camera**, hold the QR inside the frame, and wait for automatic verification. This accesses the camera attached to the computer running Flet; a remotely hosted Python process cannot access the browser user's camera. Change `LIBRAI_CAMERA_INDEX` to `1` or higher for an external camera. Manual entry remains available for development and camera failures.
- Voice commands are available from the home screen's **Voice Commands** tile and the AI Assistant's **Voice mode** selector. Use phrases such as "borrow a book", "return a book", "search Python books", "show my account", or "go home".
- Tablet microphone access requires browser permission and HTTPS when opening LIBRAI from a LAN address. Set `LIBRAI_API_BASE_URL` to the backend's LAN/HTTPS URL for the tablet build; `127.0.0.1` points back to the tablet itself and will not reach the computer.
- For tablet HTTPS testing, run the Flet web app on the computer and place an HTTPS reverse proxy in front of it. With Caddy installed, use `caddy reverse-proxy --from https://YOUR-LAN-IP:8443 --to 127.0.0.1:8550 --internal-certs`, then open `https://YOUR-LAN-IP:8443` on the tablet and trust the local certificate when prompted.
- Voice recordings are limited to 15 seconds, temporary local files are removed after upload, and transcription failures leave the typed request box available as a fallback.
- Abandoned speech files older than one hour are removed when the assistant page opens, preventing interrupted tablet sessions from accumulating temporary audio.
- Before production, set `LIBRAI_ENV=production`, a unique `SECRET_KEY`, explicit `CORS_ORIGINS`, database backups, SMTP settings, and an HTTPS certificate. Do not enable mock fallback in production.
- Dashboard metrics and seven-day activity use live backend data and explicit empty states.
- Report and QR-sheet downloads use short-lived signed backend URLs.
- Kiosk catalog search keeps up to five recent queries in browser-local storage.
- Borrow, return, and administrative save actions reject duplicate submissions while processing.

The complete frontend/backend coordination contract is in [`../docs/frontend_api_requirements.md`](../docs/frontend_api_requirements.md).
