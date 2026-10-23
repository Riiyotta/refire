#!/usr/bin/env node
// OPTIONAL measurement script (never run by verify_all.py). Measures every section
// contract's rendered height at a 1440px-wide viewport on each template's
// representative route and writes the result to extraction/measured-values.json
// under "sectionHeights", which extraction/wrapper_gate.py then checks.
//
// Needs: a running build of the clone and a Playwright module.
//   PLAYWRIGHT_MODULE=<path to playwright/index.mjs>   (required; never stored in the repo)
//   BASE_URL=http://127.0.0.1:5482                     (default)
// Example (from the clone root):
//   npx vite build --outDir "$SCRATCH/dist" && npx vite preview --outDir "$SCRATCH/dist" --port 5482 &
//   PLAYWRIGHT_MODULE=... node design-repo/extraction/measure_sections.mjs --write
// Without --write the JSON is printed to stdout only.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const ledgerPath = path.join(here, "measured-values.json");
const BASE = process.env.BASE_URL || "http://127.0.0.1:5482";
const VIEWPORT = { width: 1440, height: 900 };
if (!process.env.PLAYWRIGHT_MODULE) {
  console.error("Set PLAYWRIGHT_MODULE to the path of playwright/index.mjs");
  process.exit(2);
}
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE).href);

// section id -> how to find it in the rendered page. Selectors are structural (the
// clone has no per-section attributes): main's direct children in template order.
const HOME_MAIN = ["hero.video-title", "content.numbered-statement", "content.title-description", "stats.card-grid", "media.scroll-picture", "ticker.marquee", "content.event-accordion", "media.text-image-shader"];
const CHROME = {
  "chrome.header": "header",
  "chrome.scroll-progress": "div.fixed.z-99[class*='h-[2px]']",
  "chrome.cookie-pane": "div.fixed.bottom-0.right-0.z-99",
  "chrome.cursor": "div.fixed.z-103",
};
const PRELOADER = "div.fixed.z-100.h-screen.w-screen";
const OVERLAY = ".contact-popup";

const PAGES = [
  { route: "/", template: "template.home", url: "/int/", mainChildren: HOME_MAIN.concat(["chrome.footer"]) },
  { route: "*", template: "template.not-found", url: "/int/this-page-does-not-exist", mainChildren: ["error.not-found"], mainSelectors: { "error.not-found": ".error-page" } },
];

const rectOf = (page, sel) => page.evaluate((s) => {
  const el = document.querySelector(s);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return { h: Math.round(r.height * 10) / 10, fixed: getComputedStyle(el).position === "fixed" };
}, sel);

const browser = await chromium.launch();
const out = { sections: [], pages: [] };
for (const pg of PAGES) {
  const ctx = await browser.newContext({ viewport: VIEWPORT });
  const page = await ctx.newPage();
  await page.goto(BASE + pg.url, { waitUntil: "commit" });
  await page.waitForSelector(PRELOADER, { state: "attached", timeout: 15000 });
  const pr = await rectOf(page, PRELOADER);
  out.sections.push({ route: pg.route, section: "chrome.preloader", heightPx: pr.h, inFlow: !pr.fixed, selector: PRELOADER });
  await page.waitForSelector(PRELOADER, { state: "detached", timeout: 30000 });
  await page.waitForSelector("main", { timeout: 15000 });
  await page.waitForTimeout(1500);
  await page.mouse.move(700, 450);
  await page.waitForTimeout(500);
  const main = await page.evaluate(() => document.querySelector("main").getBoundingClientRect().height);
  out.pages.push({ route: pg.route, template: pg.template, inFlowHeightPx: Math.round(main * 10) / 10, selector: "main" });
  for (const [id, sel] of Object.entries(CHROME)) {
    if (pg.template === "template.not-found" && id === "chrome.scroll-progress") continue; // forbidden on the 404
    const r = await rectOf(page, sel);
    if (r) out.sections.push({ route: pg.route, section: id, heightPx: r.h, inFlow: !r.fixed, selector: sel });
  }
  // contact overlay: open it through the header pill, then measure
  await page.click("header .pill");
  await page.waitForTimeout(1500);
  const ov = await rectOf(page, OVERLAY);
  if (ov) out.sections.push({ route: pg.route, section: "overlay.contact", heightPx: ov.h, inFlow: !ov.fixed, selector: OVERLAY + " (opened)" });
  for (let i = 0; i < pg.mainChildren.length; i++) {
    const id = pg.mainChildren[i];
    const sel = (pg.mainSelectors && pg.mainSelectors[id]) || `main > :nth-child(${i + 1})`;
    const r = await rectOf(page, sel);
    if (r) out.sections.push({ route: pg.route, section: id, heightPx: r.h, inFlow: !r.fixed, selector: sel });
  }
  await ctx.close();
}
await browser.close();

const result = {
  viewport: VIEWPORT,
  measuredWith: "headless Chromium via Playwright against a production build of the clone (vite build + vite preview), after the preloader finished",
  tool: "extraction/measure_sections.mjs",
  note: "Heights are getBoundingClientRect().height in CSS px at the viewport above. inFlow=false means position:fixed (does not add to page height). pages[].inFlowHeightPx is the height of <main>. Regenerate with measure_sections.mjs --write; wrapper_gate.py checks it.",
  pages: out.pages,
  sections: out.sections,
};
if (process.argv.includes("--write")) {
  const led = JSON.parse(fs.readFileSync(ledgerPath, "utf8"));
  led.sectionHeights = result;
  fs.writeFileSync(ledgerPath, JSON.stringify(led, null, 2) + "\n");
  console.error("wrote sectionHeights to extraction/measured-values.json");
}
console.log(JSON.stringify(result, null, 2));
