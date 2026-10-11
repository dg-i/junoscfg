# Batches

Use this file only when one request contains several tasks. A batch is an
orchestration unit, not automatically one change.

## Classify after the shared preflight and before phase 1

For the standard and docs lanes, several tasks are one coherent change only
when all of these hold:

- they serve one user-visible outcome and one proposal;
- they have the same zone, owners, approval policy, and release fate;
- they can be reviewed and reverted together without leaving a partial promise;
- their combined diff is reviewable as one unit and fits one bounded context:
  `codemap.md` for code or `docs-plan.md` for documentation; and
- one acceptance story can name every task without an unrelated conjunction.

One coherent standard or docs change may name several capabilities and tasks.
It still has one branch, pull request, change folder, full checkpoint,
risk-required phase-6 verdict, metrics pair, and archive.

The fix lane has one failure mode, one regression test, and its existing file
and line caps. Several repair steps for that failure may share the fix. Several
failure modes are separate fixes, or one standard-lane `bug` when they form one
coherent outcome outside the fix caps. The fix route keeps its zone-selected
human review and receives independent Test/Challenge or Reviewer work only
when the shared high-risk floor requires it.

If any condition fails, make separate changes. Never put several live change
folders in one pull-request diff. The batch may share a plan, dependency order,
question round, and owner review window. Every independent standard or docs
change keeps its own approved artifacts, targeted checks, immutable checkpoint,
review record, metrics, and merge decision. Every independent fix keeps its own
regression test, full check, zone-selected review, and merge decision.

## Execute

The **Orchestrator** plans the batch, dependency order, conflicts, serialized
paths, and role requirements. It starts Builders in isolated worktrees and
starts required Test/Challenge and Reviewer roles with fresh isolated context
and the capability the assurance policy requires. It relays their recorded
reports, rules within owner instructions, and alone merges to the default
branch. It never substitutes its own reasoning for an independent verdict.

A Builder owns one change branch and worktree. It reports **STOP-T** after its
phase-4 material when independent Test/Challenge work is required, then waits
for the Orchestrator's ruling. It reports **STOP-R** after phase 5 and its one
full checkpoint, then waits for review. Every stop names the change folder,
base and head SHAs, zone, risk evidence, and roles required. A challenge or
repeated failure stops its change while unrelated Builders may continue.

`[tool.template.batch].max-builders` is the machine-wide limit, default 3.
Run at most that many Builders, each on its own branch and worktree. The main
checkout is only for merges, archive commits, and tags. A worktree runs its
full checkpoint at most once before review; no more than `max-builders` full
checks run across the machine at once. Targeted and fast checks may run as the
phase rules require.

Changes matching any `[tool.template.batch].serialized-paths` glob run one at
a time; use it for repository-declared regenerated artifacts. Changes that edit
the same file never overlap. A dependent change starts only after its
predecessor merges and its branch is created from the updated default branch.

Inside one coherent change, run targeted tests as each task lands and take one
full checkpoint after the last implementation task. Independent changes never
share checkpoint evidence. A repository-declared expensive tier in
`expensive-tiers` runs once for a change whose diff touches its `paths`, or once
at the batch boundary when independent changes can share the exact combined
input. Never rerun an expensive tier for a review-fix round.

## Merge a parallel branch

The Orchestrator rebases the branch onto the current default branch, then reruns
affected tests and the fast set. If the rebase brought runtime changes into the
branch, rerun the full checkpoint. Resolve generated-artifact conflicts only by
regenerating from their sources. Choose the version from the current default
branch at merge time, fast-forward the branch, perform the archive commit and
tag, and remove the worktree. A later green branch never stands in for this
change's evidence.

## Review and approval

One coherent standard or docs change receives the review its risk floor and
assurance preference require after all tasks are implemented. Independent
changes never borrow another change's verdict or omission rationale. A required
Reviewer may inspect a small related window, but writes a separate report in
each change folder and receives every accepted correction it found.

Batch the owner's questions and acceptance summaries where that reduces
interruptions. An answer still identifies each change it accepts. A final
integration review may inspect dependency order, shared contracts, duplicate
answers, migrations, and the cumulative diff; it supplements rather than
replaces each change's review.

Do not claim that shared review saves tokens or time. For a trial, add preserved
Field/Value rows to every participating `metrics.md`: `Batch id`, `Batch review
mode`, `Batch check executions`, `Batch integration-only findings`, and `Batch
escaped regressions`. The existing review-usage and human-effort fields carry
tokens, findings, and minutes. Change review policy only after the paired sample
in the measurement plan reaches its decision threshold.
