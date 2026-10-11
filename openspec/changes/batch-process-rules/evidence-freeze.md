## Resolved instructions

The owner's task of 2026-10-11 as resolved in `instruction-integrity.md`: docs lane (C1, C2 move
`mkdocs.yml`, `pyproject.toml` and version lines out), worktree only (C3, C7, C8), no owner
questions (C4), assurance `economy` (C5, C6), gitignored briefs trimmed outside the change (C9),
missing oracle tests as follow-ups (C10).

## Requirements

None: `skip_specs: true`. The reader task in `docs-plan.md` is the acceptance target.

## Evidence

- Upstream: `../agent-ready-python` latest tags `v0.9.0`, `checks-v0.15.11`; installed in a1cbae2.
- Oracle check survey (phase 0): check 2 covered over (a); check 3 partly (universal statements over (a), full IR only over shapes); check 4 over (b) only; check 5 over (a) with all rules on and addresses only; checks 1 and 6 uncovered.
- Timings at 29bbfe8: the six check files 17.6 s, 3,664 passed, 5 xfailed; the output loop 51 s, 192 outputs.
- The loop's stderr shows a `FutureWarning: Possible nested set at position 4` from `src/junoscfg/convert/field_validator.py:206` on 48 runs (a schema pattern compiled as written): ledgered as PROC-F1.
- `docs/decisions/2026-10-10-commit-device-captures-as-the-oracle.md`: the jvd clone is the opt-in breadth tier; this change keeps that and drops it from per-change evidence.

## Non-goals

As in `proposal.md`: `--jvd` and its tests and CI job stay; nav and `pyproject.toml` are
`batch-process-config`; T1–T4 are separate test-only changes; no upstream file is edited.

## Acceptance criteria

Every `docs-plan.md` QA item passes as recorded in `tasks.md`; `agent-ready check --set full`
passes once; the Reviewer finds no inaccurate claim or broken command left open.

## Performance expectations

None, because no runtime code changes. Process effect: per-change corpus evidence falls from the
owner's 45–90 minutes to about 70 seconds (17.6 s checks + 51 s loop per tree).

## Outstanding decisions

None, because the owner delegated the `--jvd` fate to the decision record and asked for no questions.

## Execution and checkpoint

- Assurance preference: economy
- Risk floor: normal (no red zone, break, trust boundary, public surface or cross-domain work)
- Roles required: Builder; fresh isolated Reviewer (added by the Builder, see preflight); Finalizer
- Resume point: phase 4 (QA tasks); last valid evidence 29bbfe8 plus this freeze

## Delta log

- Freeze established: proposal at the phase-1 commit, `docs-plan.md` and this file at the phase-2 commit.
