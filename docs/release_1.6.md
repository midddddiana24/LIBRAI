# LIBRAI 1.6 Android update

**Newer release available:** use [LIBRAI 1.7.0](release_1.7.0.md) (version 1.7.0/code 11) for conversational chat and the book-opening startup. The 1.6.0 details below are the earlier build record.

Version **1.6.0**, Android version code **8**, package `ai.librai.kiosk`.
API: `https://librai-api-free-pg.onrender.com/api/v1`.
Includes the deployed library chatbot and AI improvements from commit `7cfa077`, registration with staff approval, ID-assisted form entry, and Gmail notification administration.

## Build verification - 17 October 2026

- `npm run android:sync`: passed using the live HTTPS API.
- `gradlew.bat assembleDebug`: **BUILD SUCCESSFUL in 1m 14s**.
- `aapt dump badging`: version 1.6.0/code 8; minimum Android API 26 (Android 8), target API 36; camera and recording permissions present.
- `apksigner verify`: passed. The signer certificate matches the previous local 1.5.1 APK.
- ZIP checks: new chatbot, configured live API, local OCR model and current logo are present; Gmail credential files are absent.
- File size: 48,043,252 bytes.
- SHA-256: `94c8c9125c0c61c8dd1c5db1ea2ec899b7f77c093696ddcd646897b7a1950f63`.
- Repeated `adb devices -l` checks found no attached device. Installation and physical acceptance remain pending.

## Install the update

1. Copy `generated/releases/LIBRAI-1.6.0-debug.apk` to your Android tablet, or use `web/android/app/build/outputs/apk/debug/app-debug.apk`.
2. Open the APK, allow installation from the file manager if Android asks, and choose **Update**. Keep the existing app installed. Stop if Android reports a signing mismatch; do not uninstall as a workaround.
3. In Android Settings > Apps > LIBRAI Kiosk > App details, verify **1.6.0**.
4. Open the app with internet connected. Confirm **Library online** and the new chat in **Ask LIBRAI**.

If USB debugging is connected and authorized, from the project root:

```powershell
adb devices -l
adb install -r generated/releases/LIBRAI-1.6.0-debug.apk
adb shell am start -n ai.librai.kiosk/.MainActivity
```

## Physical acceptance

No Android device was detected when this build started. Build success and browser tests do not prove physical hardware behavior.

- Ask **How do I register?** in chat, then a book topic. Confirm chat history and book cards. End session and verify history is gone.
- Dictate an English question, a Filipino question and mixed speech in a quiet room, then typical library noise. Review what was heard before tapping Send or Run command. Record mismatches rather than assuming recognition succeeded.
- Tap **Read answer aloud** and confirm clear, audible sound; test Stop reading.
- Borrow a book > Open camera: scan `docs/design_previews/camera-test-qr.png`. It is a fake ID. Expected result: ID validation error after decoding, never a borrowing. Allow camera permission when asked.
- Use designated library test records for an actual borrow/return only when the tablet is available and a staff member can verify the outcome. No real circulation was performed for this build.
- This APK is a debug build for internal testing. It does not update an installed app automatically or publish to Google Play.
