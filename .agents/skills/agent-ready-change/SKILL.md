---
name: agent-ready-change
description: Run one change through the workflow, one phase per session, from proposal to archive on the OpenSpec CLI. Use for every change to this repository, fix lane included.
---

# Change

One change is one branch, one pull request, one change folder under
`openspec/changes/<slug>/`. Invoke as `agent-ready-change <phase>`, and read
this file and the one phase file you are running. Do not read the others; they
cost tokens you will not use.

| Phase | File | Ends with |
|---|---|---|
| 1 Intent | `phases/1-intent.md` | the proposal, approved |
| 2 Spec | `phases/2-spec.md` | the code-map slice and the delta, approved |
| 3 Design | `phases/3-design.md` | the design and the reuse verdict, approved; `feature` and `new-dependency` only |
| 4 Tests | `phases/4-tests.md` | the acceptance tests, reviewed |
| 5 Implement | `phases/5-implement.md` | every task ticked, the checks green |
| 6 Review | `phases/6-review.md` | the review report, from a fresh session |
| 7 Archive | `phases/7-archive.md` | metrics filled, the change archived |

Three types carry a body of their own, read beside the phase from intent on:
`types/stage-up.md`, `types/pivot.md`, `types/spike.md`.

## Lanes

The change's `.openspec.yaml` declares `type` and zone, and the lane follows.
The fix lane, type `fix`, is a ten-line proposal, one regression test, and
code: two files, thirty lines, no delta, and `skip_specs: true`, in any zone.
Write the test first and watch it fail; `agent-ready lane` runs it against the
merge base and fails the pull request when it passes there. The zone's tier
picks the reviewer, not the route. A fix that exceeds those caps is retyped
`bug` and takes the standard lane, which every other type takes and which runs
every phase its type needs. A spike is a branch that never merges; its outputs
reach main on one standard-lane change.

## Sessions

Consecutive phases with no human approval between them may share a session.
Implement to review never does: the review starts fresh, because a review
anchored on the code it just wrote finds what it expects. Only the change
folder crosses a session boundary; there is no handoff file, and nothing
relies on compaction.

## The tools

OpenSpec owns the change folder: `openspec new change <slug>` creates it under
the `agent-ready` schema, `openspec status --change <slug>` shows which
artefacts are done and which are blocked, `openspec instructions <artifact>
--change <slug>` prints the instruction and template for one artefact,
`openspec validate <slug> --strict` checks it. Phase 7 applies reviewed
main-spec edits while the live folder remains; after merge, `openspec archive
<slug> --yes --skip-specs` moves the folder. `agent-ready` adds `metrics`,
`scaffold decision`, `decisions`, `render levers`, `stage`, `reconcile`, `lane`,
`retired`, and `codemap`, each named in the phase that uses it. A gap is reported, never
scripted around.

## Asking

Ask the way `agent-ready-onboard` does: in prose and never as a menu, in one
batch at the end of a phase, each question numbered and carrying the evidence
you derived and what you would do. Never fill a judgement call with a
plausible guess; an unanswered question is the phase's output.

## Stage

The declared stage in `[tool.template.stage]` sets a default each phase
reverses: alpha specifies the thinnest slice and removes rather than keeps;
beta and release deprecate before removing and declare every break in the
proposal. Each phase file carries the stage paragraph that applies to it, and
`types/stage-up.md` is the change that moves the stage.

## Stopping

Stop and report when the same check or test fails twice in a row, when a
phase's question is unanswered, when a failing existing test in release looks
like a break, or when you are about to write a fact you cannot point at
evidence for.
