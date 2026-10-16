<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

As resolved in `instruction-integrity.md`: docs lane; the owner's ruling of 2026-10-16 relayed
by the coordinator (C1); activation on `master` (C2); executed evidence recorded beside the
reviews' wording where they differ (C3, C4); the BACKLOG link convention (C5).

## Requirements

None: `skip_specs: true`. The reader task in `docs-plan.md` is the acceptance target.

## Evidence

- The two archived reviews named in `docs-plan.md`.
- Reproducers at 716a9d1: `private_test_data/makeover-work/backlog-open-findings/probes-716a9d1.txt`.
- Strict MkDocs baseline on 716a9d1: exit 1, 48 warnings, all `BACKLOG.md` links outside
  `docs/` (`mkdocs-base.txt` in the same folder).

## Non-goals

As in `proposal.md`.

## Acceptance criteria

Every `docs-plan.md` QA item passes as recorded in `tasks.md`; the fresh Reviewer's verdict is
Merge; `agent-ready check --set full` passes once before review and once, canonically, before
merge.

## Performance expectations

None, because no runtime code changes.

## Outstanding decisions

None, because the owner's ruling and the coordinator's brief settle every entry.

## Execution and checkpoint

- Assurance preference: economy; risk floor not high (`instruction-integrity.md`)
- Roles required: Builder; a fresh isolated Reviewer dispatched by the coordinator; bounded
  finalization by the Builder
- Resume point: phase 6 (review); QA evidence in `tasks.md`

## Delta log

- Freeze established 2026-10-16 on a294b07 (proposal) under the owner's ruling.
- Phase 5, 2026-10-16: documents at 30368ba; activation on master 3ec85f0 merged in (C2); base for review and metrics 3ec85f0. The per-entry probe path moved into each entry's IDs line so every entry names its probe; no criterion changed.

## Scope and completion

Outcome: every pending finding the brief lists is backlogged once, reproducibly, with its
ruling and interim. Exclusions: the proposal's non-goals. No dependency on another change.
