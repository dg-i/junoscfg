## Resolved instructions

instruction-integrity.md resolves owner authorization and standing economy assurance.
User explicitly preserves all assurance and permits local integration and upstream work.

## Requirements

schema-pipeline/test-selection delta supersedes directory-only tooling breadth.
Shared fixtures, configuration, deletions and uncertain dependencies remain conservative.

## Evidence

Current affected_tests.py treats every tools non-Markdown path alike. Tests use static
imports, literal import_module and opaque file loaders. Independent challenge found
schema_content_worker also executes through the root conftest, requiring full coverage.
Full strategy-a already excludes the affected hook and runs aggregate coverage.

## Non-goals

No tests/assertions/coverage reductions, schema bypass, new local evidence cache,
consumer changes, dependency pruning, hidden timing exclusions or pushes.

## Acceptance criteria

Cover direct/transitive test dependencies, opaque known loaders, cycles, imports,
unknown/deleted tools, malformed sources, shared inputs, configuration and bookkeeping.
Existing selector tests and new focused tests in tests/tooling/test_affected_tests.py
pin these cases. Independent challenge and fresh review remain required.

## Performance expectations

Compare equivalent tool edits before/after including ordinary hooks. Report setup,
failed commands and final checkpoint separately and in end-to-end totals. Existing
400/200/95s workload targets remain; absent measurements stay UNMEASURED.

## Outstanding decisions

None. Owner directly requests this behavior; uncertain cases retain broad execution.

## Execution and checkpoint

- Assurance preference: economy
- Risk floor: high for assurance selection
- Roles required: Builder, independent Test/Challenge, fresh Reviewer, Finalizer
- Resume point: phase 4 tests after this freeze is committed

## Delta log

- Freeze established from v0.28.14 plus independent challenge source inspection.

## Scope and completion

One affected-test behavior change; upstream reviewed workflow adoption is a dependency
with exact updater commit. Shared reusable evidence is used only after its API is
qualified upstream. Strict lane/readiness/spec gates precede the stable full checkpoint.

- Shared API qualification: ordinary execution uses existing verification.execute,
  with tests for exact command, failed result and unavailable identity fallback.
  No second cache or environment normalization. Focused acceptance was rerun after
  adding the adapter; no prior full checkpoint existed to invalidate.
