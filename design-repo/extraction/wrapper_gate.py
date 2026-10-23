#!/usr/bin/env python3
"""Whole-page-wrapper quality gate (run by verify_all.py; also usable alone).

A section that is really a whole page (or most of one) hides the page's real
structure from retrieval and composition. This gate checks the measured heights
recorded in extraction/measured-values.json -> sectionHeights (1440px viewport,
written by the optional extraction/measure_sections.mjs) against these rules:

  HERO height        a section whose semantic.category is HERO:
                       > 1800px  WARN
                       > 3000px  FAIL unless whitelisted (rule "hero-height")
  page share         one in-flow section's height / its page's in-flow height:
                       > 50%     WARN
                       > 60%     FAIL unless whitelisted (rule "page-share")
  missing data       every section of every template needs a measurement on that
                     template's route, and every route needs a page height.
                     A missing, non-numeric or orphaned measurement is an ERROR.

Whitelist: extraction/wrapper-whitelist.json. Each entry needs route, section,
rule, reviewedBy, a justification of 30+ characters and a maxHeightPx strictly
above the measured height (so the section cannot silently grow). A whitelisted
finding is reported as a WARN, never silenced. reviewedBy values are agent
attestations unless a person says otherwise; they are not human sign-offs.

Usage:  python3 extraction/wrapper_gate.py          # prints findings, exit 1 on any FAIL
"""
import glob
import json
import os
import sys

sys.dont_write_bytecode = True
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RULE_ID = "WRAPPER_HEIGHT_GATE"  # the compatibility/graph.json rule this module enforces
HERO_WARN_PX = 1800
HERO_FAIL_PX = 3000
SHARE_WARN = 0.50
SHARE_FAIL = 0.60
JUSTIFICATION_MIN_CHARS = 30
WHITELIST_KEYS = {"route", "section", "rule", "reviewedBy", "justification", "maxHeightPx"}
RULES = ("hero-height", "page-share")


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def evaluate(sections, templates, ledger, whitelist):
    """Return [(status, message)] with status FAIL or WARN. Empty list = clean."""
    out = []

    def fail(m):
        out.append(("FAIL", m))

    def warn(m):
        out.append(("WARN", m))

    sh = ledger.get("sectionHeights")
    if not isinstance(sh, dict):
        return [("FAIL", "measured-values.json has no sectionHeights block (run extraction/measure_sections.mjs --write)")]
    pages = {}
    for p in sh.get("pages", []):
        if not isinstance(p, dict) or not isinstance(p.get("route"), str) or not _num(p.get("inFlowHeightPx")) or p["inFlowHeightPx"] <= 0:
            fail("malformed page measurement %r" % (p,))
            continue
        if p["route"] in pages:
            fail("duplicate page measurement for route %r" % p["route"])
        pages[p["route"]] = p["inFlowHeightPx"]
    meas = {}
    for m in sh.get("sections", []):
        if not isinstance(m, dict) or not isinstance(m.get("route"), str) or not isinstance(m.get("section"), str) or not _num(m.get("heightPx")) or m["heightPx"] <= 0 or not isinstance(m.get("inFlow"), bool):
            fail("malformed section measurement %r" % (m,))
            continue
        key = (m["route"], m["section"])
        if key in meas:
            fail("duplicate measurement for %s on route %r" % (m["section"], m["route"]))
        meas[key] = m

    expected = set()
    for tid, t in templates.items():
        for route in t["routes"]:
            if route not in pages:
                fail("missing page height for route %r (%s)" % (route, tid))
            for n in t["nodes"]:
                expected.add((route, n["section"]))
                if (route, n["section"]) not in meas:
                    fail("missing measurement: %s on route %r (%s)" % (n["section"], route, tid))
    for key in sorted(set(meas) - expected):
        fail("orphan measurement %s on route %r is not in any template" % (key[1], key[0]))
    for route in sorted(set(pages) - {r for t in templates.values() for r in t["routes"]}):
        fail("orphan page measurement for route %r" % route)

    # ---- whitelist shape
    wl = {}
    entries = whitelist.get("entries") if isinstance(whitelist, dict) else None
    if not isinstance(entries, list):
        fail("wrapper-whitelist.json has no entries list")
        entries = []
    for e in entries:
        if not isinstance(e, dict) or set(e) != WHITELIST_KEYS:
            fail("whitelist entry must have exactly %s: %r" % (sorted(WHITELIST_KEYS), e))
            continue
        if e["rule"] not in RULES:
            fail("whitelist entry for %s on route %r has unknown rule %r" % (e["section"], e["route"], e["rule"]))
            continue
        if not isinstance(e["reviewedBy"], str) or not e["reviewedBy"].strip():
            fail("whitelist entry for %s on route %r has no reviewedBy" % (e["section"], e["route"]))
        if not isinstance(e["justification"], str) or len(e["justification"].strip()) < JUSTIFICATION_MIN_CHARS:
            fail("whitelist entry for %s on route %r needs a justification of %d+ characters" % (e["section"], e["route"], JUSTIFICATION_MIN_CHARS))
        m = meas.get((e["route"], e["section"]))
        if m is None:
            fail("whitelist entry for %s on route %r matches no measurement" % (e["section"], e["route"]))
            continue
        if not _num(e["maxHeightPx"]) or e["maxHeightPx"] <= m["heightPx"]:
            fail("whitelist entry for %s on route %r: maxHeightPx %r is not above the measured %spx" % (e["section"], e["route"], e["maxHeightPx"], m["heightPx"]))
            continue
        wl[(e["route"], e["section"], e["rule"])] = e
    used = set()

    def waived(route, sec, rule):
        if (route, sec, rule) in wl:
            used.add((route, sec, rule))
            return True
        return False

    # ---- HERO height
    for (route, sec), m in sorted(meas.items()):
        cat = sections.get(sec, {}).get("semantic", {}).get("category")
        if cat == "HERO":
            h = m["heightPx"]
            if h > HERO_FAIL_PX:
                if waived(route, sec, "hero-height"):
                    warn("HERO %s on %r is %spx (> %d) but whitelisted (reviewed)" % (sec, route, h, HERO_FAIL_PX))
                else:
                    fail("HERO %s on %r is %spx (> %d): a whole-page wrapper, decompose it or whitelist it" % (sec, route, h, HERO_FAIL_PX))
            elif h > HERO_WARN_PX:
                warn("HERO %s on %r is %spx (> %d)" % (sec, route, h, HERO_WARN_PX))

    # ---- page share
    for (route, sec), m in sorted(meas.items()):
        if not m["inFlow"] or route not in pages:
            continue
        share = m["heightPx"] / pages[route]
        if share > SHARE_FAIL:
            if waived(route, sec, "page-share"):
                warn("%s on %r holds %.1f%% of the page (> %d%%) but is whitelisted (reviewed)" % (sec, route, share * 100, SHARE_FAIL * 100))
            else:
                fail("%s on %r holds %.1f%% of the page's in-flow height (> %d%%)" % (sec, route, share * 100, SHARE_FAIL * 100))
        elif share > SHARE_WARN:
            warn("%s on %r holds %.1f%% of the page's in-flow height (> %d%%)" % (sec, route, share * 100, SHARE_WARN * 100))
    for key, e in sorted(wl.items()):
        if key not in used:
            warn("whitelist entry for %s on route %r (%s) is not needed by any measurement; remove it" % (key[1], key[0], key[2]))
    return out


def summary(sections, templates, ledger):
    sh = ledger.get("sectionHeights", {})
    pages = {p["route"]: p["inFlowHeightPx"] for p in sh.get("pages", []) if isinstance(p, dict) and "route" in p}
    n = len(sh.get("sections", []))
    heroes = [m for m in sh.get("sections", []) if sections.get(m.get("section"), {}).get("semantic", {}).get("category") == "HERO"]
    best = {}
    for m in sh.get("sections", []):
        if m.get("inFlow") and m.get("route") in pages and _num(m.get("heightPx")):
            s = m["heightPx"] / pages[m["route"]]
            if m["route"] not in best or s > best[m["route"]][0]:
                best[m["route"]] = (s, m["section"])
    shares = "; ".join("%r: %.1f%% (%s)" % (r, v[0] * 100, v[1]) for r, v in sorted(best.items())) or "n/a"
    return "%d measurements; tallest HERO %s; largest in-flow share per route %s" % (
        n, "%spx" % max(m["heightPx"] for m in heroes) if heroes else "n/a", shares)


def load_inputs(repo=REPO):
    sections = {}
    for p in glob.glob(os.path.join(repo, "sections", "*.json")):
        with open(p, encoding="utf-8") as f:
            c = json.load(f)
        sections[c["id"]] = c
    with open(os.path.join(repo, "templates", "templates.json"), encoding="utf-8") as f:
        templates = json.load(f)["templates"]
    with open(os.path.join(repo, "extraction", "measured-values.json"), encoding="utf-8") as f:
        ledger = json.load(f)
    with open(os.path.join(repo, "extraction", "wrapper-whitelist.json"), encoding="utf-8") as f:
        whitelist = json.load(f)
    return sections, templates, ledger, whitelist


def main():
    sections, templates, ledger, whitelist = load_inputs()
    findings = evaluate(sections, templates, ledger, whitelist)
    for status, msg in findings:
        print("%-4s  %s" % (status, msg))
    fails = sum(1 for s, _ in findings if s == "FAIL")
    print("wrapper_gate: %s; %d FAIL, %d WARN" % (summary(sections, templates, ledger), fails, len(findings) - fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
