# LIBRAI 1.5 delivery and tablet acceptance

Version: **1.5**, Android version code **6**, package `ai.librai.kiosk`.
API: `https://librai-api-free-pg.onrender.com/api/v1`.
Source branch: `online-admin-postgres`.

## Included

- Three-step Borrow screen with the illustrated ID scanner and explicit borrowing confirmation.
- Open-book/L logo in kiosk, staff screens, web startup/favicon, and Android adaptive launcher/splash.
- Gemini fallback after a failed TokenRouter request, speech/recommendation request limits, and speech calls moved off the async event loop.
- Tests isolated from real AI keys and cloud media.

## Clean backend verification

The dependencies in `requirements.txt` installed in a new temporary environment with `uv`. The complete backend suite returned `37 passed, 186 warnings in 67.96s`. The warnings are deprecations in the pinned FastAPI/Starlette stack on Python 3.14, not test failures.

## APK

Build completed: `BUILD SUCCESSFUL in 1m 58s`. Commands: `npm run android:sync`, then `gradlew.bat assembleDebug`.

- Artifact: `web/android/app/build/outputs/apk/debug/app-debug.apk` (39,866,054 bytes).
- SHA-256: `859a28c43fbed487d22a425bc2063ff4594fdc7b48ab950f9c77b1c15d588913`.
- `aapt dump badging`: `ai.librai.kiosk`, version 1.5/code 6, minimum Android API 26, target API 36, camera and microphone permissions declared.
- `apksigner verify`: passed, Android Debug signing certificate. This is an internal testing APK, not a Play Store release build.
- APK ZIP checks confirmed the current HTTPS API, `borrow-stages`, and the exact new transparent logo asset.

## Physical tablet checks — pending

An Infinix X6531 was subsequently connected by USB. `adb install -r` returned **Success**, and the installed package reports **1.5 / code 6**. LIBRAI launched on its 720x1600 screen. At the first test, both Wi-Fi and mobile data were off and the app correctly showed the connection-lost message; live audio/QR checks are pending an internet connection. No device serial number is stored here. These checks must not be marked complete based on browser simulations or a successful build.

1. Connect by USB, enable USB debugging, and approve the computer. `adb devices -l` must show the tablet as `device`, not `unauthorized`.
2. Install the updated APK with `adb install -r web/android/app/build/outputs/apk/debug/app-debug.apk` from the project root. If Android reports a signature mismatch, stop; do not uninstall and erase app data as a workaround.
3. Launch LIBRAI. Confirm the new logo, the new Borrow screen, and **Library online**.
4. Tap **Hear instructions**. A person must confirm the sound is audible and understandable. Check tablet volume and installed TTS voice settings if silent.
5. Tap **Voice command**, grant microphone access, say **borrow a book**, stop recording, and inspect the editable transcript before running it. Repeat with **manghiram ng libro**. Record what was said and what appeared if they differ.
6. Open **Ask LIBRAI**, dictate an English and a Filipino question, submit it, then use **Read answer aloud**. A person must confirm actual playback.
7. Open Borrow, tap **Open camera**, grant camera access, and scan a designated test library ID and book copy. Verify the displayed details. Borrow only after confirmation, inspect the server receipt/due date, and return the same designated test copy.
8. End the session. Confirm personal information disappears. Repeat a connection check on school Wi-Fi and another internet connection.

## Website and API deployment

Push source only to `online-admin-postgres`. Render deployment is separate from GitHub publication. Verify the website loads `librai-symbol-v2.png` and a kiosk bundle containing `borrow-stages` before claiming the new interface is live.

Use the existing Neon-backed API service. Keep its database/object-storage values and `SECRET_KEY` stable. Do not recreate the old SQLite service from the default `render.yaml`. If auto-deploy is disabled, use **Manual Deploy → Deploy latest commit** on the intended API and kiosk services.
