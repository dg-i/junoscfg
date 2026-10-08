# Phase 2 — Spec

## Outcome

`codemap.md`, the slice of the symbol index the change reads, and one delta
per capability the proposal names at `specs/<domain>/<capability>/spec.md`,
valid under `openspec validate <slug> --strict` and approved by the domain's
owners.

## The code-map slice

`agent-ready codemap build`, then `agent-ready codemap slice --change <slug>`,
which writes `codemap.md` from the symbol index: modules ranked by the paths
the proposal's domains name, each domain in turn, then their neighbours in the
import map, then by churn, cut at 1,500 tokens, each with its zone, layer, and contract path and,
beside every public symbol, the `agent-ready codemap show` command that prints
it alone. Later phases stay within the slice unless a concrete counterexample
requires a minimal read outside it. Record each extra path as its own row in
the existing Field/Value table in `metrics.md`:
`| Context expansion: <path> | <reason> |`. The archive metrics writer
preserves these rows. Refresh the slice when appropriate, and keep
`agent-ready codemap check`.

## Specification challenges

Approved artifacts remain the baseline; do not silently change approved intent
or weaken tests. When evidence challenges an approved proposal, spec, test, or
contract, stop affected implementation and create or update
`openspec/changes/<slug>/review.md` under `## Specification challenges`. Repeat
a subsection for each challenge with `Artifact`, `Counterexample`, `User impact`, `Proposed correction`, and `Decision`. A counterexample states its
input, observed or logically demonstrated result, violated invariant, and
whether evidence was executed or is a proposed probe. Include observable user
impact within the declared promise; trust-boundary validation is correctness
even when omitted from the proposal. Propose corrected criteria and affected
tests/specs without inventing compatibility or robustness requirements.

Set `Decision` to `Pending owner decision` until the owner records accept,
reject, or clarify with rationale and evidence/reference. Preserve rejected
challenges. Agents cannot approve their own proposals. Continue unaffected work.
While pending, use only the safest reversible interpretation already fixed by
existing architecture; record its architectural evidence and interim action in
`Decision`, which is not approval. If none exists, or acting changes approved
behavior or has irreversible effects, report the blocker and wait. Do not merge
with an unresolved correctness challenge. Owner-accepted corrections return
through the existing spec/test approval points. See the review template.

## The delta

1. `openspec instructions specs --change <slug>` prints the template.
2. One file per capability, at the exact path. Sections are ADDED, MODIFIED,
   REMOVED, and RENAMED Requirements, nothing else.
3. Every requirement in EARS form, WHEN a condition THEN the system SHALL a
   behaviour, with at least one scenario and the id of an acceptance test:
   `Tests: tests/<file>.py::<test>`. A test that does not exist yet is written
   in phase 4; a requirement that names none fails `agent-ready reconcile`.
   A requirement about a capability several entry points expose names each
   door in its scenarios, the readers the intent search found and never the
   stage's surface list, and its test drives every door.
4. A MODIFIED block carries the whole requirement, every scenario it keeps
   included: `archive` replaces the block, and strict validation refuses one
   that drops a scenario silently.
5. A new capability carries a Purpose someone wrote, in a sentence or two.
6. `[NEEDS CLARIFICATION]` marks a gap you could not close; it is a question
   for the human, never a placeholder to fill.
7. A requirement about a pair of inverse functions, serialise and
   deserialise, parse and render, encode and decode, states which direction
   is the identity, since render after parse is not one for unnormalised
   input.

Lite spec is the default. A full spec, with error conditions and design
implications spelled out, only for cross-domain, API, migration, or security
changes.

## Stage

In alpha a feature delta that only adds is a question back to the human, and
so is an addition a fixer makes from a review finding the proposal did not ask
for. A REMOVED section in alpha is the normal shape of a pivot. In beta and
release a removal follows a deprecation requirement from an earlier change,
and the delta of a declared break names the migration.

## Questions you must ask

1. Which existing requirement does this change contradict, if any? Quote both.
2. Which acceptance test pins each new requirement, and does it exist?

## Approval

The domain owners' review of the delta: CODEOWNERS routes
`openspec/changes/*/specs/<domain>/**` to them. Where the repository has no
pull requests, the owner's commit.
