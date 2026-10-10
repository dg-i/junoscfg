# Phase 4 — Tests

## Documentation-only route

Type `docs` follows phase 4 in `types/docs.md` and stops before the code route
below.

## Outcome

The acceptance tests the evidence freeze names, and any contract test changes,
written in one pass with no implementation. Risk-required independent
Test/Challenge evidence is separate from the Builder's tests.

## Process

1. For each requirement in the delta, the test its `Tests:` line names, in
   that file and under that name: `uv run --locked --group dev agent-ready
   reconcile` reads the id phase 2
   wrote and fails while the test does not exist. A requirement with several
   doors has one test that drives each door with the input only the richer
   side accepts, the override set and unset.
2. Contract tests where a module's `__all__` or a Protocol changes: the
   conformance suite runs over real and fake implementations.
3. A requirement about a pair names one round-trip property as its test. Its
   Hypothesis strategy is derived from the value type and never from the
   table, so inputs the table does not cover reach a hand-written remainder
   and fail it. Hypothesis is approved in the toolbox already, so the change
   that writes the first pair adds it to the dev group without a design.
4. No implementation. A test that passes before the change exists is not
   testing the change. A scanning test asserts what it scanned, not only what
   it found, or an empty scan passes it; a test asserts the property the
   feature exists for, not that something moved; a test command that can skip
   everything needs a check that it did not.
5. Apply the role policy from the freeze. High risk and maximum assurance use a
   context-isolated Test/Challenge role; balanced uses it for behavioural
   changes; economy omits it below the mandatory floor. The independent role
   challenges criteria and proposes or writes adversarial tests but does not
   implement the product. Record why it ran or why policy omitted it.
6. The human reviews the test files under the existing zone approval policy,
   not the whole diff. Consolidate any material questions. Approved tests are
   the baseline, subject to the formal challenge path; never silently change
   approved intent or weaken a kept requirement's assertion. After approval,
   progress automatically to implementation without an owner relay.

## Specification challenges

A challenge goes in `openspec/changes/<slug>/review.md` with `Artifact`,
`Counterexample`, `User impact`, `Proposed correction`, and `Decision`; the
owner decides, and only a safe reversible action may proceed while pending.
A concrete counterexample may justify minimal reads outside `codemap.md`'s
slice. Record each extra path as its own row in the existing Field/Value table
in `openspec/changes/<slug>/metrics.md`:
`| Context expansion: <path> | <reason> |`. The archive metrics writer
preserves these rows. Apply phase 2's explicit slice-refresh triggers and keep
`uv run --locked --group dev agent-ready codemap check`.
Every new counterexample also receives the evidence-freeze delta consistency
check before the affected acceptance criteria change.

## Stage

A failing existing test in alpha means the spec decides: a test for a removed
requirement is deleted, never rewritten with a weaker assertion and kept, and a
test for a kept requirement is a real failure. In release a failing existing
test is presumptively a break: stop and report. A new skip marker is residue
in alpha.

## Questions you must ask

1. Does any existing test contradict the delta? Which requirement wins?

## Approval

The human approves the test files as the zone policy requires. The Builder then
records the checkpoint and continues without asking for a phase transition.
