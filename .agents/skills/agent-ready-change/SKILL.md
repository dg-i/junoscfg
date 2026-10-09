---
name: agent-ready-change
description: Run one change through the workflow, one phase per session, from proposal to archive on the OpenSpec CLI. Use for every change to this repository, fix lane included.
---

# Change

One change is one branch, one pull request, one change folder under
`openspec/changes/<slug>/`. Invoke as `agent-ready-change <phase>`, and read
this file and the one phase file you are running. Do not read the others; they
cost tokens you will not use.

The standard lane follows these phases. The fix lane follows the shorter route
under **Lanes** and does not run the phase files.

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
Its complete route is:

1. Create or switch to its dedicated branch. Run `git status --short`; do not
   begin with governed changes outside `HEAD`.
2. Run `npx --yes @fission-ai/openspec@1.13.0 new change <slug>`, then write a
   proposal of at most ten lines and set `type: fix`, the zone, and
   `skip_specs: true` in `.openspec.yaml`. Commit that approved intent before
   code or tests. The common OpenSpec graph is type-blind: its other status
   entries are not fix-lane obligations.
3. Write the one regression test and watch it fail, implement the repair, and
   commit the test and code. `uv run --locked --group dev agent-ready lane`
   also runs the added test against the merge base and rejects one that passed
   there.
4. Run `uv run --locked --group dev --with griffe --with tach --with
   towncrier --with vulture agent-ready check --set full`. The zone's tier
   decides who reviews the test and diff. After approval, merge, then archive
   with `npx --yes @fission-ai/openspec@1.13.0 archive <slug> --yes
   --skip-specs` in a separate archive-only commit or pull request.

A fix proposal names the failure mode that remains after the fix: a repair that
turns a loud failure into a quiet wrong answer is worse than the failure, and
the caps never ask. A fix that exceeds those caps is retyped `bug` and takes the
standard lane. A spike is a branch that never merges; its outputs reach main on
one standard-lane change.

## Sessions

Consecutive phases with no human approval between them may share a session.
Human approval ends the session: start the next phase fresh and carry only the
change folder. Implement to review is also fresh, because a review anchored on
the code it just wrote finds what it expects. There is no handoff file, and
nothing relies on compaction.

## The tools

OpenSpec owns the change folder. Invoke it only as `npx --yes
@fission-ai/openspec@1.13.0 ...`; invoke the check package only as `uv run
--locked --group dev agent-ready ...`. The longer full-check command in the
lane route supplies its four runtime tools explicitly. OpenSpec `new change
<slug>` creates the folder under the `agent-ready` schema, `status --change
<slug>` shows the common artifact graph, `instructions <artifact> --change
<slug>` prints one template, and `validate <slug> --strict` checks it. Phase 7
applies reviewed main-spec edits while the live folder remains; after merge,
`archive <slug> --yes --skip-specs` moves the folder. `agent-ready` adds `metrics`,
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
