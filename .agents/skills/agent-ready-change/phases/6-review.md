# Phase 6 — Review

Type `docs` follows phase 6 in `types/docs.md` and stops before the code route below.

## Outcome

`review.md`: the risk-required fresh isolated verdict with ranked findings and
duplicated providers, or the recorded policy reason review was not required.

## A fresh isolated Reviewer

Use the freeze's risk floor and assurance preference. High risk always requires
this Reviewer; balanced adds yellow zones; maximum assurance adds every standard
or docs change; economy omits it below the floor. Record an omission without
presenting Builder self-review as independent.

The Reviewer is fresh and isolated from Builder reasoning and write access. It
reads the freeze, delta, touched contracts, challenge evidence, tests, and diff,
in that order. Its model is at least as capable as the Builder. Provider-specific
mechanisms are implementation details. If the runtime cannot supply the required
isolation or capability, record a runtime/operator correction and stop.

Coherent tasks in one change receive one review after implementation. Independent
changes receive a separate verdict and `review.md` each, even when acceptance is batched
or one fresh Reviewer processes a bounded window. An integration review only
supplements those verdicts; use `batches.md` for the boundary.

An accepted correction runs its regression and `agent-ready check --set fast`,
then returns to the same isolated Reviewer. Rerun the full set only if runtime
code, tests, generated artifacts, or configuration changed since its checkpoint;
it replaces standalone pre-commit and full tests.

## Findings

- A finding names the requirement or contract line it violates and the diff
  line that violates it, or identifies a concrete trust boundary/invariant and
  counterexample where criteria omit it. Record an omitted-criteria challenge;
  do not suppress a correctness finding for lack of a requirement citation.
- A finding about something the toolbox, the standard library, a declared
  dependency, or this repository already provides names the provider.
- No gate sees fidelity, nor whether a documented claim still holds: caps,
  interfaces, the lane and the tests all pass on output the thing produced
  for would reject. The reviewer's job is the part no gate covers.
- Where the change's record contradicts an instruction the owner gave, that
  contradiction is the first thing to check: a reversal on one experiment is
  the commonest wrong finding of the implementer's own.
- A review that touches what a decision record governs cites the record's id.
- "I could not check X" names the next failure: it goes to the carry-forward
  list of the change, not only into the report.

## Specification challenges

Record challenges in `openspec/changes/<slug>/review.md` with `Artifact`,
`Counterexample`, `User impact`, `Proposed correction`, and `Decision`. The
Reviewer edits no code, spec, or test; agents cannot approve their own proposals.
The owner decides; preserve existing entries, and proceed only with safe reversible
work. Record each justified slice read in the Field/Value table in `metrics.md`:
`| Context expansion: <path> | <reason> |`. The archive metrics writer preserves
these rows. Apply phase 2's triggers, check the freeze, tick review, leave metrics open.

Before concluding, answer these prompts:

1. **Trust-boundary input:** What attacker-controlled input crosses a trust
   boundary, and can it violate the existing boundary invariant even where the
   proposal and tests omit validation?
2. **Incompatible-but-valid input:** What input valid under the declared product
   promise conflicts with implementation assumptions? Show a
   counterexample; do not restore retired inputs or invent compatibility
   promises.
3. **Shared blind spot:** Could implementation and all acceptance tests satisfy
   the same incorrect criterion while violating the user's stated outcome or an
   existing trust boundary? Identify independent evidence and propose corrected
   criteria through the challenge path.
4. **Second answer:** does the diff answer a question the slice already
   answers, with a capability the other side lacks, an override, a fallback,
   a parameter, an error path? Name both. Where the proposal lists the
   readers of an override, check each of them, inside the slice or not, as a
   context expansion. A split elsewhere is the garden sweep's, not yours.
5. **Stated figures and non-goals:** rerun every number the proposal or the
   record rests on from what this repository holds, and read a non-goal that
   says *cannot* as a claim: find its evidence or report it unproven. A figure
   nobody can rerun and a blocker nobody checked are both findings.

## Stage

Alpha: residue is a finding class, and a finding that asks for compatibility,
configurability, generality, or a defensive check is excluded, with three
exceptions that stay: validation of data crossing a trust boundary, which is
correctness, a property the change removes, which is correctness whatever it
asks for, and a second answer, whose fix may remove the capability from both
sides rather than add it to one. Excluded findings arrive in disguise: a
fallback for data written before a migration, a test that exercises a retired
surface only to assert its absence, a documentation line restored for a
retired concept. Beta: residue and a missing changelog fragment. Release: a
missing deprecation, a missing fragment, an undeclared surface change.

## Approval

The human reads the report before the diff; surviving findings count at archive.
