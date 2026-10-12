# Phase 2 — Spec

Type `docs` follows phase 2 in `types/docs.md` and stops before the code route
below.

## Outcome

An approved `codemap.md` plus one valid delta per named capability at
`specs/<domain>/<capability>/spec.md`, followed by an approved
`evidence-freeze.md` that is the execution baseline.

## The code-map slice

`uv run --locked --group dev agent-ready codemap slice --change <slug>` rebuilds
the index and writes the 1,500-token slice: proposal-domain modules in turn,
import neighbours, then churn, with zone, layer, contract, and a `codemap show`
command per public symbol. It is the bounded starting point, not a ban on
necessary context: containing modules, direct callers and dependencies,
contracts, and affected tests may be read automatically. Record a context row
only when the change crosses into another responsibility or domain:
`| Context expansion: <path> | <reason> |`; archive preserves the row.

Repeated expansion caused by the same module or domain is a cohesion-review
signal. Review responsibilities and the public surface; split only across a
named responsibility boundary and only when the split reduces relevant context
without increasing import coupling, cycles, or duplicated interfaces. Never
split code merely to make this generated slice shorter.

Rerender after a proposal-domain change, a referenced move or rename, a
zone/layer/contract-placement change, or implementation outside the slice, and
run `agent-ready codemap check`. New symbols, churn, and unrelated modules do
not refresh this bounded spec-phase picture.

## Specification challenges

Record counterevidence in `openspec/changes/<slug>/review.md` with `Artifact`,
`Counterexample`, `User impact`, `Proposed correction`, and `Decision`. The
owner decides; pending challenges permit only a safe reversible action. Record
each cross-responsibility or cross-domain read in the existing Field/Value table in `metrics.md` as
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

## Evidence-freeze gate

At the end of this phase, create `evidence-freeze.md` from its OpenSpec
template. Resolve and cite the effective instructions, requirements, evidence,
non-goals, acceptance criteria, performance expectations, and outstanding
decisions. Record the assurance preference, risk floor, required roles, and
resume point. Phase 2 cannot close with a material outstanding decision.

Any instruction or evidence arriving after the freeze triggers a delta
consistency check before affected work continues. Append the source, change,
conflicts and criteria affected, invalidated work, and reruns required. An
unchanged conclusion is still recorded; silently absorbing a delta is not.
Regenerate only the artifacts the delta invalidates, once per distinct delta.
If the same delta triggers regeneration again, diagnose the unstable source
instead of looping.

Before committing changed records, run `agent-ready fields` and `agent-ready
caps`; correct their diagnostics before the commit and phase hand-off.

## Stage

In alpha, question an add-only feature or an unrequested review addition;
REMOVED is a pivot's normal shape. Beta/release removals follow an earlier
deprecation, and a declared break names its migration.

## Questions you must ask

1. Which existing requirement does this change contradict, if any? Quote both.
2. Which acceptance test pins each new requirement, and does it exist?

## Approval

CODEOWNERS routes the delta to domain owners; without pull requests, approval
is the owner's commit. Once the freeze is approved, the continuous Builder
progresses automatically to design when required and otherwise to verification.

## Scope baseline

Freeze the intended outcome as well as criteria and exclusions. Follow
`docs/how-to/review-scope.md` when classifying new evidence: a valid
omitted-criteria challenge follows the owner ruling and delta check; an
independent improvement goes to the declared backlog without enlarging scope.
