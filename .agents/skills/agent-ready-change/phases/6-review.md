# Phase 6 — Review

## Outcome

`review.md`: the findings that affect correctness or violate a contract,
ranked, and anything the toolbox, the standard library, or a declared
dependency already provides. The reviewer edits nothing.

## A fresh session

The review never shares a session with the implementation. On Claude Code a
read-only subagent; on Codex a new session opened on the branch. Either reads
the delta, the contracts of the modules touched, the tests, and the diff, in
that order of leverage, and nothing the implementer wrote about its own work.
The reviewer model is at least as capable as the implementer's.

## Findings

- A finding names the requirement or contract line it violates and the diff
  line that violates it, or identifies a concrete trust boundary/invariant and
  counterexample where criteria omit it. Record an omitted-criteria challenge;
  do not suppress a correctness finding for lack of a requirement citation.
- A finding about something the toolbox, the standard library, or a declared
  dependency already provides names the provider.
- The classes follow the stage, below. A finding outside them is not written.
- Rank by consequence. The human reads findings, not prose.

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

## Stage

Alpha: residue is a finding class, and a finding that asks for compatibility,
configurability, generality, or a defensive check is excluded, with two
exceptions that stay: validation of data crossing a trust boundary, which is
correctness, and a property the change removes, which is correctness whatever
it asks for. Excluded findings arrive in disguise: a fallback for data written
before a migration, a test that exercises a retired surface only to assert its
absence, a documentation line restored for a retired concept. Beta: residue
and a missing changelog fragment. Release: a missing deprecation, a missing
fragment, an undeclared surface change.

## Approval

The human reads the report before the diff. Findings that survive the human's
review are counted at archive.
