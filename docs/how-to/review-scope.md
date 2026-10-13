<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Contain review scope and defer independent work

## Freeze the outcome

Before implementation, approve the intended behavioural outcome, acceptance
criteria, and exclusions in the proposal and evidence freeze (the short lanes
keep these in their proposal). Documentation changes name the reader's task.
Fix defects that prevent that outcome and regressions introduced by the change,
including consequences outside edited files. Route independent defects to the
backlog. File location and severity alone never authorize more implementation.
Preserve applicable existing requirements; an exclusion cannot waive one.

## Classify and rule

Use the existing finding ID and authoritative ruling described in
[lifecycle-ledger.md](lifecycle-ledger.md). Record the evidence, relation to the
frozen outcome, disposition, and destination in the change's `review.md`.
The Orchestrator rules within owner instructions; disputed scope classifications
use that same ruling path. Requirement changes require the owner's ruling.
Pending decisions do not authorize implementation or weaken acceptance criteria.

An omitted-criteria challenge is valid when a concrete counterexample shows
that incomplete criteria undermine the agreed outcome or an applicable existing
requirement. Use the specification-challenge fields and freeze delta check.
An independent improvement is separate work, even when presented as a challenge.

## Review corrections

The initial review examines the complete change. Follow-up reviews verify
accepted corrections and their consequences, including affected callers,
contracts, tests, and documentation. Apply the existing evidence-invalidation
and rerun rules. Independent discoveries take the backlog route.
Reopen a closed finding only with new evidence material to its ruling; explain
what evidence changes the decision. Preserve the original finding and ruling.
The append-only ledger represents reopening as a linked new finding ID and a
new ruling, never a second ruling on the old ID. Repetition or a new reviewer
alone is not new evidence. There are no time limits or review-round caps.

## One backlog destination

Default to application-owned [docs/BACKLOG.md](../BACKLOG.md). When an existing
issue tracker is declared there, that tracker is the sole authoritative item
and status destination; the file is a pointer, not a parallel backlog. Respect
an existing application declaration and make it discoverable from that file.
Each item records a stable finding ID (qualify a change-local ID with its change
slug), defect, impact, reproducer or evidence, source-change link, and status.
Reuse the review ID; a tracker issue number may accompany it. Keep original
review evidence in its change folder, preserving links through archive moves
or using an immutable commit permalink. Create an OpenSpec change only when
the item is selected for implementation, and link the item to that change.

An authoritative backlog disposition resolves an independent finding's
obligation within the current review. Merely copying text into the backlog
does not. Ordinary backlog items neither block unrelated completion nor join
an active batch automatically. Select them explicitly as separate work.

## Binding obligations

A carry-forward is a condition of accepting the current change, not an ordinary
backlog item. Preserve its owning change, risk, dependencies, checkpoint,
expiry and renewal/closure authority under the lifecycle rules. Explicitly
record genuine dependencies and existing binding obligations in the ruling
and batch plan. Backlog placement cannot cancel them. A change completes when
its current obligations and binding acceptance conditions are satisfied;
independent findings need dispositions, not unrelated repairs.
