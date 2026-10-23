Source: https://refire.com/int/

# Route inventory: refire.com/int/

Measured 2026-10-22 with Playwright, plus the Next.js build manifest and the page JS bundle.

## Main finding: /int/ is a one-page site

The `/int/` locale is a static Next.js export with only two pages in its build:

```
https://refire.com/int/_next/static/LurkF7eLrQpBzbw6WpCW3/_buildManifest.js
sortedPages: ["/", "/_app", "/_error"]
__NEXT_DATA__: {"page":"/","buildId":"LurkF7eLrQpBzbw6WpCW3","assetPrefix":"/int","nextExport":true}
```

Every `<a>` on the home page (with the CONTACT overlay open and closed) points to one of these:

| href | Kind | Status |
|---|---|---|
| https://refire.com/int/files/refire.pdf (hero "View Our Brochure", plus the TextImageSection link) | PDF download | excluded (download) |
| mailto:media@refire.com, mailto:info@refire.com, mailto:test@test.en | mailto | excluded |
| tel:+17907909238, tel:+18932332030 | tel | excluded |

The other controls do not link anywhere:
- The header logo is a `<button>`, not a link. It has no href, and its click behavior is part of the home spec.
- The header "CONTACT" pill is a `<button>` that opens `ContactPopup` in place. The URL and hash stay the same.
- The cookie pane has only a "Close" button.
- The BackToTop button, accordion `Item_openBtn` buttons, and the contact-form `Select` (Media / Sales / General) are all buttons.

There is no hamburger menu, footer nav, or link to news, projects or detail pages. A grep of `pages/index-*.js` finds `to:` targets only for the PDF and mailto links.

## Routes

| Route (rebuild) | Template | Page title | Source URL | Spec |
|---|---|---|---|---|
| `/` | Home | `Refire` | https://refire.com/int/ | `CLONE_SPEC.md` (other agent, not covered here) |
| `*` (catch-all / 404) | NotFound (Next.js default `_error`) | `404: This page could not be found` | https://refire.com/int/404 (also `/int/404.html`) | `specs/404.md` |

There are no data-driven templates, so no `*.data.json` files were written.

### Server behavior (for routing decisions)
- `https://refire.com/int/404` and `/int/404.html` return 200 with the error page.
- Any other unknown path under refire.com returns **301 to https://en.refire.com/**. This was tested on `/`, `/robots.txt`, `/sitemap.xml`, `/int/sitemap.xml`, `/int/about`, `/int/contact/`, `/int/news/`, `/int/products/`, `/int/careers/`, `/int/privacy/`, `/int/terms/`, `/cn/`, `/en/`, `/de/` and `/jp/`. So in production, nobody reaches the 404 page by mistake. The rebuild can either render the NotFound page for unknown routes (recommended for an SPA) or redirect to `/`.
- No sitemap.xml or robots.txt exists. Both redirect.

## Other locale (noted, NOT specced)

**https://en.refire.com/** is a different site on a separate host with a separate codebase (163 KB HTML, not the /int/ Next build). Its links:

`/`, `/about`, `/investor-relations`, `/markets`, `/partners`, `/privacy`, `/products`, `/stories` (index), `/stories/{7806,7810,7878,7880,8508,8519,8521}` (story detail template), `/terms`. External links: LinkedIn and WeChat. Mailto links: info@ and sales@.

Nothing on /int/ links to en.refire.com. You only reach it through the server's 301 fallback. If the rebuild should include those pages, en.refire.com needs its own recon pass. It has a different design system.

## Shared components

| Component (source CSS module) | Home | 404 | Notes |
|---|---|---|---|
| Header (`Header_root__l5VTQ`): logo button, live clock `Time_root` ("HH:MM GMT"), CONTACT `PillButton` with `SplitTextAnimate` letters | yes | yes | **Same as home Header** (identical CSS-module class hashes from the shared `_app` bundle). Geometry measured on the 404: 1440 → height 77, padding 22.5px 0, logo at x22.5 y29.9, 119.25×17.25. 390 → height 68, padding 18.72px 0, logo 10.4/26.2, 108.2×15.6, clock 217.3/27.8 60.4×12.5, pill 298.5/18.7 81.1×30.5. Fixed, z 99, color rgb(254,254,254), `mix-blend-mode: difference`. See the 404 quirk in specs/404.md. |
| CookiePane (`CookiePane_root__Iz8eF`) | yes | yes | **Same as home.** Fixed bottom-right. 1440: 322.5×57 at x1117.5, padding 19.5px, bg rgb(254,254,254), text rgb(6,5,8) 12px/18px. 390: full width 390×52 at bottom. Copy: "We use cookies to make things better" / "Close". |
| CustomCursor (`CustomCursor_cursor`, `_circle` 32×32 rgba(181,181,181,0.25)) | yes | yes | **Same as home.** |
| Preloader ("0%" … "initializing…" with "++ 1.00784 / 1.00811" ticker) | yes | yes (briefly on first paint, then removed from the DOM) | **Same as home preloader.** |
| ContactPopup (`ContactPopup_root`, opened by the header CONTACT pill) | yes | yes (pill present) | **Same as home.** It is an overlay, not a route. |
| Footer, BackToTop | yes | **no** | Home only. |

## Page transitions

Not applicable. The only routes are the home page and a 404 that no in-site link reaches, so there is no client-side navigation and no route-transition animation to measure.
