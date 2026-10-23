# Clone of https://refire.com/int/ in this project (src/pages, src/components). Original route inventory: specs/ROUTES.md.

Source: Clone of https://refire.com/int/ in this project (src/pages, src/components). Original route inventory: specs/ROUTES.md.
Status: **measured-from-codebase**
2 routes · 2 templates · 16 unique sections

> Generated from `ia.json` by `build.mjs`. Edit the JSON, not this file.

## Shape of the site

The largest 2 templates (Home, 404 Not Found) account for 2 of 2 routes (100%). The remaining 0 routes span 0 templates.

| template | routes | share |
|---|---:|---:|
| Home | 1 | 50% |
| 404 Not Found | 1 | 50% |

## Page chrome

**1 routes carry chrome = `full`** — Home.

**1 routes carry chrome = `reduced`** — 404 Not Found.

## Sections by reuse

How widely a section is shared determines whether it belongs in a shared
component library or stays local to its page.

| section | category | templates | routes | implementation | scope |
|---|---|---:|---:|---|---|
| `chrome.preloader` | CHROME | 2 | 2 | `src/components/layout/Preloader.jsx` | Every template; Layout renders it on mount by default. |
| `chrome.header` | CHROME | 2 | 2 | `src/components/layout/Header.jsx` | Every template. |
| `chrome.contact-overlay` | OVERLAY | 2 | 2 | `src/components/layout/ContactOverlay.jsx` | Every template; opened from the header's Contact pill. |
| `chrome.cookie-pane` | CHROME | 2 | 2 | `src/components/layout/CookiePane.jsx` | Every template. |
| `chrome.cursor` | CHROME | 2 | 2 | `src/components/layout/Cursor.jsx` | Every template, on hover-capable devices. |
| `chrome.scroll-progress` | CHROME | 1 | 1 | `src/components/layout/ScrollProgress.jsx` | Only the home template; the 404 turns it off (showProgress=false). |
| `hero.video` | HERO | 1 | 1 | `src/components/home/Hero.jsx` | Only the home template. |
| `content.save-the-date` | CONTENT | 1 | 1 | `src/components/home/SaveTheDate.jsx` | Only the home template. |
| `content.about` | CONTENT | 1 | 1 | `src/components/home/AboutRefire.jsx` | Only the home template. |
| `content.key-stats` | CONTENT | 1 | 1 | `src/components/home/KeyStats.jsx` | Only the home template. |
| `media.scrolled-picture` | MEDIA | 1 | 1 | `src/components/home/ScrolledPicture.jsx` | Only the home template. |
| `media.ticker` | MEDIA | 1 | 1 | `src/components/home/Ticker.jsx` | Only the home template. |
| `content.event-details` | CONTENT | 1 | 1 | `src/components/home/Hannover.jsx` | Only the home template. |
| `media.text-image` | CTA | 1 | 1 | `src/components/home/TextImage.jsx` | Only the home template. |
| `footer.copyright` | FOOTER | 1 | 1 | `src/components/layout/Footer.jsx` | Only the home template; the 404 turns it off (showFooter=false). |
| `error.not-found` | ERROR | 1 | 1 | `src/pages/NotFound.jsx` | Only the 404 template. |

**5 shared sections** appear in more than one template and belong in a component library.

**11 single-use sections** appear in exactly one template. Building these
as "reusable" components up front would be speculative — keep them page-local
until a second caller actually appears.

## Templates

### Home — `template.home`

1 route · `/int/` · chrome: **full**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.preloader` | shared ×2 |
| 2 | CHROME | `chrome.header` | shared ×2 |
| 3 | CHROME | `chrome.scroll-progress` | page-local |
| 4 | OVERLAY | `chrome.contact-overlay` | shared ×2 |
| 5 | CHROME | `chrome.cookie-pane` | shared ×2 |
| 6 | CHROME | `chrome.cursor` | shared ×2 |
| 7 | HERO | `hero.video` | page-local |
| 8 | CONTENT | `content.save-the-date` | page-local |
| 9 | CONTENT | `content.about` | page-local |
| 10 | CONTENT | `content.key-stats` | page-local |
| 11 | MEDIA | `media.scrolled-picture` | page-local |
| 12 | MEDIA | `media.ticker` | page-local |
| 13 | CONTENT | `content.event-details` | page-local |
| 14 | CTA | `media.text-image` | page-local |
| 15 | FOOTER | `footer.copyright` | page-local |

### 404 Not Found — `template.not-found`

1 route · `/int/404` · chrome: **reduced**

| # | category | section | |
|---:|---|---|---|
| 1 | CHROME | `chrome.preloader` | shared ×2 |
| 2 | CHROME | `chrome.header` | shared ×2 |
| 3 | OVERLAY | `chrome.contact-overlay` | shared ×2 |
| 4 | CHROME | `chrome.cookie-pane` | shared ×2 |
| 5 | CHROME | `chrome.cursor` | shared ×2 |
| 6 | ERROR | `error.not-found` | page-local |

## Section reference

### CHROME

_Fixed, site-wide UI rendered by the shared Layout around every page's content (header, progress bar, cookie pane, cursor, preloader)._

**`chrome.preloader`** — Full-screen loading overlay with a 0–100% progress line and counter and blinking dots. It fades and blurs out, then unmounts and hands off to the page's entrance animation.

· Every template; Layout renders it on mount by default. · appears on 2 routes · implemented by `src/components/layout/Preloader.jsx`

**`chrome.header`** — Fixed top bar with the Refire logo, a live HH:MM GMT clock and a Contact pill that opens the contact overlay. It uses a difference blend mode, never hides on scroll, and has no nav menu. On the 404 it renders near-invisible white-on-white, matching the original.

· Every template. · appears on 2 routes · implemented by `src/components/layout/Header.jsx`

**`chrome.scroll-progress`** — 2px fixed bar showing smoothed page scroll progress, drawn with a difference blend.

· Only the home template; the 404 turns it off (showProgress=false). · appears on 1 routes · implemented by `src/components/layout/ScrollProgress.jsx`

**`chrome.cookie-pane`** — Small cookie notice that fades in on mount and has a Close button. It stays mounted with pointer events off after closing.

· Every template. · appears on 2 routes · implemented by `src/components/layout/CookiePane.jsx`

**`chrome.cursor`** — Custom cursor that follows the pointer with easing, shrinks on press and fades when the pointer leaves the window.

· Every template, on hover-capable devices. · appears on 2 routes · implemented by `src/components/layout/Cursor.jsx`

### OVERLAY

_Modal or dialog UI opened on demand above the page (the contact overlay). Utility UI, not page content._

**`chrome.contact-overlay`** — Full-screen contact form: department select, name/email/message inputs, phone numbers (tel links) and opening hours. Page scroll is locked while it is open, and on mobile it scrolls internally. Submission is blocked because the real endpoint is unknown.

· Every template; opened from the header's Contact pill. · appears on 2 routes · implemented by `src/components/layout/ContactOverlay.jsx`

### HERO

_The first full-viewport block of a page._

**`hero.video`** — Full-viewport muted, looping background video with the 'A New → Generation / of fuel cell systems' headline, side labels and a 'view our brochure' link to the local PDF.

· Only the home template. · appears on 1 routes · implemented by `src/components/home/Hero.jsx`

### CONTENT

_Text-led editorial blocks: headings, paragraphs, stats, accordions._

**`content.save-the-date`** — Numbered '01 Save the date' block: a decorative line, a header row and one large paragraph that reveals word by word.

· Only the home template. · appears on 1 routes · implemented by `src/components/home/SaveTheDate.jsx`

**`content.about`** — '(About Refire)' title next to a short company description.

· Only the home template. · appears on 1 routes · implemented by `src/components/home/AboutRefire.jsx`

**`content.key-stats`** — Row of three key-figure cards, each with a label, index number, title and large value.

· Only the home template. · appears on 1 routes · implemented by `src/components/home/KeyStats.jsx`

**`content.event-details`** — Hannover Messe event block: title and details, a 5-item accordion, and contact email links (mailto).

· Only the home template. · appears on 1 routes · implemented by `src/components/home/Hannover.jsx`

### MEDIA

_Image- or motion-led blocks whose main job is visual (scroll-linked picture, marquee)._

**`media.scrolled-picture`** — Full-width photo whose side inset shrinks from 2% to full bleed while it zooms from 1 to 1.1, both tied to scroll position.

· Only the home template. · appears on 1 routes · implemented by `src/components/home/ScrolledPicture.jsx`

**`media.ticker`** — 'Visit Us —' marquee that auto-scrolls at about 36px/s, can be dragged with momentum, and pauses off-screen.

· Only the home template. · appears on 1 routes · implemented by `src/components/home/Ticker.jsx`

### CTA

_Conversion blocks: a closing pitch whose job is to send the visitor to an action (here, the brochure download)._

**`media.text-image`** — Two-column block pairing a WebGL image (mouse-driven distortion plus a slide/zoom entrance at about 70% in view) with a title, text and a brochure link.

· Only the home template. · appears on 1 routes · implemented by `src/components/home/TextImage.jsx`

### FOOTER

_The closing row at the bottom of a page._

**`footer.copyright`** — Bottom row with the copyright line and a Back To Top button.

· Only the home template; the 404 turns it off (showFooter=false). · appears on 1 routes · implemented by `src/components/layout/Footer.jsx`

### ERROR

_Body content for error states._

**`error.not-found`** — Stock 'Next.js-style' 404 body, centered in the viewport: '404' with a right divider and 'This page could not be found.' It uses the system font stack, not SuisseIntl, and inverts in OS dark mode.

· Only the 404 template. · appears on 1 routes · implemented by `src/pages/NotFound.jsx`
