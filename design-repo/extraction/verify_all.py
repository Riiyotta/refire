#!/usr/bin/env python3
"""One-shot integrity check for this design-repo.

Run from anywhere:  python3 extraction/verify_all.py [--source-root PATH]

The repo root is derived from this file's location (never hardcoded). Citations
(`cite` / `*Cite` lists of {at, quote}) are resolved against the clone project
that contains this design-repo (default: the parent directory, override with
--source-root). When that source tree is absent -- e.g. in a standalone copy --
the source-dependent checks WARN instead of failing; every structural check
still runs, including citation ranges against the line counts recorded in
extraction/measured-values.json.

Drift checks proven to fail on bad input by schema/tests/adversarial_test.py
(scratch-copy mutations): allowlist parity, allowlist version, counts, citation
range, citation quote, unledgered citation path, pinned asset policies, graph <->
validator agreement, absolute paths, entryPoints, citation coverage, contract <->
schema parity, theme resolution, stack-neutral ids.

Also: asset availability (closed three-way enum pinned in code), the sourceBrand pattern registry
(every pattern compiles, matches its own mustMatch examples and the literal it cites, and is pinned by an
independent canary string in this file) and live generated-mode enforcement (canary leaks must be rejected
by the real validator), section contracts (closed schema, source vs semantic objects, retrieval-ineligible pin),
section provenance (every `source` resolved against the real file and the IA), one HERO per
template, and the whole-page-wrapper gate (extraction/wrapper_gate.py over the measured heights).
Those are proven by schema/tests/adversarial_test.py and extraction/prove_drift.py.

Exit code 0 = no FAIL (warnings allowed), 1 = at least one FAIL.
"""
import argparse
import glob
import json
import math
import os
import re
import sys

sys.dont_write_bytecode = True
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "schema"))

# Compliance-critical pins held in code, independent of the JSON they check
# (MASTER-GUIDE 3.23: membership in the enum is not enough).
PINNED_POLICIES = {
    "brand.logo": "placeholder-only",
    "brand.favicon": "placeholder-only",
    "media.hero-video": "placeholder-only",
    "media.hero-poster": "placeholder-only",
    "media.scroll-picture": "placeholder-only",
    "media.shader-picture": "placeholder-only",
    "media.social-image": "placeholder-only",
    "document.brochure": "placeholder-only",
    "font.brand-typeface": "must-reuse-exact",
}
# Availability of every asset role by PageSpec mode, held here independently of schema/semantic_validate.py (which keeps
# its own copy) and of assets/asset-roles.json: a registry edit alone cannot loosen a role, and all three must agree.
PINNED_AVAILABILITY = {
    "brand.logo": "reference-only",
    "brand.favicon": "reference-only",
    "media.hero-video": "reference-only",
    "media.hero-poster": "reference-only",
    "media.scroll-picture": "reference-only",
    "media.shader-picture": "reference-only",
    "media.social-image": "reference-only",
    "document.brochure": "reference-only",
    "font.brand-typeface": "blocked-for-generation",
    "ui.icon": "generation-safe",
    "brand.logo-placeholder": "generation-safe",
    "media.video-placeholder": "generation-safe",
    "media.image-generated": "generation-safe",
    "document.placeholder": "generation-safe",
    "font.system-stack": "generation-safe",
    "person.fictional": "generation-safe",
    "url.placeholder": "generation-safe",
    "copy.original": "generation-safe",
    "brand.fictional": "generation-safe",
}
AVAILABILITY_VALUES = ("reference-only", "generation-safe", "blocked-for-generation")
# One canary string per sourceBrand pattern id, held here in code: a pattern that is removed or loosened until the canary
# slips through makes verify_all fail, because the real validator must still reject it in a generated PageSpec.
CANARIES = {
    "brand-refire": ("GENERATED_MODE_BRAND", "Refire"),
    "brand-refire-spaced": ("GENERATED_MODE_BRAND", "R E F I R E"),
    "brand-product-prisma": ("GENERATED_MODE_BRAND", "PRISMA XXII"),
    "cta-view-brochure": ("GENERATED_MODE_CTA", "view our brochure"),
    "cta-visit-us": ("GENERATED_MODE_CTA", "Visit Us"),
    "cta-brand-verb": ("GENERATED_MODE_CTA", "Get Refire"),
    "copy-company-descriptor": ("GENERATED_MODE_COPY", "an international hydrogen energy technology company"),
    "copy-founding-story": ("GENERATED_MODE_COPY", "the most abundant element in the universe"),
    "copy-expansion-pitch": ("GENERATED_MODE_COPY", "is actively expanding its footprint"),
    "copy-hero-tagline": ("GENERATED_MODE_COPY", "Creating a Sustainable Future"),
    "copy-key-stats": ("GENERATED_MODE_COPY", "83K+"),
    "copy-event-programme": ("GENERATED_MODE_COPY", "Save the date"),
    "copy-event-booth": ("GENERATED_MODE_COPY", "BOOTH C45"),
    "copy-chrome-microcopy": ("GENERATED_MODE_COPY", "We use cookies to make things better"),
    "url-source-domain": ("GENERATED_MODE_URL", "https://refire.com/int/"),
    "url-source-placeholder-mailto": ("GENERATED_MODE_URL", "test@test.en"),
    "url-source-phone": ("GENERATED_MODE_URL", "+1 790 790 9238"),
    "asset-logo": ("GENERATED_MODE_ASSET", "inline-svg:logo-refire"),
    "asset-media-files": ("GENERATED_MODE_ASSET", "main-new.mp4"),
    "asset-public-path": ("GENERATED_MODE_ASSET", "/int/images/other.jpg"),
    "asset-favicon": ("GENERATED_MODE_ASSET", "apple-touch-icon.png"),
    "asset-typeface": ("GENERATED_MODE_ASSET", "SuisseIntl"),
    "person-partner-greengt": ("GENERATED_MODE_PERSON", "GreenGT"),
    "person-partner-apas": ("GENERATED_MODE_PERSON", "APAS"),
    "person-event-hannover": ("GENERATED_MODE_PERSON", "Hannover Messe"),
}
# Evasion canaries: the real validator must still reject these after normalisation (NFKC, zero-width, soft hyphen, curly quotes).
NORMALISATION_CANARIES = (
    ("GENERATED_MODE_BRAND", "Re\u200bfire"),
    ("GENERATED_MODE_BRAND", "Re\u00adfire"),
    ("GENERATED_MODE_BRAND", "\uff32\uff45\uff46\uff49\uff52\uff45"),
    ("GENERATED_MODE_COPY", "Select a department you\u2019d like to reach"),
    ("GENERATED_MODE_COPY", "We use cookies\u200b to make things better"),
    ("GENERATED_MODE_URL", "\uff0b\uff11 \uff17\uff19\uff10 \uff17\uff19\uff10 \uff19\uff12\uff13\uff18"),
)
# Utility/runtime UI that must stay retrievalEligible:false. Held here independently of
# schema/semantic_validate.py, which keeps its own copy; the contracts and the allowlist must
# equal both (editing contract + allowlist together cannot move the pin).
PINNED_RETRIEVAL_INELIGIBLE = frozenset({"chrome.cookie-pane", "chrome.cursor", "chrome.preloader", "overlay.contact"})
# Built from pieces so this file never contains the literal machine-path prefixes.
ABS_PATH = re.compile("|".join(["/" + "Users/", "/" + "home/", "[A-Za-z]:" + r"\\" + "Users"]))
STACK_WORDS = re.compile(r"(?i)(react|jsx|tailwind|gsap|lenis|three|vite|classname|nextjs|next\.js|webpack|usestate|useeffect)")
JUNK = {".DS_Store", "Thumbs.db", "desktop.ini"}
CITE_RE = re.compile(r"^(@?[^\s:@]+(?:/[^\s:]+)*):(\d+)(?:-(\d+))?$")

results = []  # (status, check, message)


def record(status, check, msg=""):
    results.append((status, check, msg))


def load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return json.load(f)


def json_files():
    out = []
    for p in glob.glob(os.path.join(REPO, "**", "*.json"), recursive=True):
        out.append(os.path.relpath(p, REPO))
    return sorted(out)


def iter_cites(obj, where):
    """Yield (location, cite-dict) for every cite / *Cite list in a JSON tree."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if (k == "cite" or k.endswith("Cite")) and isinstance(v, list):
                for c in v:
                    yield where + "." + k, c
            else:
                yield from iter_cites(v, where + "." + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_cites(v, "%s[%d]" % (where, i))


def collapse(s):
    return re.sub(r"\s+", " ", s).strip()


def count_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    if not data:
        return 0
    return data.count(b"\n") + (0 if data.endswith(b"\n") else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", default=os.path.dirname(REPO))
    args = ap.parse_args()
    src_root = os.path.abspath(args.source_root)
    # The source tree counts as present only if it really contains the cited project.
    source_present = os.path.isfile(os.path.join(src_root, "src", "index.css"))

    # ---------------------------------------------------------------- 1 parse
    docs = {}
    bad = []
    for rel in json_files():
        try:
            docs[rel] = load(rel)
        except Exception as e:  # noqa: BLE001
            bad.append("%s: %s" % (rel, e))
    record("FAIL" if bad else "PASS", "json-parse", "; ".join(bad) or "%d JSON files parse" % len(docs))
    if bad:
        return finish()

    manifest = docs["registry.manifest.json"]
    allow = docs["tokens/llm/component-allowlist.json"]
    schema = docs["schema/pagespec.schema.json"]
    roles_doc = docs["assets/asset-roles.json"]
    roles = roles_doc["roles"]
    tf = docs["templates/templates.json"]
    graph = docs["compatibility/graph.json"]
    ledger = docs["extraction/measured-values.json"]
    mp_doc = docs["tokens/llm/motion-patterns.json"]["patterns"]
    sections = {d["id"]: (rel, d) for rel, d in docs.items() if rel.startswith("sections/")}
    comps = {d["id"]: (rel, d) for rel, d in docs.items() if rel.startswith("components/")}
    prims = {d["id"]: (rel, d) for rel, d in docs.items() if rel.startswith("primitives/")}
    token_files = {rel: d for rel, d in docs.items() if re.match(r"tokens/(00|10|20|30)-", rel)}
    tokens = {}
    for d in token_files.values():
        tokens.update(d["tokens"])

    # ---------------------------------------------------------------- 2 schema is draft-07
    try:
        import jsonschema
        jsonschema.Draft7Validator.check_schema(schema)
        record("PASS", "schema-draft07", "pagespec.schema.json is a valid Draft-07 schema")
    except ImportError:
        record("FAIL", "schema-draft07", "jsonschema not installed: pip install -r extraction/requirements.txt")
        return finish()
    except Exception as e:  # noqa: BLE001
        record("FAIL", "schema-draft07", str(e)[:300])

    # ---------------------------------------------------------------- 3 examples validate (both layers)
    import semantic_validate as sv
    repo_model = sv.Repo(REPO)
    probs = []
    examples = sorted(glob.glob(os.path.join(REPO, "schema", "example*.json")))
    for p in examples:
        with open(p, encoding="utf-8") as f:
            errs, _w = sv.validate(json.load(f), repo_model)
        if errs:
            probs.append("%s: %s" % (os.path.basename(p), errs[:3]))
    record("FAIL" if probs or not examples else "PASS", "examples-validate", "; ".join(probs) or "%d example instances: 0 errors" % len(examples))

    # ---------------------------------------------------------------- 4 allowlist parity
    probs = []
    for kind, found in (("sections", sections), ("components", comps), ("primitives", prims)):
        listed = set(allow.get(kind, []))
        real = set(found)
        for x in sorted(listed - real):
            probs.append("phantom %s entry %r (no contract file)" % (kind, x))
        for x in sorted(real - listed):
            probs.append("orphan %s contract %r (no allowlist entry)" % (kind, x))
        for cid, (rel, _d) in found.items():
            if os.path.splitext(os.path.basename(rel))[0] not in (cid, cid.split(".", 1)[-1]):
                probs.append("file %s does not match id %s" % (rel, cid))
    if set(allow.get("templates", [])) != set(tf["templates"]):
        probs.append("allowlist templates %s != templates.json %s" % (allow.get("templates"), sorted(tf["templates"])))
    record("FAIL" if probs else "PASS", "allowlist-parity", "; ".join(probs) or "sections/components/primitives/templates all 1:1 with contract files")

    # ---------------------------------------------------------------- 5 versions
    probs = []
    if manifest.get("allowlistVersion") != allow.get("version"):
        probs.append("manifest allowlistVersion %r != allowlist version %r" % (manifest.get("allowlistVersion"), allow.get("version")))
    psv = schema["properties"]["pageSpecVersion"].get("const")
    if manifest.get("pageSpecVersion") != psv:
        probs.append("manifest pageSpecVersion %r != schema const %r" % (manifest.get("pageSpecVersion"), psv))
    record("FAIL" if probs else "PASS", "version-parity", "; ".join(probs) or "allowlistVersion and pageSpecVersion match (repositoryVersion is documentation-only)")

    # ---------------------------------------------------------------- 6 allowlist settable properties == schema
    probs = []
    if sorted(allow.get("pageSpecProperties", [])) != sorted(schema["properties"]):
        probs.append("pageSpecProperties drift")
    if sorted(allow.get("nodeProperties", [])) != sorted(schema["definitions"]["node"]["properties"]):
        probs.append("nodeProperties drift")
    mprops = sorted({k for name, d in schema["definitions"].items() if name.startswith("motion.") for k in d["properties"]})
    if sorted(allow.get("motionProperties", [])) != mprops:
        probs.append("motionProperties %s != schema %s" % (allow.get("motionProperties"), mprops))
    for name, d in schema["definitions"].items():
        if name.startswith("motion.") and d.get("additionalProperties") is not False:
            probs.append("%s is not closed" % name)
    record("FAIL" if probs else "PASS", "allowlist-properties", "; ".join(probs) or "allowlist node/motion/page properties equal the schema; every motion object closed")

    # ---------------------------------------------------------------- 7 asset roles closed + pinned
    probs = []
    enum = schema["definitions"]["assetRole"]["enum"]
    if not (set(enum) == set(roles) == set(allow.get("assetRoles", []))):
        probs.append("assetRole sets differ: schema %d, roles %d, allowlist %d" % (len(enum), len(roles), len(allow.get("assetRoles", []))))
    for rid, info in roles.items():
        if info.get("generationPolicy") not in roles_doc["generationPolicies"]:
            probs.append("%s has unknown policy %r" % (rid, info.get("generationPolicy")))
        if not info.get("guidance"):
            probs.append("%s has no AI-generation/licensing guidance" % rid)
    for rid, want in PINNED_POLICIES.items():
        if rid not in roles:
            probs.append("pinned role %s missing" % rid)
            continue
        if roles[rid]["generationPolicy"] != want:
            probs.append("pinned role %s must be %r, is %r" % (rid, want, roles[rid]["generationPolicy"]))
        if roles_doc.get("pinnedPolicies", {}).get(rid) != want:
            probs.append("pinnedPolicies[%s] must be %r" % (rid, want))
    for sid, (_rel, c) in sections.items():
        sv._walk_desc(c["content"]["fields"], lambda d, sid=sid: probs.append("%s slot uses unknown role %r" % (sid, d["assetRole"])) if d.get("assetRole") and d["assetRole"] not in roles else None)
    if source_present:
        for rid, info in roles.items():
            for s in info["allowedReferenceSources"]:
                if s.startswith("/int/") and not os.path.isfile(os.path.join(src_root, "public", s.lstrip("/"))):
                    probs.append("%s reference source %s missing from public/" % (rid, s))
    record("FAIL" if probs else "PASS", "asset-roles", "; ".join(probs) or "%d roles closed across schema/allowlist/registry; %d compliance pins hold" % (len(roles), len(PINNED_POLICIES)))

    # ---------------------------------------------------------------- 7b asset availability (R3), pinned in code
    probs = []
    for rid, info in roles.items():
        av = info.get("availability")
        if av not in AVAILABILITY_VALUES:
            probs.append("%s availability %r is not one of %s" % (rid, av, list(AVAILABILITY_VALUES)))
        if not info.get("generatedModeGuidance"):
            probs.append("%s has no generatedModeGuidance" % rid)
        subs = info.get("generationSafeSubstitutes", [])
        if av in ("reference-only", "blocked-for-generation"):
            if not subs:
                probs.append("%s (%s) has no generationSafeSubstitutes" % (rid, av))
            for s in subs:
                if s not in roles or roles[s].get("availability") != "generation-safe":
                    probs.append("%s substitute %r is not a generation-safe role" % (rid, s))
        elif subs:
            probs.append("generation-safe role %s must not list substitutes" % rid)
    if set(PINNED_AVAILABILITY) != set(roles):
        probs.append("availability pin covers %s but the registry has %s" % (sorted(PINNED_AVAILABILITY), sorted(roles)))
    for rid, want in PINNED_AVAILABILITY.items():
        if roles.get(rid, {}).get("availability") != want:
            probs.append("pinned availability of %s is %r, registry says %r" % (rid, want, roles.get(rid, {}).get("availability")))
        if roles_doc.get("pinnedAvailability", {}).get(rid) != want:
            probs.append("registry pinnedAvailability[%s] must be %r" % (rid, want))
    if dict(sv.PINNED_AVAILABILITY) != PINNED_AVAILABILITY:
        probs.append("semantic_validate.PINNED_AVAILABILITY differs from the verify_all pin: %s" % sorted(set(sv.PINNED_AVAILABILITY.items()) ^ set(PINNED_AVAILABILITY.items())))
    if set(roles_doc.get("availabilityValues", {})) != set(AVAILABILITY_VALUES) or set(roles_doc.get("modes", {})) != {"reference", "generated"}:
        probs.append("registry availabilityValues / modes are not the closed sets")
    for need in ("brand.logo-placeholder", "media.image-generated", "media.video-placeholder", "person.fictional", "url.placeholder", "copy.original"):
        if PINNED_AVAILABILITY.get(need) != "generation-safe":
            probs.append("generation-safe role %s is required" % need)
    for rid in ("brand.logo", "brand.favicon"):
        if roles[rid]["generationPolicy"] == "must-reuse-exact" or PINNED_AVAILABILITY.get(rid) != "reference-only":
            probs.append("a real wordmark/logo (%s) can never be must-reuse-exact or generation-safe" % rid)
    safe = {rid for rid, w in PINNED_AVAILABILITY.items() if w == "generation-safe"}
    for sid, (_rel, c) in sections.items():
        union = []
        slots = []

        def slot(desc, sid=sid):
            if desc.get("assetRole"):
                slots.append(desc)
                for g in desc.get("generatedAssetRoles", []):
                    if g not in union:
                        union.append(g)
                if not desc.get("generatedAssetRoles"):
                    probs.append("%s: asset field for %s lists no generatedAssetRoles" % (sid, desc["assetRole"]))
                for g in desc.get("generatedAssetRoles", []):
                    if g not in safe:
                        probs.append("%s: generatedAssetRoles lists %s, which is not generation-safe" % (sid, g))
                    elif not roles.get(g, {}).get("pageSpecSlot"):
                        probs.append("%s: generated role %s is not a pageSpecSlot role" % (sid, g))
        sv._walk_desc(c["content"]["fields"], slot)
        if sorted(c.get("generatedAssetRoles", [])) != sorted(union) or len(c.get("generatedAssetRoles", [])) != len(set(c.get("generatedAssetRoles", []))):
            probs.append("%s: section generatedAssetRoles %s != union of its fields %s" % (sid, c.get("generatedAssetRoles"), union))
    if sorted(allow.get("generationSafeAssetRoles", [])) != sorted(safe):
        probs.append("allowlist generationSafeAssetRoles != the generation-safe roles")
    if allow.get("modes") != ["reference", "generated"]:
        probs.append("allowlist modes != ['reference', 'generated']")
    if schema["properties"].get("mode", {}).get("enum") != ["reference", "generated"] or "mode" not in schema["required"]:
        probs.append("schema mode must be a required closed enum ['reference', 'generated']")
    record("FAIL" if probs else "PASS", "asset-availability", "; ".join(probs[:6]) + (" (+%d more)" % (len(probs) - 6) if len(probs) > 6 else "") if probs else "%d roles: closed three-way availability pinned in code (semantic_validate.py and verify_all.py agree with the registry), %d generation-safe, every reference-only/blocked role has generation-safe substitutes, every asset slot lists generatedAssetRoles" % (len(roles), len(safe)))

    # ---------------------------------------------------------------- 7c sourceBrand registry (R2): derived, evidenced, pinned
    probs = []
    sb = roles_doc.get("sourceBrand", {})
    spats = sb.get("patterns", {})
    if set(spats) != set(sv.SOURCE_CODES):
        probs.append("sourceBrand.patterns categories %s != validator SOURCE_CODES %s" % (sorted(spats), sorted(sv.SOURCE_CODES)))
    seen_ids = set()
    n_pat = 0
    for cat, block in spats.items():
        if block.get("code") != sv.SOURCE_CODES.get(cat):
            probs.append("%s: registry code %r != validator code %r" % (cat, block.get("code"), sv.SOURCE_CODES.get(cat)))
        if not block.get("patterns"):
            probs.append("%s has no patterns (the validator would fail closed)" % cat)
        compiled = []
        for pt in block.get("patterns", []):
            n_pat += 1
            pid = pt.get("id", "?")
            if pid in seen_ids:
                probs.append("duplicate pattern id %s" % pid)
            seen_ids.add(pid)
            if pt.get("kind") not in ("literal", "generalisation") or not pt.get("description") or not pt.get("mustMatch") or not pt.get("cite"):
                probs.append("%s: needs kind (literal|generalisation), description, mustMatch and cite" % pid)
                continue
            try:
                rx = re.compile(sv.norm_scan(pt["pattern"]), re.I)
            except re.error as e:
                probs.append("%s: pattern does not compile: %s" % (pid, e))
                continue
            compiled.append((pid, rx))
            for m in pt["mustMatch"]:
                if not rx.search(sv.norm_scan(m)):
                    probs.append("%s does not match its own mustMatch example %r" % (pid, m))
            if pt["kind"] == "literal" and not any(rx.search(sv.norm_scan(c.get("quote", ""))) for c in pt["cite"]):
                probs.append("%s is a literal pattern but matches none of its cited source quotes" % pid)
        for neg in block.get("mustNotMatch", []):
            for pid, rx in compiled:
                if rx.search(sv.norm_scan(neg)):
                    probs.append("%s: control %r must not match but %s does" % (cat, neg, pid))
        if not block.get("mustNotMatch"):
            probs.append("%s has no mustNotMatch controls" % cat)
    for pid in CANARIES:
        if pid not in seen_ids:
            probs.append("pinned pattern %s was removed from the registry" % pid)
    for pid in seen_ids - set(CANARIES):
        probs.append("pattern %s has no canary pin in verify_all.py" % pid)
    if not str(sb.get("reviewStatus", "")).startswith("UNREVIEWED"):
        probs.append("sourceBrand.reviewStatus must say UNREVIEWED unless a human review is recorded (it is not)")
    for k in ("names", "normalization", "notApplicable", "reservedUrlHosts"):
        if not sb.get(k):
            probs.append("sourceBrand.%s missing" % k)
    record("FAIL" if probs else "PASS", "source-brand-registry", "; ".join(probs[:6]) + (" (+%d more)" % (len(probs) - 6) if len(probs) > 6 else "") if probs else "%d patterns in %d categories: compile, match their mustMatch examples and cited literals, controls stay clean, every id pinned by a canary (UNREVIEWED by a human)" % (n_pat, len(spats)))

    # ---------------------------------------------------------------- 7d generated mode is really enforced (R1/R2/R4)
    probs = []
    import copy as _copy
    by_tpl = {}
    for pth in examples:
        with open(pth, encoding="utf-8") as fh:
            ex = json.load(fh)
        if ex.get("mode") not in ("reference", "generated"):
            probs.append("%s has no valid mode" % os.path.basename(pth))
        by_tpl.setdefault(ex.get("template"), {}).setdefault(ex.get("mode"), []).append((os.path.basename(pth), ex))
    for tid in tf["templates"]:
        for md in ("reference", "generated"):
            if not by_tpl.get(tid, {}).get(md):
                probs.append("template %s has no mode:%s example" % (tid, md))
    gen_home = next((ex for n_, ex in by_tpl.get("template.home", {}).get("generated", [])), None)
    ref_home = next((ex for n_, ex in by_tpl.get("template.home", {}).get("reference", [])), None)

    def host(spec, text):
        s = _copy.deepcopy(spec)
        nd = next(x for x in s["nodes"] if x["section"] == "content.title-description")
        nd["content"]["description"] = text
        return s

    def rejected(spec, code):
        errs, _w = sv.validate(spec, repo_model)
        return any(e[0] == code for e in errs)
    if gen_home and ref_home:
        for pid, (code, text) in CANARIES.items():
            if not rejected(host(gen_home, "A line with " + text + " in it"), code):
                probs.append("canary %s (%r) is not rejected as %s in a generated page" % (pid, text, code))
        for code, text in NORMALISATION_CANARIES:
            if not rejected(host(gen_home, "A line with " + text + " in it"), code):
                probs.append("normalisation canary %r is not rejected as %s" % (text, code))
        # reference mode must keep validating real content: the same canary text stays legal there
        errs, _w = sv.validate(host(ref_home, "A line with Refire and PRISMA XXII and view our brochure in it"), repo_model)
        if any(e[0].startswith("GENERATED_MODE") for e in errs):
            probs.append("generated-mode rules fire on a reference page: %s" % [e[0] for e in errs if e[0].startswith("GENERATED_MODE")])
        # asset rules
        def setrole(spec, role, src):
            s = _copy.deepcopy(spec)
            nd = next(x for x in s["nodes"] if x["section"] == "chrome.header")
            nd["content"]["logo"] = {"assetRole": role, "src": src}
            return s
        for role, src, code in (("brand.logo", "placeholder:brand.logo", "GENERATED_MODE_REFERENCE_ASSET"), ("brand.logo", "inline-svg:logo-refire", "GENERATED_MODE_REFERENCE_ASSET"),
                                ("media.video-placeholder", "placeholder:media.video-placeholder", "GENERATED_MODE_ROLE"), ("font.brand-typeface", "placeholder:font.brand-typeface", "GENERATED_MODE_REFERENCE_ASSET")):
            if not rejected(setrole(gen_home, role, src), code):
                probs.append("generated page with role %s (%s) is not rejected as %s" % (role, src, code))
        loose = _copy.deepcopy(gen_home)
        nd = next(x for x in loose["nodes"] if x["section"] == "hero.video-title")
        nd["content"]["link"]["href"] = "placeholder:document.brochure"
        if not rejected(loose, "GENERATED_MODE_REFERENCE_ASSET"):
            probs.append("generated page linking placeholder:document.brochure is not rejected")
        flipped = _copy.deepcopy(repo_model)
        flipped.roles["brand.logo"]["availability"] = "generation-safe"
        errs, _w = sv.validate(setrole(gen_home, "brand.logo", "placeholder:brand.logo"), flipped)
        if not any(e[0] in ("ASSET_AVAILABILITY_DRIFT", "GENERATED_MODE_REFERENCE_ASSET") for e in errs):
            probs.append("a registry-only availability edit is not caught by the code pin")
        empty = _copy.deepcopy(repo_model)
        empty.patterns["brand"] = []
        if not rejected(gen_home, "GENERATED_MODE_PATTERNS_MISSING") and not any(e[0] == "GENERATED_MODE_PATTERNS_MISSING" for e in sv.validate(gen_home, empty)[0]):
            probs.append("an empty pattern category does not fail closed")
    else:
        probs.append("need both a reference and a generated template.home example")
    record("FAIL" if probs else "PASS", "generated-mode", "; ".join(probs[:6]) + (" (+%d more)" % (len(probs) - 6) if len(probs) > 6 else "") if probs else "every template has a reference and a generated example; %d canary leaks (plus %d normalisation evasions) are rejected by the real validator in a generated page and stay legal in a reference page; reference-only/blocked roles, wrong-slot roles, registry-only availability edits and an emptied pattern category are all rejected" % (len(CANARIES), len(NORMALISATION_CANARIES)))

    # ---------------------------------------------------------------- 8 contract <-> schema parity
    probs = []

    def cmp_field(desc, sch, path):
        t = desc["type"]
        if t == "object":
            props = sch.get("properties", {})
            if set(props) != set(desc["fields"]) or set(sch.get("required", [])) != set(desc["fields"]) or sch.get("additionalProperties") is not False:
                probs.append("%s: object fields %s != schema %s" % (path, sorted(desc["fields"]), sorted(props)))
                return
            for k, d in desc["fields"].items():
                cmp_field(d, props[k], path + "." + k)
        elif t == "list":
            if sch.get("type") != "array" or sch.get("minItems") != desc["minItems"] or sch.get("maxItems") != desc["maxItems"]:
                probs.append("%s: list bounds drift" % path)
                return
            cmp_field(desc["item"], sch["items"], path + "[]")
        elif t == "string":
            if sch.get("type") != "string" or sch.get("maxLength") != desc.get("maxChars") or sch.get("pattern") != desc.get("pattern"):
                probs.append("%s: string constraints drift" % path)
        elif t == "const":
            if sch.get("const") != desc["value"]:
                probs.append("%s: const drift" % path)
        elif t == "asset":
            if sch.get("allOf", [{}, {}])[1].get("properties", {}).get("assetRole", {}).get("enum") != [desc["assetRole"]] + list(desc.get("generatedAssetRoles", [])):
                probs.append("%s: asset role pin drift (schema enum must be the slot role plus its generatedAssetRoles)" % path)
        elif t == "link":
            if sch.get("$ref") != "#/definitions/href." + desc["hrefKind"]:
                probs.append("%s: link kind drift" % path)
        elif t == "integer":
            if (sch.get("minimum"), sch.get("maximum")) != (desc["minimum"], desc["maximum"]):
                probs.append("%s: integer bounds drift" % path)

    for sid, (_rel, c) in sections.items():
        sc = schema["definitions"].get("content." + sid)
        sm = schema["definitions"].get("motion." + sid)
        if not sc or not sm:
            probs.append("%s has no schema content/motion definition" % sid)
            continue
        cmp_field({"type": "object", "fields": c["content"]["fields"]}, sc, sid)
        if sm["properties"]["pattern"].get("const") != c["motion"]["pattern"]:
            probs.append("%s motion pattern drift" % sid)
        if ("threshold" in c["motion"]) != ("threshold" in sm["properties"]) or ("threshold" in c["motion"] and sm["properties"]["threshold"]["const"] != c["motion"]["threshold"]):
            probs.append("%s motion threshold drift" % sid)
        if c["motion"].get("reducedMotionFallback") != "none-in-source":
            probs.append("%s reducedMotionFallback must record 'none-in-source'" % sid)
        for d in ("desktop", "tablet", "mobile"):
            if d not in c.get("responsive", {}):
                probs.append("%s responsive lacks %s" % (sid, d))
    if set(schema["definitions"]["node"]["properties"]["section"]["enum"]) != set(sections):
        probs.append("schema section enum != sections/")
    for name in schema["definitions"]:
        if name.startswith(("content.", "motion.")) and name.split(".", 1)[1] not in sections:
            probs.append("schema definition %s has no contract" % name)
    record("FAIL" if probs else "PASS", "contract-schema-parity", "; ".join(probs[:8]) or "all %d section contracts match their schema content/motion definitions" % len(sections))

    # ---------------------------------------------------------------- 9 templates + routes
    probs = []
    for tid, t in tf["templates"].items():
        for n in t["nodes"]:
            if not isinstance(n, dict) or not {"section", "required", "repeatable"} <= set(n):
                probs.append("%s node %r is not a structured object" % (tid, n))
                continue
            if n["section"] not in sections:
                probs.append("%s lists unknown section %s" % (tid, n["section"]))
        for f in t.get("forbiddenSections", []):
            if f in [n["section"] for n in t["nodes"]]:
                probs.append("%s lists its own forbidden section %s" % (tid, f))
    for sid, (_rel, c) in sections.items():
        using = sorted(tid for tid, t in tf["templates"].items() if sid in [n["section"] for n in t["nodes"]])
        if sorted(c["usedInTemplates"]) != using:
            probs.append("%s usedInTemplates %s != templates %s" % (sid, c["usedInTemplates"], using))
    seen = {}
    for r in tf["routes"]:
        seen.setdefault(r["path"], []).append(r["template"])
        if r["template"] not in tf["templates"] or r["path"] not in tf["templates"][r["template"]]["routes"]:
            probs.append("route %s not bound by its template" % r["path"])
    for p, ts in seen.items():
        if len(ts) != 1:
            probs.append("route %s assigned %d times" % (p, len(ts)))
    for tid, t in tf["templates"].items():
        for p in t["routes"]:
            if p not in seen:
                probs.append("%s route %s missing from routes[]" % (tid, p))
    record("FAIL" if probs else "PASS", "templates-routes", "; ".join(probs) or "%d templates with structured nodes; %d routes mapped 1:1" % (len(tf["templates"]), len(tf["routes"])))

    # ---------------------------------------------------------------- 9b section contracts: closed schema, source vs semantic, retrieval pin
    probs = []
    csch = repo_model.contract_schema
    try:
        jsonschema.Draft7Validator.check_schema(csch)
    except Exception as e:  # noqa: BLE001
        probs.append("section-contract.schema.json is not valid Draft-07: %s" % str(e)[:120])
    for rule, cid, msg in sv.lint_contracts(repo_model):
        probs.append("%s %s: %s" % (rule, cid, msg))
    if csch.get("additionalProperties") is not False:
        probs.append("section-contract schema top level is not closed")
    for k in ("semantic", "source"):
        if csch["properties"][k].get("additionalProperties") is not False:
            probs.append("section-contract schema %s object is not closed" % k)
    if csch["properties"]["retrievalEligible"].get("type") != "boolean":
        probs.append("retrievalEligible must be a closed boolean in the contract schema")
    if sorted(allow.get("sectionContractProperties", [])) != sorted(csch["properties"]):
        probs.append("allowlist sectionContractProperties != section-contract schema properties")
    if sorted(allow.get("semanticCategories", [])) != sorted(csch["properties"]["semantic"]["properties"]["category"]["enum"]):
        probs.append("allowlist semanticCategories != section-contract schema category enum")
    inelig = {sid for sid, (_r, c) in sections.items() if c.get("retrievalEligible") is False}
    if inelig != set(PINNED_RETRIEVAL_INELIGIBLE):
        probs.append("retrieval-ineligible contracts %s != verify_all pin %s" % (sorted(inelig), sorted(PINNED_RETRIEVAL_INELIGIBLE)))
    if set(allow.get("retrievalIneligibleSections", [])) != set(PINNED_RETRIEVAL_INELIGIBLE):
        probs.append("allowlist retrievalIneligibleSections != verify_all pin")
    if set(sv.PINNED_RETRIEVAL_INELIGIBLE) != set(PINNED_RETRIEVAL_INELIGIBLE):
        probs.append("semantic_validate pin %s != verify_all pin %s" % (sorted(sv.PINNED_RETRIEVAL_INELIGIBLE), sorted(PINNED_RETRIEVAL_INELIGIBLE)))
    for sid, (_r, c) in sections.items():
        reason = c.get("retrievalEligibleReason")
        if c.get("retrievalEligible") is False and not (isinstance(reason, str) and len(reason.strip()) >= 30):
            probs.append("%s: retrievalEligibleReason must be 30+ characters" % sid)
    for tid, t in tf["templates"].items():
        heroes = [n["section"] for n in t["nodes"] if sections.get(n["section"], ("", {}))[1].get("semantic", {}).get("category") == "HERO"]
        if len(heroes) > 1:
            probs.append("%s has %d HERO-class sections %s; a marketing page gets one hero" % (tid, len(heroes), heroes))
    record("FAIL" if probs else "PASS", "section-contracts", "; ".join(probs[:6]) + (" (+%d more)" % (len(probs) - 6) if len(probs) > 6 else "") if probs else "%d contracts satisfy the closed contract schema; %d retrieval-ineligible sections match the code pins (semantic_validate.py and verify_all.py) and the allowlist; at most one HERO per template" % (len(sections), len(inelig)))

    # ---------------------------------------------------------------- 9c section provenance: every source object resolved
    probs = []
    ledger_sources = ledger.get("sources", {})
    ia = None
    ia_path = os.path.join(src_root, "ia.json")
    if source_present and os.path.isfile(ia_path):
        with open(ia_path, encoding="utf-8") as f:
            ia = json.load(f)
    ia_by_file = {s.get("implementedBy"): (iid, s) for iid, s in (ia or {}).get("sections", {}).items()}
    src_cache = {}
    for sid, (_r, c) in sections.items():
        s = c.get("source", {})
        m = re.fullmatch(r"(\d+)-(\d+)", str(s.get("lines", "")))
        f = s.get("file", "")
        key = f
        if not m or key not in ledger_sources:
            probs.append("%s: source %s:%s is not in the ledger or has malformed lines" % (sid, f, s.get("lines")))
            continue
        a, b = int(m.group(1)), int(m.group(2))
        if a < 1 or b < a or b > ledger_sources[key]["lines"]:
            probs.append("%s: source lines %d-%d out of range of %s (%d lines)" % (sid, a, b, f, ledger_sources[key]["lines"]))
            continue
        if source_present:
            real = next((rp + f[len(al):] for al, rp in ledger.get("pathAliases", {}).items() if f.startswith(al + "/")), f)
            full = os.path.join(src_root, real)
            if not os.path.isfile(full):
                probs.append("%s: source file %s missing from source root" % (sid, f))
                continue
            if f not in src_cache:
                with open(full, encoding="utf-8", errors="replace") as fh:
                    src_cache[f] = fh.read().split("\n")
            lines = src_cache[f]
            if b > len(lines):
                probs.append("%s: source lines %d-%d exceed the real file (%d lines)" % (sid, a, b, len(lines)))
                continue
            if not re.search(r"\bfunction\s+%s\b" % re.escape(s["id"]), lines[a - 1]):
                probs.append("%s: line %d of %s does not declare function %s" % (sid, a, f, s["id"]))
            tag = re.search(r"<([a-z][a-z0-9]*)\b", "\n".join(lines[a - 1:b]))
            if not tag or tag.group(1) != s["tag"]:
                probs.append("%s: first host element in %s:%d-%d is <%s>, contract says <%s>" % (sid, f, a, b, tag.group(1) if tag else "none", s["tag"]))
            if ia is not None:
                hit = ia_by_file.get(real)
                if not hit:
                    probs.append("%s: no IA section is implementedBy %s" % (sid, real))
                elif hit[1].get("category") != c["semantic"]["category"]:
                    probs.append("%s: semantic.category %s != IA %s category %s" % (sid, c["semantic"]["category"], hit[0], hit[1].get("category")))
    record("FAIL" if probs else "PASS", "section-provenance", "; ".join(probs[:6]) + (" (+%d more)" % (len(probs) - 6) if len(probs) > 6 else "") if probs else "%d source objects resolve (ledger ranges%s); semantic categories%s" % (len(sections), ", real function declaration and first host element" if source_present else "", " agree with ia.json" if ia is not None else " not compared (no ia.json beside the source)"))

    # ---------------------------------------------------------------- 9d whole-page-wrapper gate
    import wrapper_gate
    gate_findings = wrapper_gate.evaluate({sid: c for sid, (_r, c) in sections.items()}, tf["templates"], ledger, docs.get("extraction/wrapper-whitelist.json", {}))
    gfails = [m for s, m in gate_findings if s == "FAIL"]
    record("FAIL" if gfails else "PASS", "wrapper-gate", "; ".join(gfails[:6]) + (" (+%d more)" % (len(gfails) - 6) if len(gfails) > 6 else "") if gfails else wrapper_gate.summary({sid: c for sid, (_r, c) in sections.items()}, tf["templates"], ledger))
    for s, m in gate_findings:
        if s == "WARN":
            record("WARN", "wrapper-gate", m)

    # ---------------------------------------------------------------- 10 graph <-> enforcement agreement
    probs = []
    with open(os.path.join(REPO, "schema", "semantic_validate.py"), encoding="utf-8") as f:
        vsrc = f.read()
    with open(os.path.join(REPO, "schema", "pagespec.schema.json"), encoding="utf-8") as f:
        ssrc = f.read()
    gsem = {r["id"] for r in graph["rules"] if r["enforcedBy"] == "semantic"}
    if gsem != set(sv.SEMANTIC_RULES):
        probs.append("graph semantic rules %s vs validator registry %s" % (sorted(gsem ^ set(sv.SEMANTIC_RULES)), "symmetric difference"))
    for rid in gsem:
        if vsrc.count('"%s"' % rid) < 2:
            probs.append("rule %s is registered but never emitted by the validator" % rid)
    gcon = {r["id"] for r in graph["rules"] if r["enforcedBy"] == "contract"}
    if gcon != set(sv.CONTRACT_RULES):
        probs.append("graph contract rules %s vs validator CONTRACT_RULES %s" % (sorted(gcon), sorted(sv.CONTRACT_RULES)))
    for rid in gcon:
        if vsrc.count('"%s"' % rid) < 2:
            probs.append("contract rule %s is registered but never emitted by lint_contracts" % rid)
    ggate = {r["id"] for r in graph["rules"] if r["enforcedBy"] == "gate"}
    if ggate != {wrapper_gate.RULE_ID}:
        probs.append("graph gate rules %s != wrapper_gate.RULE_ID %s" % (sorted(ggate), wrapper_gate.RULE_ID))
    for r in graph["rules"]:
        if r["severity"] not in ("error", "warn"):
            probs.append("rule %s bad severity" % r["id"])
        if r["enforcedBy"] == "schema" and ("rule:" + r["id"]) not in ssrc:
            probs.append("schema rule %s has no rule:%s marker in the schema" % (r["id"], r["id"]))
        if r["enforcedBy"] not in ("schema", "semantic", "contract", "gate"):
            probs.append("rule %s has unknown enforcedBy" % r["id"])
    for rule, tids in graph.get("exceptions", {}).items():
        for t in tids:
            if t not in tf["templates"]:
                probs.append("exception %s names unknown template %s" % (rule, t))
    record("FAIL" if probs else "PASS", "graph-enforcement", "; ".join(probs) or "%d graph rules each enforced by the layer they name (%d semantic, %d contract, %d gate, %d schema)" % (len(graph["rules"]), len(gsem), len(gcon), len(ggate), len(graph["rules"]) - len(gsem) - len(gcon) - len(ggate)))

    # ---------------------------------------------------------------- 11 manifest counts recomputed
    def ntok(folder):
        return sum(len(d["tokens"]) for rel, d in token_files.items() if rel.startswith("tokens/" + folder))
    actual = {
        "foundationTokens": ntok("00-foundation"), "semanticTokens": ntok("10-semantic"), "componentTokens": ntok("20-component"), "layoutTokens": ntok("30-layout"),
        "typeRoles": len([k for k in tokens if k.startswith("type.")]), "themes": len([r for r in docs if r.startswith("tokens/themes/")]),
        "primitives": len(prims), "components": len(comps), "sections": len(sections), "templates": len(tf["templates"]), "routes": len(tf["routes"]),
        "assetRoles": len(roles), "graphRules": len(graph["rules"]), "exampleInstances": len(examples),
        "retrievalIneligibleSections": len([1 for _r, c in sections.values() if c.get("retrievalEligible") is False]),
        "measuredSections": len(ledger.get("sectionHeights", {}).get("sections", [])),
        "motionPatterns": len(mp_doc),
        "generationSafeAssetRoles": len(safe),
        "sourceBrandPatterns": n_pat,
        "generatedExampleInstances": len([1 for _t, md in by_tpl.items() for k, v in md.items() if k == "generated" for _x in v]),
    }
    diff = {k: (manifest.get("counts", {}).get(k), v) for k, v in actual.items() if manifest.get("counts", {}).get(k) != v}
    extra = set(manifest.get("counts", {})) - set(actual)
    record("FAIL" if diff or extra else "PASS", "manifest-counts", ("drift (manifest, actual): %s %s" % (diff, sorted(extra))) if diff or extra else "counts recomputed from disk: %s" % actual)

    # ---------------------------------------------------------------- 11b README states the real counts
    readme_path = os.path.join(REPO, "README.md")
    if os.path.isfile(readme_path):
        with open(readme_path, encoding="utf-8") as f:
            readme = f.read()
        stale = ["%s=%s" % (k, v) for k, v in actual.items() if ("| `%s` | %s |" % (k, v)) not in readme]
        record("FAIL" if stale else "PASS", "readme-counts", ("README counts table missing/stale for: " + ", ".join(stale)) if stale else "README counts table equals the recomputed counts")
    else:
        record("FAIL", "readme-counts", "README.md missing")

    # ---------------------------------------------------------------- 12 citations
    sources = ledger.get("sources", {})
    aliases = ledger.get("pathAliases", {})

    def resolve_alias(path):
        for a, real in aliases.items():
            if path.startswith(a + "/"):
                return real + path[len(a):]
        return path
    probs, warns = [], []
    file_cache = {}
    n_cites = 0
    for rel, d in docs.items():
        for loc, c in iter_cites(d, rel):
            n_cites += 1
            at = c.get("at", "") if isinstance(c, dict) else ""
            m = CITE_RE.match(at)
            if not m or not isinstance(c.get("quote"), str) or not c["quote"].strip():
                probs.append("%s: malformed citation %r" % (loc, c))
                continue
            path, a = m.group(1), int(m.group(2))
            b = int(m.group(3) or a)
            if path not in sources:
                probs.append("%s: %s is not in the measured-values ledger" % (loc, path))
                continue
            if a < 1 or b < a or b > sources[path]["lines"]:
                probs.append("%s: %s out of range (ledger records %d lines)" % (loc, at, sources[path]["lines"]))
                continue
            if not source_present:
                continue
            full = os.path.join(src_root, resolve_alias(path))
            if not os.path.isfile(full):
                probs.append("%s: cited file %s missing from source root" % (loc, path))
                continue
            if path not in file_cache:
                with open(full, encoding="utf-8", errors="replace") as f:
                    file_cache[path] = f.read().split("\n")
            lines = file_cache[path]
            if b > len(lines):
                probs.append("%s: %s exceeds the real file (%d lines)" % (loc, at, len(lines)))
                continue
            if collapse(c["quote"]) not in collapse(" ".join(lines[a - 1:b])):
                probs.append("%s: quote not found at %s: %r" % (loc, at, c["quote"][:70]))
    if source_present:
        for path, info in sources.items():
            full = os.path.join(src_root, resolve_alias(path))
            if os.path.isfile(full) and count_lines(full) != info["lines"]:
                warns.append("%s changed length since extraction (%d -> %d lines); quotes still verified" % (path, info["lines"], count_lines(full)))
    else:
        warns.append("source tree not found at %s: citation ranges checked against the ledger only; quote checks skipped" % ("--source-root" if args.source_root != os.path.dirname(REPO) else "the parent directory"))
    cited_paths = {CITE_RE.match(c.get("at", "")).group(1) for d in docs.values() for _l, c in iter_cites(d, "") if isinstance(c, dict) and CITE_RE.match(c.get("at", ""))}
    for p in sorted(set(sources) - cited_paths):
        warns.append("ledger source %s is never cited" % p)
    record("FAIL" if probs else "PASS", "citations", "; ".join(probs[:10]) + (" (+%d more)" % (len(probs) - 10) if len(probs) > 10 else "") if probs else "%d citations: format, ledger membership and ranges valid%s" % (n_cites, "; every quote found in its cited lines" if source_present else ""))
    for w in warns:
        record("WARN", "citations", w)

    # ---------------------------------------------------------------- 13 citation coverage
    probs = []
    for rel, d in token_files.items():
        for k, v in d["tokens"].items():
            if not v.get("cite"):
                probs.append("token %s (%s) has no citation" % (k, rel))
    for kind in (sections, comps, prims):
        for cid, (_rel, c) in kind.items():
            if not c.get("cite"):
                probs.append("%s has no citation" % cid)
    for sid, (_rel, c) in sections.items():
        for part in ("motion", "responsive"):
            if not c.get(part, {}).get("cite"):
                probs.append("%s.%s has no citation" % (sid, part))

        def need(desc, sid=sid):
            if desc.get("type") in ("string", "const", "asset", "link", "list", "integer", "email") and not desc.get("cite"):
                probs.append("%s field without citation: %s" % (sid, desc))
        sv._walk_desc(c["content"]["fields"], need)
    for f in tf["pageMeta"].values():
        if not f.get("cite"):
            probs.append("pageMeta field without citation")
    for rid, info in roles.items():
        if info.get("origin") == "generation-safe-addition":
            if not info.get("description"):
                probs.append("generation-safe role %s has no description" % rid)
        elif not info.get("cite"):
            probs.append("asset role %s has no citation" % rid)
    for tid, t in tf["templates"].items():
        if not t.get("cite"):
            probs.append("template %s has no citation" % tid)
    for r in tf["routes"]:
        if not r.get("cite"):
            probs.append("route %s has no citation" % r["path"])
    record("FAIL" if probs else "PASS", "citation-coverage", "; ".join(probs[:8]) or "every token, section (content/motion/responsive), copy budget, asset role, template and route is cited")

    # ---------------------------------------------------------------- 14 copy budgets
    probs = []
    for sid, (_rel, c) in sections.items():
        def chk(desc, sid=sid):
            if desc.get("type") == "string" and "observed" in desc:
                n = sv.word_count(desc["observed"])
                if desc.get("observedWords") != n:
                    probs.append("%s observedWords %s != %d for %r" % (sid, desc.get("observedWords"), n, desc["observed"][:30]))
                if desc["maxWords"] < n:
                    probs.append("%s maxWords below observed" % sid)
                if not desc.get("allowEmpty") and desc["maxWords"] != max(1, math.ceil(n * 1.2)):
                    probs.append("%s maxWords %d breaks the ceil(observed x 1.2) rule" % (sid, desc["maxWords"]))
        sv._walk_desc(c["content"]["fields"], chk)
    record("FAIL" if probs else "PASS", "copy-budgets", "; ".join(probs[:6]) or "every maxWords = ceil(observedWords x 1.2) of the real copy, and observedWords recounts correctly")

    # ---------------------------------------------------------------- 15 token references, catalog, policy, themes
    probs = []

    def refs(v):
        if isinstance(v, str):
            for m in re.finditer(r"\{([a-z0-9.-]+)\}", v):
                yield m.group(1)
        elif isinstance(v, dict):
            for k2, x in v.items():
                if k2 == "cite" or k2.endswith("Cite"):
                    continue  # quotes are verbatim source text, not token references
                yield from refs(x)
        elif isinstance(v, list):
            for x in v:
                yield from refs(x)
    for k, v in tokens.items():
        for ref in refs(v):
            if ref not in tokens:
                probs.append("%s references missing token {%s}" % (k, ref))
    for kind in (sections, comps, prims):
        for cid, (_rel, c) in kind.items():
            for t in c.get("tokens", []):
                if t not in tokens:
                    probs.append("%s uses missing token %s" % (cid, t))
            for ref in refs(c.get("motion", {})):
                if ref not in tokens:
                    probs.append("%s motion references missing {%s}" % (cid, ref))
    cat = docs["tokens/llm/token-catalog.json"]["categories"]
    for c, lst in cat.items():
        for t in lst:
            if t not in tokens:
                probs.append("catalog %s lists missing token %s" % (c, t))
            if t.split(".")[0] != c:
                probs.append("catalog key %s does not match token prefix of %s" % (c, t))
    listed_ids = {x for lst in cat.values() for x in lst}
    for k in tokens:
        if k.split(".")[0] in cat and k not in listed_ids:
            probs.append("token %s has a catalog category (%s) but is missing from tokens/llm/token-catalog.json" % (k, k.split(".")[0]))
    pol = docs["tokens/llm/token-policy.json"]["rawValueRestrictions"]
    if set(pol) != set(cat):
        probs.append("token-policy keys %s != catalog keys %s" % (sorted(pol), sorted(cat)))
    for th_rel in [r for r in docs if r.startswith("tokens/themes/")]:
        th = docs[th_rel]
        modes = th.get("modes", {"default": th.get("resolves", {})})
        for mode, mapping in modes.items():
            for sem, val in mapping.items():
                if sem not in tokens:
                    probs.append("%s resolves unknown token %s" % (th_rel, sem))
                    continue
                if mode in ("default", "light"):
                    ref = re.fullmatch(r"\{(.+)\}", tokens[sem]["$value"]).group(1)
                    if tokens[ref]["$value"] != val:
                        probs.append("%s: %s resolves to %s but foundation %s is %s" % (th_rel, sem, val, ref, tokens[ref]["$value"]))
                elif val not in {t["$value"] for k, t in tokens.items() if k.startswith("color.")}:
                    probs.append("%s %s value %s is not a foundation colour" % (th_rel, mode, val))
    if manifest.get("defaultTheme") not in [docs[r]["id"] for r in docs if r.startswith("tokens/themes/")]:
        probs.append("defaultTheme does not exist")
    record("FAIL" if probs else "PASS", "token-integrity", "; ".join(probs[:8]) or "%d tokens: references, catalog, policy keys and theme resolution all consistent" % len(tokens))

    # ---------------------------------------------------------------- 15b motion-pattern vocabulary equals the contracts and the schema
    probs = []
    mp = docs["tokens/llm/motion-patterns.json"]["patterns"]
    from_contracts = {}
    for sid, (_r, c) in sections.items():
        from_contracts.setdefault(c["motion"]["pattern"], []).append(sid)
    if set(mp) != set(from_contracts):
        probs.append("motion-patterns.json patterns %s != contracts %s" % (sorted(mp), sorted(from_contracts)))
    for pid, e in mp.items():
        if sorted(e.get("sections", [])) != sorted(from_contracts.get(pid, [])):
            probs.append("motion pattern %s lists sections %s, contracts use it in %s" % (pid, e.get("sections"), sorted(from_contracts.get(pid, []))))
        if not e.get("cite"):
            probs.append("motion pattern %s has no citation" % pid)
    for sid in sections:
        if schema["definitions"]["motion." + sid]["properties"]["pattern"].get("const") not in mp:
            probs.append("%s: schema motion pattern is not in motion-patterns.json" % sid)
    record("FAIL" if probs else "PASS", "motion-patterns", "; ".join(probs[:6]) or "%d motion patterns equal the contracts' const-locked patterns and the schema" % len(mp))

    # ---------------------------------------------------------------- 16 absolute paths + junk files
    probs = []
    for p in glob.glob(os.path.join(REPO, "**", "*"), recursive=True):
        base = os.path.basename(p)
        if base in JUNK or base == "__MACOSX":
            probs.append("junk file %s" % os.path.relpath(p, REPO))
        if os.path.isfile(p) and os.path.splitext(p)[1] in (".json", ".md", ".py", ".txt", ".sh"):
            with open(p, encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if ABS_PATH.search(line):
                        probs.append("absolute machine path in %s:%d" % (os.path.relpath(p, REPO), i))
    for p in glob.glob(os.path.join(REPO, "**", ".*"), recursive=True):
        if os.path.basename(p) in JUNK:
            probs.append("junk file %s" % os.path.relpath(p, REPO))
    record("FAIL" if probs else "PASS", "paths-and-junk", "; ".join(sorted(set(probs))[:8]) or "no absolute machine paths; no OS junk files")

    # ---------------------------------------------------------------- 17 entryPoints inside the package
    probs = []

    def eps(v):
        if isinstance(v, str):
            yield v
        elif isinstance(v, list):
            for x in v:
                yield from eps(x)
        elif isinstance(v, dict):
            for x in v.values():
                yield from eps(x)
    for e in eps(manifest.get("entryPoints", {})):
        if e.startswith(("/", "\\")) or ".." in e.replace("\\", "/").split("/") or re.match(r"^[A-Za-z]:", e):
            probs.append("entryPoint %r points outside design-repo" % e)
        elif not os.path.exists(os.path.join(REPO, e)):
            probs.append("entryPoint %r does not exist" % e)
    record("FAIL" if probs else "PASS", "entry-points", "; ".join(probs) or "every entryPoint is inside design-repo and exists")

    # ---------------------------------------------------------------- 18 stack-neutral identifiers
    probs = []
    idents = list(tokens) + list(sections) + list(comps) + list(prims) + list(schema["definitions"]) + list(schema["properties"]) + list(roles)
    for sid, (_rel, c) in sections.items():
        idents += list(c["content"]["fields"])
        idents.append(c["motion"]["pattern"])
    for x in idents:
        if STACK_WORDS.search(x):
            probs.append("identifier %r leaks source-stack vocabulary" % x)
    if manifest.get("sourceStack", {}).get("documentationOnly") is not True:
        probs.append("sourceStack must be documentationOnly")
    record("FAIL" if probs else "PASS", "stack-neutral", "; ".join(probs) or "%d identifiers checked; stack recorded only as documentation" % len(idents))

    # ---------------------------------------------------------------- 19 structural facts still true in source
    if source_present:
        probs = []
        for fact in ledger.get("structuralFacts", []):
            chk = fact.get("absenceCheck")
            if not chk:
                continue
            rx = re.compile(chk["pattern"])
            for base in chk["paths"]:
                full = os.path.join(src_root, base)
                files = [full] if os.path.isfile(full) else glob.glob(os.path.join(full, "**", "*"), recursive=True)
                for fp in files:
                    if os.path.isfile(fp):
                        with open(fp, encoding="utf-8", errors="replace") as f:
                            if rx.search(f.read()):
                                probs.append("%s: %s now matches %r -- the recorded fact no longer holds" % (fact["id"], os.path.relpath(fp, src_root), chk["pattern"]))
        record("FAIL" if probs else "PASS", "structural-facts", "; ".join(probs) or "absence facts re-verified against current source (no reduced-motion handling)")
    else:
        record("WARN", "structural-facts", "source tree absent: absence facts not re-verified")
    return finish()


def finish():
    width = max(len(c) for _s, c, _m in results) if results else 10
    for status, check, msg in results:
        print("%-4s  %-*s  %s" % (status, width, check, msg))
    fails = sum(1 for s, _c, _m in results if s == "FAIL")
    warns = sum(1 for s, _c, _m in results if s == "WARN")
    print("\nverify_all: %d checks, %d FAIL, %d WARN" % (len({c for _s, c, _m in results}), fails, warns))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
