# LIBRAI 1.6.2

## Home and discovery

- Removed the home catalog search form; **Find a book** still opens the searchable catalog.
- Moved voice commands and the language selector beside **Hear instructions**. Transcript review before running a command remains enabled.
- Kept four large home actions and three secondary actions across the tablet width.
- Added 24 px gaps between discovery cards and between filters and results.

## Android installation

Version **1.6.2**, code **10**, package `ai.librai.kiosk`.

Local file: `generated/releases/LIBRAI-1.6.2-debug.apk`.

Download: [LIBRAI 1.6.2 APK](https://github.com/midddddiana24/LIBRAI/releases/download/v1.6.2/LIBRAI-1.6.2-debug.apk).

Open the APK on the tablet and choose **Update** over the existing debug-signed app. Verify version 1.6.2 in Android settings. Website deployment does not automatically update the installed APK.

Production signing remains skipped at the user's request. This is an internal test APK; physical tablet microphone, camera and speaker checks remain manual. No backend or database changes were required.

## Checks

- Production web build, Capacitor sync and lint passed.
- Layout/navigation smoke passed at all eight sizes from 320 × 740 to 1440 × 1000, including 600 × 960, 768 × 1024, 960 × 600 and 1024 × 768. Checks include absent home search, toolbar order, discovery spacing, staff navigation and reduced motion.
- Simulated voice UI passed: command navigation, dictation and read-aloud control.
- Earlier runs exposed landscape overflow; the final responsive rules passed without relaxing the assertions. One intermediate UI run timed out while Gradle was running; the final run completed separately.
- Final Android build: `BUILD SUCCESSFUL in 34s`; `apksigner verify` passed. Package inspection confirms 1.6.2/code 10 and the same debug signing certificate as 1.6.1.
- Packaged HTML, JavaScript and CSS match the final web build byte for byte; live API configuration is present and Gmail credential files are absent.
- APK size: 48,124,436 bytes. SHA-256: `53b081e5d8f0c57ed46d18c1f59c61be97d2e98550f97571a8668f6d5b1cda77`.
- Published code: `f9d0e83` on `online-admin-postgres`. Render's live asset `index-gv1Q6VET.js` contains the new home and discovery markup.
- Public website browser checks passed at 600 × 960, 768 × 1024, 960 × 600 and 1024 × 768, checking no home search, voice placement, tablet fit and discovery gap against the live service.
