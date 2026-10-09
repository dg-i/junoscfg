# Phase 7 — Archive

## Documentation-only route

Type `docs` follows phase 7 in `types/docs.md` and stops before the code route
below.

## Outcome

The change folder under `openspec/changes/archive/`, reviewed requirements in
the main capability specs, and `metrics.md` plus `metrics.json` carrying
provenanced evidence.

## Process

After implementation and review, in this order:

1. While the live change folder exists, apply its reviewed delta to
   `openspec/specs/` on the same branch. Use `npx --yes
   @fission-ai/openspec@1.13.0 archive` in a disposable
   checkout to produce the main-spec result, then bring those spec edits into
   the live branch without moving its change folder. Review the resulting
   main specs against the delta. The lane gate requires the live folder for
   these governed edits. Run `npx --yes @fission-ai/openspec@1.13.0 validate
   <slug> --strict` and `npx --yes @fission-ai/openspec@1.13.0 validate
   --specs`; resolve any new-capability Purpose placeholder.
2. Commit code, tests, main specs, and the live change folder, then record
   full immutable base and code-head commit IDs. Run `uv run --locked --group
   dev agent-ready metrics <slug> --base-sha SHA --head-sha SHA` before merge,
   while the live folder
   exists. Optional `--session-log PATH --runtime codex|claude
   --session-binding PATH` imports a native JSONL window declared by the
   operator; `--human-effort PATH` imports explicit human observations. The
   binding and manual files carry the same change and SHA pair. Missing or
   unsupported evidence remains `UNMEASURED`; no agent estimates it.
3. Review both metrics files, tick the metrics lifecycle task, run `uv run
   --locked --group dev agent-ready lane`, and commit the evidence files and
   task update. Then merge. The capture head remains
   the code commit, even if the evidence commit or squash merge has another ID.
   A change whose point is that something works better now records the
   measurement that shows it as a row of `metrics.md`, where the next person
   finds it. With every task ticked, `uv run --locked --group dev agent-ready
   lane` expects `review.md` and `metrics.md` in the folder before the merge:
   presence, not approval.
4. Archive only when `tasks.md` has no open box and `npx --yes
   @fission-ai/openspec@1.13.0 status --change <slug>` shows every common
   artifact complete. Conditional artifacts are enforced by lane, not status.
   An open task is a question for the human, never a warning to pass, and `npx
   --yes @fission-ai/openspec@1.13.0 validate --archived` fails an archived
   change that carries one. Then run `npx --yes
   @fission-ai/openspec@1.13.0 validate <slug> --strict` and `npx --yes
   @fission-ai/openspec@1.13.0 archive <slug> --yes --skip-specs`.
   The main specs were already reviewed and merged. A fix-lane change has
   `skip_specs: true` and no delta.
5. `npx --yes @fission-ai/openspec@1.13.0 list --specs` confirms the capability
   and requirement count.
6. Commit the archive-only move on the default branch. Where the default branch
   is protected, a small pull request carries that commit.

OpenSpec moves both metrics files with the change folder. Context-expansion
rows in the existing `metrics.md` Field/Value table survive capture. They
record a decision to expand context, not measured read telemetry.

The pre-merge spec application is part of the same reviewed change. Never
merge a live delta with unapplied main-spec edits: after the merge, the
supported `--skip-specs` archive operation moves the folder without applying
the delta a second time.

## Approval

The merge was the approval. Archiving records it.
