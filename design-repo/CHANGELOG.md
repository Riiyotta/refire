# Changelog

## 1.2.0 — explicit generation mode, asset availability, generated examples

A minor release that changes the PageSpec shape, so `pageSpecVersion` goes 1.0.0 -> 1.1.0 and `allowlistVersion` 1.1.0 -> 1.2.0. Found by running the baseline audit first (6 FAIL: no `mode`, no generated-mode rules, no asset availability, no pins, no substitutes) and fixing all of them.

### Added

- **`mode`**: a required, closed `"reference" | "generated"` enum on every PageSpec (graph rule `MODE_CLOSED_ENUM`). It replaces the earlier `provenance` field of the same two values. The two existing examples are `reference`.
- **Generated-mode rules** in `schema/semantic_validate.py`: `GENERATED_MODE_REFERENCE_ASSET`, `_ROLE`, `_BRAND`, `_CTA`, `_COPY`, `_URL`, `_ASSET`, `_PERSON`, plus `ASSET_AVAILABILITY_DRIFT` and `GENERATED_MODE_PATTERNS_MISSING` (an empty pattern category fails closed). Strings are normalised (NFKC, zero-width and soft-hyphen removal, curly quotes, Unicode dashes) before matching. `GENERATED_NO_PROPRIETARY_COPY` and `GENERATED_CONTACT_DATA_RESERVED` are kept; the latter now also accepts `*.example` / `*.invalid` mailbox hosts.
- **`assets/asset-roles.json#sourceBrand`**: 25 patterns in 6 categories (brand, cta, copy, url, asset, people), derived from literals in this project's source, each with `cite` evidence (resolved by `verify_all.py`), `mustMatch` examples and per-category `mustNotMatch` controls, a recorded normalisation, and `notApplicable` notes (no ratings, no outbound links, no legal entity, no named individuals).
- **Asset availability**: every role has a closed `availability` (`reference-only` | `generation-safe` | `blocked-for-generation`), `generatedModeGuidance` and, for reference-only and blocked roles, `generationSafeSubstitutes`. Nine generation-safe roles were added (19 roles in total): `brand.logo-placeholder`, `media.video-placeholder`, `media.image-generated`, `document.placeholder`, `font.system-stack`, `person.fictional`, `url.placeholder`, `copy.original`, `brand.fictional`. `font.brand-typeface` is `blocked-for-generation`.
- **`generatedAssetRoles`** on every section contract (and on each asset or link field inside it), wired through `schema/section-contract.schema.json`, the allowlist and the PageSpec schema (each asset slot's role is now an enum of the source role plus its generation-safe roles; `href.document` accepts `placeholder:document.<role>`).
- **Availability pinned in code**: `PINNED_AVAILABILITY` in `schema/semantic_validate.py` and, independently, in `extraction/verify_all.py`. `verify_all.py` also holds one canary string per pattern id and six normalisation canaries, so removing or loosening a pattern, or switching generated mode off in the validator, fails verification.
- **Generated examples for both templates**: `schema/example.generated.pagespec.json` (rewritten with the new roles and original copy; the previous version reused the source's cookie, consent and department-select sentences, which the new rules reject) and the new `schema/example.generated-not-found.pagespec.json`. Fictional brand "Brindle Valley", reserved addresses, fictional phone numbers.
- **Token rules (R10)**: the token catalog and policy already existed and were verified. Added the semantic rules `TOKEN_RAW_COLOR`, `TOKEN_RAW_LENGTH`, `TOKEN_STYLE_DECLARATION`, `TOKEN_UNKNOWN`, `TOKEN_NO_OVERRIDE_SLOT` (a PageSpec has no token or style slot, so any such shape in a string is rejected), a two-way catalog check in `verify_all.py` (a real token with a catalog category must be listed), and `tokens/llm/motion-patterns.json` (12 patterns derived from the contracts, with a parity check).
- `verify_all.py` checks `asset-availability`, `source-brand-registry`, `generated-mode` and `motion-patterns`. Graph rules 29 -> 45.
- Adversarial suite: 125 -> 253 cases (126 PageSpec mutations, 2 warn-severity, 22 contract, 24 gate and 79 repo-drift cases), covering mode, brand/logo, copy, CTA, URL and contact data, proprietary media, third-party identity, normalisation evasions and tokens, with reference and generated controls. `extraction/prove_drift.py`: 41 -> 84 cases (pins, registry edits, validator stops enforcing generated mode, pattern removal and loosening, token catalog drift).

### Changed

- Counts: `assetRoles` 10 -> 19, `graphRules` 29 -> 45, `exampleInstances` 3 -> 4; new `motionPatterns` 12, `generationSafeAssetRoles` 10, `sourceBrandPatterns` 25, `generatedExampleInstances` 2.
- `asset-roles.json` gained `generationPolicies["may-generate-new"]`; roles with `origin: "generation-safe-addition"` carry a `description` instead of a source citation (there is no source usage to cite).

### Honest limits

- **No human has reviewed the pinned patterns.** `sourceBrand.reviewStatus` is `UNREVIEWED` and `verify_all.py` fails if it ever claims otherwise.
- Detection is string and regex based: a paraphrase, a translation, an unfolded homoglyph or text inside an image passes. The theme id `theme.refire-dark` stays in generated PageSpecs because the schema binds the home template to it.

## 1.1.0 — contract taxonomy, retrieval pin, wrapper gate

A minor, additive release. The PageSpec schema is unchanged.

### Baseline failures fixed (found by reproducing them first)

- **`verify_all.py` reported 1 FAIL (`citations`) and the adversarial suite `FAILURES PRESENT`.** Both had one root cause. Eight citations pointed at three gitignored files (the original site's saved CSS and JS bundles and two scratch pixel-audit captures) that exist only on the machine that built the repo. In any other checkout `src/index.css` is present, so the source tree counted as present, the cited files were missing and the check failed. The adversarial suite's Part C failed only because its "unmutated scratch copy" control inherited that FAIL. Nothing was weakened or loosened. The citations now point at tracked evidence: `CLONE_SPEC.md` (which records the original's `:root` colours, 1920 design width and the NBSP fact) and `extraction/evidence/pixel-audit-1440-excerpt.txt` (verbatim capture lines).
- `extraction/prove_drift.py` was named in the task but did not exist; it is now written (see below).

### Added

- `schema/section-contract.schema.json`: a closed Draft-07 schema for every `sections/*.json`. Each contract now has distinct closed `source` {id, tag, file, lines} and `semantic` {id, category} objects, replacing the free-text `category` string.
- `retrievalEligible` (closed boolean) with `retrievalEligibleReason` (30+ characters, required when false) on every contract. False for `chrome.cookie-pane`, `overlay.contact`, `chrome.preloader`, `chrome.cursor`. Pinned in code in `semantic_validate.py` and independently in `verify_all.py`, mirrored in the allowlist (`retrievalIneligibleSections`, `sectionContractProperties`, `semanticCategories`).
- `extraction/wrapper_gate.py`, `extraction/wrapper-whitelist.json`, `extraction/measure_sections.mjs` and the `sectionHeights` block in `extraction/measured-values.json` (21 measurements at 1440px).
- `verify_all.py` checks `section-contracts`, `section-provenance` and `wrapper-gate`; one HERO per template.
- 4 graph rules (`SECTION_CONTRACT_CLOSED`, `SECTION_SOURCE_SEMANTIC_DISTINCT`, `RETRIEVAL_ELIGIBILITY_PINNED` enforced by the `contract` layer; `WRAPPER_HEIGHT_GATE` by the `gate` layer): 25 -> 29 rules.
- Adversarial Parts A2 (22 contract mutations + 2 controls) and A3 (24 gate cases + 1 control), 10 more Part C repo mutations, and `extraction/prove_drift.py` (41 scratch-copy cases).

### Changed

- `media.text-image-shader` is now `semantic.category: CTA` (a closing pitch whose only action is the brochure link), and `overlay.contact` is `OVERLAY`. `ia.json` gained the `CTA` and `OVERLAY` categories to match; `IA.md` and `matrix.csv` were regenerated by `build.mjs`.
- `ONE_HERO` and `HERO_FIRST_IN_MAIN` now key on `semantic.category == HERO`, not an id prefix.
- Versions: `repositoryVersion` 1.0.0 -> 1.1.0, `allowlistVersion` 1.0.0 -> 1.1.0, `pageSpecVersion` stays 1.0.0. Counts: `graphRules` 25 -> 29, new `retrievalIneligibleSections` 4 and `measuredSections` 21.

## 1.0.1 — citation refresh after source fix

- The clone source changed in two places:
  - `src/index.css` gained 2 lines inside `.scrolled-picture-clip` (`overflow: hidden`, which stops the 1.1x zoom from widening the page).
  - `src/App.jsx` now passes React Router future flags.
- Updated to match:
  - every `index.css` citation at line 448 or later moved down by 2;
  - the router citation's quote now uses the unchanged `basename` prefix;
  - the ledger line count went from 469 to 471.
- No token, contract or rule values changed.

## 1.0.0 — initial build

This was a from-scratch build following the design-repo-extraction BUILD-GUIDE. The build order was:

1. tokens
2. primitives
3. components
4. sections
5. templates
6. compatibility graph
7. schema
8. examples
9. semantic validator
10. adversarial tests
11. manifest, allowlist and docs

### Contents

| Area | What was built |
|---|---|
| Tokens | 220 in total: 163 foundation, 25 semantic, 16 component and 16 layout. The foundation set includes 42 text roles. There are 2 themes. |
| Contracts | 11 primitives, 7 components and 16 section contracts. Every section has a content contract (with `maxWords` budgets), constraints, motion, a structured responsive block and citations. |
| Templates | 2 templates with structured node objects, and 2 routes mapped 1:1. en.refire.com is recorded as a deliberate out-of-scope decision. |
| Graph | 25 rules: 19 enforced by the semantic validator and 6 by the schema, with named exceptions for the hero-less 404. |
| Asset roles | A closed vocabulary of 10 roles, wired through the schema, the allowlist and the examples. It includes generation and licensing guidance for a real company. 9 compliance pins are held in `verify_all.py`. |
| Examples | Three PageSpecs: the home reference, the 404 reference, and a generated home page that uses placeholders only. |
| Validation | A Draft-07 schema with closed motion objects and const-locked patterns and thresholds. The semantic validator cross-checks every PageSpec against its declared template's real node list. |
| Verification | An adversarial suite covering PageSpec mutations, controls, and repo-drift mutations on a scratch copy. Also `verify_all.py`, a self-containment test and the packager. |

### Corrections to groundwork, verified against the current source

- **Cursor lerp.** It is 0.12, not 0.2. CLONE_SPEC.md and the `src/motion/README.md` hook table both say 0.2.
- **`src/motion/README.md` is stale in places.** It describes the eases, the preloader and the cookie-pane motion as not yet implemented. They are implemented.
- **Preloader counter.** It has no zero padding.
- **Pill label swap.** It is sequential out-in.
- **ASSET_MANIFEST.json local paths.** They are wrong: `public/assets/...` should be `public/int/...`.
- **SuisseIntl Mono.** The clone never declares it.

### Hardening found by the adversarial suite during the build

- **Protocol-relative URLs.** A URL such as `//host` in the middle of a string was not caught at first. `NO_EXTERNAL_HREF` now catches it.
- **Proprietary copy reuse.** At first, copy was only flagged on a whole-string match. A generated page could get past this by embedding a proprietary sentence inside new text. Reuse is now detected as any shared run of 6 or more consecutive words. The rule text in `compatibility/graph.json` was updated to match.
- **Path alias.** Citations to the home-section component directory now use the `@home` alias. This keeps a literal grep for absolute home-directory paths at zero hits.
