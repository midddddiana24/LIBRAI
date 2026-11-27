# LIBRAI 1.9.3 - admin QR downloads

Root cause: QR JSON returned /qr/download/... while the route exists under /api/v1/qr/download/.... Existing backend tests silently prepended the missing prefix. A regression following download_url verbatim reproduced HTTP 404 before the fix.

QR responses now return the complete API path. The frontend also supports older API-relative QR paths. Browser QR downloads, QR sheets and report exports use fetch/blob/download links instead of asynchronous window.open; server errors appear in the current admin screen. On native Capacitor, external HTTPS navigation delegates signed download links to the device browser. Existing signatures, authorization, ticket expiry and QR identities are preserved.

Checks: six isolated admin backend tests; build/lint/Capacitor sync; mocked admin browser verifies canonical and legacy QR URLs, PNG filenames, no popup, expired-ticket messages and PDF report downloads; four-size shared UX checks. Gradle BUILD SUCCESSFUL in 48s. Physical Android file saving remains unverified.

APK: generated/releases/LIBRAI-1.9.3-debug.apk, version 1.9.3/build 16, existing debug signer. Packaged HTML/JS/CSS match current dist byte-for-byte.
SHA-256: c5690adbcc5fa1c5e1b0f2dbd54daf8adfb2cde4959371625e61671dd9dd1791
