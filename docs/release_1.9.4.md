# LIBRAI 1.9.4 - coherent 3D startup

The old book was a flat PNG with unrelated page rectangles over it. Its parent faded throughout opening, obscuring the depth. The ready logo only had 420 ms and could disappear before its own image loaded; a delayed-logo test reproduced a ready frame with naturalWidth=0 and Home after 467 ms.

The new opening uses a CSS 3D cover with separate front/inside faces, spine, page block and two hinged double-sided leaves. The existing logo is reused on the cover and in a 700 ms perspective reveal, with a 1.2 second ready-stage budget before Home. Artwork readiness now tracks the logo rather than the old large book image; slow/missing artwork has a bounded fallback. The ready callback is held in a ref so parent idle-counter renders cannot continually restart its timer. Static HTML and versioned startup CSS use the same book, preserving the existing kiosk home identity and reduced-motion/offline behavior.

Checks: production build/lint; six startup sizes; delayed/missing logo; offline retry; reduced motion; actual page-transform motion and preserve-3d parent opacity; decoded-logo and ready-hold timing; four-size shared UX. Gradle BUILD SUCCESSFUL in 29s. Signature verified with existing debug signer. All packaged HTML/JS/CSS plus startup stylesheet match current dist bytes.

APK: generated/releases/LIBRAI-1.9.4-debug.apk, version 1.9.4/build 17.
SHA-256: ab787355222c5899d9a8f138bd784889aab3a0f17fcf73a6466710c74c66c170

Physical Android GPU smoothness and playback remain manual acceptance checks. No backend, library records, QR identities or email configuration were changed for this animation fix.
