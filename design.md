# LIBRAI design system

The kiosk serves students on an Android tablet. The administration site serves library staff on desktop, tablet, and phone. Both use the same identity, typography, colors, and control states.

## Direction

Modern-minimal, Cobalt service desk. Use the Workbench family for application views: show the task and its controls directly. The kiosk has an edge-aligned app bar, four large service choices, and a voice/search dock. Staff pages have a persistent side rail on desktop and an inline menu on mobile. The existing library symbol stays recognizable.

The previous blue surround and decorative device bezel must not return. The tablet's physical screen supplies its own frame. Keep a normal home screen within the available viewport from 600x960 portrait and 960x600 landscape upwards. Expanded transcripts, errors, keyboard use, and enlarged text may increase the page height; allow scrolling rather than hiding controls.

## Tokens and typography

The executable source is [tokens.css](tokens.css). The entry point imports it after the legacy styles, then imports `web/src/library-modern.css` for the new visual layer.

- Display: locally bundled Outfit Variable, generally weight 600-650, upright.
- Body and controls: locally bundled Source Sans 3 Variable, weight 400-600.
- Ink: midnight navy. Base: white and cool tinted grey. Accent: cobalt.
- Mint, peach, and lilac are restricted to book illustrations and semantic supporting surfaces.
- Use named color, font, space, radius, and motion tokens. No external font request is required.
- Page titles remain short, left aligned, and within two lines at phone sizes.

## Components and states

Keep Borrow, Return, Find, and Discover as the main kiosk choices. Use original SVG book illustrations for these actions, and the existing Lucide icons for compact staff controls. Decorative icons have `aria-hidden`; controls retain explicit names and visible labels.

Kiosk primary controls are at least 48 CSS px tall. Staff controls are at least 44 px, with compact table actions allowed at 40 px. Focus rings are immediate and visible. Disabled buttons retain their actual prerequisite, busy, or offline state. Errors remain visible and use text as well as color. Never animate the final result of a borrowing or return before the API confirms it.

Staff tables scroll inside their own container at narrow widths. Explicit Previous and Next controls remain available. Totals come from the dashboard API, with a dash while unavailable. Do not add invented trends, charts, readers, or transactions to production views.

## Motion

One GSAP entry sequence clarifies a screen change: up to 8 px translation and opacity, 320 ms, 25 ms stagger. It does not replay on ordinary data refreshes. Button presses compress slightly; task art moves a few pixels on hover. No ambient animation, scroll pinning, carousel, or marketing funnel is needed in the kiosk.

`prefers-reduced-motion: reduce` disables spatial entry and press effects. Startup progress and existing inline loading indicators communicate pending work without blocking navigation after completion.

## Design selection record

The GPT Taste seeded selection used seed 92 and returned Artistic Asymmetry, Outfit, inline illustration/status strip/expandable panel, and active-selection/entry motion. For application screens, this becomes left-aligned functional headings, service illustrations, connection status, and the staff menu. Marketing AIDA sections and pinned scroll scenes would conflict with the tablet's service workflow.

UI/UX Pro Max returned Swiss minimalism and accessible typography, but its FAQ landing-page structure did not match the kiosk. Only the relevant readability and touch guidance was adopted; semantic React buttons, visible focus, and reduced motion were verified separately.

## Exports

`tokens.css` is the complete portable export. Equivalent core mappings for other consumers:

```css
/* Tailwind v4 */
@theme {
  --color-paper: oklch(100% 0 0);
  --color-ink: oklch(27% .045 260);
  --color-accent: oklch(49% .21 264);
  --font-display: 'Outfit Variable', sans-serif;
  --font-body: 'Source Sans 3 Variable', sans-serif;
}
```

```json
{
  "color": {
    "paper": { "$value": "oklch(100% 0 0)", "$type": "color" },
    "ink": { "$value": "oklch(27% .045 260)", "$type": "color" },
    "accent": { "$value": "oklch(49% .21 264)", "$type": "color" }
  }
}
```

```css
/* shadcn-style semantic aliases */
:root {
  --background: var(--color-paper);
  --foreground: var(--color-ink);
  --primary: var(--color-accent);
  --primary-foreground: var(--color-on-dark);
  --border: var(--color-rule);
  --ring: var(--color-focus);
}
```
