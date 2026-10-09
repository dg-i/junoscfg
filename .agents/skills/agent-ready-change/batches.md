# Batches

Use this file only when one request contains several tasks. A batch is an
orchestration unit, not automatically one change.

## Classify before phase 1

For the standard and docs lanes, several tasks are one coherent change only
when all of these hold:

- they serve one user-visible outcome and one proposal;
- they have the same zone, owners, approval policy, and release fate;
- they can be reviewed and reverted together without leaving a partial promise;
- their combined diff is reviewable as one unit and fits one bounded context:
  `codemap.md` for code or `docs-plan.md` for documentation; and
- one acceptance story can name every task without an unrelated conjunction.

One coherent standard or docs change may name several capabilities and several
verification and implementation tasks. It still has one branch, pull request,
change folder, pre-review full checkpoint, phase-6 review, metrics pair, and
archive.

The fix lane has one failure mode, one regression test, and its existing file
and line caps. Several repair steps for that failure may share the fix. Several
failure modes are separate fixes, or one standard-lane `bug` when they form one
coherent outcome outside the fix caps. The fix route keeps its zone-selected
human review and does not acquire a phase-6 agent review.

If any condition fails, make separate changes. Never put several live change
folders in one pull-request diff. The batch may share a plan, dependency order,
question round, and owner review window. Every independent standard or docs
change keeps its own approved artifacts, targeted checks, immutable checkpoint,
`review.md`, metrics, and merge decision. Every independent fix keeps its own
regression test, full check, zone-selected review, and merge decision.

## Execute

Order independent changes by dependency. Merge a predecessor before
implementation starts on a change that needs its code, then branch the dependent
change from the updated target. Independent changes with no dependency may run
in parallel on separate branches or worktrees. Stop an affected change for a
challenge or repeated failure and continue only changes that do not depend on
it.

Inside one coherent change, run targeted tests as each task lands and run the
full pre-review checkpoint once, after the last implementation task. Do not run
one full checkpoint per checklist item. Across independent changes, do not let a
later green head stand in for an earlier change's checkpoint.

## Review and approval

One coherent standard or docs change receives one fresh phase-6 review after
all its tasks are implemented. Independent standard or docs changes receive one
correctness verdict each before merge, even when one fresh reviewer session
processes a small, related review window. Write a separate report in each change
folder and return every accepted correction to the reviewer that found it.

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
