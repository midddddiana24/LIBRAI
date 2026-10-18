# LIBRAI 1.7.0

## Changes

- Book-opening 2.5D startup: generated open-book artwork, animated cover and paper leaves, then existing logo. Connecting, ready, offline/retry and reduced-motion states use actual API readiness. The opening lasts up to 950 ms plus a 420 ms ready transition when the server responds quickly; longer network waits do not restart the opening.
- Chat intent routing for explanations, comparisons, research clarification, catalog requests, real policies and verified account help.
- Up to four completed non-account turns provide short conversation context; all session-clearing rules remain.
- English/Filipino conversation, deterministic bilingual library answers and response-language read-aloud selection.
- Member-scoped active loans, due dates, recorded fines and renewal eligibility; actual renewals continue in My account with existing checks.

## Android update

Version **1.7.0**, code **11**, package `ai.librai.kiosk`.

Local APK: `generated/releases/LIBRAI-1.7.0-debug.apk`.

Download after publication: [LIBRAI 1.7.0 APK](https://github.com/midddddiana24/LIBRAI/releases/download/v1.7.0/LIBRAI-1.7.0-debug.apk).

On the tablet, open the downloaded APK and choose **Update** over the existing debug-signed app. Website deployment does not update installed APK assets automatically. Production signing remains skipped at the user's request. Physical tablet microphone, camera, speaker and animation performance checks remain manual.

## Generated artwork

Built-in image generation produced `web/public/images/librai-startup-book.png`. The prompt requested a single centered, almost frontal open library book with ivory pages, restrained royal-blue cover, layered paper edges and a small blue bookmark; a clean dimensional editorial illustration readable at 180 pixels; real transparent alpha, generous margins, no text, letters, symbols, logo, sparkles, people, scenery or device frame. Code animates separate paper/cover overlays and uses the existing LIBRAI logo without replacing it.

## Verification

- Isolated backend suite: **80 passed**, one existing Starlette/httpx deprecation warning; temporary SQLite fixtures with external services/autosend disabled. No library records were used as test fixtures.
- Live provider checks returned an English database explanation, a simpler follow-up, a Filipino Python/Java comparison, and a catalog intent for an explicit book request. These were synthetic questions, with no private account data.
- Generated content is not guaranteed correct. Database and account validation does not validate general educational claims.
- Backend schema changes are additive request fields; no database migration or new service is required.
- Production web build, Capacitor sync, lint and regenerated API types passed.
- Startup browser checks passed at 320, 375, 414, 600, 768 and 960 px widths: asset loading, connection → ready → Home, offline → retry → Home, overflow and reduced motion. The test observes the brief ready transition through DOM mutations to avoid missing it during browser scheduling delays.
- Real isolated API/browser checks passed for scanned-member grants, conversation payloads, account-result exclusion, catalog follow-ups, policy settings, no-match, error/retry and session clearing including late replies. Voice controls passed with simulated recordings/TTS; these do not measure physical speech recognition.
- Responsive/navigation regression passed eight sizes, 320 × 740 through 1440 × 1000, including both tablet orientations.
- Final Gradle output: `BUILD SUCCESSFUL in 45s`. `apksigner verify` passed with the same debug certificate as the previous APK. `aapt dump badging` confirms 1.7.0/code 11.
- APK: 49,574,026 bytes; SHA-256 `1ef68daa631cd3c5631906c40a4ad9165edb0e34aaec7b51920a89d21f26cac4`. Packaged HTML, JavaScript, CSS and startup stylesheet match the final web build byte for byte. Startup art and the live HTTPS API are present; Gmail OAuth/client-secret files are absent.
