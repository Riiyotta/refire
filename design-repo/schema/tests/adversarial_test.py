#!/usr/bin/env python3
"""Adversarial suite: proves every rule rejects bad input and every control passes.

Part A  PageSpec mutations, validated in-process with schema/semantic_validate.py
        (schema layer + semantic layer). Each must be REJECTED with the expected rule.
Part B  Controls: the three example instances, plus one control synthesized
        generically per template from that template's own node list (so a new
        template is covered with no new control code). Each must PASS with 0 errors.
Part A2 Section-contract mutations (in-process, sv.lint_contracts on a modified copy of the
        contracts): the closed contract schema, distinct source/semantic objects and the
        retrievalEligible pin must each reject their defect; unmutated contracts and a
        boundary control (a 30-character reason) must pass.
Part A3 Wrapper-gate mutations (in-process, extraction/wrapper_gate.py on modified measurements):
        HERO >1800 warns, >3000 fails; one section >50% of a page warns, >60% fails; the
        whitelist waives only with a reviewed, justified, bounded entry; missing data is an error.
Part C  Repo drift mutations: the design-repo is copied to a scratch directory in
        the OS temp dir, one defect is injected, and extraction/verify_all.py must
        FAIL on the expected check. The unmutated scratch copy must PASS.

Run:  python3 schema/tests/adversarial_test.py [--source-root PATH] [--skip-repo]
Exit code 0 only if every mutation is rejected and every control passes.
"""
import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "schema"))
sys.path.insert(0, os.path.join(REPO, "extraction"))
import semantic_validate as sv  # noqa: E402
import wrapper_gate as wg  # noqa: E402

MODEL = sv.Repo(REPO)


def load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return json.load(f)


HOME = load("schema/example.pagespec.json")
NF = load("schema/example.not-found.pagespec.json")
GEN = load("schema/example.generated.pagespec.json")


def idx(spec, section):
    return next(i for i, n in enumerate(spec["nodes"]) if n["section"] == section)


def node(spec, section):
    return spec["nodes"][idx(spec, section)]


def m(base, fn):
    s = copy.deepcopy(base)
    fn(s)
    return s


def swap(spec, a, b):
    i, j = idx(spec, a), idx(spec, b)
    spec["nodes"][i], spec["nodes"][j] = spec["nodes"][j], spec["nodes"][i]


def insert_before(spec, before, n):
    spec["nodes"].insert(idx(spec, before), copy.deepcopy(n))


def remove(spec, section):
    spec["nodes"].pop(idx(spec, section))


FOOTER = node(HOME, "chrome.footer")
PROGRESS = node(HOME, "chrome.scroll-progress")
STATS = node(HOME, "stats.card-grid")
NOT_FOUND_BODY = node(NF, "error.not-found")
ABS = "/" + "Users/someone/refire"  # built from pieces: keeps the repo free of the literal prefix

MUTATIONS = [
    # --- the seven required categories
    ("wrong section order for the template", HOME, lambda s: swap(s, "ticker.marquee", "media.scroll-picture"), ["TEMPLATE_NODE_SEQUENCE"]),
    ("wrong order: hero after the statement", HOME, lambda s: swap(s, "hero.video-title", "content.numbered-statement"), ["TEMPLATE_NODE_SEQUENCE", "HERO_FIRST_IN_MAIN"]),
    ("section not allowed in template (stats on the 404)", NF, lambda s: insert_before(s, "error.not-found", STATS), ["SECTION_ALLOWED_IN_TEMPLATE"]),
    ("section not allowed in template (404 body on home)", HOME, lambda s: insert_before(s, "chrome.footer", NOT_FOUND_BODY), ["SECTION_ALLOWED_IN_TEMPLATE"]),
    ("external https href on the hero link", HOME, lambda s: node(s, "hero.video-title")["content"]["link"].__setitem__("href", "https://refire.com/int/files/refire.pdf"), ["SCHEMA", "NO_EXTERNAL_HREF"]),
    ("external http href hidden in a mailto title", HOME, lambda s: node(s, "overlay.contact")["content"].__setitem__("titleHref", "http://example.com"), ["SCHEMA", "NO_EXTERNAL_HREF"]),
    ("protocol-relative URL in body copy", HOME, lambda s: node(s, "content.title-description")["content"].__setitem__("description", "see //cdn.example.net/x"), ["NO_EXTERNAL_HREF"]),
    ("unknown assetRole", HOME, lambda s: node(s, "hero.video-title")["content"]["video"].__setitem__("assetRole", "media.stock-footage"), ["SCHEMA", "ASSET_ROLE_SLOT"]),
    ("extra motion field", HOME, lambda s: node(s, "ticker.marquee")["motion"].__setitem__("inventedAnimation", "spin"), ["SCHEMA"]),
    ("footer on the 404", NF, lambda s: s["nodes"].append(copy.deepcopy(FOOTER)), ["ERROR_PAGE_NO_FOOTER_NO_PROGRESS", "SECTION_ALLOWED_IN_TEMPLATE"]),
    ("progress bar on the 404", NF, lambda s: s["nodes"].insert(2, copy.deepcopy(PROGRESS)), ["ERROR_PAGE_NO_FOOTER_NO_PROGRESS", "SECTION_ALLOWED_IN_TEMPLATE"]),
    # --- schema layer
    ("missing reducedMotionFallback", HOME, lambda s: node(s, "hero.video-title")["motion"].pop("reducedMotionFallback"), ["SCHEMA"]),
    ("reducedMotionFallback claims handling that does not exist", HOME, lambda s: node(s, "hero.video-title")["motion"].__setitem__("reducedMotionFallback", "fade-only"), ["SCHEMA"]),
    ("motion pattern swapped to another section's", HOME, lambda s: node(s, "ticker.marquee")["motion"].__setitem__("pattern", "fade"), ["SCHEMA"]),
    ("reveal threshold changed 0.3 -> 0.5", HOME, lambda s: node(s, "content.title-description")["motion"].__setitem__("threshold", 0.5), ["SCHEMA"]),
    ("unknown template", HOME, lambda s: s.__setitem__("template", "template.blog"), ["SCHEMA"]),
    ("invented section type", HOME, lambda s: s["nodes"].insert(7, {"section": "content.testimonials", "content": {}, "motion": {"pattern": "fade", "reducedMotionFallback": "none-in-source"}}), ["SCHEMA", "SECTION_ALLOWED_IN_TEMPLATE"]),
    ("extra content field", HOME, lambda s: node(s, "ticker.marquee")["content"].__setitem__("color", "#ff0000"), ["SCHEMA"]),
    ("contact form declared submitting", HOME, lambda s: node(s, "overlay.contact")["content"].__setitem__("formSubmission", "submits"), ["SCHEMA"]),
    ("404 message rewritten", NF, lambda s: node(s, "error.not-found")["content"].__setitem__("message", "Oops, nothing here."), ["SCHEMA"]),
    ("404 document title rewritten", NF, lambda s: s["meta"].__setitem__("title", "Not found"), ["SCHEMA"]),
    ("stat value over maxChars", HOME, lambda s: node(s, "stats.card-grid")["content"]["cards"][0].__setitem__("value", "4,000+"), ["SCHEMA"]),
    ("four stat cards (grid is three)", HOME, lambda s: node(s, "stats.card-grid")["content"]["cards"].append({"label": "key stat", "index": 4, "caption": "x", "value": "1"}), ["SCHEMA"]),
    ("variant missing on a variant-bearing section", HOME, lambda s: node(s, "content.numbered-statement").pop("variant"), ["SCHEMA"]),
    ("variant invented on a variant-less section", HOME, lambda s: node(s, "ticker.marquee").__setitem__("variant", "fast"), ["SCHEMA"]),
    # --- structural
    ("required section removed (hero)", HOME, lambda s: remove(s, "hero.video-title"), ["REQUIRED_SECTIONS_PRESENT", "ONE_HERO"]),
    ("duplicate non-repeatable footer", HOME, lambda s: s["nodes"].append(copy.deepcopy(FOOTER)), ["NON_REPEATABLE_ONCE"]),
    ("footer not last", HOME, lambda s: swap(s, "chrome.footer", "media.text-image-shader"), ["FOOTER_LAST", "TEMPLATE_NODE_SEQUENCE"]),
    ("hero added to the hero-less 404 (named exception does not mean allowed)", NF, lambda s: insert_before(s, "error.not-found", node(HOME, "hero.video-title")), ["ONE_HERO", "SECTION_ALLOWED_IN_TEMPLATE"]),
    ("home template on an invented route", HOME, lambda s: s.__setitem__("route", "*"), ["ROUTE_TEMPLATE_BINDING"]),
    ("404 template bound to '/'", NF, lambda s: s.__setitem__("route", "/"), ["ROUTE_TEMPLATE_BINDING"]),
    ("theme does not match template", HOME, lambda s: s.__setitem__("theme", "theme.system-error"), ["THEME_TEMPLATE_BINDING"]),
    # --- runtime / content
    ("maxWords overflow on the statement", HOME, lambda s: node(s, "content.numbered-statement")["content"].__setitem__("statement", " ".join(["word"] * 40)), ["MAX_WORDS"]),
    ("maxWords overflow on meta description", HOME, lambda s: s["meta"].__setitem__("description", " ".join(["word"] * 60)), ["MAX_WORDS"]),
    ("markup injected into an accordion body", HOME, lambda s: node(s, "content.event-accordion")["content"]["schedule"][0].__setitem__("body", "<img src=x onerror=alert(1)>"), ["NO_MARKUP_IN_TEXT"]),
    ("asset role valid but wrong for the slot", HOME, lambda s: node(s, "hero.video-title")["content"]["video"].__setitem__("assetRole", "media.scroll-picture"), ["SCHEMA", "ASSET_ROLE_SLOT"]),
    ("reference instance points at an unlisted asset", HOME, lambda s: node(s, "media.scroll-picture")["content"]["image"].__setitem__("src", "/int/images/other.jpg"), ["ASSET_SOURCE_POLICY"]),
    # --- real-company protections (generated provenance)
    ("generated page reuses the real Refire logo", GEN, lambda s: node(s, "chrome.header")["content"]["logo"].__setitem__("src", "inline-svg:logo-refire"), ["ASSET_SOURCE_POLICY"]),
    ("generated page reuses the hero film", GEN, lambda s: node(s, "hero.video-title")["content"]["video"].__setitem__("src", "/int/videos/main-new.mp4"), ["ASSET_SOURCE_POLICY"]),
    ("generated page reuses product photography", GEN, lambda s: node(s, "media.text-image-shader")["content"]["image"].__setitem__("src", "/int/images/prisma-2.jpg"), ["ASSET_SOURCE_POLICY"]),
    ("generated page links the real brochure", GEN, lambda s: node(s, "hero.video-title")["content"]["link"].__setitem__("href", "/int/files/refire.pdf"), ["ASSET_SOURCE_POLICY"]),
    ("generated page copies proprietary copy verbatim", GEN, lambda s: node(s, "content.title-description")["content"].__setitem__("description", load("schema/example.pagespec.json")["meta"]["description"]), ["GENERATED_NO_PROPRIETARY_COPY"]),
    ("generated page embeds a proprietary sentence", GEN, lambda s: node(s, "content.numbered-statement")["content"].__setitem__("statement", "Hello. We look forward to meeting you there."), ["GENERATED_NO_PROPRIETARY_COPY"]),
    ("generated page reuses the Refire brand name", GEN, lambda s: node(s, "chrome.footer")["content"].__setitem__("brand", "Refire"), ["GENERATED_NO_PROPRIETARY_COPY"]),
    ("generated page uses a real refire.com email", GEN, lambda s: node(s, "content.event-accordion")["content"]["contacts"][0].__setitem__("email", "media@refire.com"), ["GENERATED_CONTACT_DATA_RESERVED"]),
    ("generated page uses a real phone number", GEN, lambda s: node(s, "overlay.contact")["content"]["phoneList"]["lines"][0].__setitem__("href", "tel:+17907909238"), ["GENERATED_CONTACT_DATA_RESERVED"]),
]

WARN_MUTATIONS = [
    ("meta description differs from the about description", HOME, lambda s: s["meta"].__setitem__("description", "A short different description."), "META_DESCRIPTION_MIRRORS_ABOUT"),
    ("stat indexes out of sequence", HOME, lambda s: node(s, "stats.card-grid")["content"]["cards"][0].__setitem__("index", 7), "STAT_INDEXES_SEQUENTIAL"),
]


def synthesized_controls():
    """One control per template, built from the template's own node list."""
    pool = {}
    for ex in (HOME, NF):
        for n in ex["nodes"]:
            pool.setdefault(n["section"], n)
    out = []
    for tid, t in MODEL.templates.items():
        ref = HOME if tid == HOME["template"] else NF if tid == NF["template"] else None
        spec = {"pageSpecVersion": "1.0.0", "id": "page.control-" + tid.split(".")[1], "template": tid, "route": t["routes"][0], "theme": t["theme"],
                "provenance": "reference", "meta": copy.deepcopy(ref["meta"]) if ref else {"title": "x", "description": "x"},
                "nodes": [copy.deepcopy(pool[n["section"]]) for n in t["nodes"] if n["required"]]}
        out.append(("synthesized control for " + tid, spec))
    return out


def part_a_b():
    rows, ok = [], True
    for name, base, fn, expect in MUTATIONS:
        errs, _w = sv.validate(m(base, fn), MODEL)
        got = sorted({e[0] for e in errs})
        hit = bool(errs) and any(x in got for x in expect)
        ok &= hit
        rows.append(("REJECTED" if hit else "MISSED", name, ",".join(got) or "-"))
    for name, base, fn, rule in WARN_MUTATIONS:
        errs, warns = sv.validate(m(base, fn), MODEL)
        hit = not errs and any(w[0] == rule for w in warns)
        ok &= hit
        rows.append(("WARNED" if hit else "MISSED", name + " (warn-severity rule)", rule if hit else str([e[0] for e in errs])))
    controls = [("example.pagespec.json", HOME), ("example.not-found.pagespec.json", NF), ("example.generated.pagespec.json", GEN)] + synthesized_controls()
    for name, spec in controls:
        errs, warns = sv.validate(spec, MODEL)
        ok &= not errs
        rows.append(("PASSES" if not errs else "BROKEN", "control: " + name, "%d errors, %d warnings" % (len(errs), len(warns)) if not errs else str(errs[:2])))
    return rows, ok


# ------------------------------------------------------------------ Part A2 / A3
def lint(fn):
    r = copy.deepcopy(MODEL)
    fn(r)
    return sorted({e[0] for e in sv.lint_contracts(r)})


def _flip_cookie(r):
    c = r.sections["chrome.cookie-pane"]
    c["retrievalEligible"] = True
    c.pop("retrievalEligibleReason")


def _hero_off(r):
    c = r.sections["hero.video-title"]
    c["retrievalEligible"] = False
    c["retrievalEligibleReason"] = "A hero is page content; this reason is long enough but the pin must still reject it."
    r.allowlist["retrievalIneligibleSections"].append("hero.video-title")


def _reason(sid, text):
    return lambda r: r.sections[sid].__setitem__("retrievalEligibleReason", text)


CONTRACT_MUTATIONS = [
    ("cookie banner flipped to retrievable", _flip_cookie, "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("cookie banner flipped in contract AND allowlist together", lambda r: (_flip_cookie(r), r.allowlist["retrievalIneligibleSections"].remove("chrome.cookie-pane")), "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("hero made ineligible in contract AND allowlist together (pin holds)", _hero_off, "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("reason of 29 characters", _reason("overlay.contact", "x" * 29), "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("reason missing on an ineligible section", lambda r: r.sections["chrome.preloader"].pop("retrievalEligibleReason"), "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("reason present on an eligible section", lambda r: r.sections["chrome.header"].__setitem__("retrievalEligibleReason", "x" * 40), "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("retrievalEligible is the string 'false'", lambda r: r.sections["chrome.cursor"].__setitem__("retrievalEligible", "false"), "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("retrievalEligible is the integer 0", lambda r: r.sections["chrome.cursor"].__setitem__("retrievalEligible", 0), "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("retrievalEligible missing", lambda r: r.sections["chrome.header"].pop("retrievalEligible"), "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("allowlist retrievalIneligibleSections drifts", lambda r: r.allowlist["retrievalIneligibleSections"].remove("chrome.cursor"), "RETRIEVAL_ELIGIBILITY_PINNED"),
    ("unknown top-level contract field", lambda r: r.sections["chrome.footer"].__setitem__("category", "chrome"), "SECTION_CONTRACT_CLOSED"),
    ("unknown constraints field", lambda r: r.sections["chrome.footer"]["constraints"].__setitem__("sticky", True), "SECTION_CONTRACT_CLOSED"),
    ("semantic.category outside the closed enum (FEATURES)", lambda r: r.sections["stats.card-grid"]["semantic"].__setitem__("category", "FEATURES"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
    ("semantic.category in the wrong case", lambda r: r.sections["hero.video-title"]["semantic"].__setitem__("category", "hero"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
    ("semantic.id differs from the contract id", lambda r: r.sections["chrome.footer"]["semantic"].__setitem__("id", "chrome.header"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
    ("semantic object missing", lambda r: r.sections["chrome.footer"].pop("semantic"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
    ("source object missing", lambda r: r.sections["chrome.footer"].pop("source"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
    ("extra field inside source", lambda r: r.sections["chrome.footer"]["source"].__setitem__("category", "FOOTER"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
    ("extra field inside semantic", lambda r: r.sections["chrome.footer"]["semantic"].__setitem__("file", "src/components/layout/Footer.jsx"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
    ("source.tag outside the closed set", lambda r: r.sections["chrome.footer"]["source"].__setitem__("tag", "main"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
    ("source.lines malformed", lambda r: r.sections["chrome.footer"]["source"].__setitem__("lines", "10..33"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
    ("source.file not a source path", lambda r: r.sections["chrome.footer"]["source"].__setitem__("file", "Footer.jsx"), "SECTION_SOURCE_SEMANTIC_DISTINCT"),
]


def part_a2():
    rows, ok = [], True
    for name, fn, rule in CONTRACT_MUTATIONS:
        got = lint(fn)
        hit = rule in got
        ok &= hit
        rows.append(("REJECTED" if hit else "MISSED", "contract: " + name, ",".join(got) or "-"))
    controls = [("unmutated section contracts", lambda r: None), ("reason of exactly 30 characters (boundary)", _reason("overlay.contact", "x" * 30))]
    for name, fn in controls:
        got = lint(fn)
        ok &= not got
        rows.append(("PASSES" if not got else "BROKEN", "control: " + name, "0 errors" if not got else ",".join(got)))
    return rows, ok


def _gate_inputs():
    sections, templates, ledger, whitelist = wg.load_inputs(REPO)
    return copy.deepcopy(sections), copy.deepcopy(templates), copy.deepcopy(ledger), copy.deepcopy(whitelist)


def _m(ledger, route, section):
    return next(x for x in ledger["sectionHeights"]["sections"] if x["route"] == route and x["section"] == section)


def _wl(whitelist, route, section, rule, **over):
    e = {"route": route, "section": section, "rule": rule, "reviewedBy": "agent:test (attestation)", "justification": "Reviewed fixture entry used only inside the adversarial suite.", "maxHeightPx": 9000}
    e.update(over)
    whitelist["entries"].append(e)


# (name, mutation(ledger, whitelist), expected statuses present, statuses that must be absent)
GATE_CASES = [
    ("HERO exactly 1800px: no finding", lambda l, w: _m(l, "/", "hero.video-title").__setitem__("heightPx", 1800), set(), {"FAIL"}),
    ("HERO 1801px warns", lambda l, w: _m(l, "/", "hero.video-title").__setitem__("heightPx", 1801), {"WARN"}, {"FAIL"}),
    ("HERO exactly 3000px warns only", lambda l, w: _m(l, "/", "hero.video-title").__setitem__("heightPx", 3000), {"WARN"}, {"FAIL"}),
    ("HERO 3001px fails", lambda l, w: _m(l, "/", "hero.video-title").__setitem__("heightPx", 3001), {"FAIL"}, set()),
    ("HERO 3500px + valid whitelist -> WARN, no FAIL", lambda l, w: (_m(l, "/", "hero.video-title").__setitem__("heightPx", 3500), _wl(w, "/", "hero.video-title", "hero-height", maxHeightPx=4000)), {"WARN"}, {"FAIL"}),
    ("HERO 3500px + whitelist maxHeightPx 3500 (not above) fails", lambda l, w: (_m(l, "/", "hero.video-title").__setitem__("heightPx", 3500), _wl(w, "/", "hero.video-title", "hero-height", maxHeightPx=3500)), {"FAIL"}, set()),
    ("HERO 3500px + whitelist justification of 29 characters fails", lambda l, w: (_m(l, "/", "hero.video-title").__setitem__("heightPx", 3500), _wl(w, "/", "hero.video-title", "hero-height", maxHeightPx=4000, justification="x" * 29)), {"FAIL"}, set()),
    ("HERO 3500px + whitelist without reviewedBy fails", lambda l, w: (_m(l, "/", "hero.video-title").__setitem__("heightPx", 3500), _wl(w, "/", "hero.video-title", "hero-height", maxHeightPx=4000, reviewedBy=" ")), {"FAIL"}, set()),
    ("section at 50.0% of the page: no share warning for it", lambda l, w: _m(l, "/", "content.event-accordion").__setitem__("heightPx", l["sectionHeights"]["pages"][0]["inFlowHeightPx"] * 0.5), set(), {"FAIL"}),
    ("section at 55% warns", lambda l, w: _m(l, "/", "content.event-accordion").__setitem__("heightPx", l["sectionHeights"]["pages"][0]["inFlowHeightPx"] * 0.55), {"WARN"}, {"FAIL"}),
    ("section at 60.0% warns only", lambda l, w: _m(l, "/", "content.event-accordion").__setitem__("heightPx", l["sectionHeights"]["pages"][0]["inFlowHeightPx"] * 0.6), {"WARN"}, {"FAIL"}),
    ("section at 61% fails", lambda l, w: _m(l, "/", "content.event-accordion").__setitem__("heightPx", l["sectionHeights"]["pages"][0]["inFlowHeightPx"] * 0.61), {"FAIL"}, set()),
    ("section at 61% + valid whitelist -> WARN", lambda l, w: (_m(l, "/", "content.event-accordion").__setitem__("heightPx", l["sectionHeights"]["pages"][0]["inFlowHeightPx"] * 0.61), _wl(w, "/", "content.event-accordion", "page-share", maxHeightPx=5000)), {"WARN"}, {"FAIL"}),
    ("a fixed (not in-flow) tall section is not counted toward page share", lambda l, w: _m(l, "/", "overlay.contact").update({"heightPx": 6000}), set(), {"FAIL"}),
    ("404's page-share waiver removed fails", lambda l, w: w["entries"].clear(), {"FAIL"}, set()),
    ("unneeded whitelist entry warns", lambda l, w: _wl(w, "/", "hero.video-title", "hero-height", maxHeightPx=2000), {"WARN"}, {"FAIL"}),
    ("whitelist entry for an unknown rule fails", lambda l, w: _wl(w, "/", "hero.video-title", "anything"), {"FAIL"}, set()),
    ("a section measurement missing is an error", lambda l, w: l["sectionHeights"]["sections"].remove(_m(l, "/", "stats.card-grid")), {"FAIL"}, set()),
    ("a page height missing is an error", lambda l, w: l["sectionHeights"]["pages"].pop(), {"FAIL"}, set()),
    ("sectionHeights block missing is an error", lambda l, w: l.pop("sectionHeights"), {"FAIL"}, set()),
    ("non-numeric height is an error", lambda l, w: _m(l, "/", "hero.video-title").__setitem__("heightPx", "900"), {"FAIL"}, set()),
    ("zero height is an error", lambda l, w: _m(l, "/", "hero.video-title").__setitem__("heightPx", 0), {"FAIL"}, set()),
    ("duplicate measurement is an error", lambda l, w: l["sectionHeights"]["sections"].append(dict(_m(l, "/", "hero.video-title"))), {"FAIL"}, set()),
    ("orphan measurement is an error", lambda l, w: l["sectionHeights"]["sections"].append({"route": "/", "section": "content.testimonials", "heightPx": 5, "inFlow": True}), {"FAIL"}, set()),
]


def part_a3():
    rows, ok = [], True
    sections, templates, ledger, whitelist = _gate_inputs()
    base = wg.evaluate(sections, templates, ledger, whitelist)
    ctl = not any(s == "FAIL" for s, _ in base)
    ok &= ctl
    rows.append(("PASSES" if ctl else "BROKEN", "control: unmutated measurements + whitelist", "%d findings, 0 FAIL" % len(base) if ctl else str(base[:2])))
    for name, fn, want, absent in GATE_CASES:
        sections, templates, ledger, whitelist = _gate_inputs()
        fn(ledger, whitelist)
        got = {s for s, _ in wg.evaluate(sections, templates, ledger, whitelist)}
        # the unmutated baseline carries one reviewed WARN (the 404), so WARN is only asserted when it is the point of the case
        hit = want <= got and not (absent & got)
        if not want and not (absent & got):
            hit = True
        ok &= hit
        rows.append(("REJECTED" if hit and "FAIL" in want else "WARNED" if hit and "WARN" in want else "PASSES" if hit else "MISSED", "gate: " + name, ",".join(sorted(got)) or "-"))
    return rows, ok


# ------------------------------------------------------------------ Part C
def edit_json(root, rel, fn):
    p = os.path.join(root, rel)
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    fn(d)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def edit_text(root, rel, fn):
    p = os.path.join(root, rel)
    with open(p, encoding="utf-8") as f:
        t = f.read()
    with open(p, "w", encoding="utf-8") as f:
        f.write(fn(t))


def first_cite(d):
    return d["tokens"]["color.paper"]["cite"][0]


REPO_MUTATIONS = [
    ("phantom allowlist entry", "allowlist-parity", lambda r: edit_json(r, "tokens/llm/component-allowlist.json", lambda d: d["sections"].append("content.phantom"))),
    ("orphan contract (allowlist entry removed)", "allowlist-parity", lambda r: edit_json(r, "tokens/llm/component-allowlist.json", lambda d: d["primitives"].remove("primitive.line"))),
    ("allowlistVersion drift", "version-parity", lambda r: edit_json(r, "registry.manifest.json", lambda d: d.__setitem__("allowlistVersion", "9.9.9"))),
    ("manifest count drift", "manifest-counts", lambda r: edit_json(r, "registry.manifest.json", lambda d: d["counts"].__setitem__("sections", 17))),
    ("README counts table goes stale", "readme-counts", lambda r: edit_text(r, "README.md", lambda t: t.replace("| `sections` | 16 |", "| `sections` | 15 |"))),
    ("citation out of range", "citations", lambda r: edit_json(r, "tokens/00-foundation/color.json", lambda d: first_cite(d).__setitem__("at", "tailwind.config.cjs:9999"))),
    ("citation in range but quoting the wrong code", "citations", lambda r: edit_json(r, "tokens/00-foundation/color.json", lambda d: first_cite(d).__setitem__("at", "tailwind.config.cjs:12")), "needs-source"),
    ("citation to a path outside the ledger", "citations", lambda r: edit_json(r, "tokens/00-foundation/color.json", lambda d: first_cite(d).__setitem__("at", "src/invented.js:1"))),
    ("malformed citation", "citations", lambda r: edit_json(r, "tokens/00-foundation/color.json", lambda d: first_cite(d).__setitem__("at", "tailwind.config.cjs"))),
    ("token citation removed", "citation-coverage", lambda r: edit_json(r, "tokens/00-foundation/radius.json", lambda d: d["tokens"]["radius.card"].__setitem__("cite", []))),
    ("pinned asset policy changed to a different VALID value (role + pinnedPolicies both edited)", "asset-roles", lambda r: edit_json(r, "assets/asset-roles.json", lambda d: (d["roles"]["brand.logo"].__setitem__("generationPolicy", "may-reuse-exact"), d["pinnedPolicies"].__setitem__("brand.logo", "may-reuse-exact")))),
    ("graph rule with no enforcement", "graph-enforcement", lambda r: edit_json(r, "compatibility/graph.json", lambda d: d["rules"].append({"id": "UNENFORCED_RULE", "severity": "error", "enforcedBy": "semantic", "description": "x"}))),
    ("schema-enforced rule marker removed from the schema", "graph-enforcement", lambda r: edit_text(r, "schema/pagespec.schema.json", lambda t: t.replace("rule:CONTACT_FORM_NON_SUBMITTING", "rule:REMOVED"))),
    ("absolute machine path injected", "paths-and-junk", lambda r: edit_text(r, "README.md", lambda t: t + "\nSee " + ABS + "/src\n")),
    ("OS junk file present", "paths-and-junk", lambda r: open(os.path.join(r, "sections", ".DS_Store"), "w").close()),
    ("entryPoint escaping the package", "entry-points", lambda r: edit_json(r, "registry.manifest.json", lambda d: d["entryPoints"].__setitem__("evidence", "../src/index.css"))),
    ("contract field added without schema", "contract-schema-parity", lambda r: edit_json(r, "sections/ticker.marquee.json", lambda d: d["content"]["fields"].__setitem__("subtitle", {"type": "string", "observedWords": 1, "maxWords": 2, "copyClass": "proprietary", "observed": "x", "cite": d["content"]["fields"]["text"]["cite"]}))),
    ("theme resolves to a value the foundation does not have", "token-integrity", lambda r: edit_json(r, "tokens/themes/refire-dark.json", lambda d: d["resolves"].__setitem__("text.primary", "#ffffff"))),
    ("source-stack word leaks into a token id", "stack-neutral", lambda r: edit_json(r, "tokens/30-layout/layout.json", lambda d: d["tokens"].__setitem__("layout.tailwind-gutter", d["tokens"]["layout.gutter"]))),
    ("copy budget inflated beyond the evidence rule", "copy-budgets", lambda r: edit_json(r, "sections/hero.video-title.json", lambda d: d["content"]["fields"]["eyebrow"].__setitem__("maxWords", 50))),
    ("retrieval pin dropped from verify_all.py (code pin independent of the JSON)", "section-contracts", lambda r: edit_text(r, "extraction/verify_all.py", lambda s: s.replace('"chrome.cookie-pane", "chrome.cursor", "chrome.preloader", "overlay.contact"})', '"chrome.cookie-pane", "chrome.cursor", "chrome.preloader"})', 1))),
    ("retrieval pin dropped from semantic_validate.py (second independent pin)", "section-contracts", lambda r: edit_text(r, "schema/semantic_validate.py", lambda s: s.replace('    "overlay.contact",\n})', '})', 1))),
    ("cookie banner made retrievable in contract and allowlist together", "section-contracts", lambda r: (edit_json(r, "sections/chrome.cookie-pane.json", lambda d: (d.__setitem__("retrievalEligible", True), d.pop("retrievalEligibleReason"))), edit_json(r, "tokens/llm/component-allowlist.json", lambda d: d["retrievalIneligibleSections"].remove("chrome.cookie-pane")))),
    ("section contract gains an unknown field", "section-contracts", lambda r: edit_json(r, "sections/chrome.footer.json", lambda d: d.__setitem__("category", "chrome"))),
    ("source.lines points at the wrong part of the file", "section-provenance", lambda r: edit_json(r, "sections/chrome.footer.json", lambda d: d["source"].__setitem__("lines", "1-9")), "needs-source"),
    ("semantic.category disagrees with ia.json", "section-provenance", lambda r: edit_json(r, "sections/content.title-description.json", lambda d: d["semantic"].__setitem__("category", "MEDIA")), "needs-source"),
    ("HERO section measured at 3500px", "wrapper-gate", lambda r: edit_json(r, "extraction/measured-values.json", lambda d: next(x for x in d["sectionHeights"]["sections"] if x["section"] == "hero.video-title").__setitem__("heightPx", 3500))),
    ("one section holds 65% of the home page", "wrapper-gate", lambda r: edit_json(r, "extraction/measured-values.json", lambda d: next(x for x in d["sectionHeights"]["sections"] if x["section"] == "content.event-accordion").__setitem__("heightPx", 4300))),
    ("a section measurement goes missing", "wrapper-gate", lambda r: edit_json(r, "extraction/measured-values.json", lambda d: d["sectionHeights"]["sections"].remove(next(x for x in d["sectionHeights"]["sections"] if x["section"] == "ticker.marquee")))),
    ("wrapper gate dropped from the graph", "graph-enforcement", lambda r: edit_json(r, "compatibility/graph.json", lambda d: d.__setitem__("rules", [x for x in d["rules"] if x["id"] != "WRAPPER_HEIGHT_GATE"]))),
    ("motion object reopened (additionalProperties true)", "allowlist-properties", lambda r: edit_json(r, "schema/pagespec.schema.json", lambda d: d["definitions"]["motion.ticker.marquee"].__setitem__("additionalProperties", True))),
]


def run_verify(root, source_root):
    cmd = [sys.executable, "-B", os.path.join(root, "extraction", "verify_all.py")]
    if source_root:
        cmd += ["--source-root", source_root]
    p = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    return p.returncode, p.stdout


def part_c(source_root):
    rows, ok = [], True
    tmp = tempfile.mkdtemp(prefix="refire-drift-")
    try:
        base = os.path.join(tmp, "design-repo")
        shutil.copytree(REPO, base, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        code, out = run_verify(base, source_root)
        ok &= code == 0
        rows.append(("PASSES" if code == 0 else "BROKEN", "control: unmutated scratch copy", "verify_all exit %d" % code))
        for item in REPO_MUTATIONS:
            name, check, fn = item[0], item[1], item[2]
            if len(item) > 3 and item[3] == "needs-source" and not source_root:
                rows.append(("SKIPPED", name, "quote checks need the source tree (pass --source-root)"))
                continue
            work = os.path.join(tmp, "m")
            shutil.rmtree(work, ignore_errors=True)
            shutil.copytree(base, work)
            fn(work)
            code, out = run_verify(work, source_root)
            failed = [line.split()[1] for line in out.splitlines() if line.startswith("FAIL")]
            hit = code == 1 and check in failed
            ok &= hit
            rows.append(("REJECTED" if hit else "MISSED", name, "verify_all FAIL " + ",".join(failed) if failed else "exit %d" % code))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return rows, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", default=os.path.dirname(REPO))
    ap.add_argument("--skip-repo", action="store_true")
    args = ap.parse_args()
    src = os.path.abspath(args.source_root)
    src = src if os.path.isfile(os.path.join(src, "src", "index.css")) else None

    rows, ok = part_a_b()
    print("Part A/B  PageSpec mutations and controls")
    for r in rows:
        print("  %-8s %-78s %s" % r)
    total_ok = ok
    rows, ok = part_a2()
    print("\nPart A2  section-contract mutations (closed schema, source vs semantic, retrieval pin)")
    for r in rows:
        print("  %-8s %-78s %s" % r)
    total_ok &= ok
    rows, ok = part_a3()
    print("\nPart A3  wrapper-gate mutations (heights, page share, whitelist, missing data)")
    for r in rows:
        print("  %-8s %-78s %s" % r)
    total_ok &= ok
    if not args.skip_repo:
        rows, ok = part_c(src)
        print("\nPart C  repo drift mutations (scratch copy in the OS temp dir; source tree %s)" % ("present" if src else "ABSENT"))
        for r in rows:
            print("  %-8s %-78s %s" % r)
        total_ok &= ok
    n_mut = len(MUTATIONS) + len(WARN_MUTATIONS) + len(CONTRACT_MUTATIONS) + len(GATE_CASES) + (0 if args.skip_repo else len(REPO_MUTATIONS))
    print("\nadversarial: %s (%d mutations, %d PageSpec + 2 contract + 1 gate + %d repo controls)" % ("ALL REJECTED, ALL CONTROLS PASS" if total_ok else "FAILURES PRESENT", n_mut, 3 + len(MODEL.templates), 0 if args.skip_repo else 1))
    return 0 if total_ok else 1


if __name__ == "__main__":
    sys.exit(main())
