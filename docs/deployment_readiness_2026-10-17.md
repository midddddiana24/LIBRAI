# LIBRAI deployment and AI check

## Follow-up: dependency installation resolved

The subsequent clean installation used `uv venv` and `uv pip install -r requirements.txt` with Python 3.14.3. All 64 packages installed successfully, including FastAPI 0.116.1 and Uvicorn 0.35.0. The full backend suite then completed: **37 passed, 186 deprecation warnings in 67.96 seconds**. This resolves the earlier PyPI installation limitation described in the original audit below. Deprecation warnings remain; no test failed.

Android packaging and publication follow-up is tracked in [the version 1.5 checklist](release_1.5.md).

## Follow-up: publication and connected-device testing

Source commit `12fa2a2` was pushed to `online-admin-postgres`. The public website was then verified to contain the new Borrow layout and exact new logo. The live API was healthy and its new recommendation request limit was observed without calling a model or writing library records.

Android 1.5/code 6 was built and installed on the connected Infinix X6531. The user confirmed the real microphone transcription **Romance** matched what they said, and that the answer was audible. The default QR engine opened without decoding; ML Kit then decoded the exact non-member test QR on the same device. Version **1.5.1/code 7**, which selects ML Kit explicitly, was subsequently built, signed, and installed. The regular Borrow-screen camera retest is pending the user's result. This device is a phone; it does not replace testing on the intended tablet or establish general speech accuracy.

Checked 17 October 2026 in `C:/Users/rober/Desktop/LIBRAI`, branch `online-admin-postgres`.

## Verdict

The live API and its AI features passed the checks below. The local application is suitable for a controlled deployment after the pending changes are committed, pushed, and deployed. Final acceptance on the Android tablet is still required. This is a functional readiness check, not a complete security audit or load test.

The public website serves the shared modern design, but **does not yet contain the new Borrow layout**. Its compiled API address is correctly set to `https://librai-api-free-pg.onrender.com/api/v1`.

## Live checks

| Check | Result |
| --- | --- |
| API `/health` | HTTP 200, `status=healthy`, `database=connected` |
| Website | HTTP 200; deployed kiosk chunk `KioskApp-CMDGCWTp.js` |
| CORS for website | HTTP 200; exact website origin allowed |
| CORS for Android | HTTP 200; `https://localhost` allowed |
| English AI search | HTTP 200, `ai_available=true`, `fallback_used=false`, one catalog book, about 2.20 seconds |
| Filipino AI search | HTTP 200, `ai_available=true`, `fallback_used=false`, one catalog book, about 1.48 seconds |
| Speech transcription | HTTP 200, correctly transcribed “Find books about Python programming.”, about 2.02 seconds |
| Database migration revision | Configured Neon database and repository both at `f1a8c9d3e721` (head), checked without running a migration |

The live speech input was a known English WAV synthesized locally. This proves the upload/API/provider transcription path for that sample. It does not establish recognition accuracy for a person speaking Filipino, background noise, or the tablet microphone. Initial public requests timed out; subsequent requests succeeded. Startup responsiveness remains a practical acceptance check.

The two live AI searches create ordinary search/interaction records. No real borrowing, return, member, or catalog record was changed by these requests.

## Local checks

- Production frontend build: passed (`npm run build`).
- Frontend lint: passed (`npm run lint`).
- Command/audio unit checks: 5 passed (`npm run test:voice`).
- Simulated voice UI: passed command review/navigation, dictation, silence rejection, and read-aloud controls (`VOICE_UI_URL=http://127.0.0.1:4190 npm run test:voice-ui`).
- Borrow UI: passed at 320x740, 414x896, 600x960, 768x1024, and 1024x768, including verification grants, unavailable-copy rejection, explicit confirmation, receipt, and session clearing (`npm run test:borrow-ui`).
- Backend tests after fixes: 37 passed in the working environment. Test database was temporary SQLite, with cloud AI and storage disabled or explicitly mocked.
- Real local API-to-Gemini checks with an isolated test catalog: English and Filipino AI responses used only the supplied book; speech transcription returned the expected sentence; catalog recommendations and health passed. These checks did not write to the production database or media bucket.
- Working environment `pip check`: no broken requirements. Its FastAPI/Uvicorn versions differ from `requirements.txt`; a separate clean dependency check is recorded below.
- Git does not track `.env`, `.env.local`, `.neon`, database files, or signing keystores in the checked patterns.

### Dependency reproducibility limit

The working environment has FastAPI 0.141.1 and Uvicorn 0.52.4; deployment pins 0.116.1 and 0.35.0. Installing just those runtime pins in an isolated environment succeeded, but that environment lacked the remaining application dependencies and could not run the suite. A subsequent full clean install was stopped after repeated PyPI timeouts while resolving `typing-extensions`. Therefore, **37 passing backend tests apply to the working environment, not a verified fresh Render-equivalent installation**. Check the actual Render build/install log and rerun API smoke checks after deployment. No dependency versions in the project were changed.

## Fixes made during this check

1. **Provider fallback:** the local TokenRouter credential was rejected. Previously, its presence prevented Gemini from being tried. Failed TokenRouter ranking now tries configured Gemini before using local catalog fallback. A regression test covers the failure path. The live API already passed its own Gemini requests; the local credential failure does not establish a problem with Render's credential.
2. **Public AI request limits:** speech transcription and recommendations now use the existing request limiter. Tests verify HTTP 429 and `Retry-After`.
3. **Speech concurrency:** the synchronous transcription call now runs in a worker thread instead of blocking the async request loop. A test checks that execution is outside the event loop.
4. **Test isolation:** ordinary tests now disable inherited real storage and AI credentials. The first test run inherited storage credentials and uploaded three generated test artifacts; those exact artifacts were removed and their absence confirmed. The test database was temporary throughout.

The local settings currently permit only the legacy Flet origins. Use the correct CORS values in Render; the live CORS values passed the check. No secret values were changed or added.

## Deploy in this order

1. Review and publish the pending changes on `online-admin-postgres`. A local build does not publish them.
2. Deploy the **existing Neon-backed API service** and preserve its database, object-storage credentials, and stable `SECRET_KEY`. Do not recreate the old SQLite service from the default `render.yaml`; that manifest still describes the legacy API and old frontend API URL. `render.free-persistent.yaml` describes the Neon-backed service.
3. Deploy the kiosk service from the same branch with `VITE_API_BASE_URL=https://librai-api-free-pg.onrender.com/api/v1`. Build: `cd web && npm ci && npm run build`. Start: `node web/server.mjs`.
4. Recheck API health, CORS, AI search, and the Borrow layout in the public site's assets.
5. Rebuild the Android package with a higher version code before installing the update. The existing debug APK is version 1.4/code 5 and predates the Borrow redesign and these backend fixes. No APK was rebuilt in this audit.
6. On the real tablet, check camera and microphone permissions, English/Filipino recording, audible text-to-speech, a real QR borrow/return, admin sign-in, and the update installation. Use designated test records for circulation.

Text-to-speech uses the device/browser speech engine, not a backend TTS endpoint. Its controls passed simulated browser checks; audible playback and installed Filipino voices were not verified. Live admin credentials were not requested, so live admin sign-in was not tested.

## Logo recommendation — proposal only

The current cream/teal book symbol has been inspected. No image has been generated or replaced because the requested next step is a recommendation.

| Direction | Description |
| --- | --- |
| **Open book + L — recommended** | Two clean page shapes with an L suggested by the spine/page. Flat cobalt and navy, rounded geometry, readable at small size. Library identity remains immediate. |
| Book + reader | Two pages and a restrained circular reader silhouette. Friendly and student oriented. |
| L bookmark | A single folded bookmark forming an L. Compact and distinctive, with a less explicit library cue. |

Recommended generation brief: an icon-only open-book/L symbol; flat cobalt/navy; balanced proportions; transparent background; clear at 24–48 px; no lettering or tiny decorative detail. Prepare a light-background version, a white version for the admin rail, and an Android icon treatment after selecting the concept. Imagegen should produce the concept first; implementation follows the selected design.
