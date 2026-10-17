# Modern redesign validation

Checked locally on 17 October 2026. This is a visual/interaction redesign of the React kiosk and staff app. It does not change the FastAPI data contract.

## Passed checks

- `npm run build`: TypeScript and Vite production build passed.
- `npm run lint`: passed.
- `npm run test:voice`: all five command/audio checks passed.
- `npm run test:voice-ui`: command navigation, silence rejection, transcript review, question dictation, and read-aloud controls passed using simulated audio.
- `npm run test:design-ui`: passed at 320x740, 375x812, 414x896, 600x960, 768x1024, 960x600, 1024x768, and 1440x1000. Checked four kiosk destinations, staff menu open/close, catalog form, sign-out/sign-in, and horizontal overflow. Tablet home screens fit without vertical scrolling at the tested tablet sizes.
- Default GSAP entry settles to the visible end state. Reduced-motion mode suppresses spatial hover effects.
- At 375 px and 200% root text size, the home screen had no horizontal overflow or overflowing button text. It can scroll vertically to preserve access.
- Rendered kiosk/dashboard text contrast was inspected with WCAG luminance ratios. An inherited low-contrast breadcrumb color was corrected. Focus styles remain visible.
- `npm audit --omit=dev`: no reported production dependency vulnerabilities at the time checked. This is not a complete security audit.
- Gradle `assembleDebug`: built Android version 1.4, version code 5.

## Design review

Shared app tokens, restrained cobalt controls, original book SVGs, consistent staff icons, immediate errors/focus, and one view-entry sequence replace the previous mixed visual layers. No decorative phone frame, invented production metrics, gradient headline, scroll pinning, auto-playing sound, or stock photo was added. Existing API-backed records and QR confirmations remain authoritative.

Hallmark checks were applied to the app surface. Marketing-only section, theme-rotation-between-pages, and testimonial gates do not apply to a single shared library application. No blanket 58/58 compliance claim is made.

## Boundaries

Browser checks intercept the API and use sample values. They do not prove live database writes, real voice-recognition accuracy, or a real QR camera session. No Android device was attached; APK installation and physical tablet testing remain to be done. Screenshots are local previews, not evidence of a public Render deployment.

Deploy the new commit from `online-admin-postgres` to the Render kiosk service before expecting the website to change. The APK bundles its own web assets and must be installed separately.
