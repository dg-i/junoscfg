# Phase 2 — Spec

Type `docs` follows phase 2 in `types/docs.md` and stops before the code route
below.

## Outcome

An approved `codemap.md` plus one valid delta per named capability at
`specs/<domain>/<capability>/spec.md`.

## The code-map slice

`uv run --locked --group dev agent-ready codemap slice --change <slug>` rebuilds
the index and writes the 1,500-token slice: proposal-domain modules in turn,
import neighbours, then churn, with zone, layer, contract, and a `codemap show`
command per public symbol. Later phases stay inside it unless a concrete
counterexample requires a minimal read. Record each extra path in `metrics.md`
as `| Context expansion: <path> | <reason> |`; archive preserves the row.

Rerender after a proposal-domain change, a referenced move or rename, a
zone/layer/contract-placement change, or implementation outside the slice, and
run `agent-ready codemap check`. New symbols, churn, and unrelated modules do
not refresh this bounded spec-phase picture.

## Specification challenges

Record counterevidence in `openspec/changes/<slug>/review.md` with `Artifact`,
`Counterexample`, `User impact`, `Proposed correction`, and `Decision`. The
owner decides; pending challenges permit only a safe reversible action. Record
every extra read in the existing Field/Value table in `metrics.md` as
`| Context expansion: <path> | <reason> |`; the archive metrics writer
preserves it. Follow the shared protocol in the skill root.

## The delta

1. Run `openspec instructions specs --change <slug>`; write one exact-path file
   per capability with only ADDED, MODIFIED, REMOVED, or RENAMED Requirements.
2. Use EARS: WHEN condition THEN the system SHALL behaviour. Give each
   requirement a scenario and `Tests: tests/<file>.py::<test>`; phase 4 writes a
   missing test and `agent-ready reconcile` rejects a missing id.
3. For capability exposed through several entry points, scenarios name every
   reader found in intent and the test drives every door, never the stage list.
4. A MODIFIED block repeats the complete requirement and every retained
   scenario because archive replaces it.
5. A new capability has a human-written Purpose. `[NEEDS CLARIFICATION]` is a
   question, never a placeholder.
6. For inverse pairs, state which direction is the identity; render after parse
   is not an identity for unnormalised input.

Lite is default; cross-domain, API, migration, or security changes use full.

## Stage

In alpha, question an add-only feature or an unrequested review addition;
REMOVED is a pivot's normal shape. Beta/release removals follow an earlier
deprecation, and a declared break names its migration.

## Questions you must ask

1. Which existing requirement does this change contradict, if any? Quote both.
2. Which acceptance test pins each new requirement, and does it exist?

## Approval

CODEOWNERS routes the delta to domain owners; without pull requests, approval
is the owner's commit.
