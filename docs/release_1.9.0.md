# LIBRAI 1.9.0 — kiosk and admin UX improvements

## Delivered

| Recommendation | Implementation |
| --- | --- |
| Precise Help | Measured popovers, specific QR/camera/confirmation/finish targets, four-stage borrowing progress, registration section targets, contextual admin targets, reserved dock/minimize for small screens. |
| Error recovery | Field-level native/server validation; forms retain values; typed QR failures remain editable; scan errors sit beside the active controls; no automatic retry of writes. |
| Actionable dashboard | Real API counts link to pending registrations, overdue loans and failed emails. |
| My account | Active loans first; History/Reservations/Fines/Notifications tabs; real totals and pagination beyond the previous 50-record cap; truthful renewal eligibility and reasons. |
| Book discovery | Real cover images with broken/missing-image fallback, stock text and shelf locations. |
| Chat readability | Flexible conversation region, visual viewport sizing, preserved reading position and explicit Latest messages; reply source labels and voice transcript review preserved. |
| Registration | ID/Academic/Contact/Review groups; optional-email delivery explanation; declarations and staff approval unchanged. |
| Admin tables | Explicit columns, text status badges, contextual row action names, server status filters, page sorting/search labelled honestly, actual totals and horizontal mobile containment. |
| Confirmations | Accessible dialogs with exact record/recipient details for library QR email, send, retry, fine payment and reservation cancellation; Escape/cancel restores focus and sends no action. |
| Language | English/Filipino interface selector independent of speech-recognition language; core home/navigation, member forms/account, transactions, QR controls, scanner labels and chat controls translated. Server messages and technical terms may retain English. Help keeps its own language selection. |
| Version clarity | About panel on kiosk/admin shows client version 1.9.0, build 13, API address and observed connection state; explains manual APK updates. |
| Accessibility and motion | Existing focus rings/reduced motion preserved; large targets, semantic field descriptions/errors, tab controls and dialog focus; restrained button/receipt/loading effects. |

## API changes

- `GET /api/v1/borrowings?overdue=true` filters active/overdue loans with due_at in the past, including ACTIVE records not yet marked OVERDUE. Authentication/grant checks remain required.
- Borrowing projections include `renewal_unavailable_reason`; `can_renew` now also accounts for another member's waiting reservation. The renewal operation still performs its existing authoritative checks.
- API validation errors retain structured field information in the frontend ApiError.fields map. No database migration or new dependency was added.

## Verification

- Full isolated backend suite: **82 passed**, one existing Starlette/httpx warning, 121.56 seconds. Includes new overdue filtering and truthful renewal-projection tests.
- Production frontend build, lint, API type generation and Capacitor sync passed.
- Shared browser UX: English/Filipino switch, About/version, actual cover display, no write from language/About, near-field server validation and retained input; 320/600/768/960 widths. Translated tablet Home remains within viewport height.
- Admin mocked browser: attention links/counts, overdue query, filter reset, page sorting/search, pagination, explicit and cancelled confirmation flows, focus restoration and mobile containment. No real emails or production API requests.
- Member synthetic browser: active/overdue loans, history record 53, reservation/notification pages, empty data, grouped form, local/server validation, optional-email submission and Filipino labels at 320/768/1024/1440 widths.
- Dedicated Help browser: four widths including simulated 320×360 keyboard shrink, precise target hit-testing/non-overlap, real progress gates, invalid QR retention, both languages, modal precedence, Escape and session clearing.
- Regression: eight-size kiosk/admin layout/navigation, five-size borrowing confirmation flow, real isolated API chat and synthetic-card OCR/registration/staff approval/notification queue passed. Voice smoke passed with simulated audio/TTS.

## Delivery and limits

Local Android artifact: `generated/releases/LIBRAI-1.9.0-debug.apk`, version 1.9.0/code 13. It uses the existing debug signer; choose Update over the prior debug app. Website and API changes must be deployed together for the new overdue filter and renewal reason; this implementation does not publish or change hosted services.

Real tablet keyboard, camera, microphone, speaker and animation acceptance remain manual. The UI does not repair the previously observed provider availability or Gmail OAuth authorization problems. No email was sent and no live member or circulation data was changed. These checks are not a full WCAG certification or load test.

## Android artifact verification

Gradle reported `BUILD SUCCESSFUL in 26s`. Signature verification passed and matches the previous debug signer. Package inspection confirms 1.9.0/code 13, with debugging enabled for this internal build. Packaged HTML/JavaScript/CSS match the final web build byte for byte; Gmail credential filenames are absent.

File size: 49,594,306 bytes. SHA-256: `39a36c4c92caf7ecab0a85b8a89f985c2e76c8f4c43db75b5ecf9f2c4edba86d`.
