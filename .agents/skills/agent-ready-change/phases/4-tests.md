<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

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
   and fail it. Check the approved toolbox and dev dependencies before choosing Hypothesis.
   Use existing tools when sufficient; a new dependency follows the design and
   owner approval policy, never an assumed blanket approval.
4. No implementation. A behavioural defect needs a test that fails before the
   repair; a new behaviour needs an acceptance test that the old code cannot
   satisfy. A refactor or other behaviour-preserving change may instead name
   existing tests, static checks, equivalence evidence, or a property test that
   proves preservation. A scanning test asserts what it scanned, not only what
   it found, or an empty scan passes it; a test command that can skip everything
   needs a check that it did not.
5. Run the independent Test/Challenge work recorded at preflight. It challenges
   criteria and tests without implementing product code.
6. The human reviews the test files under the existing zone approval policy,
   not the whole diff. Consolidate any material questions. Approved tests are
   the baseline, subject to the formal challenge path; never silently change
   approved intent or weaken a kept requirement's assertion. After approval,
   progress automatically to implementation without an owner relay.
7. Before committing changed records, run `agent-ready fields` and `agent-ready
   caps`; correct their diagnostics before the commit and phase hand-off.

## Stage

A failing existing test in alpha means the spec decides: a test for a removed
requirement is deleted, never rewritten with a weaker assertion and kept, and a
test for a kept requirement is a real failure. In release a failing existing
test is presumptively a break: stop and report. A new skip marker is residue
in alpha.

## Resolve from evidence; ask only material unresolved questions

1. Does any existing test contradict the delta? Which requirement wins?

## Approval

The human approves the test files as the zone policy requires. The Builder then
records the checkpoint and continues without asking for a phase transition.
