Source: https://refire.com/int/

# Refire /int/ home page: clone spec

Measured live with Playwright (Chromium) on 2026-10-22 at 1440x900, 1280x800 and 390x844, and cross-checked against the saved bundles in `Refire_files/` (`887c3946dd796d39.css` = global/components, `36daa2ec82bd5e7c.css` = page sections, `_app-6a7d6076843df9fb.js` = runtime/animation system, `index-0bba0de55cdcb42c.js` = page content + section components, `fb7d5399-…js` = three.js r150).

Assets: see `ASSET_MANIFEST.json`. Reference screenshots are in `reference/`:
- `desktop-1440-fullpage.png`: stitched from 8 viewport shots at scroll 0/899/1799/2699/3599/4499/5399/5697. The fixed header shows up once per 900px band because the page uses virtual scrolling. The cookie pane is visible in these shots.
- `desktop-1440-viewport-NN-scrollY.png`: the individual viewport shots, all with reveals finished.
- `desktop-1440-contact-overlay.png`: Contact overlay open.
- `mobile-390-fullpage.png` and `mobile-390-viewport-NN-*.png` (cookie pane closed). In the band from 4535 to 4653 the WebGL image is still black because it hadn't animated in yet (see 3.8).

---

## 0. Global system

### 0.1 Stack observed
- Next.js (pages router), React, CSS Modules plus styled-jsx (the preloader uses styled-jsx).
- **GSAP 3.8.0** (`window.gsapVersions`), with the Club plugins **CustomEase, DrawSVGPlugin, InertiaPlugin, Draggable** and a **SplitText**-style splitter (their own React splitter, see 4.2). **No ScrollTrigger usage on this page.** The string appears in the bundle, but scroll is handled by a custom engine.
- **Custom virtual smooth-scroll engine.** This is not Lenis or Locomotive. `body` is `position:fixed`, `#__next` is `100vw x 100vh; overflow:hidden`. Each top-level section (`.backface` wrapper) gets its own `transform: matrix(1,0,0,1,0,-Y)`, and sections outside the viewport are culled (they stop updating). Wheel delta maps 1:1 to target scroll (120 wheel units → 120px measured). Each GSAP tick, current scroll lerps to target with blend **0.1**: `current = current*(1-0.1) + target*0.1`. Touch/drag swipe raises the blend toward 0.7 while dragging and uses 0.054 with velocity-based inertia after release. Keys: ArrowDown/Up = ±100px, Space = +200px.
  - **Build recommendation:** use Lenis (`lerp: 0.1, wheelMultiplier: 1, smoothWheel: true`) on native scroll. It looks identical, and IntersectionObserver plus scroll-progress math stays simple.
- **three.js r150** (`window.__THREE__ = "150"`) for one WebGL image (3.8).
- **No IntersectionObserver.** In-view detection runs from the scroll engine's per-frame bounds (thresholds in 4.1).
- Native `<video>` for the hero background.

### 0.2 Breakpoints and the fluid unit
All sizes are fluid, written as `calc((N / var(--gfs)) * 100 * 1vw)`. This spec writes that as **F(N)**.

| Range | `--gfs` | F(N) in px | `--gap-content` (side gutter) |
|---|---|---|---|
| > 834px (desktop) | 1920 | N x vw / 1920 → **1440: 0.75N**, **1280: 0.6667N** | F(30) → 22.5px @1440, 20px @1280 |
| 521–834px (tablet) | 744 | N x vw / 744 | F(20) |
| ≤ 520px (mobile) | 375 | N x vw / 375 → **390: 1.04N** | F(10) → 10.4px @390 |

Media queries are `max-width:834px` and `max-width:520px`. Hover rules sit under `@media (hover:hover)`, and `:active` mirrors them under `@media (hover:none)`. Many small text sizes are clamped `max(12px, F(N))`. Keep those clamps; they are why some 1280 values stay at 12px.

Tailwind tip: define a plugin or CSS var `--gfs` with the same breakpoints and a helper `f(N)`, e.g. `calc(N / var(--gfs) * 100vw)`, then use arbitrary values.

### 0.3 Color tokens (`:root`, verbatim)
```
--primary-color:#fefefe;  --dark-color:#060508;  --alt-dark-color:#0e0e0e;  --grey-color:#c8c8c8;
--alt-dark-grey2:#8e8e8e; --dark-grey-color:#8b8b8b; --alt-dark-grey-color:#383739; --alt-grey-color:#848484;
--darkness-grey-color:#555; --light-grey-color:silver; --light-dark-color:#2a2a2a; --most-dark-color:#383838;
--alt-light-grey-color:#3d3c3e; --code-dark-color:#4f4f4f; --red-color:#c39797; --gb-color:#828183;
--most-light-grey:#d0d0d0; --tr-grey-color:rgba(6,5,8,.15); --ttf:ease; --td:0.3s
```
Used on this page:
- Page/section background #060508 (every section after the hero sets `background-color: var(--dark-color)`; `Home_root` itself is #fefefe underneath).
- Text #fefefe.
- Muted labels #8b8b8b.
- Light grey labels #c8c8c8.
- Dim headings #383739 ("(About Refire)", "Hannover Messe", Hannover address subtitle).
- Card bg #0e0e0e.
- Accordion body #888888 (literal `#888`).
- Footer rule #555555.
- Hero center text #8e8e8e with `mix-blend-mode:difference`.
- Cookie pane #fefefe bg / #060508 text, link #d0d0d0.
- Contact form select border #828183.
- Submit hover bg #383838.
- Selection: `::selection { background:#a59e99 }` (later rule wins over the earlier #004fe4).

### 0.4 Fonts
```css
@font-face{font-family:SuisseIntl;src:url(/assets/fonts/SuisseIntl-Thin.woff2) format("woff2"),url(...-Thin.woff) format("woff");font-weight:200;font-style:normal;font-display:swap}
@font-face{font-family:SuisseIntl;src:url(/assets/fonts/SuisseIntl-Light.woff2) ...;font-weight:300;...}
@font-face{font-family:SuisseIntl;src:url(/assets/fonts/SuisseIntl-Regular.woff2) ...;font-weight:400;...}
@font-face{font-family:SuisseIntl;src:url(/assets/fonts/SuisseIntl-Medium.woff2) ...;font-weight:500;...}
/* SuisseIntl Mono 400 is declared upstream but unused on this page */
```
- Body stack: `font-family: SuisseIntl, Arial, Helvetica, sans-serif`.
- Body base: `font-size:F(16); line-height:F(20)`, i.e. 12px/15px @1440, 10.67/13.33 @1280, 16.64/20.8 @390.
- Body: `color:#060508; background:#fefefe; text-rendering:optimizeLegibility`, scrollbar hidden.
- Weights used: 200 (stat numbers), 300 (hero title, hero center text, big paragraph, preloader %), 400 (everything else), 500 (key-card top info).

### 0.5 Reset essentials (from global CSS)
- `box-sizing:border-box` everywhere.
- `h1–h6 {margin:0; font-size:inherit; font-weight:inherit}`.
- `p, figure {margin:0}`.
- Lists unstyled.
- Buttons fully reset (`background:transparent; border:none; font:inherit; color:inherit; letter-spacing:inherit`).
- `a {color:inherit; text-decoration:none}`.
- `svg {display:block; width:100%; height:100%; fill:currentColor}`. This matters because many icons rely on it.
- `img, video {display:block}`.

### 0.6 Layering (z-index)
| Layer | z | Position |
|---|---|---|
| Custom cursor | 103 | fixed |
| Preloader | 100 | fixed, 100vw x 100vh |
| Header | 99 | fixed, `mix-blend-mode:difference` |
| Page progress bar | 99 | fixed top, `mix-blend-mode:difference` |
| Cookie pane | 99 | fixed bottom-right |
| Contact overlay | 89 | fixed full-screen |
| Hero overlays (decor, scroll, cursor info) | 2 | absolute within hero |

---

## 1. Typography: every text role

Values are font-size / line-height; unitless line-heights are multipliers. Font is SuisseIntl in every case. 1440 and 390 values were confirmed against computed styles. 768 values are computed from the CSS (tablet was not loaded live).

| Role | Weight | Transform | Color | Letter-spacing | 1440 (fs / lh) | 1280 | 768 (tablet) | 390 |
|---|---|---|---|---|---|---|---|---|
| Preloader percent (00%..100%) | 300 | none | #fefefe | normal | 56.25px / 1 | 50px / 1 | 61.94px / 1 | 37.44px / 1 |
| Preloader decor text | 400 | uppercase | #c8c8c8 | .3em | 10.5px / 1 | 9.33px / 1 | 14.45px / 1 | 12.48px / 1 |
| Preloader '++' | 400 | none | #c8c8c8 | .3em | 15px / 1 | 13.33px / 1 | 20.65px / 1 | 16.64px / 1 |
| Header time 'HH:MM GMT' | 400 | uppercase | #fefefe (blend difference) | normal | 12px / 15px | 10.67px / 13.33px | 16.52px / 20.65px | 12.48px / 1 |
| Header Contact pill | 400 | uppercase | #fefefe | normal | 12px / 1 | 10.67px / 1 | 16.52px / 1 | 12.48px / 1 |
| Hero '+ +' decor | 400 | uppercase | #fefefe | normal | 15px / 1.2 | 13.33px / 1.2 | 20.65px / 1.2 | 16.64px / 1.2 |
| Hero 'Scroll' | 400 | uppercase | #8b8b8b | .3em | 12px / 22px | 12px / 22px | 14.45px / 24.77px | 12.48px / 1 |
| Hero cursor info 'X . n / Y . n' | 400 | uppercase | #c8c8c8 | .3em | 12px / 1.2 | 12px / 1.2 | 14.45px / 1.2 | 12.48px / 1.2 |
| Hero subtitle 'introducing' | 400 | uppercase | #c8c8c8 | .3em | 12px / 22px | 12px / 22px | 14.45px / 24.77px | 12.48px / .9 |
| Hero title 'A New / Generation' | 300 | capitalize | #fefefe | normal | 117.75px / 109.5px | 104.67px / 97.33px | 84.65px / .9 | 57.2px / .9 |
| Hero center text 'of fuel cell systems' | 300 | first letter of each word uppercase (see 3.1) | #8e8e8e + mix-blend-mode:difference | .05em | 31.5px / 1 | 28px / 1 | 37.16px / 43.35px | 18.72px / .95 |
| Hero link 'view our brochure' | 400 | capitalize | #fefefe | normal | 18px / 1 | 16px / 1 | 18.58px / 1 | 12.48px / 1 |
| Section title '01 / Save the date' | 400 | uppercase | #fefefe | normal | 12px / 22px | 12px / 22px | 14.45px / 24.77px | 12.48px / 24.96px |
| TextSection subtitle 'Refire Group' | 400 | uppercase | #8b8b8b | normal | 12px / 22px | 12px / 22px | 16.52px / 24.77px | 12.48px / 24.96px |
| Big paragraph (Save the date) | 300 | none | #fefefe | normal | 71.25px / 75px | 63.33px / 66.67px | 37.16px / 39.23px | 24.96px / 26px |
| '(About Refire)' title | 400 | uppercase | #383739 | normal | 45px / 1.05 | 40px / 1.05 | 37.16px / 1.05 | 24.96px / 1.05 |
| About Refire description | 400 | none | #fefefe | normal | 18px / 1.375 | 16px / 1.375 | 14.45px / 1.375 | 12.48px / 1.4 |
| KeyCard top info 'KEY STAT / 001' | 500 | uppercase | #8b8b8b | normal | 12px / 1.5 | 10.67px / 1.5 | 16.52px / 1.5 | 12.48px / 1.5 |
| KeyCard label 'Vehicles Deployed' | 400 | capitalize | #8b8b8b | normal | 18px / 1.38 | 16px / 1.38 | 20.65px / 1.38 | 14.56px / 1.38 |
| KeyCard value '4K+' | 200 | uppercase | #fefefe | normal | 141px / 1 | 125.33px / 1 | 175.48px / 1 | 104px / 1 |
| Ticker 'Visit Us —' | 400 | capitalize | #fefefe | -.04em | 187.5px / 1.05 | 166.67px / 1.05 | 103.23px / 1.05 | 66.56px / 1.05 |
| Hannover title 'Hannover Messe' | 400 | none | #383739 | normal | 45px / 48.75px | 40px / 43.33px | 37.16px / 38.19px | 24.96px / 27.04px |
| Content title 'BOOTH C45 ...' | 400 | none | #fefefe | normal | 45px / 48.75px | 40px / 43.33px | 28.9px / 37.16px | 24.96px / 27.04px |
| Content subtitle (address) | 400 | none | #383739 | normal | 13.5px / 24.75px | 12px / 22px | 12.39px / 16.52px | 12.48px / 1.4 |
| Content text (founded in 2015...) | 400 | none | #fefefe | normal | 18px / 24.75px | 16px / 22px | 14.45px / 17.55px | 12.48px / 1.4 |
| Accordion title '17 April, PM' (h5) | 400 | none | #fefefe | normal | 28.5px / 1 | 25.33px / 1 | 20.65px / 1 | 16.64px / 1 |
| Accordion body | 400 | none | #888888 | normal | 18px / 1.375 | 16px / 1.375 | 12.39px / 1.375 | 12.48px / 1.375 |
| Contacts 'Media liaison: ...' | 400 | none | #fefefe | normal | 12px / 1 | 12px / 1 | 16.52px / 1 | 12.48px / 1 |
| TextImage title | 400 | capitalize | #fefefe | normal | 45px / 1.05 | 40px / 1.05 | 33.03px / 1.05 | 24.96px / 1.11 |
| TextImage body | 400 | none | #fefefe | normal | 18px / 1.375 | 16px / 1.375 | 12.39px / 1.4 | 12.48px / 1.4 |
| LinkArrow 'VIEW OUR BROCHURE' | 400 | uppercase | #fefefe | normal | 18px / 1 | 16px / 1 | 18.58px / 1 | 12.48px / 1 |
| Footer copyright row | 400 | col1 uppercase, col2/3 capitalize | #fefefe | normal | 15px / 1.2 | 13.33px / 1.2 | 16.52px / 1.2 | 12.48px / 1.2 |
| Cookie pane | 400 | none | #060508 on #fefefe | normal | 12px / 18px | 10.67px / 16px | 16.52px / 24.77px | 12.48px / 14.56px |

Source formulas (desktop / ≤834 / ≤520). Use these, not the px values, so intermediate widths come out right:
- Hero title F(157)/F(146), then F(82)/.9, then F(55)/.9.
- Hero center F(42)/1, then F(36)/F(42), then F(18)/.95.
- Big paragraph F(95)/F(100) wt300, then F(36)/F(38), then F(24)/F(25).
- KeyCard value F(188), then F(170), then F(100).
- Ticker F(250), then F(100), then F(64).
- Section-level 60px roles (About title, Hannover title, Content title, TextImage title) are F(60).
- Accordion title F(38), then F(20), then F(16).
- All "12px" small labels are `max(12px, F(14|16))`.

---

## 2. Fixed chrome (outside the scrolling content)

### 2.1 Preloader (first paint; dark full-screen)
Structure: `root` (fixed, 100vw x 100vh, bg #060508, color #fefefe, z 100), containing `container` (flex, align-items:flex-end, full size), containing `wrap`.
- `wrap`: `--p` CSS var 0→1, `--offset:F(220)` (F(160) tablet, F(100) mobile), padding-x F(30) (F(20) / F(10)). Measured padding 22.5px @1440.
  - `root` (inner): flex column, justify-content center, full height. Holds:
    - `progressLine`: width 100%, height 1px, overflow hidden. The child span is #fefefe and slides in from the left with `transform: translateX(calc((1 - var(--p)) * -100%))`. Measured at y=415 @1440x900, so the 70px line+text group is vertically centred.
    - `progress`: `margin-top:F(17)` (F(14) / F(8)), font F(75) wt300 lh1, text-align right, `transform: translateX(calc((1 - var(--p)) * -100%))`.
      - Contains a hidden "00%" spacer (`width: var(--offset)`) and `.numbers`, which shows the integer counter + "%". `.numbers` is `position:absolute; right:0; bottom:0; transform: translateX(calc((1 - min(max(var(--p)/.07,0),1)) * 56%))`. The divisor is `.18` on tablet and `.23` on mobile.
- `decor` (absolute full-size, flex column space-between):
  - padding F(24) (F(10) on mobile).
  - font F(14) lh1, letter-spacing .3em, uppercase, color #c8c8c8.
  - pointer-events none.
  - Top row (flex space-between): left `++` (F(20), ls .3em); right `1.00784` and `1.00811` (margin-right F(29) between them).
  - Bottom row: left `initializing` followed by three `.` dots; right `Creating a Sustainable Future`.
  - On ≤520 the "Creating a Sustainable Future" item is `display:none` and "initializing..." is centred (`margin:0 auto`).
- Dots animation: `@keyframes showHideDot {0%{opacity:0} 50%{opacity:1} 60%{opacity:1} 100%{opacity:0}}`, `2.5s ease-in-out infinite`, delays .2s/.4s/.6s.
- Progress logic: progress = fraction of `<img>` elements that have decoded (0 images → 1 after 300ms). On each change, GSAP tweens `--p` to the progress over **4s `sine.inOut`**. The counter tweens 0→100 integer (`roundProps`) over the same 4s with `sine.inOut`. When it reaches 1:
  - preloader root `opacity→0`, **duration 1s, delay .2s, sine.inOut**, then unmount;
  - simultaneously the line+counter block goes `opacity:0, filter:blur(20px)` over **2s**.
  - In practice the preloader runs about 4.2–5s.
- After unmount, the page becomes "visible" and the hero entrance runs (3.1).

### 2.2 Header (`Header_root`)
- `position:fixed; top:0; width:100%; z-index:99`.
- `padding: F(30) 0` (F(20) tablet, F(18) mobile), giving 22.5px @1440, 20px @1280, 18.72px @390. Height 77px @1440, 68.8 @1280, 68 @390.
- `color:#fefefe; mix-blend-mode:difference; pointer-events:none`; links/buttons get `pointer-events:auto`.
- `transform:translateZ(0)`.
- **Sticky, never hides on scroll** (transform stays `matrix(1,0,0,1,0,0)` throughout). No burger/menu on this page.
- `inner`: flex, align-items center, `padding: 0 var(--gap-content)`.
  - Left: **logo** button, `F(159) x F(23)` = 119.25x17.25 @1440, 106x15.3 @1280, mobile `F(104) x F(15)` = 108.2x15.6 @390. SVG fill currentColor. Click closes the Contact overlay; it does not navigate.
  - Right (`margin-left:auto`, flex):
    - **Time**: `Intl.DateTimeFormat('en-GB',{hour:'2-digit',minute:'2-digit',hour12:false,timeZone:'Atlantic/Reykjavik',timeZoneName:'short'})`, then take the part before the first comma, which renders e.g. "19:08 GMT". Updates every 1s. Placeholder before mount: "weekday, date time GMT". Font F(16)/F(20) uppercase (mobile max(12px,F(12))/1).
    - **Contact pill** (`PillButton`): `margin-left:F(42)` (F(38) / F(20)).
      - Box: `padding: F(14) F(22) F(10) F(20); width:F(116); border-radius:F(150)`, font F(16)/1 uppercase, centred. Measured 87x32 @1440 at x=1330.5. Mobile: padding `F(9) F(10) F(6)`, font F(12), width F(78) → 81.1x30.5 @390.
      - Text toggles "Contact" ↔ "Close" and opens/closes the Contact overlay. The swap is a char split-text transition, 400ms.
      - Outline: absolute SVG (viewBox 0 0 116 39) filling the button, `fill:transparent; stroke:#FEFEFE; stroke-dasharray:360 360; stroke-dashoffset:-640; transform:rotate(180deg); transition: stroke-dashoffset 1.2s cubic-bezier(.86,0,.12,1)`. At rest only part of the outline is drawn, appearing as a line under the text (see `desktop-1440-viewport-00`). **Hover:** `stroke-dashoffset:-438` draws the full pill (see viewport-02).

### 2.3 Page progress bar (`PageProgress`)
- `position:fixed; top:0; left:0; width:100%; height:2px; z-index:99`.
- `background: rgba(6,5,8,.1); mix-blend-mode:difference`.
- Inner bar: #fefefe, `transform-origin:left; transform:scaleX(calc(var(--p)/100))`. `--p` is page scroll progress 0–100, set every scroll frame.

### 2.4 Custom cursor (desktop / non-touch)
- `cursor`: `position:fixed; top:0; left:0; z-index:103; pointer-events:none`, translated to the mouse position.
- `inner`: 74x74px, centred on the point (`translate(-50%,-50%) scale(calc(1 - var(--mD)))`).
- `circle`: 100% size, `background:hsla(0,0%,71%,.25)` (rgba(181,181,181,.25)), `backdrop-filter:blur(10px)`, `border-radius:50%`, `transform:scale(var(--scale))` with `--scale:.4325`, so the visible circle is 32px. `transition: background-color .4s ease-in-out, transform .4s ease-in-out`.
- Follow: lerp with amount **0.2** per frame toward the real mouse position.
- Mouse down: `--mD` tweens to .2 over .4s (shrinks to 80%); mouse up tweens back to 0.
- Leaving the window fades opacity to 0 over .3s `power2.out`; re-entering fades to 1.
- The native cursor is not hidden by CSS.

### 2.5 Cookie pane (first visit, cookie `accept`)
- `position:fixed; bottom:0; right:0; z-index:99`.
- `width:F(430)` (322.5 @1440), `padding:F(26)` (19.5), bg #fefefe, color #060508, font F(16)/F(24) (12/18 @1440), flex space-between, align-items flex-start.
- Title "We use cookies to make things better", `width:F(276)`.
- Links block `margin-left:F(42)`: one "Close" button.
  - Style: `color:#d0d0d0; padding-left:F(9)`, a 4px (F(4)) dot `::after` at the left, opacity 0.
  - Hover: color #060508, dot opacity 1, `transition .3s ease`.
- Mobile: width 100%, font max(12px,F(12)) / max(14px,F(14)), padding F(18). Measured 390x52 at bottom.
- Fade in/out (Fade animation, 700ms). Close sets cookie `accept=true`, expiring in 1 day per the code's math.

### 2.6 Contact overlay (`ContactPopup`, opened by the header pill)
See `reference/desktop-1440-contact-overlay.png`.
- Container: `position:fixed; z-index:89; top:0; left:0; width:100%`.
  - Vars: `--bg-color:#060508; --main-color:#fefefe; --lines-color:#fefefe`.
  - Enter/exit: CSS fade, `opacity` and `visibility` over .5s ease.
  - The body is a flex column with min-height 100vh; the content has `margin-top:auto`, so it sits at the bottom.
- `Contact_root`: flex space-between, `padding: F(100) var(--gap-content) F(54)` (75 / 22.5 / 40.5 @1440), font max(12px,F(16)) / max(22px,F(24)).
  - Mobile: column, padding `F(124) gap F(10)`.
- Left column `width:F(800)` (600):
  - Title is an `<a href="mailto:test@test.en" target=_blank>` (placeholder email on the live site). Two lines, "Contact" + arrow, then "Us Today".
    - Font F(176) lh1.02, ls -.01em, capitalize, `margin-bottom:F(104)`. Measured 132px / 134.64px, mb 78.
    - Arrow SVG `F(89) x F(76)`, `margin-left:F(48)`.
    - Hover: opacity .6 (.3s ease).
    - Tablet F(80) mb F(44) (arrow F(36)xF(30), ml F(20)); mobile F(40) mb F(30) (arrow F(19)xF(16), ml F(15)).
  - Contact form block (`max-width:F(373)`): subtitle "CONTACT FORM" (#8b8b8b uppercase), then text `margin-top:F(10)`.
  - List (`display:flex; margin-top:F(84)`, items `margin-right:F(85)`): "PHONE US" block and "HOURS" block.
- Right column `width:F(783)` (587.25), `padding-top:F(30)`. The form is a grid with `row-gap:F(52)` (39px):
  - Row 1: Select "Select a department you’d like to reach*" with options Media / Sales / General.
    - Field: `padding-bottom:F(19); padding-right:F(24); border-bottom:2px solid #fefefe`; chevron icon F(16)xF(10) at top F(12) right 0.
    - Dropdown: `top:F(52)`, border 2px #828183, bg #060508.
    - Options: padding F(20) F(25), separators 2px #828183; hover underline `scaleX 0→1`, `.6s cubic-bezier(.165,.84,.44,1)`.
    - Open state rotates the icon 180deg.
  - Rows 2–3: two columns (`column-gap:F(40)`): "First Name*" | "Last Name*", then "Email*" | "Subject*".
  - Row 4: "Message*" textarea, `height:F(315)` (236.25).
  - All fields: font F(28)/1.18 (21px/24.78px @1440), `padding-bottom:F(19)`, `border-bottom:2px solid #fefefe`; placeholders are overlay divs (opacity .5 when focused).
  - Footer `margin-top:F(30)`, flex space-between, align-items flex-end:
    - Note "*By submitting, the data provided will be used to perform your request according to the Privacy Policy": `width:F(382)`, #8b8b8b, F(16)/F(24).
    - **Submit** pill (`BlackButton`): padding F(17) F(45), radius F(100), ls .15em, F(16)/F(24), uppercase. White bg (#fefefe) with #060508 text, measured 124x44 @1440.
      - Hover: dark circle (#383838, 200% size, `border-radius:100%`) slides from translateY(100%) to 0 over .6s.
      - At the same time the label slides out `translate3d(0,-400%,1px) rotate(30deg)` and a white duplicate label slides in from `translate3d(0,400%,1px) rotate(30deg)`, both `.6s cubic-bezier(.36,.28,0,.99)`.
      - Rest-state entrance: bg `transition: transform 1.5s cubic-bezier(.19,.39,0,.99) 2s`; label `1s ... 2.1s`.
- Copy (verbatim):
  - Title: `contact` / `us today` (rendered capitalized: "Contact →" / "Us Today").
  - `Contact form` / `Send us a message and we’ll get back to you as soon as possible.`
  - `Phone us` / `Germany +1 790 790 9238` / `France +1 893 233 2030`
  - `Hours` / `Monday - Friday 8:00AM - 8:00PM` / `Saturday & Sunday Closed`
  - Form labels: `Select a department you’d like to reach*`, `Media`, `Sales`, `General`, `First Name*`, `Last Name*`, `Email*`, `Subject*`, `Message*`, `*By submitting, the data provided will be used to perform your request according to the Privacy Policy`, `submit`.
- Input names: `fname, lname, email, subject, message` (all type text, plus a textarea).

---

## 3. Sections in DOM order

All sections live in `Home_root` (`position:relative; background:#fefefe; color:#060508`). Every section after the hero has `margin-top:-1px`, which hides seams between the 1px-overlapping dark blocks.

Section geometry (y = top within the page, h = height, px):

| # | Section (class) | 1440 y / h | 1280 y / h | 390 y / h | Padding desktop / ≤834 / ≤520 |
|---|---|---|---|---|---|
| 1 | Hero (`Hero_root`) | 0 / 900 | 0 / 800 | 0 / 844 | 100vh; padding-left gap |
| 2 | Save the date (`Home_aboutSection`) | 899 / 701.8 | 799 / 629 | 843 / 375 | F(120) gap F(118) / F(80) gap F(76) / F(53) gap F(45) |
| 3 | About Refire (`Home_headerSection`) | 1599.8 / 271.5 | 1427 / 241.3 | 1217 / 239.1 | F(118) 0 F(112) / F(76) 0 F(55) / F(45) 0 F(30) |
| 4 | Key stats (`Home_keystats`) | 1870.3 / 759.8 | 1667.3 / 675.3 | 1455.1 / 1246.9 | F(112) 0 F(156) / F(55) 0 F(78) / F(30) 0 F(48) |
| 5 | Scrolled picture (`Home_pictureSection`) | 2629 / 1122 | 2341.6 / 997.3 | 2701 / 665.4 | F(156) 0 F(140) / F(78) 0 F(68) / F(48) 0 F(40) |
| 6 | Ticker (`Home_tickerSection`) | 3750 / 421.9 | 3338 / 375 | 3365.5 / 153.1 | F(140) 0 F(160) / F(68) 0 F(65) / F(40) 0 F(40) |
| 7 | Hannover (`Home_hannover`) | 4170.9 / 1176.8 | 3711.9 / 1047.9 | 3517.5 / 970.7 | F(160) 0 F(205) / F(65) 0 F(75) / F(40) 0 F(46) |
| 8 | Text + WebGL image (`Home_textImageSection`) | 5346.6 / 1097.3 | 4758.9 / 975.3 | 4487.2 / 892.2 | F(205) 0 F(115) / F(75) 0 F(75) / F(46) 0 F(70) |
| 9 | Footer (`Home_footer`) | 6442.9 / 155.5 | 5733.2 / 138.3 | 5378.4 / 120 | F(115) gap 0 / F(75) gap 0 / F(70) gap 0 |
| | **Total page height** | **6598.4** | **5871.5** | **5498.4** | |

All sections 2–9: `background:#060508; color:#fefefe`.

### 3.1 Hero
Copy:
- `+ +`
- `Scroll`
- `x . {mouseX}` / `y . {mouseY}` (live cursor coords, integers)
- `introducing`
- Title lines: `A New` (followed by arrow icon) and `generation`. The source string is `"<strong>A New</strong> generation"`; it is split on `</strong>`, and the arrow goes after the first chunk.
- `of fuel cell systems`
- Link: `view our brochure` → `/int/files/refire.pdf` (`target=_blank rel="noopener noreferrer"`), followed by a chevron.

Layout:
- `Hero_root`: `position:relative; display:flex; flex-direction:column; justify-content:flex-end; height:100vh; padding-left:var(--gap-content); background:#060508; color:#fefefe`.
- `Hero_bg`: absolute inset 0, z 0. Contains `<video>` absolute 100%x100%, `object-fit:cover`, `muted loop autoplay playsinline preload="auto" poster="/int/images/poster.png"`, contextmenu prevented. The video plays only while the hero is in view and the page is visible (after the preloader); otherwise it is paused.
- Absolute overlays (z 2):
  - `decor` "+ +": top F(151) (113.25 @1440), left gap. Font F(20)/1.2; mobile top F(69) (71.8 @390), font F(16).
  - `scroll` "Scroll": top F(181) (135.75), left gap, #8b8b8b, max(12px,F(14)) / max(22px,F(24)), ls .3em.
    - Tablet top F(166).
    - Mobile: `top:auto; bottom:F(9)`, font max(12px,F(12)) lh1, `mix-blend-mode:difference` (y=822 @390).
  - `position` (CursorInfo): top F(151), right F(20) (x=1335, w=90 @1440).
    - Box: `padding-left:F(17); width:max(90px,F(110))`, ls .3em, lh1.2, #c8c8c8, two spans stacked "X . 0" / "Y . 0", with a 4px dot `::after` at top F(6) left 0.
    - Tablet top F(100) right F(20); mobile top F(80) right F(10).
    - **Shown only on non-touch devices.** Values are integer mouse clientX/Y, updated on mouse move.
- `content` (flex, align-items flex-end; mobile flex-wrap):
  - `left`: flex, align-items flex-end, padding-bottom F(12) (9).
    - Tablet: width F(403), column, align-items flex-start.
    - Mobile: padding-bottom 0, margin-bottom F(42) (43.68).
    - `leftHeader`: `flex:0 0 auto; width:F(765)` (573.75). Tablet/mobile width 100% (margin-bottom F(6) / F(10)).
      - `subtitle` "introducing": #c8c8c8, uppercase, ls .3em, `padding-left:F(18)`, `margin-bottom:F(19)`, with a 4px round dot `::after` (top 50%, left 0, currentColor). Tablet pl F(11); mobile pl F(6), mb F(17), dot 2px.
      - `title`: weight 300, capitalize, F(157)/F(146). Each line is an `inline-flex; align-items:center; flex-wrap:wrap` div.
        - Arrow icon after "A New": `margin-left:F(44); margin-top:F(14); width:F(62); height:F(52)` (46.5x39 @1440, x=393).
        - Tablet: F(38)xF(32), ml F(30), mt F(14). Mobile: F(25)xF(21), ml F(13), mt F(8).
    - `centerText` (SplitText, chars): `margin-left:F(178)`, `max-width:F(263)` (197.25), `padding-bottom:F(12)`.
      - Font F(42)/1, ls .05em, weight 300, color #8e8e8e, `mix-blend-mode:difference`. Over the teal video this renders reddish-brown; see the screenshot.
      - Rule `.Hero_centerText>div>div:first-child{text-transform:uppercase}` uppercases the first letter of each word, so it renders "Of Fuel Cell / Systems".
      - Measured x=729.8, y=819, 197.3x72 @1440.
      - Tablet: ml 0, pb 0, F(36)/F(42). Mobile: F(18)/.95, ml 0 (x=10.4, y=748 @390).
  - `right`: `display:flex; align-items:center; margin-left:auto`. Mobile: width 100%, justify-content flex-end.
    - `link`: `position:relative; inline-flex; align-items:center; padding:F(27)` (20.25); F(24)/1; capitalize; overflow hidden. Measured 223.2x58.5 flush to the bottom-right corner @1440.
      - Glass background `::after`: `background:hsla(0,0%,100%,.1); backdrop-filter:blur(F(10)); border-radius:F(15) 0 0 0` (**only the top-left corner is rounded**); z 2. Text and icon sit at z 3.
      - Chevron icon `F(10) x F(16)`, `margin-left:F(28)`, `stroke:currentColor; fill:none`.
      - Tablet: F(18), padding F(18) F(24) F(17), icon ml F(10). Mobile: max(12px,F(12)), padding F(11) F(12) F(10), icon F(5)xF(9). Measured 147.5x34.3 @390.

Entrance (runs once the preloader is gone, `isVisible=true`). Fade defaults are 700ms, ease `circ.inOut`:
| Element | Animation | From → To | Duration | Delay | Ease |
|---|---|---|---|---|---|
| Title line i (0,1) | fadeBlur | `opacity 0, yPercent 15, filter blur(20px)` → `1, 0, blur(0)` | 1500ms | 200ms x i | circ.inOut |
| Title arrow | fadeLeft | `opacity 0, xPercent -20` → `1, 0` | 700ms | 700ms | circ.inOut |
| Subtitle "introducing" | fade | opacity 0→1 | 700ms | 500ms | circ.inOut |
| "+ +", "Scroll", cursor info | fade | opacity 0→1 | 700ms | 500ms | circ.inOut |
| Center text | splitFade per **character** | opacity 0→1 | 3000ms per char | 700ms + 0.02s stagger | circ.out |
| Brochure link | fade | opacity 0→1 | 1000ms | 700ms | circ.inOut |

### 3.2 Save the date (`TextSection`, descriptionSize "big")
Copy:
- Section header: `01` (left) / `Save the date` (right)
- Subtitle: `Refire Group`
- Paragraph: `We are excited to be part of Hannover Messe’s Hydrogen & Fuel Cell Expo. We look forward to meeting you there. Stay tuned for updates and plan your visit.`

Layout @1440 (section padding 90 / 22.5 / 88.5):
- `SectionTitle` (isClear, so no own side padding):
  - A 1px line (`Line_wrap`): track `::after` currentColor at opacity .2; animated fill bar `Line_root` (#fefefe, transform-origin left).
  - Below it, `inner` flex space-between with `padding-top:F(22)` (16.5): "01" left, "SAVE THE DATE" right, uppercase, max(12px,F(16)) / max(22px,F(24)). Tablet pt F(30); mobile pt F(15).
  - Header `margin-bottom:F(82)` (61.5); tablet F(70); mobile F(34).
- `inner`: flex, align-items flex-end, justify-content space-between (column on ≤834).
- `content`: `flex-shrink:0; width:F(1470)` (1102.5). Tablet F(557); mobile 87% (321.2 @390).
  - Subtitle: #8b8b8b, uppercase, `margin-bottom:F(29)` (21.75). Tablet F(12); mobile F(10).
  - Paragraph: weight 300, F(95)/F(100). Renders as 5 lines @1440, 375px tall.

Motion (threshold 0.3; 4.1):
- Line scaleX 0→1, 1000ms, ease `easeDecorLine` = cubic-bezier(.075,.82,.165,1), delay 100ms.
- Header inner fade, 700ms, delay 200ms.
- Subtitle fade, 700ms.
- Paragraph split by **words**: each word slides `yPercent 100 → 0` inside an overflow-hidden wrapper, 800ms, stagger 0.02s, ease circ.out.

### 3.3 About Refire (`TitleDescriptionSection`, size "md")
Copy:
- Title: `(About Refire)`
- Description: `REFIRE is an international hydrogen energy technology company specializing in R&D, design, prototyping, testing, application engineering, and manufacturing of fuel cell systems for mobility and power products, superchargers, and grid support products.`

Layout:
- Flex space-between, `padding:0 var(--gap-content)`. Mobile: column.
- Title h2: color #383739 (via `--kst-color`), uppercase, F(60)/1.05. Mobile mb F(29).
- Description `width:F(722)` (541.5, x=876 @1440): F(24)/1.375. Tablet width F(342); mobile width F(294).

Motion (threshold 0.3):
- Title split by words, stagger .03s, 800ms, circ.out.
- Description fade 700ms (size md uses the fade variant).

### 3.4 Key stats (`KeyStats` → `KeyStatsList` → `KeyCard` x3)
Copy per card (top-left / top-right / label / value):
1. `key stat` / `001` / `vehicles deployed` / `4K+`
2. `key stat` / `002` / `Tonnes Of CO2 Saved` / `83K+`
3. `key stat` / `003` / `Systems Delivered` / `4K+`

The label renders capitalized with a small arrow icon after it. The number is 3-digit zero-padded.

Layout:
- `KeyStats_root`: `padding:0 var(--gap-content)`.
- List: `display:grid; grid-template-columns:repeat(3,1fr); gap:F(42)` (31.5; columns 444px @1440).
  - Tablet: 1 column, `padding:0 F(71)`, gap F(30).
  - Mobile: 1 column, padding 0, gap F(52) (54.08).
- Card: flex column, space-between.
  - `height:F(745)` (558.75 @1440, 496.7 @1280).
  - `padding:F(35) F(38) F(11)` (26.25 / 28.5 / 8.25).
  - `border-radius:F(15)` (11.25), `background:#0e0e0e`, color #fefefe.
  - Tablet: height F(550), padding F(31) F(20) F(6), radius F(14).
  - Mobile: height F(339) (352.6), padding F(10) F(14) 0 F(12), radius 14.56.
  - Top info row: flex space-between, F(16) weight 500 lh1.5, #8b8b8b, uppercase.
  - Icon (double circle SVG): `height:F(46)` (34.5), `margin-top:F(21)`, width auto (60px @1440). Mobile height F(26), mt F(12).
  - Body (bottom):
    - Header: `max-width:F(460)` (345), `padding-bottom:F(14)`, `margin-bottom:F(34)`, with a bottom 1px line `::after` #fefefe at opacity .3. Tablet pb F(11), mb F(30); mobile max-width 85%, pb F(11), mb F(15).
      - Label: inline-flex, F(24)/1.38, #8b8b8b, capitalize. Arrow SVG `F(16) x F(13)`, `margin-left:F(10)`. Tablet: F(20), arrow F(14)xF(12). Mobile: max(12px,F(14)), arrow F(11)xF(9), ml F(8).
    - Value: weight 200, F(188)/1, uppercase, `margin-left:F(-7)`.

Motion: each card has its own trigger (threshold 0.3):
- Top row fade, 700ms.
- Header fade, delay 300ms.
- Value split (words/lines) `yPercent 100→0`, delay 500ms, stagger .05s, 800ms, circ.out.

### 3.5 Scrolled picture (`ScrolledPictureSection`), scroll-linked
Image: `/int/images/prisma-1.jpg` (3840x2160), `object-fit:cover`.

Layout:
- Root `height:100vh` (78vh tablet, 68vh mobile → 573.9 @390), full width.
- `picture`: absolute inset 0, `clip-path: polygon(calc(var(--y)*1%) 0, calc(var(--x)*1%) 0, calc(var(--x)*1%) 100%, calc(var(--y)*1%) 100%)`. Initial vars: `--x:98; --y:2; --scale:1`.
- `img`: absolute 100% x 100%, `transform: scale(var(--scale)) translateZ(0)`.

Scroll link, measured. Let s = clamp(1 - sectionTop / viewportHeight, 0, 1), so s=0 when the section top is at the viewport bottom and s=1 when it reaches the viewport top. On every scroll frame, GSAP tweens the vars toward these targets, **duration .6s, ease none, overwrite auto**:
- `--scale = 1 + 0.1·s` (1 → 1.1)
- `--x = 98 + 2·s` (right edge 98% → 100%)
- `--y = 2·(1 - s)` (left edge 2% → 0%)

Measured samples @1440x900:

| sectionTop | --x | --y | --scale |
|---|---|---|---|
| 959 | 98.05 | 1.95 | 1.0025 |
| 481 | 99.00 | 1.00 | 1.050 |
| 1 | 99.94 | 0.06 | 1.097 |
| ≤ -1213 | 100 | 0 | 1.1 |

The image starts inset 2% on left and right (dark gutters ~28.8px @1440) and expands to full-bleed while zooming 10%. No pinning.

### 3.6 Ticker / marquee (`TickerSection`)
Copy: `Visit Us — ` (with a trailing space, em dash U+2014), repeated 3x. More copies are added if the rail is narrower than the viewport.

Layout:
- `ticker`: overflow hidden.
- `rail`: flex, `width:max-content`.
- Each item: `flex-shrink:0; padding-right:F(40)` (30). Font F(250)/1.05, ls -.04em, capitalize. Each item is 778.5px wide @1440 (rail 2335.6); 281.3 @390.

Motion:
- JS marquee on the GSAP ticker. Items are moved with `matrix3d` translateX and wrapped modulo the rail width.
- Auto-speed is 0.6px per frame toward the left. **Measured -36.3 px/s**, the same at every width.
- Drag/swipe with mouse or touch adds `2 x delta` with an inertial decay (`delta *= 0.5` per frame, position lerp ~0.05 frame-normalised). Links inside are disabled while dragging.
- Runs only while the section is in view (`withReset`).
- No scroll-velocity coupling.

### 3.7 Hannover Messe (`Hannover` + `Content` + accordion)
Copy:
- Left title: `Hannover Messe`
- Content title: `BOOTH C45 | HALL 13 17-21 April 2023`
- Content subtitle: `HANNOVER MESSE Exhibition Grounds, Hannover, Germany`
- Content text: `REFIRE was founded in 2015 when a passionate group of engineers came together with the shared dream of propelling the development of hydrogen energy and popularizing the application of fuel cells. REFIRE hopes to reduce mankind’s dependence on fossil energy and contribute to the harmonious coexistence among all lives on our planet by making use of “hydrogen”, the most abundant element in the universe.`
- Accordion (title / body, the body is set via innerHTML):
  1. `17 April, PM` / `Panel Discussion - Heavy Duty Trucks: is Hydrogen the Future? @Public Forum, 14:00 (STAND D25 | HALL13)`
  2. `18 April, AM` / `GreenGT x REFIRE - product presentation@REFIRE booth`
  3. `18 April, PM` / `PRISMA XXII technical unveiling@Technical Stage, 15:00 (STAND B51 | HALL 13)`
  4. `19 April, PM` / `FC Development: Holistic by Design - presentation @REFIRE booth`
  5. `20 April, PM` / `APAS x REFIRE - product presentation@REFIRE booth`
- Contacts: `Media liaison: ` + `media@refire.com` (mailto) and `General enquiries: ` + `info@refire.com` (mailto). Email links are underlined; see 5.

Layout:
- `Hannover_root`: flex space-between, `padding:0 F(204) 0 var(--gap-content)` (0 153 0 22.5 @1440).
  - Tablet: padding 0 gap.
  - Mobile: column (title above content).
- Left title: `flex:0 0 auto; width:F(352)` (264), #383739, F(60)/F(65). Tablet width F(197); mobile 100%, mb F(30).
- Content `width:F(930)` (697.5, x=589.5 @1440). Tablet F(487); mobile 100%.
  - `inner` `max-width:F(726)` (544.5). Tablet F(343); mobile 100%.
    - `header`: `margin-bottom:F(72)` (54), `max-width:F(600)` (450).
      - Title F(60)/F(65), `margin-bottom:F(14)`.
      - Subtitle F(18)/F(33), #383739.
    - Text F(24)/F(33).
  - Accordion `margin-top:F(119)` (89.25). Tablet F(63); mobile F(54).
    - Each item: a 1px `Line` above it (track 20% opacity + white fill bar). The last item also gets a line below.
    - Button: full width, flex, align-items center, `padding:F(26) 0` (19.5; row height 68.3 @1440). Tablet padding F(22) 0, justify space-between.
      - Title h5 `flex:2 1`, F(38)/1.
      - Icon (circle plus) `F(39) x F(39)` (29.25), `transition: transform .3s`. Tablet F(29).
    - Body: `padding-top:F(18); padding-bottom:F(56); width:F(740)` (555), F(24)/1.375, #888; `p` margin-bottom F(28). Tablet pt 0, pb F(24), width F(395); mobile width 85%, pb F(23).
    - Collapsed body height is 0, overflow hidden.
  - Address row `display:flex; margin-top:F(126)` (94.5); items max(12px,F(16))/1, `margin-right:F(132)` (99). Tablet: column, mt F(63), items mb F(18). Mobile: mt F(55), items mb F(14).

Accordion behaviour:
- Only one item is open at a time; clicking the open item closes it. All start closed.
- Open: `height 0 → auto`, GSAP .5s `power1.inOut`. Close: back to 0 over .5s.
- Icon rotates 45deg (plus becomes x), .3s.
- Hover draws the icon's circle: `.circle-border` has `stroke-dasharray:120; stroke-dashoffset:120 → 0` with `transition .5s`. A second circle stays visible at opacity .3.

Motion: each accordion row reveals at threshold 0.1:
- Line scaleX 0→1 (1000ms `easeDecorLine`). The top line of every item is set visible immediately; the last bottom line follows the item.
- Title split by words, stagger .03s.
- Icon fade, body fade.

### 3.8 Text + WebGL image (`TextImageSection`, `isReverse`)
Copy:
- Title: `REFIRE is actively expanding its footprint domestic and internationally` (capitalize, so it renders "REFIRE Is Actively Expanding Its Footprint Domestic And Internationally")
- Text: `In regions where policy is driving industry strategy and where commercialization can take place with fewer obstacles. We would like to help your region develop optimized policy choices, drive strategy, and build market opportunities for the benefit of the planet.`
- Link: `view our brochure` → `/int/files/refire.pdf` (rendered uppercase "VIEW OUR BROCHURE" with a chevron).

Layout:
- Root: flex `row-reverse` (image left, text right), justify space-between, `padding:0 var(--gap-content)`, `height:F(1143)` (857.25 @1440, 762 @1280).
  - Tablet: height F(500).
  - Mobile: `height:auto; flex-direction:column-reverse` (image on top).
- Both items: flex column, align-items center, `max-width:calc(50% - F(15))` (686.25 @1440), width 100%. Tablet image item `calc(50% - F(10))`. Mobile: max-width none, align-items flex-start; the image item gets `height:F(418)` (434.7) and `margin-bottom:F(57)` (59.3).
- Content: `max-width:F(630)` (472.5), `margin-right:F(80)` (60), vertically centred (`margin-top/bottom:auto`), `align-self:flex-end` (sits at the right of its half; x=885 @1440). Tablet: align-self flex-start, max-width F(290), mr 0.
  - Title F(60)/1.05, `margin-bottom:F(72)` (54). Tablet F(32), mb F(46). Mobile F(24)/1.11, mb F(14), max-width 88%.
  - Text `max-width:F(413)` (309.75), F(24)/1.375.
  - Links `margin-top:F(80)` (60), column; tablet F(42), mobile F(29).
- Image: `ShaderPicture`. A three.js canvas (absolute, 100%, z 2) over a hidden `<img src="/int/images/prisma-2.jpg" crossorigin="anonymous">` (visibility hidden, opacity 0, `object-fit:cover`).

WebGL effect (three.js r150):
- `WebGLRenderer`, pixelRatio `min(dpr,2)`, clearColor `0xEEEEEE` alpha 1, `outputEncoding = sRGBEncoding`.
- `OrthographicCamera(-w/2, w/2, h/2, -h/2, 1, 1000)` at z=2.
- `PlaneGeometry(w, h, 1, 1)`.
- `ShaderMaterial` uniforms: `time`, `progress` (0→1), `uTexture` (image), `uDataTexture` (20x20 RGBA float `DataTexture`, NearestFilter), `resolution` (vec4; z,w = cover UV rates).
- **Mouse distortion:** per frame, every data-texture cell is multiplied by relaxation **0.9**. Cells within radius `size·0.15` of the mouse grid position get `+= 100·0.7·mouse.vX·(radius/dist)` (x) and `-= 100·0.7·mouse.vY·(...)` (y), with the factor clamped to 0–10. Mouse velocity decays ×0.9 per frame. The fragment shader offsets UVs by `0.02 * offset.rg`.
- **Entrance:** when the image section is ≥70% revealed (threshold .7), `progress` tweens 0→1, **1s `circ.out`**. Effect: the image slides up from below (`uvs2.y += 1-progress`, out-of-bounds pixels are transparent black) while zooming from 1/1.2 to 1. The canvas only renders while in view.
- Shader source (verbatim from the bundle):
```glsl
// vertex
uniform float time;
varying vec2 vUv;
varying vec3 vPosition;
uniform vec2 pixels;
float PI = 3.141592653589793238;
void main() {
	vUv = uv;
	gl_Position = (projectionMatrix * modelViewMatrix) * vec4(position, 1.0);
}
// fragment
uniform float time;
uniform float progress;
uniform sampler2D uDataTexture;
uniform sampler2D uTexture;
uniform vec4 resolution;
varying vec2 vUv;
varying vec3 vPosition;
float PI = 3.141592653589793238;
float getBounds(vec2 uv) {
	return ((step(0., uv.x) * step(0., uv.y)) * (1. - step(1., uv.x))) * (1. - step(1., uv.y));
}
void main() {
	vec2 newUV = ((vUv - vec2(0.5)) / resolution.zw) + vec2(0.5);
	vec2 uvs = newUV;
	vec2 uvs2 = newUV;
	float cProgress = 1. - progress;
	uvs -= 0.5;
	uvs /= (1. + (0.2 * progress));
	uvs += 0.5;
	uvs2.y += (1. * cProgress);
	uvs.y += (0.3 * cProgress);
	float bounds1 = getBounds(uvs2);
	vec4 offset = texture2D(uDataTexture, vUv);
	gl_FragColor = texture2D(uTexture, uvs - (0.02 * offset.rg)) * bounds1;
}
```
- Cover math: `scale = max(W/imgW, H/imgH)`; `resolution.z = imgW·scale/W`; `resolution.w = imgH·scale/H`.

Text motion (threshold 0.3):
- Title split by words, stagger .1s, 800ms, circ.out.
- Text fade, delay 500ms.
- Links fade, delay 500ms.

### 3.9 Footer (`Copyright`)
Copy: `Refire ©2026` (`"Refire" + NBSP + "©" + currentYear`), ` all rights reserved`, `Back to Top` + up-arrow icon.

Layout:
- Section `padding:F(115) var(--gap-content) 0`.
- Row: `display:grid; grid-template-columns:1fr 1fr 1fr`, `padding:F(42) 0 F(25)` (31.5 / 18.75), `border-top:1px solid #555`, F(20)/1.2. Tablet padding F(24) 0 F(14), font max(12px,F(16)); mobile F(20) 0 F(10), max(12px,F(12)).
- Columns: col1 uppercase, left; col2 capitalize, centre; col3 capitalize, right.
- Back to Top: inline-flex button, arrow `F(14) x F(12)` (10.5x9) with `margin-left:F(10)`. Tablet arrow F(10)xF(8).
- Click scrolls smoothly to top using the smooth-scroll lerp.

---

## 4. Motion system

### 4.1 Reveal triggers
Every block reveals once (`withReset:false`) unless marked otherwise. The trigger is the scroll engine's "startClear" percent, `p = 1 - elementTop / viewportHeight`, and fires when `p ≥ threshold`, i.e. when the element top passes `(1 - threshold) x viewportHeight` from the top. This is equivalent to an IntersectionObserver with `rootMargin: 0px 0px -{threshold·100}% 0px` on the element's top edge. (Derived from source; consistent with the measured picture-section curve in 3.5.)

| Block | Threshold |
|---|---|
| Hero | in view at load; `withReset` (video/cursor info pause off-screen) |
| Save the date | 0.3 |
| About Refire | 0.3 |
| Each key card | 0.3 |
| Ticker | in-view (0.1), `withReset` (pauses off-screen) |
| Each accordion row, KeyStats header (unused here) | 0.1 (default) |
| Text+Image text | 0.3 |
| Shader picture entrance | 0.7 (`contextOnly`); render loop runs while ≥0.1 in view (`withReset`) |

Before reveal, elements are pre-set to their "from" state with `opacity:0` (split roots get `opacity:0; pointer-events:none` until animated).

### 4.2 Animation primitives (GSAP `fromTo`, `overwrite:true`)
- **Fade** (`dS`): default animation `fade` (opacity 0→1), duration **700ms**, ease prop default **`circ.inOut`**, delay in ms.
- **Split text** (`_Z`): text is split into words (`charType` = chars). Each unit is wrapped `<div class="element wrap" style="display:inline-flex; overflow:hidden; position:relative">` around `<div class="innerElement" style="display:inline-block">`; words are grouped in `.word` and spaces preserved.
  - Default animation `split`: `yPercent 100 → 0`.
  - Default duration **800ms**, default stagger **0.01s** (each usage overrides it, see sections), ease **`circ.out`** on enter.
  - The root `SplitTextAnimate_root` is `display:inline-block; overflow:hidden`.
- **Line** (`DM`): `scaleX 0 → 1`, transform-origin left, **1000ms**, ease **easeDecorLine** = `CustomEase "0.075, 0.82, 0.165, 1"`, i.e. `cubic-bezier(.075,.82,.165,1)`.
- **Other named animations** (from the source map): fadeBlur, fadeLeft, splitFade (opacity only, chars), fadeUp, maskIn, scaleDown, etc. Only the ones listed per section are used here.
- **Custom eases registered:** `easeDecorLine` (above), `easeFormHoverLine` = `cubic-bezier(.215,.61,.355,1)`.

### 4.3 Scroll-linked / continuous
- Smooth scroll: lerp 0.1 per frame (see 0.1).
- Page progress bar: scaleX = progress.
- Scrolled picture: clip/scale (3.5).
- Marquee: autoplay + drag (3.6).
- Shader mouse distortion (3.8).
- Custom cursor lerp 0.2 (2.4).
- **No pinning and no parallax** on this page. A parallax modifier exists in the bundle but is unused here.

---

## 5. Hover / interaction states
| Element | Hover state | Timing |
|---|---|---|
| Header Contact pill | outline `stroke-dashoffset -640 → -438` (full pill drawn) | 1.2s cubic-bezier(.86,0,.12,1) |
| Header logo | none | – |
| LinkArrow ("VIEW OUR BROCHURE" in 3.8) | GSAP timeline: underline (1px, currentColor, origin **right**) `scaleX 1 → 0`, 0.8s `power4.inOut`; then the chevron path is redrawn with DrawSVG from `"-0.2% -0.2%"` to `"0% 100%"`, 0.4s `sine.out`, starting 0.3s before the underline ends. Mouse leave reverses. | 0.8s / 0.4s |
| Hero brochure link | no hover rule (glass bg static) | – |
| Accordion button | icon circle border draws (`stroke-dashoffset 120→0`) | .5s |
| Email links (Hannover contacts) | underline (1px currentColor) collapses: `scaleX 1→0`, origin right (Button `hover-underline`). Rest state = underlined. | .5s cubic-bezier(1,0,.29,1) |
| Cookie "Close" | color #d0d0d0 → #060508, 4px dot fades in | .3s ease |
| Contact overlay title | opacity → .6 | .3s ease |
| Contact select options | text underline scaleX 0→1 | .6s cubic-bezier(.165,.84,.44,1) |
| Submit button | dark fill slides up, label swaps with a rotated slide | .6s cubic-bezier(.36,.28,0,.99) |
| Back to Top | none (button) | – |
| Cursor | follows (lerp .2); press scales to .8 | .4s |

No `box-shadow` is used anywhere on the page. Radii in use:
- Key cards F(15)
- Pill F(150)
- Hero link glass F(15) top-left only
- Submit F(100)
- Cursor 50%

Backdrop filters:
- Hero link glass `blur(F(10))`
- Cursor `blur(10px)`

---

## 6. Inline SVGs (verbatim; save as files if preferred, paths in ASSET_MANIFEST.json)

**logo-refire** (viewBox 0 0 159 23, fill currentColor):
```svg
<svg viewBox="0 0 159 23" xmlns="http://www.w3.org/2000/svg" fill="currentColor"><path d="M55.6553 0H29.1011V4.72299H55.6553V0Z"/><path d="M35.2769 13.7035V17.9553H55.6553V22.6839H29.1011V8.98047H55.6553V13.7035H35.2769Z"/><path d="M26.5767 22.6839H18.892L9.91156 13.7035H6.17018V22.6839H0V8.98047H12.8732L26.5767 22.6839Z"/><path d="M87.0335 8.98047V13.7035H66.6607V22.6839H60.4849V8.98047H87.0335Z"/><path d="M87.0335 0H60.4849V4.72299H87.0335V0Z"/><path d="M98.0833 8.98047H91.9131V22.6839H98.0833V8.98047Z"/><path d="M159 0H132.452V4.72299H159V0Z"/><path d="M138.622 13.7035V17.9553H159V22.6839H132.452V8.98047H159V13.7035H138.622Z"/><path d="M24.692 7.22497L21.1918 10.7252L15.1899 4.72324H0V0.00585938H17.4728L24.692 7.22497Z"/><path d="M130.163 22.6839H122.478L113.497 13.7035H109.756V22.6839H103.586V8.98047H116.459L130.163 22.6839Z"/><path d="M128.278 7.22497L124.778 10.7252L118.776 4.72324H91.9131V0.00585938H121.059L128.278 7.22497Z"/></svg>
```
**pill-outline** (Contact pill; class gets the dash styles from 2.2):
```svg
<svg viewBox="0 0 116 39" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M19.5 0.5H96.5C106.993 0.5 115.5 9.00659 115.5 19.5C115.5 29.9934 106.993 38.5 96.5 38.5H19.5C9.00659 38.5 0.5 29.9934 0.5 19.5C0.5 9.00659 9.00659 0.5 19.5 0.5Z" stroke="#FEFEFE"/></svg>
```
**arrow-right-long** (hero title, key-card label, contact title):
```svg
<svg viewBox="0 0 62 52" xmlns="http://www.w3.org/2000/svg"><path d="M29.5022 47.6948L34.0415 51.8852L61.9258 26.1437L34.0415 0.402134L29.5022 4.59261L49.6048 23.1505L0.969421 23.1505L0.96942 29.1369L49.6048 29.1369L29.5022 47.6948Z" fill="currentColor"/></svg>
```
**chevron-right-thin** (hero brochure link; CSS sets stroke currentColor, fill none):
```svg
<svg viewBox="0 0 10 16" xmlns="http://www.w3.org/2000/svg"><path d="M2 14L8 8L2 2" stroke-width="1.66667" stroke-linecap="square"/></svg>
```
**chevron-right-bold** (LinkArrow; fill transparent via CSS):
```svg
<svg viewBox="0 0 10 16" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M2 13.9778L8 7.98887L2 1.99996" stroke="currentColor" stroke-width="2" stroke-linecap="square"/></svg>
```
**double-circle** (key card icon; CSS `fill:transparent; max-height:100%; width:auto`):
```svg
<svg viewBox="0 0 80 46" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="23" cy="23" r="22.5" stroke="currentColor"/><circle cx="57" cy="23" r="22.5" stroke="currentColor" stroke-dasharray="1 1"/></svg>
```
**accordion-plus** (`.circle-border` animated on hover):
```svg
<svg viewBox="0 0 39 39" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="19.5" cy="19.5" r="19" opacity="0.3" stroke="currentColor" fill="none"/><circle class="circle-border" cx="19.5" cy="19.5" r="19" stroke="currentColor" fill="none"/><line x1="27" y1="19.5" x2="12" y2="19.5" stroke="currentColor"/><line x1="19.5" y1="12" x2="19.5" y2="27" stroke="currentColor"/></svg>
```
**arrow-up** (Back to Top):
```svg
<svg viewBox="0 0 12 14" xmlns="http://www.w3.org/2000/svg"><path d="M10.2464 7.01158L11.1543 6.02996L5.57739 -1.21887e-06L0.000488871 6.02996L0.908355 7.01158L4.92892 2.6644L4.92891 13.1818L6.22587 13.1818L6.22587 2.6644L10.2464 7.01158Z" fill="currentColor"/></svg>
```
**chevron-down** (contact select):
```svg
<svg width="16" height="10" viewBox="0 0 16 10" xmlns="http://www.w3.org/2000/svg"><path d="M2 2L8 8L14 2" stroke="currentColor" stroke-width="1.66667" stroke-linecap="square"/></svg>
```

---

## 7. Head / meta
- `<title>Refire</title>`, `<meta name="viewport" content="width=device-width">`
- description, og:description and twitter:description: `REFIRE is an international hydrogen energy technology company specializing in R&D, design, prototyping, testing, application engineering, and manufacturing of fuel cell systems for mobility and power products, superchargers, and grid support products.`
- `og:title`/`twitter:title` "Refire", `og:type` website, `og:image`/`twitter:image` `/int/images/prisma-1.jpg`, `twitter:card` summary_large_image, `twitter:domain` refire.com.
- Icons: favicon-32x32, favicon-16x16, apple-touch-icon 180, android-chrome 192/512 (see manifest).

---

## 8. Hard to replicate / caveats
1. **WebGL image (3.8):** a three.js plane with a custom shader, mouse-velocity displacement grid and a progress-driven reveal. Port it with three (or OGL) using the verbatim shaders. The image must be served same-origin for the texture.
2. **Custom virtual scroll:** replicate with Lenis lerp 0.1. The original translates each section separately; that isn't needed visually.
3. **Hero video:** 25.2 MB, 1920x1080, 37.27s MP4, `object-fit:cover`. Mobile shows a different crop/frame of the same video (see mobile-390-viewport-00). The center text's `mix-blend-mode:difference` colour depends on the frame underneath.
4. **mix-blend-mode:difference** on the header and progress bar. Over the white-ish frames of the video the logo/time invert (see desktop viewport-04, where the header crosses the picture).
5. **Split-text reveals** need a word/char splitter that keeps wrapping (inline-flex overflow-hidden wrappers). The GSAP SplitText Club plugin is not required.
6. **Marquee with drag inertia** (3.6).
7. **Not measured live:** the tablet range (521–834). Values come from CSS formulas, not observation. Hover states were taken from CSS/JS source; only the Contact pill hover was confirmed visually. The contact form's submit endpoint and validation messages were not exercised (submitting a real form was avoided). The mailto on the contact-overlay title is literally `mailto:test@test.en` on the live site.
8. The 6 console errors on the live page are React hydration-mismatch errors (#418, #423, #425), most likely caused by the client-rendered clock/year text. They are not visible in the UI. Do not replicate them.
