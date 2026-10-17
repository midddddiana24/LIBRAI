# ID-assisted student registration

## Student flow

1. On the kiosk home screen, choose **Register**.
2. Choose **Campus ID front** and take a photo or choose an image. Keep the text upright, close, and free of glare.
3. Review the suggested fields and choose **Apply scanned details**. Correct anything that was misread.
4. Optionally choose **Library borrower's card front** and repeat. Its card number is stored separately from the campus student number.
5. Enter the current year level and any missing fields. Email is optional.
6. Check the review/confirmation boxes and submit for staff approval.
7. The account stays **Pending** until library staff approve it. Staff then issue the LIBRAI QR used by borrowing and account lookup.

This is a library member registration, not a new administrator or password-based student portal login. A campus barcode, printed ID number, or OCR result is not a LIBRAI authorization grant. Scanning the university barcode for borrowing is outside this change.

## Staff flow

Open **Admin → Library users → Pending registrations → Review request**. Verify the campus student number and details against the card and the school's authorized records. Approve or reject explicitly. The QR action appears after approval. Duplicate public submissions do not modify an existing member; staff must resolve conflicting or mistaken numbers manually.

## What the scan reads

- Campus front: printed student number, name, and printed BS/BA course when readable.
- Library card front: explicitly labeled borrower's card number and name.
- Name order and suffixes are normalized into editable first-name/middle-initial and last-name/suffix fields.
- Year level is not inferred from renewal stamps. Emergency contacts, address, birthday, blood type, signatures, and the portrait are not extracted into registration fields.

The parser targets the supplied card layouts. It intentionally leaves uncertain/unsupported fields blank. Low-resolution photos, reflections, tilted cards, OCR punctuation errors, and different card layouts may require manual correction. There is no claim of perfect extraction from the actual submitted photographs.

## Data handling and authentication

OCR runs in a browser worker. Worker, language data, and WASM engine files are served by LIBRAI itself, with no external OCR/CDN request at scan time. ID photos and full OCR text are not uploaded to the backend, sent to Gemini, or stored by this flow. The worker terminates and the image preview is released when the scan is discarded, applied, or the form closes. The kiosk's normal session timeout also closes registration.

Only submitted form fields are sent to `/api/v1/registrations`. Public requests force PENDING status, return no member ID/QR/grant, and are rate-limited. Staff approval/rejection is authenticated and audited. QR verification/issuance and borrowing remain blocked while pending. Existing member records are not updated by public duplicate submissions.

## Verification

Local results on 17 October 2026: **43 backend tests passed**, four parser tests passed, TypeScript/Vite build and lint passed, and the real OCR/isolated-backend browser flow passed. The eight-viewport design checks also passed after correcting the short-landscape Register layout. The migration check was against a temporary database, not Neon.

- Backend tests cover registration, pending restrictions, authenticated approval/rejection, duplicate protection, separate library numbers, and request limits.
- Parser tests use synthetic identities and verify suffix/name order, separate numbers, ambiguous-number rejection, and exclusion of renewal/emergency data.
- `npm run test:registration-ui` performs **real browser OCR** on two generated synthetic card images, then calls a real isolated backend for request submission, staff approval, and QR enablement. It blocks unexpected external requests and verifies that scanning does not upload images or save records before submission.
- A migration was applied to an isolated SQLite database containing an existing member; the member was preserved and the nullable unique library-card field was added.
- Responsive kiosk/admin checks cover eight viewports, including short landscape tablet layouts.
- Screenshot: [synthetic-data registration form](design_previews/registration-review-768.png).

No real ID photos or personal details from the supplied images are included in the code, test fixtures, or screenshots. Actual Android camera capture of an ID photo and extraction quality on these real cards still need user acceptance testing.

## Deployment

This feature needs migration **c2d9e4a7b615** after **f1a8c9d3e721**. Deploy the API with `alembic upgrade head` before deploying the new website or APK. The migration adds a nullable `library_card_number` column and a unique index; it does not replace current records. Do not run seed/import scripts on the populated live database.

`npm run build` and `npm run dev` prepare self-hosted OCR files from the installed packages automatically. The generated `web/public/ocr/` folder is ignored by Git and included in the build output. The new dependencies are Tesseract.js and the packaged English language data; the latter is a build-time dependency. Only the OCR variant needed by the device is loaded when a scan starts.

The current installed 1.5.1 APK predates this feature. A new package and deployed API migration are required for production use; local implementation does not update the installed app or Render services.

## Recommended next AI improvements

1. Show whether an answer used the external model or catalog fallback, using the existing `ai_available` and `fallback_used` response fields.
2. Add and test Filipino/English catalog synonym matching so database fallback handles the same topics across both languages.
3. Maintain a small regression set of expected catalog results and voice commands, including unavailable titles and unrelated queries. Label related alternatives clearly instead of implying they are exact matches.

These are recommendations, not changes implemented by this registration feature. The current ID flow improves data entry while keeping staff review as the approval step.
