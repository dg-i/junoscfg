# Phase 6 — Review

## Outcome

`review.md`: ranked correctness or contract findings, and anything the toolbox,
standard library, a declared dependency, or this repository already provides.
The reviewer writes only the report and evidence rows and edits no code, spec, or test.

## A fresh session

The review never shares a session with the implementation. On Claude Code a
read-only subagent; on Codex a new session opened on the branch. Either reads
the delta, the contracts of the modules touched, the tests, and the diff, in
that order of leverage, and nothing the implementer wrote about its own work.
The reviewer model is at least as capable as the implementer's.

An accepted correction runs its regression and `uv run --locked --group dev
agent-ready check --set fast`,
then returns to the reviewer. After approval, rerun the full set only if runtime
code, tests, generated artifacts, or their configuration changed since the
recorded checkpoint; it replaces standalone pre-commit and full tests.

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

Create or update `openspec/changes/<slug>/review.md` under
`## Specification challenges`; preserve existing entries. Repeat a subsection
for each challenge with `Artifact`, `Counterexample`, `User impact`, `Proposed correction`, and `Decision`. State concrete input, result, invariant, and
whether evidence was executed or is a proposed probe. Include observable impact
within the declared promise; trust-boundary validation is correctness even if
criteria omit it. Propose corrected criteria and affected tests/specs without
inventing compatibility or robustness requirements. The reviewer proposes
entries but edits no code, spec, or test. The owner resolves each challenge;
agents cannot approve their own proposals, and rejected challenges remain.
While pending, use only the safest reversible interpretation already fixed by
the architecture, recording its evidence and interim action in `Decision`, not
as approval. If unavailable, report the blocker. Do not merge with unresolved
correctness challenges. Continue unaffected work. Minimal reads outside the
slice are allowed for a concrete counterexample; record each extra path as its
own row in the existing Field/Value table in `metrics.md`:
`| Context expansion: <path> | <reason> |`. The archive metrics writer
preserves these rows. Refresh the slice when appropriate.
When complete, tick the review lifecycle task in `tasks.md`; leave the metrics task open.

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
