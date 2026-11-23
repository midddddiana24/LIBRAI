# LIBRAI verification - 2026-11-24

Verdict: the implemented library workflows pass the checks below, but the system is not fully verified. Live conversational AI failed, Gmail inbox delivery was not retested, and no physical Android device was connected.

## Confirmed

- Public kiosk exposes the compact Options menu. PostgreSQL API health reports healthy/database connected and exposes the overdue filter.
- Live catalog query `Find beginner Python books` returned one matching title, response_type=catalog, fallback_used=false.
- Live policy query returned the configured three active loans / seven day loan period, response_type=policy, fallback_used=false.
- Build, lint, Capacitor sync and Android Gradle assembleDebug passed.
- Six voice/audio logic tests and ten ID parsing tests passed.
- Shared UX passed at four sizes; admin filters, dialogs, cancellation and pagination passed with mocked requests.
- Member component checks passed on retry, including 53-row history, renewability, pagination, inline validation, optional email and Filipino labels.
- Real isolated API/browser chat passed on retry: session history, personalization, follow-ups, policy settings, honest no-match, retry and session clearing.
- Real isolated registration/OCR passed through pending registration, staff approval, QR and email queue. No actual email was sent.
- Startup passed at six sizes, offline retry and reduced motion. Simulated voice navigation, dictation and speech controls passed.

## Failure and verification limits

`Explain databases in English` returned response_type=conversation, fallback_used=true: "Conversational AI is unavailable right now. Please retry." The strict online chat test correctly failed. This does not identify the provider-side cause; inspect the production provider configuration and sanitized Render logs. Catalog and policy success must not be described as general AI success.

Two initially timed-out browser checks passed on retry. Voice smoke first targeted an inactive preview port, then passed against the active preview. Full backend-suite reruns were interrupted by tool-session resets; no fresh complete-suite pass is claimed. Earlier targeted overdue/renewal tests passed (2 tests). No real production account login, registration, circulation write or Gmail inbox receipt was tested in this audit.

## Android

The previous local 1.9.0 APK did not contain the compact Options menu and did not match the current web bundle. Rebuilt local artifact: `generated/releases/LIBRAI-1.9.1-debug.apk`, application ai.librai.kiosk, version 1.9.1/code 14, 49,594,898 bytes.

SHA-256: `ad83c9e959eb01c6c4d3e9eb5bb0dbef647f9cec80241ea3be787e1a781ca978`.

APK signature verification passed, with the existing debug certificate fingerprint `f1069bb7a5ea6d0b31dbea50a8f0f95a15a1d52b2ace3ce655899e2b9fa0e427`. All 18 packaged web HTML/JS/CSS files match the rebuilt dist bytes; menu, version and production API URL markers are present.

No adb device was attached. The installed tablet version cannot be confirmed remotely. Install this file manually and check Options > About for 1.9.1/build 14. Real camera decoding, microphone transcription accuracy, audible speech and keyboard usability remain manual. This internal debug build is not production release signing. The APK has not been uploaded to a new GitHub release in this audit.
