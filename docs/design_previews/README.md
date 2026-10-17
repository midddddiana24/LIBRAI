# LIBRAI interface previews

## Modern service desk redesign (version 1.4)

The implemented screens share locally bundled Outfit/Source Sans 3 fonts, cobalt controls, original SVG service art, reduced-motion support, and a responsive staff menu. The admin numbers and catalog entries in these browser captures are **sample API responses for layout checking**. They are not proof of live records or a production deployment.

- [Implemented kiosk portrait](modern-kiosk-768.png)
- [Implemented kiosk landscape](modern-kiosk-1024.png)
- [Implemented borrow screen](modern-borrow-768.png)
- [Staff sign in](modern-admin-login.png)
- [Staff dashboard desktop](modern-admin-1440.png)
- [Staff dashboard phone](modern-admin-375.png)
- [Staff catalog and add form](modern-admin-catalog.png)

Two images were generated with the built-in image generation tool as visual references: [home concept](modern-kiosk-concept.png) and [borrow concept](modern-borrow-concept.png). They are concept artwork, not screenshots. Production UI uses HTML/CSS and original SVGs for readable text and working controls. [Exact generation prompts](modern-concept-prompts.md) are saved alongside the images. Full design rules live in [design.md](../../design.md).

To reproduce the browser checks, start the Vite preview at port 4190, then run `npm run test:design-ui` in `web/`. Set `DESIGN_SCREENSHOTS=1` to refresh the implemented screen captures. All API requests in this check are intercepted; it does not write live records.

## Previous previews

Version 1.3 removes the decorative device frame and fills the available tablet viewport. These previews use a mocked health response; no physical tablet was connected.

- [Full tablet layout in portrait](kiosk-full-tablet-768.png)
- [Full tablet layout in landscape](kiosk-full-tablet-1024.png)

These screenshots show the local version 1.1 design at tablet, phone, and desktop sizes. The admin dashboard screenshot uses sample counts from a mocked browser response; it is a layout preview, not a live account screenshot.

The version 1.2 kiosk menu follows the supplied reference image with four large illustrated actions. These are local browser previews with a mocked health response, not photos from the Android tablet.

- [New kiosk menu on tablet](kiosk-tile-menu-tablet.png)
- [New kiosk menu on phone](kiosk-tile-menu-phone.png)

- [Kiosk on tablet](kiosk-tablet.png)
- [Kiosk on phone](kiosk-phone.png)
- [Admin sign in](admin-login.png)
- [Admin dashboard with sample data](admin-dashboard-sample.png)
