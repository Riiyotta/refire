# Refire clone: information architecture

This is the information architecture (IA) for the clone of https://refire.com/int/ in this project.

`ia.json` is the only file to edit by hand. `IA.md` and `matrix.csv` are **generated** from it, so never edit them directly; they are overwritten on every build.

```bash
node validate.mjs   # hard checks: route/template totals, every section defined and used, valid categories
node build.mjs      # regenerates IA.md (readable doc) and matrix.csv (section × template matrix)
```

After adding a route or section to `ia.json`, run both again.

## What the data shows

- **The site is two routes, `/int/` (Home) and `/int/404`, one template each.** The original `/int/` locale really is a one-page site. Its build lists only `/` and the error page, and every other refire.com path redirects to en.refire.com. That is a separate site, deliberately left out of scope (see `specs/ROUTES.md`). The 404 template also serves as the catch-all for any unknown `/int/` path.
- **5 of the 16 sections are shared, and all five are site chrome:** preloader, header, contact overlay, cookie pane and cursor. They render through the shared `Layout`, so a new page gets them for free.
- **The other 11 sections are each used on one page.**
  - The scroll-progress bar and the copyright footer are the only chrome tied to one page. The 404 switches them off with `showProgress={false}` / `showFooter={false}`, which is why the 404 is classed `chrome: "reduced"`.
  - The 8 home content sections and the 404 body each appear on exactly one page. They should stay page-local until a second page needs them.
  - Their building blocks are already reusable in `src/components/ui/`: split text, reveal, accordion, marquee, arrow and underline links, and the shader picture.
- **Every section names the real component that renders it** (`implementedBy`), so this IA is a map of the actual code, not just a plan.
