# LIBRAI React client

The new client has an Android tablet kiosk at `/` and a browser admin interface at `/admin`. Both use the existing FastAPI backend. The Flet client in `frontend/` remains available during migration.

The kiosk home gives Borrow and Return the largest touch targets, with search and account close by. Each transaction shows one QR/review step at a time. A private session warns before its 90-second inactivity timeout, and the home screen disables server actions while offline. The admin interface is a separate route with the existing staff login.

On the kiosk home, tap **Voice command**, wait for **Listening**, speak, then tap **Stop recording**. Review the words shown, correct them if needed, and tap **Run command**. Commands such as “borrow a book”, “return a book”, “manghiram ng libro”, “ibalik ang libro”, and “find history books” open the matching flow. The microphone stops automatically after 12 seconds; silent recordings are rejected before upload. **Hear instructions** reads a short prompt aloud. In **Ask LIBRAI**, tap **Dictate question** to fill the editable question field, then tap **Ask**. Tap **Read answer aloud** to hear the answer using the device's installed speech voice. Voice commands only navigate or fill text; book transactions still require scanning and confirmation. Audio is sent to the backend `/speech/transcribe` endpoint, which requires `GEMINI_API_KEY` on the server. A microphone and permission are required on the tablet, and browser recording requires HTTPS or localhost.

## Local browser development

1. Start the backend from the repository root with `uvicorn backend.main:app --host 127.0.0.1 --port 8000` after applying the migrations.
2. In `web/`, run `npm ci`.
3. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` to the reachable `/api/v1` URL.
4. Run `npm run dev`. Open `http://127.0.0.1:5173/` for the kiosk or `http://127.0.0.1:5173/admin` for staff.

The browser origin must be listed in the backend's `CORS_ORIGINS`. Local Vite and Capacitor origins are in the development defaults. Production should explicitly list the deployed admin origin and `https://localhost` for the Android app.

## Android tablet build

The Android project is in `web/android`. It requires Android SDK API 36 and a full JDK 21 with `jlink`. The QR plugin requires Android API 26 or newer. The tablet must have network access to the backend, a camera, and a microphone. Grant microphone access when the app requests it.

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

The production web build, lint, voice command and silence tests, a mocked browser voice flow, and Android debug compilation pass. A generated speech sample also passed through Chrome's actual recorder and the live transcription API. Camera scanning, speech recognition quality and read-aloud on the physical tablet, device install, signing, simultaneous kiosks, and production storage still need checks. Use `npm run test:voice` for command and silence tests.
