#!/usr/bin/env python3
"""Drift proof for the whole-page-wrapper gate, the retrieval-eligibility pin, the
source/semantic provenance checks, the asset-availability pins, the sourceBrand pattern
registry and the enforcement of PageSpec mode "generated".

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


def text_edit(rel, fn):
    def go(root):
        p = os.path.join(root, rel)
        with open(p, encoding="utf-8") as f:
            s = f.read()
        new = fn(s)
        assert new != s, "text edit did not change %s" % rel
        with open(p, "w", encoding="utf-8") as f:
            f.write(new)
    return go


def roles(fn):
    return lambda r: edit_json(r, "assets/asset-roles.json", fn)


def example(name, fn):
    return lambda r: edit_json(r, "schema/%s.pagespec.json" % name, fn)


def footer_brand(value):
    return lambda d: next(n for n in d["nodes"] if n["section"] == "chrome.footer")["content"].__setitem__("brand", value)


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
    # ---- mode: required closed enum, version bump, examples per template
    ("schema: mode no longer required", lambda r: edit_json(r, "schema/pagespec.schema.json", lambda d: d["required"].remove("mode")), ("FAIL", "asset-availability"), False),
    ("schema: mode enum widened", lambda r: edit_json(r, "schema/pagespec.schema.json", lambda d: d["properties"]["mode"]["enum"].append("demo")), ("FAIL", "asset-availability"), False),
    ("pageSpecVersion in the manifest drifts from the schema const", lambda r: edit_json(r, "registry.manifest.json", lambda d: d.__setitem__("pageSpecVersion", "1.0.0")), ("FAIL", "version-parity"), False),
    ("an example loses its mode", example("example", lambda d: d.pop("mode")), ("FAIL", "examples-validate"), False),
    ("the generated home example is deleted", lambda r: os.remove(os.path.join(r, "schema", "example.generated.pagespec.json")), ("FAIL", "generated-mode"), False),
    ("the generated 404 example is deleted", lambda r: os.remove(os.path.join(r, "schema", "example.generated-not-found.pagespec.json")), ("FAIL", "generated-mode"), False),
    ("the shipped generated example leaks the source brand", example("example.generated", footer_brand("Refire")), ("FAIL", "examples-validate"), False),
    ("the shipped generated 404 example leaks a source phone number", example("example.generated-not-found", lambda d: next(n for n in d["nodes"] if n["section"] == "overlay.contact")["content"]["phoneList"]["lines"][0].__setitem__("href", "tel:+17907909238")), ("FAIL", "examples-validate"), False),
    # ---- asset availability pins (registry edits, removed pins, contract flips)
    ("registry loosens brand.logo to generation-safe (code pins hold)", roles(lambda d: d["roles"]["brand.logo"].__setitem__("availability", "generation-safe")), ("FAIL", "asset-availability"), False),
    ("registry and its documented pin loosened together (code pins hold)", roles(lambda d: (d["roles"]["media.hero-video"].__setitem__("availability", "generation-safe"), d["pinnedAvailability"].__setitem__("media.hero-video", "generation-safe"))), ("FAIL", "asset-availability"), False),
    ("availability set outside the closed enum", roles(lambda d: d["roles"]["media.hero-poster"].__setitem__("availability", "free")), ("FAIL", "asset-availability"), False),
    ("a substitute is removed from a reference-only role", roles(lambda d: d["roles"]["media.hero-video"].pop("generationSafeSubstitutes")), ("FAIL", "asset-availability"), False),
    ("pin removed from verify_all.py", text_edit("extraction/verify_all.py", lambda s: s.replace('    "brand.logo": "reference-only",\n', "", 1)), ("FAIL", "asset-availability"), False),
    ("pin removed from semantic_validate.py", text_edit("schema/semantic_validate.py", lambda s: s.replace('    "brand.logo": "reference-only",\n', "", 1)), ("FAIL", "asset-availability"), False),
    ("pin loosened in semantic_validate.py to another valid value", text_edit("schema/semantic_validate.py", lambda s: s.replace('"font.brand-typeface": "blocked-for-generation"', '"font.brand-typeface": "reference-only"', 1)), ("FAIL", "asset-availability"), False),
    ("a contract lists the reference-only logo role for generated pages", contract("chrome.header", lambda d: (d["content"]["fields"]["logo"].__setitem__("generatedAssetRoles", ["brand.logo"]), d.__setitem__("generatedAssetRoles", ["brand.logo"]))), ("FAIL", "asset-availability"), False),
    ("registry, pins in the registry and a contract flipped together (code pins hold)", both(roles(lambda d: (d["roles"]["brand.logo"].__setitem__("availability", "generation-safe"), d["roles"]["brand.logo"].pop("generationSafeSubstitutes"), d["pinnedAvailability"].__setitem__("brand.logo", "generation-safe"))), contract("chrome.header", lambda d: (d["content"]["fields"]["logo"].__setitem__("generatedAssetRoles", ["brand.logo"]), d.__setitem__("generatedAssetRoles", ["brand.logo"])))), ("FAIL", "asset-availability"), False),
    ("allowlist generationSafeAssetRoles drifts from the registry", allowlist(lambda d: d["generationSafeAssetRoles"].remove("brand.logo-placeholder")), ("FAIL", "asset-availability"), False),
    # ---- sourceBrand registry: removal and loosening of patterns
    ("pattern removed: PRISMA product name", roles(lambda d: d["sourceBrand"]["patterns"]["brand"]["patterns"].pop(2)), ("FAIL", "source-brand-registry"), False),
    ("pattern removed: source phone numbers", roles(lambda d: d["sourceBrand"]["patterns"]["url"]["patterns"].pop(2)), ("FAIL", "source-brand-registry"), False),
    ("pattern removed: cookie / form microcopy", roles(lambda d: d["sourceBrand"]["patterns"]["copy"]["patterns"].pop()), ("FAIL", "source-brand-registry"), False),
    ("pattern loosened so it misses its own examples (brand name)", roles(lambda d: d["sourceBrand"]["patterns"]["brand"]["patterns"][0].__setitem__("pattern", "refirx")), ("FAIL", "source-brand-registry"), False),
    ("pattern loosened to match nothing (CTA)", roles(lambda d: d["sourceBrand"]["patterns"]["cta"]["patterns"][0].__setitem__("pattern", "(?!)")), ("FAIL", "source-brand-registry"), False),
    ("pattern AND its mustMatch examples loosened together (no longer matches the cited source literal)", roles(lambda d: d["sourceBrand"]["patterns"]["people"]["patterns"][0].update({"pattern": "greengtx", "mustMatch": ["greengtx"]})), ("FAIL", "source-brand-registry"), False),
    ("pattern AND its mustMatch loosened together: the code canary still rejects", roles(lambda d: d["sourceBrand"]["patterns"]["people"]["patterns"][0].update({"pattern": "greengtx", "mustMatch": ["greengtx"]})), ("FAIL", "generated-mode"), False),
    ("pattern widened until a clean control matches", roles(lambda d: d["sourceBrand"]["patterns"]["cta"]["patterns"][0].__setitem__("pattern", "view|read the overview")), ("FAIL", "source-brand-registry"), False),
    ("a whole category emptied (people)", roles(lambda d: d["sourceBrand"]["patterns"]["people"].__setitem__("patterns", [])), ("FAIL", "source-brand-registry"), False),
    ("a whole category emptied (copy): the validator must fail closed", roles(lambda d: d["sourceBrand"]["patterns"]["copy"].__setitem__("patterns", [])), ("FAIL", "generated-mode"), False),
    ("pattern evidence removed", roles(lambda d: d["sourceBrand"]["patterns"]["asset"]["patterns"][0].__setitem__("cite", [])), ("FAIL", "source-brand-registry"), False),
    ("registry claims a human review that never happened", roles(lambda d: d["sourceBrand"].__setitem__("reviewStatus", "REVIEWED by the design team")), ("FAIL", "source-brand-registry"), False),
    ("pattern evidence quote not in the real source file", roles(lambda d: d["sourceBrand"]["patterns"]["brand"]["patterns"][0]["cite"][0].__setitem__("quote", "Invented quote")), ("FAIL", "citations"), True),
    # ---- the validator stops enforcing generated mode
    ("validator no longer compares mode with generated", text_edit("schema/semantic_validate.py", lambda s: s.replace('mode == "generated"', 'mode == "generated-off"')), ("FAIL", "generated-mode"), False),
    ("validator stops scanning strings against the patterns", text_edit("schema/semantic_validate.py", lambda s: s.replace("for p, s in scan_strings(spec):", "for p, s in []:", 1)), ("FAIL", "generated-mode"), False),
    ("validator stops checking asset availability", text_edit("schema/semantic_validate.py", lambda s: s.replace('if av != "generation-safe":', "if False:", 1)), ("FAIL", "generated-mode"), False),
    ("validator stops normalising (NFKC) before matching", text_edit("schema/semantic_validate.py", lambda s: s.replace('t = unicodedata.normalize("NFKC", str(text))', "t = str(text)", 1)), ("FAIL", "generated-mode"), False),
    ("validator stops failing closed on an empty category", text_edit("schema/semantic_validate.py", lambda s: s.replace("if not r.patterns.get(cat):", "if False:", 1)), ("FAIL", "generated-mode"), False),
    ("validator applies generated rules to reference pages", text_edit("schema/semantic_validate.py", lambda s: s.replace('    if mode == "generated":\n        for role, pin in', '    if mode in MODES:\n        for role, pin in', 1)), ("FAIL", "generated-mode"), False),
    ("a GENERATED_MODE rule dropped from the graph", lambda r: edit_json(r, "compatibility/graph.json", lambda d: d.__setitem__("rules", [x for x in d["rules"] if x["id"] != "GENERATED_MODE_PERSON"])), ("FAIL", "graph-enforcement"), False),
    # ---- token catalog / policy cannot drift from the real token files
    ("catalog lists a token that does not exist", lambda r: edit_json(r, "tokens/llm/token-catalog.json", lambda d: d["categories"]["text"].append("text.neon")), ("FAIL", "token-integrity"), False),
    ("catalog loses a real token", lambda r: edit_json(r, "tokens/llm/token-catalog.json", lambda d: d["categories"]["surface"].remove("surface.card")), ("FAIL", "token-integrity"), False),
    ("a real token appears that the catalog does not list", lambda r: edit_json(r, "tokens/10-semantic/color.json", lambda d: d["tokens"].__setitem__("text.fresh", dict(d["tokens"]["text.primary"]))), ("FAIL", "token-integrity"), False),
    ("policy loses a category key", lambda r: edit_json(r, "tokens/llm/token-policy.json", lambda d: d["rawValueRestrictions"].pop("border")), ("FAIL", "token-integrity"), False),
    ("motion-patterns.json loses a pattern a contract uses", lambda r: edit_json(r, "tokens/llm/motion-patterns.json", lambda d: d["patterns"].pop("marquee-drag")), ("FAIL", "motion-patterns"), False),
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
