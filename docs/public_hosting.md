# Public hosting for LIBRAI

The Android kiosk and browser admin need one public HTTPS API. This repository has a production candidate at [`render.production.yaml`](../render.production.yaml). It creates a paid FastAPI web service, paid PostgreSQL, a persistent disk for covers, photos and reports, and a static site for the React admin UI. It has **not been deployed**. The existing [`render.yaml`](../render.yaml) remains a free demo setup with local SQLite; do not use it for library records.

## Current public URLs (checked 2026-10-13)

- API: `https://librai-api-zjic.onrender.com` returned HTTP 200 from `/health` with `database: connected`. Its public OpenAPI route list matched the local 50-path snapshot. This does not establish which database or disk the live service uses.
- Kiosk: `https://librai-kiosk-zjic.onrender.com` was configured to serve the older Flet web app, including at `/admin`. The local [`render.yaml`](../render.yaml) now builds the React kiosk and admin client for that same service name, but the live service will stay on Flet until these changes are committed, pushed, and deployed.
- Preflight requests from `https://localhost` to the API's QR endpoint initially returned HTTP 400 without an `Access-Control-Allow-Origin` header. The API's **live** `CORS_ORIGINS` must include both `https://localhost` for Android and `https://librai-kiosk-zjic.onrender.com` for the browser site. The user reported updating and redeploying this setting; recheck it after the React site deploys.
- A debug Android APK has been compiled with `VITE_API_BASE_URL=https://librai-api-zjic.onrender.com/api/v1`. It is a **pilot build only** until CORS, real-camera behavior, and data persistence are verified.

An earlier live recheck accepted `https://librai-kiosk.onrender.com` but rejected the Android origin. After the API redeployed, an OPTIONS request from `https://localhost` returned HTTP 200 with `Access-Control-Allow-Origin: https://localhost` at 09:21 UTC on 2026-10-13. A subsequent check from this workspace failed DNS resolution, so the current live response should be checked again before the tablet pilot. The pasted deploy log confirms that this service used SQLite and ran the initial migrations on that deploy. Do not use this database for real library records: a Render free web service's local SQLite database is lost on restart or redeploy.

## Show the React design at the existing kiosk URL

The free demo [`render.yaml`](../render.yaml) now defines `librai-kiosk` as a Node web service. It runs `cd web && npm ci && npm run build`, then `node web/server.mjs`. The server serves `/` as the kiosk and `/admin` as the admin client. `VITE_API_BASE_URL` is set to `https://librai-api-zjic.onrender.com/api/v1` during the build; this is a public browser value, not a secret.

1. Commit and push the React files, `web/server.mjs`, and `render.yaml` to the branch connected to Render. Local edits and local APK builds do not update the website.
2. In Render, open the existing **librai-kiosk** service. If it is managed by a Blueprint, sync that Blueprint and check that the runtime changes from Python to Node. Otherwise, open **Settings > Build > Source > Edit**, choose Node, and set the build and start commands above. Set `VITE_API_BASE_URL` to the API URL in **Environment** and deploy. Render supports changing an existing native service's runtime; confirm the actual service configuration before deploying.
3. After a successful deploy, open `https://librai-kiosk-zjic.onrender.com/` in a private browser window. It should show “What would you like to do today?” and the Borrow/Return cards. Open `/admin` and confirm the React staff login appears. If the old Flet page remains, inspect which branch, commit, runtime, build command, and start command the live service actually used.
4. Test a browser API request from the new site. If the browser reports CORS, confirm the API's live `CORS_ORIGINS` contains the exact kiosk origin and redeploy the API.

Render references: [changing native runtimes](https://render.com/docs/native-runtimes#changing-a-services-runtime), [Blueprint service fields](https://render.com/docs/blueprint-spec), and [deploy settings](https://render.com/docs/deploys).

## Before creating services

1. Review Render's current charges in its dashboard. The proposed web service, database and disk incur charges when created. The free web service loses uploaded files on restart, and free PostgreSQL expires after 30 days, so it cannot hold school records reliably.
2. Connect the existing GitHub repository (`midddddiana24/LIBRAI`) to Render. The current local implementation files must be committed and pushed before Render can build them. In the Render dashboard, choose **New > Blueprint**, select the repository, and choose `render.production.yaml` as the Blueprint file. Review the proposed paid resources before syncing. Use a different name if an existing `librai-api-prod` or `librai-admin-prod` service is already managed elsewhere.
3. For the API's `CORS_ORIGINS`, initially enter `https://localhost`. After the static site is created, update it to `https://localhost,https://<actual-admin-host>` (origins have no path or trailing slash). Capacitor uses `https://localhost` on Android; the browser admin uses its real public origin.
4. The Blueprint may ask for `VITE_API_BASE_URL` before it has assigned the API hostname. Enter the expected `https://librai-api-prod.onrender.com/api/v1` for the initial build, then inspect the API service's actual URL. If Render assigned a different hostname, edit this variable and redeploy the static site. This value is compiled into the JavaScript bundle.
5. Provide at least one AI provider key to the API (`GEMINI_API_KEY` or `TOKENROUTER_API_KEY`) because the current production settings require one. Put it only in Render's environment settings. The API also needs the generated `SECRET_KEY`; keep its value stable across deploys or existing tokens will expire.

The Blueprint connects the API to Render PostgreSQL over its internal connection string. The backend converts Render's `postgresql://` URL to the installed `psycopg` driver. Alembic runs before each deploy. The disk is mounted over `generated/`, which is where this backend currently stores public covers, private user photos, and generated reports. PostgreSQL is not on that disk. Keep the API in a single instance while this local disk is used.

The hosted Uvicorn process disables raw access logs, and the application logs route templates, so short-lived grants in URLs are not written to access logs. Review Render's request-log settings separately if enabled outside this process.

## First deployment checks

1. Open `https://<actual-api-host>/health`. It must return `status: healthy` and `database: connected`.
2. Open `https://<actual-admin-host>/admin`. Open the browser developer console and check that requests go to `https://<actual-api-host>/api/v1`, without CORS or mixed-content errors. If either hostname differs from what you entered, update the Render environment variable and redeploy the affected service.
3. Add `LIBRAI_ADMIN_USERNAME`, `LIBRAI_ADMIN_EMAIL`, and `LIBRAI_ADMIN_PASSWORD` (at least 12 characters) as temporary secret environment values on the API service. In that service's Render shell, run `python -m backend.scripts.create_admin`. The script creates only one staff account, refuses to overwrite an existing username, and does not print the password. Remove the temporary password variable from Render afterward. **Do not run `backend.scripts.seed` in production**; it creates demo records and prints QR tokens.
4. Log into `/admin`, add one test book and copy, generate its QR, then test a real borrow and return on an Android tablet. Verify the admin page sees each transaction. Test Voice command, Dictate question, and Read answer aloud on the tablet after granting microphone access. Restart the API service and confirm the book, transaction, cover and reports remain available.
5. Configure and exercise PostgreSQL backup/restore and disk-file recovery before using real student records. A database backup alone does not include cover, photo or report files. Record who owns these backups and the recovery procedure.

## Build the Android app against the live API

From `web/`, set `VITE_API_BASE_URL=https://<actual-api-host>/api/v1` and run `npm run android:sync`, then build the debug APK from `web/android` with `./gradlew.bat assembleDebug`. Install it on the target tablet and test camera scanning over both school Wi-Fi and another internet connection. For routine distribution, create a signed release build and keep the signing key outside the repository. The current debug APK includes the known Render API URL, but it is still a pilot build until physical camera and persistence checks pass.

## Current limits

The React deployment change is prepared locally, not verified on the live Render service. This workspace has no connected Render account, so its current runtime, branch, deployment status, data persistence, and backups cannot be confirmed here. The feature matrix in [`frontend_feature_matrix.md`](frontend_feature_matrix.md) lists remaining UI work. Persistent disks also mean the API cannot scale to multiple Render instances without moving media to shared object storage.

Render reference: [Blueprint fields](https://render.com/docs/blueprint-spec), [persistent disks](https://render.com/docs/disks), [free tier limits](https://render.com/docs/free), and [compute plans](https://render.com/docs/compute-plans).
