# Guided Help mode — LIBRAI 1.8.0

Help is available from the kiosk header and the signed-in admin header. Select Guide this screen, or choose a task from Home/admin lists. Editing screens keep task switching in the normal navigation so the help chooser cannot discard an unfinished form.

The guide uses deterministic English/Filipino instructions, an interactive spotlight, Back/Next/Exit, optional device read-aloud and a minimize control. Action steps wait for actual screen state changes; the guide never scans, approves, borrows, returns, marks paid or sends email on behalf of the user. Existing validation and confirmation flows remain authoritative.

Coverage: kiosk Home, borrowing ID/book/review/receipt, returns, registration, search/detail/discovery, verified account and chat; all eleven authenticated admin sections, including pending-user review, book/user forms, email acceptance semantics and role-filtered settings access. Empty/missing controls receive guidance instead of invented records. Guidance remains generic and never includes private values.

Focus cycles through the guide, highlighted controls and End session. Escape exits, focus returns to Help, and session reset/sign-out removes the overlay. Native/modal camera interfaces take precedence. Resizing, scrolling and visual keyboard changes update positioning. Reduced motion removes the spotlight pulse and slide/fade effects; other users receive a 180 ms dim, 220 ms card entry and one outline pulse.

## Verification

- Backend: 80 passed, one existing deprecation warning; isolated fresh SQLite fixtures, outbound services disabled.
- Production build, TypeScript, lint and Capacitor sync passed; no new dependencies.
- Guided borrowing: five viewport sizes, English/Filipino switching, invalid ID, action-step gating, successful ID advancing instructions, Escape, zero automatic borrowing and End session clearing the open guide.
- Admin Help/navigation and layout: eight viewport sizes, 320 × 740 through 1440 × 1000.
- Real isolated API/browser chat and OCR/registration/staff-approval/email-queue workflows passed. No live circulation or email delivery was performed.

## Delivery

Android version 1.8.0/code 12 uses the existing debug signer for internal installation. Local artifact: `generated/releases/LIBRAI-1.8.0-debug.apk`. Public website and GitHub release publication are not part of this local implementation. Physical tablet camera, keyboard positioning, pronunciation and animation performance still need manual acceptance. Existing AI provider availability and Gmail authorization issues are unchanged.

Final APK verification: Gradle `BUILD SUCCESSFUL in 1m 52s`; signature verification passed; package metadata confirms 1.8.0/code 12. HTML/JavaScript/CSS inside the APK match the final web build byte for byte. File size 49,580,462 bytes. SHA-256: `13bbebdb9238a07340b366b9f05ce00a1c9b0108c312294e3e005b67238c1491`.
