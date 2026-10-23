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
            if sch.get("allOf", [{}, {}])[1].get("properties", {}).get("assetRole", {}).get("const") != desc["assetRole"]:
                probs.append("%s: asset role pin drift" % path)
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
    for r in graph["rules"]:
        if r["severity"] not in ("error", "warn"):
            probs.append("rule %s bad severity" % r["id"])
        if r["enforcedBy"] == "schema" and ("rule:" + r["id"]) not in ssrc:
            probs.append("schema rule %s has no rule:%s marker in the schema" % (r["id"], r["id"]))
        if r["enforcedBy"] not in ("schema", "semantic"):
            probs.append("rule %s has unknown enforcedBy" % r["id"])
    for rule, tids in graph.get("exceptions", {}).items():
        for t in tids:
            if t not in tf["templates"]:
                probs.append("exception %s names unknown template %s" % (rule, t))
    record("FAIL" if probs else "PASS", "graph-enforcement", "; ".join(probs) or "%d graph rules each enforced by the layer they name (%d semantic, %d schema)" % (len(graph["rules"]), len(gsem), len(graph["rules"]) - len(gsem)))

    # ---------------------------------------------------------------- 11 manifest counts recomputed
    def ntok(folder):
        return sum(len(d["tokens"]) for rel, d in token_files.items() if rel.startswith("tokens/" + folder))
    actual = {
        "foundationTokens": ntok("00-foundation"), "semanticTokens": ntok("10-semantic"), "componentTokens": ntok("20-component"), "layoutTokens": ntok("30-layout"),
        "typeRoles": len([k for k in tokens if k.startswith("type.")]), "themes": len([r for r in docs if r.startswith("tokens/themes/")]),
        "primitives": len(prims), "components": len(comps), "sections": len(sections), "templates": len(tf["templates"]), "routes": len(tf["routes"]),
        "assetRoles": len(roles), "graphRules": len(graph["rules"]), "exampleInstances": len(examples),
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
        if not info.get("cite"):
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
