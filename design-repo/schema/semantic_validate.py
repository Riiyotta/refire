#!/usr/bin/env python3
"""PageSpec validator for the Refire /int design-repo.

Two layers, both run on every call:
  1. Schema layer   - Draft-07 validation against schema/pagespec.schema.json
                      (needs the `jsonschema` package; see extraction/requirements.txt).
  2. Semantic layer - everything JSON Schema cannot express. Most importantly the
                      PageSpec is checked against its declared template's REAL node
                      list (order, required, allowed), never nodes[] in isolation.

Every semantic rule id below is also declared in compatibility/graph.json with the
same id and severity; extraction/verify_all.py fails if the two ever diverge.

It also lints the section contracts themselves (lint_contracts): every contract
must satisfy the closed schema/section-contract.schema.json (distinct `source`
provenance vs `semantic` taxonomy objects, closed boolean `retrievalEligible`
with a 30+ character reason when false), and the set of retrieval-ineligible
sections must equal PINNED_RETRIEVAL_INELIGIBLE below. That pin is held in code
here AND, independently, in extraction/verify_all.py, so editing a contract and
the allowlist together cannot move it.

Usage:
  python3 schema/semantic_validate.py                 # section contracts + schema/example*.json
  python3 schema/semantic_validate.py page.json ...   # section contracts + the given files
Exit code: 0 = no errors (warnings allowed), 1 = errors, 2 = validator unavailable.
"""
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Registry of semantic rules implemented here (must equal graph.json enforcedBy "semantic").
SEMANTIC_RULES = [
    "TEMPLATE_NODE_SEQUENCE",
    "SECTION_ALLOWED_IN_TEMPLATE",
    "REQUIRED_SECTIONS_PRESENT",
    "NON_REPEATABLE_ONCE",
    "ROUTE_TEMPLATE_BINDING",
    "THEME_TEMPLATE_BINDING",
    "ONE_HERO",
    "HERO_FIRST_IN_MAIN",
    "FOOTER_LAST",
    "ERROR_PAGE_NO_FOOTER_NO_PROGRESS",
    "NO_EXTERNAL_HREF",
    "MAX_WORDS",
    "ASSET_ROLE_SLOT",
    "ASSET_SOURCE_POLICY",
    "GENERATED_NO_PROPRIETARY_COPY",
    "GENERATED_CONTACT_DATA_RESERVED",
    "NO_MARKUP_IN_TEXT",
    "META_DESCRIPTION_MIRRORS_ABOUT",
    "STAT_INDEXES_SEQUENTIAL",
]

# Rules enforced on the section contracts themselves (graph.json enforcedBy "contract").
CONTRACT_RULES = [
    "SECTION_CONTRACT_CLOSED",
    "SECTION_SOURCE_SEMANTIC_DISTINCT",
    "RETRIEVAL_ELIGIBILITY_PINNED",
]

# Utility/runtime UI (consent banner, loading overlay, pointer layer, modal dialog) is never
# retrievable as a page section. Pinned here in code, independent of the JSON it checks
# (MASTER-GUIDE 3.23); verify_all.py holds its own copy.
PINNED_RETRIEVAL_INELIGIBLE = frozenset({
    "chrome.cookie-pane",
    "chrome.cursor",
    "chrome.preloader",
    "overlay.contact",
})
RETRIEVAL_REASON_MIN_CHARS = 30

EXTERNAL_URL = re.compile(r"(?i)(\b[a-z][a-z0-9+.-]*://|(^|[\s\"'(=])//[a-z0-9]|\bwww\.)")
SHINGLE = 6  # a shared run of this many consecutive words counts as copy reuse
RESERVED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")
FICTIONAL_TEL = re.compile(r"^tel:\+1[0-9]{3}55501[0-9]{2}$")


def _load(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as f:
        return json.load(f)


def word_count(text):
    """Words = whitespace-separated tokens containing at least one letter or digit."""
    return len([t for t in str(text).split() if re.search(r"[A-Za-z0-9]", t)])


def _norm(text):
    t = str(text).lower().replace("’", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


class Repo:
    """Loads the contracts the semantic layer needs (paths derived from __file__)."""

    def __init__(self, repo=REPO):
        global REPO
        REPO = repo
        self.root = repo
        self.schema = _load("schema/pagespec.schema.json")
        tf = _load("templates/templates.json")
        self.templates = tf["templates"]
        self.page_meta = tf["pageMeta"]
        self.sections = {}
        for path in sorted(glob.glob(os.path.join(repo, "sections", "*.json"))):
            with open(path, encoding="utf-8") as f:
                c = json.load(f)
            self.sections[c["id"]] = c
        self.roles = _load("assets/asset-roles.json")["roles"]
        self.contract_schema = _load("schema/section-contract.schema.json")
        self.allowlist = _load("tokens/llm/component-allowlist.json")
        graph = _load("compatibility/graph.json")
        self.severity = {r["id"]: r["severity"] for r in graph["rules"]}
        self.exceptions = graph.get("exceptions", {})
        self._corpus = None

    def proprietary_corpus(self):
        """Proprietary copy of the real site: contract 'observed' values + every
        provenance:'reference' example instance, walked through its contracts."""
        if self._corpus is not None:
            return self._corpus
        corpus = set()
        for f in self.page_meta.values():
            if f.get("copyClass") == "proprietary" and f.get("observed"):
                corpus.add(_norm(f["observed"]))
        for c in self.sections.values():
            _walk_desc(c["content"]["fields"], lambda d: corpus.add(_norm(d["observed"]))
                       if d.get("type") == "string" and d.get("copyClass") == "proprietary" and d.get("observed") else None)
        for path in glob.glob(os.path.join(self.root, "schema", "example*.json")):
            with open(path, encoding="utf-8") as fh:
                spec = json.load(fh)
            if spec.get("provenance") != "reference":
                continue
            for k in ("title", "description"):
                if self.page_meta.get(k, {}).get("copyClass") == "proprietary" and isinstance(spec.get("meta", {}).get(k), str):
                    corpus.add(_norm(spec["meta"][k]))
            for node in spec.get("nodes", []):
                c = self.sections.get(node.get("section"))
                if not c:
                    continue

                def take(desc, value, path):
                    if desc.get("type") == "string" and desc.get("copyClass") == "proprietary" and isinstance(value, str):
                        corpus.add(_norm(value))
                _walk(c["content"]["fields"], node.get("content", {}), "", take)
        corpus.discard("")
        self._corpus = corpus
        return corpus


def category_of(repo, section_id):
    """Taxonomy class of a section (semantic.category), or None for an unknown section."""
    return repo.sections.get(section_id, {}).get("semantic", {}).get("category")


def lint_contracts(repo):
    """Lint the section contracts. Returns [(rule_id, contract_id, message)]; all are errors."""
    errors = []
    try:
        import jsonschema
    except ImportError:
        return [("SCHEMA_VALIDATOR_UNAVAILABLE", "$", "pip install -r extraction/requirements.txt (jsonschema>=4)")]
    validator = jsonschema.Draft7Validator(repo.contract_schema)
    for cid, c in sorted(repo.sections.items()):
        for e in sorted(validator.iter_errors(c), key=lambda e: list(e.absolute_path)):
            head = str(e.absolute_path[0]) if e.absolute_path else ""
            key = e.message.split("'")[1] if e.validator == "required" and "'" in e.message else ""
            if head in ("semantic", "source") or key in ("semantic", "source"):
                rule = "SECTION_SOURCE_SEMANTIC_DISTINCT"
            elif head.startswith("retrievalEligible") or key.startswith("retrievalEligible") or e.validator == "not":
                rule = "RETRIEVAL_ELIGIBILITY_PINNED"
            else:
                rule = "SECTION_CONTRACT_CLOSED"
            text = e.message
            errors.append((rule, cid, "%s: %s" % ("/".join(str(p) for p in e.absolute_path) or "$", text[:200])))
        sem = c.get("semantic", {}) if isinstance(c.get("semantic"), dict) else {}
        if sem.get("id") != c.get("id"):
            errors.append(("SECTION_SOURCE_SEMANTIC_DISTINCT", cid, "semantic.id %r must equal the contract id" % sem.get("id")))
        src = c.get("source", {}) if isinstance(c.get("source"), dict) else {}
        if src and sem and (set(src) & set(sem)) - {"id"}:
            errors.append(("SECTION_SOURCE_SEMANTIC_DISTINCT", cid, "source and semantic must not share fields"))
    ineligible = {cid for cid, c in repo.sections.items() if c.get("retrievalEligible") is False}
    if ineligible != set(PINNED_RETRIEVAL_INELIGIBLE):
        errors.append(("RETRIEVAL_ELIGIBILITY_PINNED", "$", "retrieval-ineligible sections %s != pinned %s" % (sorted(ineligible), sorted(PINNED_RETRIEVAL_INELIGIBLE))))
    listed = set(repo.allowlist.get("retrievalIneligibleSections", []))
    if listed != set(PINNED_RETRIEVAL_INELIGIBLE):
        errors.append(("RETRIEVAL_ELIGIBILITY_PINNED", "$", "allowlist retrievalIneligibleSections %s != pinned %s" % (sorted(listed), sorted(PINNED_RETRIEVAL_INELIGIBLE))))
    return errors


def _walk_desc(fields, fn):
    for d in fields.values():
        fn(d)
        if d.get("type") == "object":
            _walk_desc(d["fields"], fn)
        if d.get("type") == "list":
            item = d["item"]
            fn(item)
            if item.get("type") == "object":
                _walk_desc(item["fields"], fn)


def _walk(fields, value, path, visit):
    """Walk a content value alongside its contract field descriptors."""
    if not isinstance(value, dict):
        return
    for key, desc in fields.items():
        if key not in value:
            continue
        v = value[key]
        p = path + "." + key
        t = desc.get("type")
        if t == "object":
            _walk(desc["fields"], v, p, visit)
        elif t == "list":
            if isinstance(v, list):
                item = desc["item"]
                for i, iv in enumerate(v):
                    if item.get("type") == "object":
                        _walk(item["fields"], iv, "%s[%d]" % (p, i), visit)
                    else:
                        visit(item, iv, "%s[%d]" % (p, i))
        else:
            visit(desc, v, p)


def _strings(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, path + "." + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _strings(v, "%s[%d]" % (path, i))


def validate(spec, repo=None):
    """Return (errors, warnings); each item is (rule_id, json_path, message)."""
    r = repo if isinstance(repo, Repo) else Repo(repo or REPO)
    errors, warnings = [], []

    def emit(rule, path, msg):
        (warnings if r.severity.get(rule, "error") == "warn" else errors).append((rule, path, msg))

    # ---- 1. schema layer
    try:
        import jsonschema
    except ImportError:
        errors.append(("SCHEMA_VALIDATOR_UNAVAILABLE", "$", "pip install -r extraction/requirements.txt (jsonschema>=4)"))
        return errors, warnings
    for e in sorted(jsonschema.Draft7Validator(r.schema).iter_errors(spec), key=lambda e: list(e.absolute_path)):
        errors.append(("SCHEMA", "$" + "".join("[%r]" % p for p in e.absolute_path), e.message[:300]))

    if not isinstance(spec, dict):
        return errors, warnings
    nodes = [n for n in spec.get("nodes", []) if isinstance(n, dict)] if isinstance(spec.get("nodes"), list) else []
    provenance = spec.get("provenance")
    tid = spec.get("template")
    tpl = r.templates.get(tid)

    # ---- 2. template cross-check (against the template's real node list)
    if tpl:
        if spec.get("route") not in tpl["routes"]:
            emit("ROUTE_TEMPLATE_BINDING", "$.route", "route %r is not bound to %s (allowed: %s)" % (spec.get("route"), tid, tpl["routes"]))
        if spec.get("theme") != tpl["theme"]:
            emit("THEME_TEMPLATE_BINDING", "$.theme", "%s requires theme %s, got %r" % (tid, tpl["theme"], spec.get("theme")))
        tnodes = tpl["nodes"]
        order = {n["section"]: i for i, n in enumerate(tnodes)}
        seen = {}
        last_idx, last_sec = -1, None
        for i, n in enumerate(nodes):
            sec = n.get("section")
            if sec not in order:
                emit("SECTION_ALLOWED_IN_TEMPLATE", "$.nodes[%d]" % i, "%r is not in %s's node list" % (sec, tid))
                continue
            key = (sec, n.get("variant"))
            seen[key] = seen.get(key, 0) + 1
            if not tnodes[order[sec]].get("repeatable") and seen[key] > 1:
                emit("NON_REPEATABLE_ONCE", "$.nodes[%d]" % i, "%r (variant %r) is non-repeatable but appears %d times" % (sec, n.get("variant"), seen[key]))
            if order[sec] < last_idx:
                emit("TEMPLATE_NODE_SEQUENCE", "$.nodes[%d]" % i, "%r must come before %r in %s" % (sec, last_sec, tid))
            elif order[sec] > last_idx:
                last_idx, last_sec = order[sec], sec
        present = {n.get("section") for n in nodes}
        for tn in tnodes:
            if tn.get("required") and tn["section"] not in present:
                emit("REQUIRED_SECTIONS_PRESENT", "$.nodes", "%s requires %r" % (tid, tn["section"]))
        for forbidden in tpl.get("forbiddenSections", []):
            for i, n in enumerate(nodes):
                if n.get("section") == forbidden:
                    emit("ERROR_PAGE_NO_FOOTER_NO_PROGRESS", "$.nodes[%d]" % i, "%s must not contain %r (no footer and no progress bar on the error page)" % (tid, forbidden))
        heroes = [i for i, n in enumerate(nodes) if category_of(r, n.get("section")) == "HERO"]
        template_has_hero = any(category_of(r, tn["section"]) == "HERO" for tn in tnodes)
        if tid not in r.exceptions.get("ONE_HERO", []):
            if len(heroes) > 1 or (template_has_hero and len(heroes) != 1):
                emit("ONE_HERO", "$.nodes", "%s needs exactly one hero, found %d" % (tid, len(heroes)))
        elif heroes:
            emit("ONE_HERO", "$.nodes[%d]" % heroes[0], "%s is a hero-less template (named exception) but contains a hero" % tid)
        if tid not in r.exceptions.get("HERO_FIRST_IN_MAIN", []):
            main = [(i, n) for i, n in enumerate(nodes) if r.sections.get(n.get("section"), {}).get("constraints", {}).get("region") == "main"]
            if main and category_of(r, main[0][1].get("section")) != "HERO":
                emit("HERO_FIRST_IN_MAIN", "$.nodes[%d]" % main[0][0], "first main-region node must be the hero, got %r" % main[0][1].get("section"))
    for i, n in enumerate(nodes):
        if n.get("section") == "chrome.footer" and i != len(nodes) - 1:
            emit("FOOTER_LAST", "$.nodes[%d]" % i, "chrome.footer must be the last node")

    # ---- 3. links: no outbound URLs anywhere
    for p, s in _strings(spec):
        if EXTERNAL_URL.search(s):
            emit("NO_EXTERNAL_HREF", "$" + p, "external URL not allowed: %r" % s[:80])

    # ---- 4. per-field content checks via section contracts
    meta = spec.get("meta") if isinstance(spec.get("meta"), dict) else {}
    for k, desc in r.page_meta.items():
        v = meta.get(k)
        if k == "title" and tpl and tpl.get("documentTitle"):
            continue  # const-locked by the schema (NOT_FOUND_COPY_LOCKED); no budget applies
        if isinstance(v, str) and word_count(v) > desc["maxWords"]:
            emit("MAX_WORDS", "$.meta." + k, "%d words > maxWords %d" % (word_count(v), desc["maxWords"]))
    corpus = r.proprietary_corpus() if provenance == "generated" else set()

    shingles = set()
    for ref in corpus:
        w = ref.split()
        shingles.update(" ".join(w[i:i + SHINGLE]) for i in range(len(w) - SHINGLE + 1))

    def copy_reused(v):
        nv = _norm(v)
        if not nv:
            return False
        if nv in corpus:
            return True
        w = nv.split()
        return any(" ".join(w[i:i + SHINGLE]) in shingles for i in range(len(w) - SHINGLE + 1))

    if provenance == "generated":
        for k in ("title", "description"):
            if r.page_meta.get(k, {}).get("copyClass") == "proprietary" and isinstance(meta.get(k), str) and copy_reused(meta[k]):
                emit("GENERATED_NO_PROPRIETARY_COPY", "$.meta." + k, "reuses Refire proprietary copy")

    for i, n in enumerate(nodes):
        contract = r.sections.get(n.get("section"))
        if not contract:
            continue
        base = "$.nodes[%d].content" % i

        def visit(desc, v, p, contract=contract):
            t = desc.get("type")
            path = base + p
            if t == "string" and isinstance(v, str):
                if word_count(v) > desc.get("maxWords", 10 ** 6):
                    emit("MAX_WORDS", path, "%d words > maxWords %d" % (word_count(v), desc["maxWords"]))
                if "<" in v or ">" in v:
                    emit("NO_MARKUP_IN_TEXT", path, "markup is not allowed in text fields")
                if provenance == "generated" and desc.get("copyClass") == "proprietary" and copy_reused(v):
                    emit("GENERATED_NO_PROPRIETARY_COPY", path, "reuses Refire proprietary copy: %r" % v[:60])
            elif t == "asset" and isinstance(v, dict):
                role = v.get("assetRole")
                if role not in r.roles:
                    emit("ASSET_ROLE_SLOT", path + ".assetRole", "unknown assetRole %r" % role)
                    return
                if role != desc["assetRole"]:
                    emit("ASSET_ROLE_SLOT", path + ".assetRole", "slot requires %r, got %r" % (desc["assetRole"], role))
                    return
                _source_policy(role, v.get("src"), path + ".src")
            elif t == "link" and isinstance(v, str):
                if desc.get("assetRole"):
                    _source_policy(desc["assetRole"], v, path)
                if provenance == "generated":
                    _contact(v, path)
            elif t == "email" and isinstance(v, str) and provenance == "generated":
                _contact("mailto:" + v, path)

        def _source_policy(role, src, path):
            info = r.roles[role]
            if provenance == "reference":
                if src not in info["allowedReferenceSources"]:
                    emit("ASSET_SOURCE_POLICY", path, "%r is not an allowed reference source for %s" % (src, role))
            elif provenance == "generated" and info["generationPolicy"] == "placeholder-only":
                if src != "placeholder:" + role:
                    emit("ASSET_SOURCE_POLICY", path, "generated pages must use 'placeholder:%s' (policy placeholder-only), got %r" % (role, src))

        def _contact(href, path):
            if href.startswith("mailto:"):
                domain = href.split("@")[-1].lower()
                if domain not in RESERVED_EMAIL_DOMAINS:
                    emit("GENERATED_CONTACT_DATA_RESERVED", path, "generated pages must use example.com/.org/.net addresses, got %r" % href)
            elif href.startswith("tel:") and not FICTIONAL_TEL.match(href):
                emit("GENERATED_CONTACT_DATA_RESERVED", path, "generated pages must use fictional +1 NXX-555-01XX numbers, got %r" % href)

        _walk(contract["content"]["fields"], n.get("content", {}), "", visit)

    # ---- 5. observed conventions (warn)
    for n in nodes:
        if n.get("section") == "content.title-description":
            d = n.get("content", {}).get("description")
            if isinstance(d, str) and isinstance(meta.get("description"), str) and _norm(d) != _norm(meta["description"]):
                emit("META_DESCRIPTION_MIRRORS_ABOUT", "$.meta.description", "differs from the title-description description (observed convention)")
        if n.get("section") == "stats.card-grid":
            cards = n.get("content", {}).get("cards", [])
            idx = [c.get("index") for c in cards if isinstance(c, dict)]
            if idx != list(range(1, len(idx) + 1)):
                emit("STAT_INDEXES_SEQUENTIAL", "$.nodes", "stat indexes %s are not 1..n" % idx)
    return errors, warnings


def main(argv):
    files = argv or sorted(glob.glob(os.path.join(REPO, "schema", "example*.json")))
    repo = Repo(REPO)
    failed = False
    cerrs = lint_contracts(repo)
    if any(e[0] == "SCHEMA_VALIDATOR_UNAVAILABLE" for e in cerrs):
        print("jsonschema not installed: pip install -r extraction/requirements.txt")
        return 2
    print("%s section contracts  (%d contracts, %d errors)" % ("PASS" if not cerrs else "FAIL", len(repo.sections), len(cerrs)))
    for e in cerrs:
        print("   error %-32s %s  %s" % e)
    failed = bool(cerrs)
    for path in files:
        with open(path, encoding="utf-8") as f:
            spec = json.load(f)
        errors, warnings = validate(spec, repo)
        if any(e[0] == "SCHEMA_VALIDATOR_UNAVAILABLE" for e in errors):
            print("jsonschema not installed: pip install -r extraction/requirements.txt")
            return 2
        name = os.path.relpath(path, REPO) if os.path.abspath(path).startswith(REPO) else os.path.basename(path)
        print("%s %s  (%d errors, %d warnings)" % ("PASS" if not errors else "FAIL", name, len(errors), len(warnings)))
        for e in errors:
            print("   error %-32s %s  %s" % e)
        for w in warnings:
            print("   warn  %-32s %s  %s" % w)
        failed = failed or bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
