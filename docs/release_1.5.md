# LIBRAI 1.5 delivery and tablet acceptance

Current version: **1.5.1**, Android version code **7**, package `ai.librai.kiosk`.
API: `https://librai-api-free-pg.onrender.com/api/v1`.
Source branch: `online-admin-postgres`.

## Publication and physical-device follow-up

- Release source commit `12fa2a2` was pushed to `online-admin-postgres` and verified against the remote branch.
- The public website subsequently served the new Borrow layout and the exact new logo. Verified entry asset: `index-DnjeATiA.js`.
- The public API returned healthy/database connected. A bounded check using invalid recommendation payloads returned thirty HTTP 422 responses, then HTTP 429 with `Retry-After: 60`, proving the new recommendation request limit was deployed. No model call or catalog/circulation write was made by that probe.
- On the connected Infinix X6531, the user dictated **Romance**, the app displayed **Heard: Romance** and an AI answer, and the user confirmed the answer was audible through **Read answer aloud**.
- The default Android scanner opened but did not decode the physical test QR. A diagnostic using the installed plugin's ML Kit engine decoded the **exact test value** successfully on the same physical device. Version 1.5.1/code 7 now selects ML Kit explicitly and has been installed successfully; the user subsequently confirmed that the normal Borrow-screen camera scans the same QR and returns the expected ID validation error.
- [Camera test QR](design_previews/camera-test-qr.png) contains `LIBRAI_CAMERA_CHECK_NOT_A_REAL_LIBRARY_ID`. It is deliberately not a real ID or book grant; successful scanning should lead to a server validation error, never a borrowing.

## Included

- Three-step Borrow screen with the illustrated ID scanner and explicit borrowing confirmation.
- Open-book/L logo in kiosk, staff screens, web startup/favicon, and Android adaptive launcher/splash.
- Gemini fallback after a failed TokenRouter request, speech/recommendation request limits, and speech calls moved off the async event loop.
- Tests isolated from real AI keys and cloud media.

## Clean backend verification

The dependencies in `requirements.txt` installed in a new temporary environment with `uv`. The complete backend suite returned `37 passed, 186 warnings in 67.96s`. The warnings are deprecations in the pinned FastAPI/Starlette stack on Python 3.14, not test failures.

## APK

Latest build completed: `BUILD SUCCESSFUL in 26s`. Commands: `npm run android:sync`, then `gradlew.bat assembleDebug`.

- Artifact: `web/android/app/build/outputs/apk/debug/app-debug.apk` (39,866,166 bytes).
- SHA-256: `7b17590c1628114da75c207c801b29227a1eab9e19e9aa6fb50451eed33cf641`.
- `aapt dump badging`: `ai.librai.kiosk`, version 1.5.1/code 7, minimum Android API 26, target API 36, camera and microphone permissions declared.
- `apksigner verify`: passed, Android Debug signing certificate. This is an internal testing APK, not a Play Store release build.
- APK ZIP checks confirmed the current HTTPS API, `borrow-stages`, and the exact new transparent logo asset.

## Physical acceptance procedure

An Infinix X6531 was subsequently connected by USB. `adb install -r` returned **Success**, and the installed package reports **1.5 / code 6**. LIBRAI launched on its 720x1600 screen. At the first test, both Wi-Fi and mobile data were off and the app correctly showed the connection-lost message; after connectivity was restored, real microphone transcription, audible speech, and the corrected QR scanner passed the user-confirmed checks recorded above. No device serial number is stored here. These checks must not be marked complete based on browser simulations or a successful build.

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
