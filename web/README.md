# LIBRAI React client

The new client has an Android tablet kiosk at `/` and a browser admin interface at `/admin`. Both use the existing FastAPI backend. The Flet client in `frontend/` remains available during migration.

## Local browser development

1. Start the backend from the repository root with `uvicorn backend.main:app --host 127.0.0.1 --port 8000` after applying the migrations.
2. In `web/`, run `npm ci`.
3. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` to the reachable `/api/v1` URL.
4. Run `npm run dev`. Open `http://127.0.0.1:5173/` for the kiosk or `http://127.0.0.1:5173/admin` for staff.

The browser origin must be listed in the backend's `CORS_ORIGINS`. Local Vite and Capacitor origins are in the development defaults. Production should explicitly list the deployed admin origin and `https://localhost` for the Android app.

## Android tablet build

The Android project is in `web/android`. It requires Android SDK API 36 and a full JDK 21 with `jlink`. The QR plugin requires Android API 26 or newer. The tablet must have network access to the backend and a camera.

In PowerShell, from `web/`:

```powershell
$env:VITE_API_BASE_URL = 'https://YOUR-API-HOST/api/v1'
npm ci
npm run android:sync
cd android
./gradlew.bat assembleDebug
```

The debug APK is written to `android/app/build/outputs/apk/debug/`. It is for development testing. A release APK/AAB needs a signing key and device testing. Do not commit the signing key. A production Android build is blocked by `scripts/check-android-env.mjs` unless the API URL is HTTPS and ends in `/api/v1`.

For a public server and admin site, follow [the hosting guide](../docs/public_hosting.md) before building an APK for distribution.

Use `npm run android:open` to open the native project in Android Studio if it is installed. After changing React code, run `npm run android:sync` again before building.

## Current verification boundary

`npm run build`, `npm run lint`, backend tests, Android debug compilation, and an isolated browser-to-API borrow/return smoke test passed locally. Browser screenshots show the kiosk home and admin login render. Camera scanning, device install, signing, simultaneous kiosks, and production storage still need checks on the actual deployment.
