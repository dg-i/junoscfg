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

- Reviewed upstream v0.14.0 requires retirement of competing vendored OpenSpec/OPSX
  discovery before update. Supported reversible retirement is within the requested
  workflow simplification; canonical OpenSpec CLI, specs and schema remain. No
  application test/coverage or review obligation is removed. Retirement and updater
  will receive fresh application review; no application full evidence yet exists.

- Independent challenge identified ignored captures/schema discovery and external
  option inputs not covered by ordinary tracked-byte proof. Ordinary reuse now
  refuses these contexts and executes tests directly. This fulfills conservative
  uncertainty criteria; new regression cases precede the first full checkpoint.

- Executed counterexample (2026-10-14, adoption attempt): a commit changing only
  `.github/workflows/ci.yml` selected no tests, yet `test_type_policy` reads that
  file; the next lock-triggered hook failed it. Enumerating tracked files that
  selected nothing also found `examples/` (named by shared support) and audit
  package data. The added named-reader requirement closes these under-selections;
  documents and change records stay unselected unless a module names them, and a
  computed root path outside tooling selects the full suite. Selector regressions
  were observed failing (18) before implementation.
- Owner decision (2026-10-14): continue this branch; keep the approved local CI
  verbatim through template adoption. Upstream preserved-workflow and skill
  Markdown defects go through the template's own workflow before adoption.
- Executed counterexample (2026-10-15, first full checkpoint at 35b26ef): two
  variants of `test_only_generated_at_may_change` failed under parallel load on a
  `.git/objects/maintenance.lock` in the fixture repository's byte snapshot. Git
  2.56 (installed 2026-10-13) starts detached automatic maintenance after
  `commit_fixture`'s commit; isolated reruns passed 3/3. The fixture commit now
  disables automatic maintenance; a trace regression failed before the fix. The
  same diagnosis showed a changed test module selected only itself, although eight
  schema test modules import `commit_fixture`/`git` from it (pre-existing on
  master). A changed test module now also selects its importing test modules under
  the tool rules; ten selector regressions were observed failing first.
- Fresh review (2026-10-15, head 5adc8ae): verdict do not merge; F1 deletion
  narrower than edit, F2 selector real-tree assertions unselected, F3 root pytest
  configuration, F4 contract overstatement and undetected indirect uses, F5
  untracked files unbound to reuse identity, F6 retired-skill residue. Owner
  decision (2026-10-15): fix all six in this change, none to backlog. Each fix has
  a regression observed failing first (15 for F1–F3, 6 for F4, 1 for F5); F6 is
  configuration text verified by fields, caps, skills and markdownlint. The
  reviewer's executed deletion counterexamples now select the importers (probe in a
  scratch worktree). Directory-reader and string-edge rules add small tooling tests:
  about 4 s to a tests/ commit and about 9 s to a tools/ commit (follow-up review
  re-measurement); bookkeeping, ci.yml and mkdocs.yml selections are unchanged.
- Follow-up review (2026-10-15, head 07ec0fc): verdict merge; F1–F6 resolved, no
  narrower selection across 1527 tracked files. Non-binding N1 (source edits did
  not select the selector's package-graph assertions), N2 (overhead figure), N3
  (gitignored test modules and a failing git listing bypassed the reuse guard), N4
  (one exact assertion weakened), N5 (loader wording), N6 (review record). Applying
  the owner's fix-in-change ruling, all six are corrected: N1 and N3 with
  regressions observed failing first (3), N4 restored to an exact list.
