# System and APK verification - 17 October 2026

## Decision

The verified backend and browser workflows support a controlled library pilot. This is not a claim that every feature works on the intended Android tablet: no USB device was detected, and the user chose manual installation. The APK is signed for internal debug testing, not a production release build.

The live website/API were checked at the published chatbot revision `7cfa077`. A tablet home-layout regression was found during this audit and corrected locally. The replacement APK is **1.6.1 / code 9**. The local layout correction has not been pushed or deployed in this audit.

## Current results

| Check | Evidence | Boundary |
| --- | --- | --- |
| Backend suite | `75 passed, 1 warning in 136.55s` | Temporary SQLite only; external email/AI/storage transports mocked in unit tests |
| Fresh schema migrations | `alembic upgrade head` reached `c2d9e4a7b615 (head)` | Fresh temporary SQLite, not a new provisioned PostgreSQL instance |
| Python dependencies | `No broken requirements found` | Local environment; not a clean reinstall or Python vulnerability scan |
| Frontend build and lint | Passed | Current local source |
| Voice command/audio unit checks | 6 passed | Includes silence rejection and English/Filipino/mixed command routing; not actual microphone accuracy |
| ID-field extraction checks | 10 passed | Parser fixtures; OCR separately checked below |
| Real OCR and registration browser flow | Passed for both synthetic card types, review, pending request, real local admin login, approval, QR enablement and email outbox | Temporary API/database; no actual notification email sent |
| Real local API/chat browser flow | Passed: verified-member requests, history, topic filters, policy settings, no-match, book detail/back, error/retry, late reply after session end | Temporary API/database |
| Borrow browser checks | Passed at 320x740, 414x896, 600x960, 768x1024 and 1024x768 | API mocked; actual borrow/return backend HTTP behavior covered by backend tests |
| Voice browser check | Passed: review before navigation, dictation and read-aloud control | Synthetic recordings and simulated speech output |
| Live API | HTTP 200, healthy, database connected, Gemini configured | Does not prove every external dependency is available |
| Live CORS | Website origin and `https://localhost` accepted | Tested preflight requests |
| Live authentication boundary | Dashboard, users and email-configuration routes returned 401 without a staff token | Live staff credentials were not requested or used |
| Live catalog/media | 6 titles returned; a catalog cover downloaded as image/webp, HTTP 200 | Cover read only; no upload or restart persistence experiment |
| Live chat | Registration guidance, unknown-topic no-match, Gemini Python ranking, history and clearing passed with real HTTP 200 responses | Created normal AI/search logs; no member/circulation mutation |
| npm production audit | 0 known vulnerabilities reported | Registry advisory check for npm production dependencies, not a full security audit |
| Tablet/admin layout sweep | Passed at 320x740, 375x812, 414x896, 600x960, 768x1024, 960x600, 1024x768 and 1440x1000; reduced-motion check passed | Browser viewports and mocked admin data, not physical Android |

## Issue found and correction

The added speech-language selector made the home page exceed the viewport at 600x960, 768x1024 and 960x600. The selector still exposes an accessible **Speech language** label. Its redundant visible label is now clipped only within the home voice dock, and portrait/short-landscape spacing was reduced slightly. The large action buttons, language selection and voice-command review remain available. Existing layout assertions were retained.

One intermediate layout run timed out waiting for an admin Menu click while the Gradle build ran concurrently. This is recorded separately from the reproducible overflow; its cause was not established. The final unchanged-script rerun after the build finished passed all eight viewports, menu/sign-in/sign-out checks and reduced-motion checks.

## Replacement APK

- File: `generated/releases/LIBRAI-1.6.1-debug.apk`.
- Package: `ai.librai.kiosk`; version **1.6.1**, code **9**.
- Gradle: **BUILD SUCCESSFUL in 2m 32s**.
- Minimum Android API 26 (Android 8); target API 36.
- `apksigner verify`: passed; certificate matches the preceding local APK.
- Size: 48,043,320 bytes.
- SHA-256: `826d3fcacceb33e805e2a8d823f0f2dcbfba4295483c3b9f1cf7f62b941d9920`.
- ZIP inspection confirmed chat, the current HTTPS API and the layout correction. Gmail OAuth/client-secret files were absent.
- `application-debuggable` is enabled. Keep this artifact for internal testing; a production distribution build needs release signing and debugging disabled.

## What still needs acceptance

1. Install 1.6.1 as an update on the actual intended tablet. No device was attached during these checks.
2. Verify real English, Filipino and mixed-speech transcription in quiet and normal library noise; confirm audible speech and Stop reading.
3. Verify real camera decoding, permissions and a designated test borrow/return on that tablet.
4. Gmail transport/queue behavior passed isolated tests, and an earlier test was confirmed by the user. Inbox delivery and current deployed Gmail OAuth authorization were not retested during this audit. No email was sent.
5. Publish the local layout correction when desired; the existing live deployment still has the layout regression at the affected viewport sizes.

No load test, exhaustive security review, Google Play release, physical Android acceptance or live admin sign-in was performed. Existing warnings: Starlette/httpx deprecation, local pip ignored-distribution metadata for `~let-desktop`, and Gradle flatDir warnings. These did not prevent the successful builds/tests above.
