# System and APK verification — 22 November 2026

## Verdict

**Core automated workflows pass, but this is not a complete functional acceptance pass.** Live conversational AI was intermittently unavailable, the local Gmail OAuth refresh token was rejected, and no Android tablet was connected for physical acceptance. Do not treat the October release report as current proof of uninterrupted AI or email delivery.

Checkout: `online-admin-postgres`, application/report HEAD `a57054b` at the start of testing. The tracked workspace was clean. Tests used isolated SQLite fixtures, synthetic members/cards and disabled outbound delivery. No application source, credentials, deployment settings, live members or circulation records were changed. Normal live AI/search checks created ordinary interaction analytics.

## Fresh results

| Area | Result | Evidence and boundary |
| --- | --- | --- |
| Backend | PASS | `pytest backend/tests -q -p no:cacheprovider --basetemp <fresh ignored audit folder>`: **80 passed**, one existing Starlette/httpx deprecation warning, 164.79 seconds. Covers authentication, QR grants, borrowing/returns, renewals, reservations, fines, registration, admin, AI and notification logic. |
| Web compilation/lint | PASS | `npm run build`, `npm run lint`: exit 0. |
| Voice commands/audio checks | PASS, simulated | Six unit tests passed; browser voice smoke passed for command navigation, dictation and read-aloud controls. No physical microphone/speaker measurement. |
| ID field parsing | PASS | Ten unit tests passed. |
| Registration/admin integration | PASS, isolated | Two synthetic card types underwent actual local OCR, editable review, pending registration, real isolated staff sign-in, approval, QR enabling and email queue creation. No email was sent. Real private card photos were not used in this audit. |
| Chat integration | PASS, isolated | Real temporary API/browser checks passed for member grants, history payloads, exclusion of account results from provider history, catalog follow-ups, policies, no-match, error/retry and clearing late replies after session end. Provider responses are disabled/simulated in these checks. |
| Startup | PASS | Six sizes from 320 × 740 to 960 × 600: book asset, connecting/ready/Home, offline/retry and reduced motion. |
| Responsive/admin navigation | PASS | Eight sizes from 320 × 740 to 1440 × 1000, including portrait and landscape tablets. |
| Borrow interface | PASS, mocked API | Five sizes: invalid QR, grants, unavailable copy, explicit confirmation, receipt and session clearing. Actual HTTP borrow/return behavior is separately covered by the backend suite. |
| Live website/API | PASS after initial delay | Website HTTP 200; initial API checks timed out, subsequent `/health` returned HTTP 200 with `healthy` and `database: connected` in 0.55 seconds. Public catalog returned six titles. CORS preflights accepted the website and `https://localhost`. |
| Live admin access control | PASS, limited | Unauthenticated dashboard returned HTTP 401. Valid production staff sign-in was not attempted. |
| Live AI | PARTIAL / intermittent failure | English explanation and follow-up initially returned real answers (`fallback_used=false`). A Filipino comparison repeatedly returned the unavailable fallback; a different Filipino database question returned a real answer. A later English follow-up also returned the fallback. The strict live chat run failed its `fallback_used=false` assertion. |
| Local provider diagnosis | ISSUE | One direct Gemini call returned HTTP **503 / UNAVAILABLE**. Its locally configured fallback provider raised **AuthenticationError**. This does not establish that Render has the same fallback credentials; production provider logs were not available. No keys were displayed or changed. |
| Gmail authorization | ISSUE, local | Refreshing the existing local Gmail OAuth credential returned HTTP **400 / invalid_grant**. No token values were printed and no email was sent. Render's deployed credential file and inbox delivery were not independently retested. |
| APK build | PASS | `gradlew.bat assembleDebug --console=plain`: **BUILD SUCCESSFUL in 1m**, 126 tasks up to date. This is an incremental build using the installed dependency cache. |
| APK package/signature | PASS, internal test build | Existing APK 1.7.0/code 11, package `ai.librai.kiosk`; `apksigner verify` passed. Minimum API 26, target API 36, camera/microphone permissions present. `application-debuggable` is enabled. |
| APK contents/public artifact | PASS | ZIP integrity, live HTTPS API, chatbot/startup assets and absence of Gmail credential filenames checked. Public GitHub asset size/digest match the local APK. |
| Real tablet | NOT TESTED | `adb devices -l` listed no device. Installed version, camera decoding, real bilingual dictation, audible speech, touch behavior and animation smoothness remain manual acceptance tasks. |

## Issues found during verification

### Live AI can fail even though HTTP 200 is returned

The backend returns an honest unavailable message with `fallback_used=true` when providers fail. That is graceful failure, not proof that conversational AI answered the question. Both Filipino and English requests exhibited this during the audit.

The older ignored `generated/verify_170_live.mjs` checked Filipino language/text but omitted a no-fallback assertion for that particular reply. It could therefore print a success message after receiving the Filipino unavailable template. The local audit helper was tightened to require `fallback_used=false` for that case. A subsequent strict run failed on an English follow-up as well, confirming that the overall live conversation cannot be marked consistently passing today.

Recommended follow-up: inspect production provider failures, verify the configured backup provider authorization, and add a bounded, tested retry strategy for transient provider failures. Do not change credentials or assume that local fallback credentials match production without checking.

### Local Gmail needs reauthorization

Google rejected the existing local refresh token. Reauthorize the sender using [the Gmail notification guide](gmail_notifications.md), then verify the deployed credential configuration and send one explicitly approved QR test email. A passing queue/unit test does not prove current OAuth authorization or inbox arrival. No email backlog was dispatched during this audit.

### Initial server delay

The first API requests timed out before subsequent requests succeeded without a configuration change. This is consistent with delayed service startup, but the hosting logs were not inspected to establish the cause. Startup offline/retry behavior passed locally; first-open latency remains a practical usability concern.

## APK identity

- File: `generated/releases/LIBRAI-1.7.0-debug.apk`.
- Size: **49,574,026 bytes**.
- SHA-256: `1ef68daa631cd3c5631906c40a4ad9165edb0e34aaec7b51920a89d21f26cac4`.
- Signing certificate SHA-256: `f1069bb7a5ea6d0b31dbea50a8f0f95a15a1d52b2ace3ce655899e2b9fa0e427`.
- Production signing remains skipped under the user's prior instruction. No new APK release was published for this audit.

## Test environment notes

The first backend run could not access the old Windows `pytest-of-rober` temporary folder: four tests passed and 76 setup errors occurred. Rerunning with a fresh ignored workspace `--basetemp` resolved the environment problem and all 80 tests passed. No permissions or production data were modified to work around it.

`pip check` reported no broken requirements, with an existing ignored `~let-desktop` distribution warning. Gradle reported existing `flatDir` warnings. Generated tracked preview screenshots were restored after browser tests; private files and credentials were left unchanged.

This audit is not an exhaustive security/load test, a clean dependency installation test, a real production staff/account acceptance test, or a physical tablet certification.
