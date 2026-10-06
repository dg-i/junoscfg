# Phase 4 — Tests

## Outcome

The acceptance tests the delta names, and any contract test changes, written
in one pass with no implementation, and reviewed by the human.

## Process

1. For each requirement in the delta, the test its `Tests:` line names, in
   that file and under that name: `agent-ready reconcile` reads the id phase 2
   wrote and fails while the test does not exist.
2. Contract tests where a module's `__all__` or a Protocol changes: the
   conformance suite runs over real and fake implementations.
3. No implementation. A test that passes before the change exists is not
   testing the change.
4. The human reviews the test files, not the diff of the whole change. Approved
   tests are the baseline, subject to the formal challenge path; never silently
   change approved intent or weaken a kept requirement's assertion.

## Specification challenges

When evidence challenges an approved proposal, spec, test, or contract, record
it in `openspec/changes/<slug>/review.md` under `## Specification challenges`,
with `Artifact`, `Counterexample`, `User impact`, `Proposed correction`, and
`Decision` for each challenge. State the concrete input, result, invariant, and
whether evidence was executed or is a proposed probe. Include user impact within
the declared promise and propose corrected criteria/tests without inventing
compatibility or robustness requirements. Stop affected implementation; agents
cannot approve their own proposals. The owner records accept/reject/clarify,
rationale, and evidence/reference; preserve rejected challenges. Pending owner
resolution, use only the safest reversible interpretation already fixed by the
architecture and record evidence and interim action in `Decision`, not as
approval. If no such interpretation exists, behavior would change, or effects
are irreversible, report the blocker and wait. Do not merge with an unresolved
correctness challenge. Continue unaffected work; accepted corrections return
through existing spec/test approval points. See the review template.

A concrete counterexample may justify minimal reads outside `codemap.md`'s
slice. Record each extra path as its own row in the existing Field/Value table
in `openspec/changes/<slug>/metrics.md`:
`| Context expansion: <path> | <reason> |`. The archive metrics writer
preserves these rows. Refresh the slice when appropriate and keep
`agent-ready codemap check`.

## Stage

A failing existing test in alpha means the spec decides: a test for a removed
requirement is deleted, never rewritten with a weaker assertion and kept, and a
test for a kept requirement is a real failure. In release a failing existing
test is presumptively a break: stop and report. A new skip marker is residue
in alpha.

## Questions you must ask

1. Does any existing test contradict the delta? Which requirement wins?

## Approval

The human approves the test files.
