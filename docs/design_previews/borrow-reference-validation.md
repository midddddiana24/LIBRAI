# Borrow screen implementation

17 October 2026. Reference: [modern-borrow-concept.png](modern-borrow-concept.png).

## Changes

- Three connected steps: Library ID, Book QR, Confirm.
- A large illustrated scan panel, camera action, and manual QR entry. Manual values remain hidden password inputs.
- Upcoming steps stay visible as informational panels. Completed steps show the verified user/book and a Change action.
- Availability, signed verification grants, explicit confirmation, server-assigned due dates, and session clearing keep the existing API contract.
- Home and the privacy message form the screen footer. The redundant generic kiosk footer is hidden on this screen.
- Existing shared typography, color tokens, focus rings, press feedback, and reduced-motion behavior remain in use. No new dependency.

## Verification

- `npm run build`: TypeScript and Vite production build passed.
- `npm run lint`: passed.
- `npm run test:borrow-ui`: checks 320x740, 414x896, 600x960, 768x1024, and 1024x768. Covers invalid QR errors, step progression, unavailable copies, explicit confirmation, signed grant submission, the pending state, receipt, changing a scan, Home, and session clearing. No horizontal overflow; the first step fits both portrait tablet sizes without vertical scrolling.
- `npm run test:design-ui`: existing kiosk navigation and staff navigation/catalog/sign-in checks passed at all eight configured viewport sizes. Normal entry motion settles; reduced motion disables spatial hover effects.

The browser tests intercept API requests with sample records. They do not write to the public library or prove real camera scanning. No APK was rebuilt or installed for this change, and these local previews do not establish a Render deployment.

## Rendered previews

- [Tablet: scan library ID](borrow-reference-768.png)
- [Smaller tablet](borrow-reference-600.png)
- [Phone](borrow-reference-414.png)
- [Tablet: review and confirm](borrow-review-768.png)
