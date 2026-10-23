# Motion hand-off (Build → Animation)

**Status: implemented.** Shared helpers: `gsap.js` (plugins + CustomEases),
`anims.js` (source animation table, preset/play), `reveal.js` (InView-style
triggers, wired in Layout via `useReveals`), `scroll.js` (progress bar,
scrolled picture), `marquee.js` (ticker engine), `useSplitSwap.js` (pill
label). Corrections found against the original bundle: cursor lerp is
**0.12**/frame (not 0.2); the pill swap is out-in (old label leaves with
sine.inOut, new one enters with circ.out after 400ms); the Text+Image text
trigger measures the whole section; the hero title arrow is a sibling of the
blurred text, not nested inside it; BlackButton has no "from" state, so its
rest transitions never animate.

Everything below is rendered in its **final visible state** today. Each element
carries a `data-anim` hook (plus optional `data-anim-delay` / `-duration` /
`-stagger` / `-ease` / `-threshold` / `-split`), so Animation can query the DOM
instead of editing component markup. Values come from CLONE_SPEC.md (section in brackets).

Shared infrastructure already in place:
- `useSite()` (`src/context/SiteContext.jsx`) gives `lenis` (Lenis, lerp 0.1, driven by `gsap.ticker`), `isVisible` (true after the preloader unmounts) and `contactOpen`.
- gsap 3.13.0 (CustomEase, DrawSVGPlugin, InertiaPlugin and Draggable are all bundled), lenis 1.1.13, three 0.150.0.
- Custom eases still to register: `easeDecorLine` = `0.075,0.82,0.165,1`, `easeFormHoverLine` = `0.215,0.61,0.355,1` [4.2].
- Reveal trigger rule [4.1]: fires once, when the element top passes `(1 - threshold) × viewportHeight`. Pre-set the "from" state (opacity 0) before the reveal.
- Split-text DOM [4.2]: `.split-root > .split-word > .split-el (overflow hidden) > .split-inner`. Tween `.split-inner`.

## Fixed chrome
| Hook | Element | Motion | Spec |
|---|---|---|---|
| `preloader` (style `--p`) | Preloader root | Tween `--p` to progress, 4s `sine.inOut`. Then root opacity → 0 over 1s (delay .2s, sine.inOut), then unmount (call `onComplete`). Currently `--p` is set directly and the preloader unmounts immediately. | 2.1 |
| `preloader-counter` | "NN%" | Integer counter 0→100 (roundProps), 4s `sine.inOut` | 2.1 |
| `preloader-progress-group` | line + counter | On complete: `opacity 0, filter blur(20px)` over 2s | 2.1 |
| `preloader-dot` ×3 | "." dots | `@keyframes showHideDot {0%{opacity:0}50%{opacity:1}60%{opacity:1}100%{opacity:0}}`, 2.5s ease-in-out infinite, delays .2/.4/.6s (in `data-anim-delay`, ms) | 2.1 |
| `split-swap` | Header pill label | Char split swap "Contact" ↔ "Close", 400ms. Label is re-keyed on toggle. | 2.2 |
| `scroll-progress` (style `--p`) | Progress bar | Set `--p` (0–100) to page scroll progress every scroll frame | 2.3 |
| `cursor` | Custom cursor | Lerp 0.2/frame toward the mouse (currently follows directly). Mousedown: `--mD` (on `.cursor-inner`) → .2 over .4s, back to 0 on up. Window leave: opacity → 0 over .3s `power2.out`; enter → 1. | 2.4 |
| `cookie-pane` | Cookie pane | Fade in/out, 700ms (currently mounts/unmounts instantly) | 2.5 |
| `black-btn-bg`, `black-btn-label` | Submit pill | Rest-state entrance: bg `transform 1.5s cubic-bezier(.19,.39,0,.99) 2s`, label `1s … 2.1s` (the "from" transform isn't in the spec) | 2.6 |

## Hero [3.1] (`data-anim-group="hero"`; runs when `isVisible` turns true; fade default 700ms `circ.inOut`)
| Hook | Element | From → To | Dur | Delay | Ease |
|---|---|---|---|---|---|
| `fadeBlur` (×2) | Title lines | `opacity 0, yPercent 15, blur(20px)` → `1, 0, blur(0)` | 1500 | 0 / 200 | circ.inOut |
| `fadeLeft` | Title arrow | `opacity 0, xPercent -20` → `1, 0` | 700 | 700 | circ.inOut |
| `fade` | "introducing", "+ +", "Scroll", cursor info | opacity 0→1 | 700 | 500 | circ.inOut |
| `splitFade` (chars) | "of fuel cell systems" | opacity 0→1 per char | 3000 | 700, stagger .02 | circ.out |
| `fade` | Brochure link | opacity 0→1 | 1000 | 700 | circ.inOut |

## Sections
| Section | Hook(s) | Motion | Threshold | Spec |
|---|---|---|---|---|
| Save the date | `line` | Fill `scaleX 0→1`, 1000ms easeDecorLine, delay 100 | 0.3 | 3.2 |
| | `fade` (SectionTitle row) | 700ms, delay 200 | | |
| | `fade` (subtitle) | 700ms | | |
| | `split` (words) | paragraph `yPercent 100→0`, 800ms, stagger .02, circ.out | | |
| About Refire | `split` (words) | title, stagger .03, 800ms, circ.out | 0.3 | 3.3 |
| | `fade` | description 700ms | | |
| Key stats (`data-anim-group="key-card"`, one trigger per card) | `fade` | top row (labels + icon), 700ms | 0.3 | 3.4 |
| | `fade` | header (label + rule), delay 300 | | |
| | `split` | value `yPercent 100→0`, delay 500, stagger .05, 800ms, circ.out | | |
| Scrolled picture | `scrolled-picture` | Each scroll frame, with s = clamp(1 - sectionTop/vh, 0, 1), tween (.6s, ease none, overwrite auto) `--scale = 1+0.1s`, `--x = 98+2s`, `--y = 2(1-s)`. Starts at 98/2/1. | — | 3.5 |
| Ticker | `marquee` (rail) | Autoplay -0.6px/frame (-36.3px/s), matrix3d translateX wrapped modulo rail width. Drag/swipe adds 2×delta with inertia (delta ×0.5/frame, position lerp ~0.05). Disable links while dragging. Run only in view (withReset). | 0.1 | 3.6 |
| Hannover accordion (`data-anim-group="accordion-row"`) | `line` | top line visible immediately; the last bottom line follows its item; 1000ms easeDecorLine | 0.1 | 3.7 |
| | `split` | title, stagger .03 | | |
| | `fade` | icon, body | | |
| Text + image (`data-anim-group="text-image"`) | `split` | title, stagger .1, 800ms, circ.out | 0.3 | 3.8 |
| | `fade` | text, delay 500 | | |
| | `fade` | links, delay 500 | | |
| | `shader-reveal` | `element.shaderApi.setProgress(p)`: progress 0→1, 1s `circ.out`, at threshold 0.7 (currently 1). Set it to 0 before reveal. | 0.7 | 3.8 |

## Already implemented by Build (interaction, not entrance or scroll motion)
- Hover/active CSS: pill outline draw, cookie Close dot, email underline collapse, Select option underline, Submit fill/label swap, accordion icon circle draw, Contact title opacity.
- LinkArrow hover GSAP timeline (underline collapse + DrawSVG chevron) [5].
- Accordion open/close: height 0↔auto, .5s `power1.inOut`, icon rotate 45deg .3s [3.7].
- Contact overlay fade: opacity/visibility .5s ease (CSS) [2.6].
- Shader mouse distortion: data-texture relaxation 0.9, radius 0.15·grid, strength 100·0.7, render loop only while in view [3.8].
