# LIBRAI AI assistant

## What changed

1. Search requires a catalog metadata match before availability, borrowing history or popularity can boost a title. It never substitutes unrelated available books when a topic has no matches. Reading-level filters require explicit level words in the title, keywords, subjects, category or description.
2. Scan your library ID in **My account**, select **Home**, then use **Discover books** or **Ask LIBRAI**. The kiosk sends the recent verification grant with the member ID. Recommended titles prefer categories in that member's borrowing history; without history, suggestions are general. No member names, email addresses or borrowing records are sent to the ranking provider.
3. Ask about borrowing limits, loan periods, renewals, reservation pickup or overdue fines. Answers read the current admin settings on every request. Unknown policies such as opening hours refer to staff. Answers are currently in English; English and Filipino question patterns are supported.
4. After a subject search, ask **Show easier ones**, **Only available books**, **Mas madali lang**, **Include unavailable**, or **Remove level filter**. The current topic and filters are displayed. **Start a new question** clears the context. New topics replace it. Policy questions preserve it.
5. **End session**, the 90-second inactivity timeout, changing the scanned member, or completing a borrowing clears personal suggestions and context. Late AI responses cannot restore them. Context is in React memory, not browser storage. Existing API search/interaction analytics still apply.
6. Gemini receives a JSON schema including allowed book IDs. Both provider paths validate and deduplicate IDs. Provider-written claims are not displayed: titles, counts and shelves come from catalog serialization. A valid empty response stays empty; provider failures use matching local candidates and show a fallback notice.

## Speech

Choose **English / Filipino (auto)**, **English**, or **Filipino** before recording. The request includes a language hint; it does not guarantee recognition accuracy. Dictation fills an editable question and still requires **Ask**. Voice commands show editable **Words heard** and require **Run command**. Borrowing still requires verified QR codes and transaction confirmation. Noise/silence checks run before upload; speech may still be misheard.

Text-to-speech uses the browser/device speech engine. English policy answers are read in English. Installed device voices and audio output must be checked on the intended tablet.

## Verification commands

Use an isolated temporary SQLite DATABASE_URL for backend pytest; never run the suite against the Neon production database. External providers, media storage and automatic email are disabled in test fixtures.

From `web`:

```text
npm run build
npm run lint
npm run test:voice
npm run test:voice-ui
npm run test:ai-ui
```

Browser smoke scripts expect the production preview on port 4190 (`VOICE_UI_URL=http://127.0.0.1:4190` for voice). The AI browser script starts its own temporary SQLite API, redirects all API calls there and blocks unexpected external requests. It checks real scanned-member grants, personalization requests, follow-ups, policies, no-match results, session clearing and viewport overflow. Voice smoke uses synthetic recordings/transcripts; it does not measure real speech recognition.

## Physical tablet acceptance - pending

The user will connect the intended Android tablet later. Test each phrase in a quiet room and again with typical library background noise:

| Phrase | Expected review/action |
| --- | --- |
| Borrow a book | Borrow screen only after Run command |
| Manghiram ng libro | Same borrowing flow |
| Ibalik ang libro | Return screen only after review |
| Ilang books ang puwedeng hiramin? | Assistant question; Ask reads the configured limit |
| Find books about Python programming | Catalog search |
| May libro ba tungkol sa Python para sa baguhan? | Assistant; matching beginner metadata only |
| Show easier ones | Same subject with beginner filter |
| Only available books | Same subject with available copies only |
| Silence / fan noise | No command; retry or correct if misheard |

Record spoken phrase, actual transcript, corrected transcript, language selection, noise condition and outcome. Tap **Read answer aloud**, confirm intelligible sound, stop reading, then end the session and confirm prior member context is gone. Test the newly built APK separately from the website; an old installed APK does not acquire new bundled UI automatically.

## Known limits

This is bounded metadata matching with a small bilingual synonym map, not unrestricted semantic retrieval or general conversational memory. Level accuracy depends on catalog tagging. Available-copy counts describe stock at response time, not a reservation or promise that a later borrow succeeds. Provider validation does not prove every relevance judgment correct. Feedback is stored for staff review; it does not automatically train a model.

## Verification result - 17 October 2026

- Isolated backend suite: **71 passed**, one existing Starlette/httpx deprecation warning.
- Production frontend build: passed. Frontend lint: passed.
- Voice unit checks: **6 passed**. Browser voice smoke: passed (synthetic audio/transcripts).
- Real isolated API/browser flow: passed, including member grants, follow-up context, policy values, no-match and session clearing; 768px and 390px overflow checks passed.
- A live ranking request with synthetic catalog metadata returned a valid structured Gemini response and the expected allowed ID. The locally configured TokenRouter key returned AuthenticationError; Gemini fallback worked. No credentials were changed.
- No live library database records were used for test fixtures or circulation. No notification email was sent for this task.
- Deployment and APK rebuild were not performed in this change. Physical Android voice/noise testing is pending until the user connects the intended tablet.

Schema reference: [Google Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output). Schema validity is separate from factual correctness, so catalog validation remains server-side.

## Chat screen

Ask LIBRAI now displays a dedicated library chat. It retains up to 20 question/reply pairs for the current kiosk session, including book cards, provider-fallback notices and feedback per reply. Suggested opening questions, a loading reply, editable voice dictation, read aloud and retry are available. Book details have a **Back to chat** action. No floating widget or admin chatbot was added.

**Start a new question** clears the displayed messages and topic context. The same clearing occurs on End session, inactivity or member changes. Message text is rendered as plain React text; model output cannot insert HTML. The conversation transcript stays in memory; the API still records its existing search and interaction analytics. The backend receives the current question, bounded topic/level/availability context and an optional verified member grant, not the full message transcript. This supports library follow-ups, not unrestricted conversational memory or general web research.

Borrowing, return and registration procedure questions use the actual existing kiosk workflows. The bot does not execute transactions or approve registrations. Staff approval and QR confirmation remain required.

Chat verification: production build, lint, isolated real API/browser conversation (history, follow-ups, book details and Back to chat, failed request and retry, session clearing), simulated voice dictation/read aloud, and 768px/390px viewport checks. Physical tablet and live deployment remain pending.

Latest chat verification: **75 backend tests passed**, one existing Starlette/httpx deprecation warning. Production build, lint, real isolated API/browser chat checks (including a late reply after End session), and simulated voice UI passed. No new dependencies were added.
