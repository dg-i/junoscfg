---
name: agent-ready-change
description: Implement an application change, fix, or docs update through the governing workflow.
---

<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Change

One change has a branch and `openspec/changes/<slug>/`. Start with
`phases/0-preflight.md`, then load only the selected route below. For several
requested tasks, first read `batches.md` to determine their change boundaries.

| Route | Read after preflight |
|---|---|
| One failure mode and regression (`fix`), or non-behavioural `maintenance` | `short-lanes.md` |
| Documents only (`docs`), no runtime code, tests, executable config or behaviour specs | `types/docs.md` |
| Standard behavioural or structural change | One phase at a time: 1-intent, 2-spec, 3-design (feature/new-dependency only), 4-tests, 5-implement, 6-review, 7-archive under `phases/` |

For `pivot`, `stage-up`, or `spike`, also read the matching `types/` file.
A spike never merges. A fix spanning several files remains a fix if every edit
repairs one failure mode; explicit application fix-lane limits still apply.

## Authority and continuation

The Builder owns specification, implementation, accepted fixes and bounded
finalization. Continue across non-decision boundaries; existing user authorization
covers routine edits and phase transitions. Ask only for material unresolved
product/policy decisions, with evidence and a recommendation in one batch.
Never infer acceptance from silence or an agent-authored commit. Application
approval, archive, version and integration requirements remain binding.

Before implementation, freeze outcome, criteria and exclusions in the lane's
existing records. Follow `docs/how-to/review-scope.md` for findings and backlog
routing. Record the next incomplete step and last valid evidence there at
meaningful checkpoints and before interruption. Read sources once per unchanged
revision. New instructions or counterevidence require a delta check: identify
changed criteria, invalidated work and required reruns before affected work.
Continue unaffected work while a material decision is pending.

## Roles

Every lane receives a fresh isolated Reviewer, with no Builder reasoning or
suggested verdict. Give it the immutable base/head, criteria, contracts, diff,
verification evidence and verdict destination. It edits no product files and is
at least as capable as the Builder. A short lane uses a lightweight `review.md`;
standard and docs lanes use their review procedure. Application policy may add
reviewers or human approval; preferences cannot subtract those controls.

Independent Test/Challenge work is mandatory for red zones, security or trust
boundaries, data migration, declared breaks, named public-surface changes, and
cross-domain changes, on every lane. The standing `[tool.template.assurance]`
preference adds Test/Challenge for behavioural changes under `balanced`, and
for every change under `maximum-assurance`; `economy` adds none. Record required
roles and the application policy citation once in preflight; the freeze refers
to it. Unavailable independence blocks completion, never becomes self-review.

## Verification

The executable authority is `uv run --locked --group dev agent-ready check
--set full`. The runner supplies missing tools through uv’s isolated tool environments. Prepare changelog fragments
and declared inputs, commit the implementation with review/metrics tasks still
open, and run full before review on every lane. Do not duplicate its hooks or
application suite on the same snapshot. Docs retains integrity checks and uses
its QA plan in place of application tests.

After corrections, run focused evidence and `agent-ready check --set fast`;
changes to whole-command inputs (runtime code, tests, generated artifacts,
configuration, lockfiles, base, command, task scope or execution identity) also
require full again before the follow-up verdict. Task ticks and evidence-only
records do not invalidate a passing runtime checkpoint. Expensive tiers and caches retain
their own input validity rules. For activated `strategy-a/1`, use
`docs/how-to/verification-evidence.md`; readiness and lifecycle gates still apply.
Close review and metrics only with evidence, then run the lane gate. A file's
presence proves neither independence nor owner acceptance.

Classify failures before retrying. Repair tooling failures from evidence; they
are not counterevidence to a specification. Stop an unchanged failing attempt
without new evidence or a changed hypothesis. Never weaken an oracle to pass.

## Specification challenges

Keep approved criteria as the baseline. Record concrete counterevidence in
`review.md` under `Specification challenges`: `Artifact`, `Counterexample`,
`User impact`, `Proposed correction`, and `Decision`. Distinguish executed
results from proposed probes. Set the decision to `Pending owner decision`;
the owner accepts, rejects or clarifies with reasons. Preserve rejected entries.
Only a safe reversible interim action fixed by existing architecture may proceed
while pending. Unresolved correctness challenges block completion. Accepted
corrections update affected criteria, tests and evidence through the delta check.

## Tools and completion

All `agent-ready ...` commands in this skill and route files mean
`uv run --locked --group dev agent-ready ...` in this application.

OpenSpec supplies artifact operations through `npx --yes
@fission-ai/openspec@1.13.0`: new change, instructions, status, validate and archive.
Its type-blind graph does not add artifacts omitted by the selected lane.
Do not install generic OpenSpec skills or OPSX commands. Inspect existing local
entries with `agent-ready budget --report`; `agent-ready skills --retire-openspec
<outside-discovery-directory>` moves competing entries intact for recovery.

Run fields and caps before committing change records. Standard/docs metrics use
`agent-ready metrics`; read `docs/how-to/capture-change-metrics.md` when capturing.
Missing observations stay UNMEASURED. Short lanes need metrics only if application
policy requires them. Finalization cannot change approved meaning or verdicts.
Integrate/archive only with required acceptance, completed tasks and valid evidence,
in the application's resolved order; stop dependent commands on any failure.

Installed agent-ready skills are template-owned: improvements belong upstream.
At entry and completion, read only `Cadence state` in `docs/VERIFICATION.md` and the
`Routine cadence check` section of `docs/how-to/improve-verification.md`. Load `docs/how-to/improve-verification.md` when due, unknown, pending, or when
verification itself changes. Optional feedback never blocks requested work.
