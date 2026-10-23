# Refire /int design-repo

**Status:** `design-review-pending`. `productionApproved: false`. Nothing here is approved for production until a human design review signs it off. Repository version `1.1.0` (see `CHANGELOG.md`).

This repo is an AI-ready, machine-validated description of the rebuilt **refire.com/int/** site: tokens, primitives, components, section contracts, page templates, a compatibility graph, a Draft-07 PageSpec schema and a semantic validator. A generator can use it to compose pages that keep Refire's structure, typography, rhythm and motion without inventing colours, copy budgets or sections. Every value cites the real source, and the citations are machine-verified.

It is a **snapshot** of the clone project that contains it (its parent directory). That project is read-only evidence and is not shipped with this folder.

---

## Real company, real content: read this before generating anything

Refire is a real hydrogen fuel-cell company, and the user is authorized by Refire to rebuild its site. Its **logo, product photography (PRISMA images), hero film, brochure PDF and proprietary copy belong to Refire.**

- A generator may reuse the **structure**: sections, tokens and motion.
- It must **never fabricate, trace, re-encode, imitate or reproduce** those assets, and never reuse that copy on any new page.
- Every new page is a PageSpec with `"provenance": "generated"`. It must:
  - use `placeholder:<assetRole>` sources for every placeholder-only role (logo, favicon, hero video and poster, both product photos, social image, brochure);
  - use original copy;
  - use reserved example contact data: `@example.com/.org/.net` addresses and fictional `+1 NXX-555-01XX` numbers.
- `schema/semantic_validate.py` enforces this through `ASSET_SOURCE_POLICY`, `GENERATED_NO_PROPRIETARY_COPY` and `GENERATED_CONTACT_DATA_RESERVED`.
- SuisseIntl is a **commercially licensed** typeface (`font.brand-typeface`, policy `must-reuse-exact`). Use it only inside the authorized rebuild. Outside it, fall back to the declared stack (Arial, Helvetica, sans-serif). Never redistribute the font files.
- `"provenance": "reference"` is reserved for the documented reproduction of the authorized clone. That means the two examples `schema/example.pagespec.json` and `schema/example.not-found.pagespec.json`.

`assets/asset-roles.json` holds the closed asset-role vocabulary (10 roles) with per-role generation and licensing guidance. The compliance-critical policies are pinned twice: in the JSON, and independently in `extraction/verify_all.py`.

## Scope

| Route | Template | Notes |
|---|---|---|
| `/` | `template.home` | The one-page marketing site. |
| `*` | `template.not-found` | Stock "404 \| This page could not be found." page, set in the system font stack. |

`/int/` really is a one-page site: the original build manifest lists only `/`, `/_app` and `/_error`. Every route is served under the base path `/int`.

**en.refire.com is deliberately OUT of scope.** The user chose this. It is a separate site with its own codebase and design system, and nothing on /int/ links to it. **Do not recreate it from this repo.** It is recorded in `templates/templates.json#outOfScope`.

## Structural facts (documented, not normalized away)

Each fact is cited in `extraction/measured-values.json#structuralFacts`.

1. **No outbound links.** The user required that the site link to no external domain. The only links are:
   - the local PDF `/int/files/refire.pdf`;
   - `mailto:` links: the two event contacts, plus the contact title's `mailto:test@test.en`, a placeholder copied verbatim from the original;
   - two `tel:` links.

   The schema's href patterns and the `NO_EXTERNAL_HREF` rule reject http(s), any `scheme://`, protocol-relative `//host` and `www.` values.
2. **The contact form never submits.** Submission is blocked and the real endpoint is unknown. A PageSpec must declare `formSubmission: "non-submitting"`, and no other value validates.
3. **The 404 header is near-invisible by design.** It renders white-on-white, because the difference blend does not invert against the fixed white body. This matches the original, so do not "fix" it. The 404 also has **no progress bar and no footer**, enforced by `ERROR_PAGE_NO_FOOTER_NO_PROGRESS`.
4. **No reduced-motion handling exists**, in either the clone or the original. All motion always runs. This is recorded as a fact, not a recommendation:
   - every node carries `motion.reducedMotionFallback: "none-in-source"`, the only value that validates;
   - `verify_all.py` re-greps the source for reduced-motion handling on every run, so the claim cannot silently go stale.
5. **Real company content.** See the section above.

## Layout

```
README.md  CHANGELOG.md  registry.manifest.json
tokens/00-foundation/   color, sizing (fluid model), breakpoint, typography (families, weights, 42 text roles), radius, layer, effect, motion, icon
tokens/10-semantic/     text.* / surface.* / border.* roles
tokens/20-component/    approved component-scoped values
tokens/30-layout/       gutter, section paddings, grids and splits per breakpoint
tokens/themes/          theme.refire-dark (default), theme.system-error (light + prefers-dark modes)
tokens/llm/             component-allowlist.json, token-catalog.json, token-policy.json
assets/asset-roles.json closed assetRole vocabulary + generation/licensing policy
primitives/  components/  sections/      contracts (purpose, props or content, tokens, motion, responsive, citations)
templates/templates.json                 2 templates (structured nodes), 2 routes, page meta budgets, out-of-scope record
compatibility/graph.json                 29 rules with severity and the layer that enforces each (schema, semantic, contract, gate)
schema/pagespec.schema.json              Draft-07 PageSpec contract
schema/example*.pagespec.json            home (reference), 404 (reference), generated home (placeholders only)
schema/section-contract.schema.json     closed Draft-07 shape of every sections/*.json (source vs semantic, retrievalEligible)
schema/semantic_validate.py              schema layer + semantic layer + section-contract lint
schema/tests/adversarial_test.py         mutations that must be rejected + controls that must pass
extraction/measured-values.json          citation ledger, groundwork corrections, exclusions, structural facts
extraction/verify_all.py                 repo integrity and drift checks (includes the wrapper gate)
extraction/wrapper_gate.py               whole-page-wrapper gate over measured section heights
extraction/wrapper-whitelist.json        reviewed exceptions to the gate (agent attestations, not human sign-offs)
extraction/measure_sections.mjs          OPTIONAL: re-measures section heights into measured-values.json (needs Playwright)
extraction/prove_drift.py                drift proof for the gate, the retrieval pin and the source/semantic checks
extraction/evidence/                     verbatim excerpts of two untracked pixel-audit capture lines
extraction/selfcontain_test.py           isolated-copy proof
extraction/package.py                    builds ../design-repo.zip with the CLI zip tool
extraction/requirements.txt              jsonschema>=4
```

## How a generator composes a page

1. **Pick a template** from `templates/templates.json`. Copy its `nodes` in order. Every node is `required` and non-repeatable, because only one real instance of each page shape exists and nothing in the evidence supports dropping or reordering sections.
2. **Fill each node** with three things:
   - `content`: exactly the fields in `sections/<id>.json#content.fields`, within `maxWords`, `maxChars` and the list bounds;
   - `variant`: only where the contract enumerates one;
   - `motion`: the const pattern and threshold, plus `reducedMotionFallback: "none-in-source"`.

   There is **no style or token override field**. Styling is owned by the contracts (`tokens/llm/token-policy.json`).
3. **Set `provenance: "generated"`**. Use `placeholder:<role>` for media and the brochure, and reserved example contact data.
4. **Validate** with `python3 schema/semantic_validate.py my-page.json`. Exit 0 means no errors. Warnings flag observed conventions:
   - the meta description mirrors the about description;
   - stat indexes run 1..n.

`schema/example.generated.pagespec.json` is a complete worked example.

## Sizing model

All lengths are fluid against a design canvas per breakpoint:

| Breakpoint | Viewport | Design width |
|---|---|---|
| desktop | above 834px | 1920 |
| tablet | 521–834px | 744 |
| mobile | 520px and below | 375 |

- A value `{designPx: N}` resolves to `N / designWidth × 100vw`.
- `{designPx: N, minPx: 12}` adds the `max(12px, …)` clamp that many labels use.
- `{ratio}` is a unitless line-height. `{px}` is fixed (used only by the 404 body).
- The cascade is desktop-first, and every token states all three breakpoints explicitly, with inheritance already resolved.
- Source utility classes are resolved to these values. Class names never appear as contract fields.

## Motion

`tokens/00-foundation/motion.json` holds every duration, easing (neutral names, with the original library name kept only as `sourceName`), stagger, threshold and continuous-motion parameter. The values reflect the current source, which corrects the original spec in several places:

- the cursor follows with lerp **0.12**;
- the header label swap is sequential out-in;
- the preloader counter has no zero padding;
- fades use circular-in-out;
- reveal thresholds are 0.1, 0.3 and 0.7;
- the text+image reveal measures the whole section.

## Verification

Requires Python 3.8+ and `pip install -r extraction/requirements.txt`. The design-repo adds nothing to the clone's `package.json`.

```bash
python3 schema/semantic_validate.py          # examples: schema + semantic, 0 errors
python3 schema/tests/adversarial_test.py     # every mutation rejected, every control passes
python3 extraction/verify_all.py             # integrity + drift checks (add --source-root PATH to point at the clone)
python3 extraction/wrapper_gate.py           # the whole-page-wrapper gate alone
python3 extraction/prove_drift.py            # scratch-copy proof that the gate / pins / provenance checks fail on injected defects (--scratch DIR needs an empty dir)
python3 extraction/selfcontain_test.py       # copies this folder alone into the OS temp dir and reruns everything
python3 extraction/package.py                # LAST: rebuilds ../design-repo.zip, junk-free
```

`verify_all.py` checks the following:

- **Allowlist:** parity with contract files, and its version.
- **Versions:** pageSpecVersion against the schema const.
- **Schema parity:** the allowlist's settable properties, and every contract against its schema definition.
- **Asset roles:** closure across schema, allowlist and registry, plus the pinned policies.
- **Templates and routes:** structured nodes, 1:1 route coverage.
- **Graph:** every rule is enforced by the layer it names.
- **Counts:** the manifest counts, recomputed from disk, and this README's counts table.
- **Citations:**
  - every citation is in the ledger and in range;
  - every quote is found verbatim in its cited lines, when the source is present;
  - every token, section, copy budget, asset role, template and route carries a citation.
- **Copy budgets:** follow the evidence rule.
- **Tokens:** references, catalog and policy keys, and theme resolution are consistent.
- **Section contracts:** every contract satisfies the closed `schema/section-contract.schema.json`; the retrieval-ineligible set equals two independent code pins and the allowlist; at most one HERO-class section per template.
- **Section provenance:** every `source` object resolves (ledger range, then the real file's function declaration and first rendered element) and each `semantic.category` agrees with the clone's `ia.json`.
- **Wrapper gate:** measured section heights against the thresholds below.
- **Hygiene:** no absolute machine paths, no OS junk files, `entryPoints` stay inside the package, identifiers are stack-neutral.
- **Structural facts:** re-verified against the current source.

The adversarial suite's Part C proves that each drift check fails on injected bad input. It works on a scratch copy in the OS temp dir.

**Without the clone project alongside** (for example, after unzipping this folder elsewhere), quote checks and source re-greps are skipped with a WARN. Citation ranges are still checked against the line counts recorded in the ledger.

**Evidence files:** every cited file is tracked in the clone's git repository. The original's saved bundles and the pixel-audit scratch captures are gitignored, so a clean clone does not have them; the values they supported are cited through `CLONE_SPEC.md` (which records them) and `extraction/evidence/` (verbatim excerpts of the two capture lines this repo cites).

**Citation format:** `{at: "path:line[-line]", quote: "..."}`, with paths relative to the clone project. `@home` is shorthand for the clone's home-section component directory, as declared in `extraction/measured-values.json#pathAliases`.

## Section contracts: provenance vs taxonomy

Each `sections/*.json` carries two distinct, closed objects (`schema/section-contract.schema.json`):

| Object | Fields | Says | Checked by |
|---|---|---|---|
| `source` | `id`, `tag`, `file`, `lines` | where the section is implemented: the real component, the first element it renders, its file (`@home` = `src/components/home`) and line range | `verify_all.py` `section-provenance`: ledger range, then the real file declares `function <id>` at the first line and its first host element is `<tag>` |
| `semantic` | `id`, `category` | what the section is for; `id` equals the contract id; `category` is the closed set `CHROME, HERO, CONTENT, MEDIA, CTA, OVERLAY, FOOTER, ERROR` (no `FEATURES`) | `lint_contracts` (schema + id equality), and `verify_all.py` compares it with `ia.json` through the shared file path |

The id prefix is a name, not a class: `media.text-image-shader` is `semantic.category: CTA`. HERO rules (`ONE_HERO`, `HERO_FIRST_IN_MAIN`, the gate) key on `semantic.category`, never on an id prefix.

**`retrievalEligible`** is a closed boolean on every contract (true by default). Utility/runtime UI is `false` and must carry `retrievalEligibleReason` of 30+ characters: `chrome.cookie-pane` (consent banner), `overlay.contact` (modal dialog), `chrome.preloader` (loading overlay), `chrome.cursor` (pointer overlay layer). The set is pinned in code twice, in `schema/semantic_validate.py` and independently in `extraction/verify_all.py`, and mirrored in the allowlist's `retrievalIneligibleSections`. Editing a contract and the allowlist together cannot move it.

## Whole-page-wrapper gate

A section that is really a whole page hides the page's structure. `extraction/wrapper_gate.py` (run by `verify_all.py`) checks the heights in `extraction/measured-values.json` `sectionHeights` (1440x900 viewport, headless Chromium against a production build of the clone; regenerate with the optional `extraction/measure_sections.mjs --write`, which needs `PLAYWRIGHT_MODULE` and a running preview):

| Rule | WARN | FAIL |
|---|---|---|
| HERO-class section height | above 1800px | above 3000px |
| One in-flow section's share of its page's in-flow height | above 50% | above 60% |
| Missing, malformed, duplicate or orphan measurement | | always |

A FAIL is waived only by an entry in `extraction/wrapper-whitelist.json` with `reviewedBy`, a `justification` of 30+ characters and a `maxHeightPx` above the measured height; the finding is then still reported as a WARN. The single entry (the 404 body is 100% of a one-section page) is an **automated agent attestation, not a human sign-off**.

Measured at 1440px (in-flow sections only; fixed chrome is recorded but not counted):

| Route | Section | Class | Height px | Share of page |
|---|---|---|---|---|
| `/` (page 6598.9px) | `hero.video-title` | HERO | 900 | 13.6% |
| | `content.numbered-statement` | CONTENT | 702.3 | 10.6% |
| | `content.title-description` | CONTENT | 271.5 | 4.1% |
| | `stats.card-grid` | CONTENT | 759.8 | 11.5% |
| | `media.scroll-picture` | MEDIA | 1122 | 17.0% |
| | `ticker.marquee` | MEDIA | 421.9 | 6.4% |
| | `content.event-accordion` | CONTENT | 1176.8 | 17.8% (largest) |
| | `media.text-image-shader` | CTA | 1097.3 | 16.6% |
| | `chrome.footer` | FOOTER | 155.5 | 2.4% |
| `*` (page 900px) | `error.not-found` | ERROR | 900 | 100% (whitelisted, reviewed) |

Fixed chrome (header 77, scroll progress 2, cookie pane 57, cursor 74, preloader 900, contact overlay 900) is recorded in the ledger with `inFlow: false`. The home page has one HERO and no section above 18% of the page, so nothing on it is a page wrapper; both templates are different page types (a one-page marketing site and the stock error page) that merely share the chrome, and each has its own node list.

## Counts (recomputed by verify_all.py; a mismatch fails)

| key | value |
|---|---|
| `foundationTokens` | 163 |
| `semanticTokens` | 25 |
| `componentTokens` | 16 |
| `layoutTokens` | 16 |
| `typeRoles` | 42 |
| `themes` | 2 |
| `primitives` | 11 |
| `components` | 7 |
| `sections` | 16 |
| `templates` | 2 |
| `routes` | 2 |
| `assetRoles` | 10 |
| `graphRules` | 29 |
| `exampleInstances` | 3 |
| `retrievalIneligibleSections` | 4 |
| `measuredSections` | 21 |

## Copy budgets

`maxWords = ceil(observedWords × 1.2)` of the real copy. For list fields the longest observed item sets the budget. A word is a whitespace-separated token that contains a letter or digit.

There is one documented exception: the scroll-picture `alt` is empty in the source (the image is decorative). Its ceiling of 12 is stated as such, not as an observed budget.

Every text field also carries a `copyClass`:

- `proprietary`: Refire's own marketing, event and brand copy. Generated pages are checked against reusing it.
- `ui-microcopy`: generic interface labels such as "Contact", "Close", "submit" and the form placeholders. These may be reused.
- `locked`: const values such as the stock 404 strings and `formSubmission`.

The class of each field is a documented judgement in `sections/*.json`.

## Groundwork corrections

`CLONE_SPEC.md`, `src/motion/README.md`, `ASSET_MANIFEST.json` and the specs were treated as a first draft and spot-checked against the source. Corrections, each cited in `extraction/measured-values.json#corrections`:

- **Cursor lerp** is 0.12, not 0.2. `CLONE_SPEC.md` §2.4, §4.3 and §5 say 0.2, and so does the hook table in `src/motion/README.md`.
- **`src/motion/README.md`** still describes pre-implementation state in three places:
  - eases "still to register";
  - preloader "set directly";
  - cookie pane "mounts instantly".

  The code does all three properly.
- **Preloader counter** has no zero padding. `CLONE_SPEC.md` §1 says "00%..100%".
- **Pill label swap** is sequential out-in, not a single 400ms transition.
- **`ASSET_MANIFEST.json` `local` paths** say `public/assets/...`. The real copies are under `public/int/...`.
- **SuisseIntl Mono** is not "declared but unused" in the clone: the clone does not declare it at all. Only the original declares it.

The measured overlay geometry fix (content block at y 204.1, 1440×695.9 at 1440px) was confirmed against both the original and the clone captures.

## Versioning

- `repositoryVersion` is `1.1.0`: a minor bump for the new section-contract schema, retrieval pin, provenance checks and wrapper gate, all additive (the PageSpec shape is unchanged, so `pageSpecVersion` stays `1.0.0`).
- `allowlistVersion` is machine-checked against `tokens/llm/component-allowlist.json`.
- `pageSpecVersion` is machine-checked against the schema const.
- `repositoryVersion` is documentation-only and hand-maintained; nothing checks it.

## Delivery

- **The clone itself:** `npm ci`, then `npm run dev` or `npm run build`, from its lockfile. Never ship `node_modules`.
- **This folder:** delivered as `design-repo.zip`, built by `extraction/package.py`. It uses the CLI `zip` tool, stages in the OS temp dir, and excludes `__MACOSX`, `.DS_Store`, `Thumbs.db`, `desktop.ini` and bytecode.
- Rebuild the zip last, after every change.
- If the project ever becomes a git repository, gitignore the zip. Never commit it next to the live folder.
