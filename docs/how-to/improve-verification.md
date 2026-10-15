<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Improve testing and verification

This policy improves this application repository. Keep shared state in
`docs/VERIFICATION.md`; retain evidence in its existing CI or change records.
Reviews are invitations, not merge gates or permission to expand a change.

## Establish the baseline and targets

At onboarding, agree the four dimensions below and the three feedback stages.
Greenfield budgets are provisional until representative tests exist. For
brownfield, reuse representative measurements or measure existing commands in
the required environment; record gaps and a provisional accepted budget. An
unknown value is UNMEASURED with a reason, never zero or an invented estimate.
On refresh, reassess the baseline using comparable evidence; measure affected
stages when checks or their environment change. Preserve targets and accepted
limits unless the owner explicitly revises them with a reason.

| Dimension | Evidence and target |
|---|---|
| Feedback time | Elapsed time for each stage, including slow outliers; record environment, revision, command, cache state and observation count. Keep compute cost and queue delay separate. |
| Behavioural assurance | Critical behaviours and failure modes, their detecting checks and remaining gaps. Coverage locates gaps; it does not prove meaningful assertions. |
| Reliability | Flaky failures, reruns and false alarms; control clocks, randomness, shared state and external dependencies. |
| Corpus organisation | Predictable test locations and ownership, selectable test levels, explicit fixtures, independence, useful assertions and justified overlap. Prescribe properties, not a universal directory layout. |

For local fast checks, pull-request verification, and scheduled/release
verification, record commands, observed baseline, accepted time budget, target,
tolerance and evidence. An unused stage needs a reason. State which risks must
be checked before merge or release; moving checks later cannot waive that need.
Compare equivalent workloads with repeated observations and a declared tolerance;
a single slow run prompts investigation, not an automatic regression verdict.

Budgets constrain accepted cost; targets describe desired outcomes. Missing a
target does not block unrelated work. A material new regression must be resolved
or explicitly accepted by the owner with evidence and a reason. Existing gaps
remain visible; serious existing gaps need attention even when untouched.
Never skip required verification or report an incomplete run as successful to
meet a budget. Accept explicit tradeoffs: necessary assurance may cost more time.

## Improve within a change

When tests, fixtures, check configuration or verification workflows are affected,
assess the affected checks against all four dimensions. Record the conclusion in
the existing change evidence; a brief “no improvement warranted” is valid.
Optimise measured bottlenecks and preserve required assurance. Explain remaining
coverage before removing redundant tests. An escaped defect prompts assessment
of which layer should have detected it and a durable regression test where useful.

Keep local improvements proportional to the agreed scope. Independent restructuring
uses the authoritative backlog under `docs/how-to/review-scope.md`; touching a
test does not authorise a corpus rewrite. Give selected improvements an owner,
expected benefit, success check and review point. Prefer one or two at a time.
Evaluate prior improvements before selecting more; retain unsuccessful outcomes.

For concurrency or selective expensive checks, use the
[parallel verification qualification guide](parallel-verification.md). It defines
complete execution controls, audited nonselection and admitted-workflow timing.

## Routine cadence check

Read only `Cadence state` in `docs/VERIFICATION.md`. Resolve its integration
branch to a SHA without fetching. A pending invitation stays pending. Otherwise,
verify the anchor occurs in `git rev-list --first-parent <head-sha>` and count
`git rev-list --first-parent --count <anchor-sha>..<head-sha>`; at or above the
recorded interval, read the next section and prepare the assessment. Missing
state, shallow history, an absent anchor or Git failure is unknown, never zero:
read the next section to resolve it. Below the interval, stop this optional
cadence inspection. Do not load past outcomes or the rest of this guide unless
verification changes. No response changes neither pending state nor decisions.

## Determine when a review is due

At the first agent interaction, change completion, refresh completion and job end,
read only the `Cadence state` section of `docs/VERIFICATION.md`, stopping at
the next heading. Its current integration branch, anchor, interval and pending
status are sufficient; do not load historical outcomes. Load this guide only
when counting is due/unknown, feedback is pending, or verification changes. Use the configured integration
branch, not a feature branch's internal commits. Default interval: 10 commits.
Resolve that branch to an immutable SHA. Verify that the cadence anchor is on
its first-parent history, then use Git directly:

```sh
git rev-list --first-parent <integration-head-sha>
git rev-list --first-parent --count <cadence-anchor-sha>..<integration-head-sha>
```

Replace placeholders with validated recorded SHAs. Each first-parent commit,
including a merge commit, counts once; side-branch commits do not also count.
Squashes count once. Initialisation anchors at the current integration head;
it does not trigger a retrospective review of all history. A missing anchor,
rewritten history or shallow clone is unknown, not zero: obtain available
history or ask the owner to agree a new anchor, retaining the previous record.
Use the local integration ref without fetching solely for this invitation and
record the observed head; new remote commits become visible after normal sync.

When due, prepare a short assessment from existing evidence and record `pending`
with the assessed head. During unattended multi-commit work, defer the invitation
until job end and consolidate all thresholds into one. Before inviting, refresh
the assessment through the current observed integration head and record that SHA;
this includes commits made after the threshold during the job. A pending invitation
survives interruption or failure and is surfaced at the next user interaction.
Do not repeat an unanswered invitation in the same session or interrupt work
waiting for an optional reply. This is an interaction-time workflow, not a
background scheduler or an executable timing gate.

## Review with the user

Separate measurements, agent judgments and user feedback. Show timing trends,
reliability problems, assurance gaps, structural friction and results of prior
improvements; absent evidence stays unknown. Ask how well testing and verification
are working and what causes friction. Satisfaction favours preserving the approach;
specific friction favours targeted changes; dissatisfaction prompts diagnosis and
broader options with costs, not an automatic redesign. Satisfaction cannot erase
a serious assurance gap. Examine useful catches, escaped defects, diagnostic
waste and maintenance effort, not just speed or number of reviews completed.

On completion, record feedback and decisions, set last-reviewed SHA and cadence
anchor to the assessed head, and clear pending. On decline, record the declined
head, advance only the cadence anchor to that head, and clear pending; offer again
after the next interval. No response leaves pending; it is not a decline or
approval. Threshold crossings during a pending review remain consolidated.
Do not advance to a newer, unassessed head. Reconcile concurrent record edits
without losing feedback or moving the anchor backwards. Commit state through the
normal change workflow; do not add unrelated files to an exact updater receipt.

## Learn beyond this application

Keep compact problem, action, context, expected benefit and observed-result records
here, with evidence links; no raw session logs are needed. Cross-application
analysis is a separate, explicitly initiated activity after experience exists.
Generalise recurring findings, validate proposed template changes, and obtain
permission before sharing application evidence. Private application content stays
here. Completed reviews alone do not establish that the template is effective.
