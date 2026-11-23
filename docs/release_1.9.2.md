# LIBRAI 1.9.2 - startup animation fix

The opening could end before the 1.5 MB book image arrived, leaving blank artwork, and the old minimum duration cut off the final page turn. Reproduced with a delayed image and a fast health response.

The shared startup now waits for decoded artwork, uses a CSS book when it fails or takes more than two seconds, and gives the opening 1.6 seconds after artwork resolution before the ready transition. Reduced motion, actual server readiness, offline retry and the existing home design remain intact. The startup CSS link is versioned to avoid stale browser styling. Initial HTML has visible fallback artwork and explicit image dimensions.

Validation: production build/lint and Capacitor sync; six startup sizes; delayed/missing image regressions; offline retry; reduced motion; changing page transforms; shared UX at four sizes. Gradle BUILD SUCCESSFUL; signature verified with existing debug certificate; APK 1.9.2/build 15 web assets and startup CSS match dist.

Local artifact: generated/releases/LIBRAI-1.9.2-debug.apk
SHA-256: 29110a432d166ba56cfac5c02fbccbb7cf15316088405211ae30b5de92f1d729

Physical tablet animation acceptance remains manual. This release does not repair the separately observed conversational AI provider failure.
