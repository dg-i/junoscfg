## Resolved instructions

instruction-integrity.md, including C1 administrative surface-zone grouping and C2 prior owner authorization, governs this standard bug lane.

## Requirements

Three requirements in specs/schema-pipeline/test-selection/spec.md: tooling/shared inputs, deleted tests and hook invocation, and nonduplicated directory coverage.

## Evidence

At a7da186, tools/affected_tests.py selects only runtime Python, existing test Python, and five global inputs. tools/schema_verification.py and tests/data/device/grammar-corpus.json select nothing. The hook files filter omits tools; pre-commit excludes deleted files from filtering.
No selector CONTRACT exists; tests/CONTRACT.md is the authoritative test-layer contract. Existing package/importer tests remain the preservation baseline.

## Non-goals

No runtime or named surface changes, qualification admission/cache changes, CI matrix or oracle changes, or heuristic fixture ownership inference.

## Acceptance criteria

Every requirement names exact pytest tests in the delta. Tool/config inputs select tooling; shared data selects all; missing test paths select an existing ancestor; hook always invokes the selector; nested paths do not duplicate collection. Existing source/importer and document assertions remain intact.
Independent challenge omitted under economy and normal risk; parent arranges fresh review.

## Performance expectations

Document-only selection stays empty; mixed directory/file selection avoids duplicate pytest collection. Full-suite speed improvement belongs to the separate tooling-performance change; this repair makes omitted verification truthful, not faster.

## Outstanding decisions

None, because owner approved the optimization plan and orchestrator resolved administrative classification.

## Execution and checkpoint

- Assurance preference: economy.
- Risk floor: normal; ordinary pre-commit selection only, no trust-boundary or runtime change.
- Roles required: Builder, fresh Reviewer, Finalizer.
- Resume point: phase 4, acceptance tests; phase 3 is inapplicable to bug.

## Delta log

- Freeze established after intent commit e71b4f7, before tests and implementation.

## Scope and completion

Close demonstrated coverage omissions with conservative existing test layers and deduplicate overlapping targets. Keep package/importer behavior and unrelated document fast path. Parent serializes activation and full checkpoint; no unresolved obligations.
