# Changelog

## Unreleased — citation refresh after source fix

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
