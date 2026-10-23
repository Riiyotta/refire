#!/usr/bin/env python3
"""Drift proof for the whole-page-wrapper gate, the retrieval-eligibility pin and the
source/semantic provenance checks.

Each case copies this design-repo into a scratch directory, injects ONE defect, runs
extraction/verify_all.py on the copy and asserts the expected outcome: a FAIL on a named
check, or (for warn-tier cases) exit 0 with a WARN carrying the expected text. The
unmutated copy must pass. Nothing is ever changed in the real repo.

Usage:
  python3 extraction/prove_drift.py                       # scratch dir = a fresh dir in the OS temp dir
  python3 extraction/prove_drift.py --scratch DIR         # DIR must exist and be empty; its contents are removed afterwards
  python3 extraction/prove_drift.py --source-root PATH    # clone project for quote/IA checks (default: the parent directory)
Cases that need the real source tree are SKIPPED (and counted as skipped) without one.
Exit code 0 only if the control passes and every case behaves as expected.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def edit_json(root, rel, fn):
    p = os.path.join(root, rel)
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    fn(d)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")


def meas(d, route, section):
    return next(m for m in d["sectionHeights"]["sections"] if m["route"] == route and m["section"] == section)


def ledger(fn):
    return lambda r: edit_json(r, "extraction/measured-values.json", fn)


def whitelist(fn):
    return lambda r: edit_json(r, "extraction/wrapper-whitelist.json", fn)


def both(*fns):
    return lambda r: [f(r) for f in fns]


def entry(route, section, rule, **over):
    e = {"route": route, "section": section, "rule": rule, "reviewedBy": "agent:test (attestation, not a human sign-off)",
         "justification": "Drift-proof fixture: a deliberately reviewed exception used only in a scratch copy.", "maxHeightPx": 9000}
    e.update(over)
    return e


def add_entry(**kw):
    return whitelist(lambda d: d["entries"].append(entry(**kw)))


def set_h(route, section, h):
    return ledger(lambda d: meas(d, route, section).__setitem__("heightPx", h))


HERO = ("/", "hero.video-title")
BIG = ("/", "content.event-accordion")  # page height 6598.9px


def contract(sid, fn):
    return lambda r: edit_json(r, "sections/%s.json" % sid, fn)


def allowlist(fn):
    return lambda r: edit_json(r, "tokens/llm/component-allowlist.json", fn)


# (name, mutation, expectation, needs_source)
#   expectation: ("FAIL", check) | ("WARN", check, text-fragment)
CASES = [
    # ---- wrapper gate: HERO height
    ("HERO 2000px (> 1800) warns", set_h(*HERO, 2000), ("WARN", "wrapper-gate", "hero.video-title on '/' is 2000px"), False),
    ("HERO 3500px (> 3000) fails", set_h(*HERO, 3500), ("FAIL", "wrapper-gate"), False),
    ("HERO 3500px with a valid reviewed whitelist entry downgrades to WARN", both(set_h(*HERO, 3500), add_entry(route="/", section="hero.video-title", rule="hero-height", maxHeightPx=4000)), ("WARN", "wrapper-gate", "hero.video-title on '/' is 3500px (> 3000) but whitelisted"), False),
    ("HERO 3500px, whitelist maxHeightPx not above measured, fails", both(set_h(*HERO, 3500), add_entry(route="/", section="hero.video-title", rule="hero-height", maxHeightPx=3400)), ("FAIL", "wrapper-gate"), False),
    ("HERO 3500px, whitelist for the wrong rule does not waive", both(set_h(*HERO, 3500), add_entry(route="/", section="hero.video-title", rule="page-share", maxHeightPx=4000)), ("FAIL", "wrapper-gate"), False),
    # ---- wrapper gate: page share
    ("one section at 53% of the page warns", set_h(*BIG, 3500), ("WARN", "wrapper-gate", "holds 53"), False),
    ("one section at 65% of the page fails", set_h(*BIG, 4300), ("FAIL", "wrapper-gate"), False),
    ("65% section with a valid reviewed whitelist entry downgrades to WARN", both(set_h(*BIG, 4300), add_entry(route="/", section="content.event-accordion", rule="page-share", maxHeightPx=5000)), ("WARN", "wrapper-gate", "content.event-accordion on '/' holds 65"), False),
    ("the 404's reviewed page-share waiver removed fails (100% of its page)", whitelist(lambda d: d["entries"].clear()), ("FAIL", "wrapper-gate"), False),
    ("404 waiver whose maxHeightPx equals the measured height fails", whitelist(lambda d: d["entries"][0].__setitem__("maxHeightPx", 900)), ("FAIL", "wrapper-gate"), False),
    # ---- wrapper gate: whitelist quality
    ("whitelist justification under 30 characters fails", whitelist(lambda d: d["entries"][0].__setitem__("justification", "single section")), ("FAIL", "wrapper-gate"), False),
    ("whitelist entry without reviewedBy fails", whitelist(lambda d: d["entries"][0].__setitem__("reviewedBy", "")), ("FAIL", "wrapper-gate"), False),
    ("whitelist entry with an extra field fails (closed)", whitelist(lambda d: d["entries"][0].__setitem__("note", "x")), ("FAIL", "wrapper-gate"), False),
    ("unneeded whitelist entry warns", add_entry(route="/", section="hero.video-title", rule="hero-height", maxHeightPx=2000), ("WARN", "wrapper-gate", "not needed"), False),
    # ---- wrapper gate: missing data is an error
    ("a section's measurement missing fails", ledger(lambda d: d["sectionHeights"]["sections"].remove(meas(d, "/", "stats.card-grid"))), ("FAIL", "wrapper-gate"), False),
    ("a page height missing fails", ledger(lambda d: d["sectionHeights"]["pages"].pop(0)), ("FAIL", "wrapper-gate"), False),
    ("the whole sectionHeights block missing fails", ledger(lambda d: d.pop("sectionHeights")), ("FAIL", "wrapper-gate"), False),
    ("a non-numeric height fails", set_h(*HERO, "tall"), ("FAIL", "wrapper-gate"), False),
    ("an orphan measurement fails", ledger(lambda d: d["sectionHeights"]["sections"].append({"route": "/", "section": "content.testimonials", "heightPx": 500, "inFlow": True, "selector": "x"})), ("FAIL", "wrapper-gate"), False),
    ("manifest measuredSections count drift fails", lambda r: edit_json(r, "registry.manifest.json", lambda d: d["counts"].__setitem__("measuredSections", 22)), ("FAIL", "manifest-counts"), False),
    # ---- retrieval eligibility
    ("cookie banner flipped to retrievable (contract only)", contract("chrome.cookie-pane", lambda d: (d.__setitem__("retrievalEligible", True), d.pop("retrievalEligibleReason"))), ("FAIL", "section-contracts"), False),
    ("cookie banner flipped in contract AND allowlist together (pins hold)", both(contract("chrome.cookie-pane", lambda d: (d.__setitem__("retrievalEligible", True), d.pop("retrievalEligibleReason"))), allowlist(lambda d: d["retrievalIneligibleSections"].remove("chrome.cookie-pane"))), ("FAIL", "section-contracts"), False),
    ("hero made retrieval-ineligible (contract and allowlist together)", both(contract("hero.video-title", lambda d: (d.__setitem__("retrievalEligible", False), d.__setitem__("retrievalEligibleReason", "A hero is page content; this reason is long enough but the pin must still reject it."))), allowlist(lambda d: d["retrievalIneligibleSections"].append("hero.video-title"))), ("FAIL", "section-contracts"), False),
    ("retrievalEligibleReason under 30 characters", contract("overlay.contact", lambda d: d.__setitem__("retrievalEligibleReason", "utility dialog")), ("FAIL", "section-contracts"), False),
    ("retrievalEligibleReason missing on an ineligible section", contract("chrome.preloader", lambda d: d.pop("retrievalEligibleReason")), ("FAIL", "section-contracts"), False),
    ("retrievalEligible as the string 'false' (not a closed boolean)", contract("chrome.cursor", lambda d: d.__setitem__("retrievalEligible", "false")), ("FAIL", "section-contracts"), False),
    ("retrievalEligible missing", contract("chrome.header", lambda d: d.pop("retrievalEligible")), ("FAIL", "section-contracts"), False),
    ("allowlist retrievalIneligibleSections drifts from the contracts", allowlist(lambda d: d["retrievalIneligibleSections"].remove("chrome.cursor")), ("FAIL", "section-contracts"), False),
    # ---- closed contract schema, source vs semantic
    ("unknown top-level field on a contract", contract("chrome.footer", lambda d: d.__setitem__("category", "chrome")), ("FAIL", "section-contracts"), False),
    ("semantic.category outside the closed enum", contract("chrome.footer", lambda d: d["semantic"].__setitem__("category", "FEATURES")), ("FAIL", "section-contracts"), False),
    ("semantic.id differs from the contract id", contract("chrome.footer", lambda d: d["semantic"].__setitem__("id", "chrome.header")), ("FAIL", "section-contracts"), False),
    ("source object missing", contract("chrome.footer", lambda d: d.pop("source")), ("FAIL", "section-contracts"), False),
    ("extra field inside source", contract("chrome.footer", lambda d: d["source"].__setitem__("category", "FOOTER")), ("FAIL", "section-contracts"), False),
    ("taxonomy field smuggled into source (category)", contract("chrome.footer", lambda d: d["semantic"].__setitem__("file", "src/components/layout/Footer.jsx")), ("FAIL", "section-contracts"), False),
    ("a second HERO-class section on the home template", contract("media.scroll-picture", lambda d: d["semantic"].__setitem__("category", "HERO")), ("FAIL", "section-contracts"), False),
    ("source.lines past the end of the file (ledger range)", contract("chrome.footer", lambda d: d["source"].__setitem__("lines", "10-9999")), ("FAIL", "section-provenance"), False),
    ("source.file outside the ledger", contract("chrome.footer", lambda d: d["source"].__setitem__("file", "src/components/layout/Invented.jsx")), ("FAIL", "section-provenance"), False),
    ("source range in bounds but not the component (real file)", contract("chrome.footer", lambda d: d["source"].__setitem__("lines", "1-9")), ("FAIL", "section-provenance"), True),
    ("source.tag wrong for the rendered element (real file)", contract("chrome.footer", lambda d: d["source"].__setitem__("tag", "section")), ("FAIL", "section-provenance"), True),
    ("source.id names a different component (real file)", contract("chrome.footer", lambda d: d["source"].__setitem__("id", "Header")), ("FAIL", "section-provenance"), True),
    ("semantic.category valid but disagrees with ia.json (real source)", contract("content.title-description", lambda d: d["semantic"].__setitem__("category", "MEDIA")), ("FAIL", "section-provenance"), True),
]


def run_verify(root, source_root):
    cmd = [sys.executable, "-B", os.path.join(root, "extraction", "verify_all.py")]
    if source_root:
        cmd += ["--source-root", source_root]
    p = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    rows = []
    for line in p.stdout.splitlines():
        parts = line.split(None, 2)
        if len(parts) >= 2 and parts[0] in ("PASS", "FAIL", "WARN"):
            rows.append((parts[0], parts[1], parts[2] if len(parts) > 2 else ""))
    return p.returncode, rows


def judge(code, rows, expect):
    if expect[0] == "FAIL":
        hit = [m for s, c, m in rows if s == "FAIL" and c == expect[1]]
        return code == 1 and bool(hit), "verify_all FAIL " + ",".join(sorted({c for s, c, _ in rows if s == "FAIL"})) if code else "exit 0 (not rejected)"
    hit = [m for s, c, m in rows if s == "WARN" and c == expect[1] and expect[2] in m]
    return code == 0 and bool(hit), ("exit 0 + WARN: " + hit[0][:70]) if hit else "no matching WARN (exit %d)" % code


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch")
    ap.add_argument("--source-root", default=os.path.dirname(REPO))
    args = ap.parse_args()
    src = os.path.abspath(args.source_root)
    src = src if os.path.isfile(os.path.join(src, "src", "index.css")) else None
    if args.scratch:
        scratch = os.path.abspath(args.scratch)
        if not os.path.isdir(scratch) or os.listdir(scratch):
            print("--scratch must be an existing EMPTY directory: %s" % scratch)
            return 2
        owned = False
    else:
        scratch, owned = tempfile.mkdtemp(prefix="refire-prove-drift-"), True
    ok, skipped, results = True, 0, []
    try:
        base = os.path.join(scratch, "base", "design-repo")
        shutil.copytree(REPO, base, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        code, rows = run_verify(base, src)
        fails = [c for s, c, _ in rows if s == "FAIL"]
        results.append(("PASSES" if code == 0 else "BROKEN", "control: unmutated scratch copy", "verify_all exit %d %s" % (code, fails)))
        ok &= code == 0
        for name, fn, expect, needs_source in CASES:
            if needs_source and not src:
                skipped += 1
                results.append(("SKIPPED", name, "needs the real source tree (--source-root)"))
                continue
            work = os.path.join(scratch, "work", "design-repo")
            shutil.rmtree(os.path.join(scratch, "work"), ignore_errors=True)
            shutil.copytree(base, work)
            fn(work)
            code, rows = run_verify(work, src)
            hit, detail = judge(code, rows, expect)
            ok &= hit
            results.append((("REJECTED" if expect[0] == "FAIL" else "WARNED") if hit else "MISSED", name, detail))
    finally:
        if owned:
            shutil.rmtree(scratch, ignore_errors=True)
        else:
            for x in os.listdir(scratch):
                shutil.rmtree(os.path.join(scratch, x), ignore_errors=True)
    for r in results:
        print("  %-8s %-86s %s" % r)
    print("\nprove_drift: %s (%d cases, %d skipped, source tree %s)" % ("ALL DRIFT CASES BEHAVE AS EXPECTED" if ok else "FAILURES PRESENT", len(CASES), skipped, "present" if src else "ABSENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
