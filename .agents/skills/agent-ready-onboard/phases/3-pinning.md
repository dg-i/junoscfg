# Phase 3 — Pinning

Brownfield only. Greenfield has nothing to pin: the tests arrive with the code.

## Outcome

Characterization tests covering the current behaviour of every module where a
change could go unnoticed, committed and passing, before any agent changes that
code; each pinned zone dated in its zone table entry.

## Why this comes first

Pin today's behaviour, then let the agent work. A gate installed before the
behaviour is pinned tells you the code is tidy; it does not tell you it still
does what it did. This is the one ordering in brownfield onboarding that is not
yours to vary.

## Ranking

Not by tier. A zone's tier is what a mistake there would cost, which is why it
governs approvals; it says nothing about whether a mistake would be caught.
Rank by exposure instead: the cost of being wrong weighed against what already
covers the code. A red zone with a thorough test suite is close to pinned
already, and a yellow one that nothing exercises and that deletes files outside
the repository is where behaviour changes without anyone noticing.

Phase 1's evidence carries what you need: the tier, the tests that reach each
area, whether the acceptance path touches it, and what it does outside the
process. Propose an order from those and let the human correct it — the first
pass of this on a real repository put the well-tested core first and an
untested module with destructive side effects in the middle.

## What to do

How deep this goes is the declared stage's to set, never the order's. Under
alpha, stop at one characterization test per named surface, placed in the zone
that owns it, plus one per zone that owns no named surface. Under beta, pin the
public surface, which includes a name's failure modes and every CLI option:
pin the exception a name raises and the option a command takes, not only the
name and the command. Under release, everything exposed.

Use the application's existing test and acceptance environment, including its container route and domain checks. Preserve separate fast and acceptance commands. For each module in that order, write tests that record what it does now,
including the behaviour that looks wrong. A characterization test is not an
assertion that the behaviour is correct; it is a record that it was this before
you touched it.

A test counts as pinning once it has been seen to fail: write it, break what it
guards, watch it go red, restore, watch it go green. A run after a mutation is
evidence only once the mutated file was read back and found changed, through
the path the tests use, a bind mount or any other copy of the tree included: a
mutation that silently failed to apply prints the same green. Commit after the
red run was read, never before: a commit message that claims a result not yet
established is the one false statement in this phase that nobody will catch.

Where the current behaviour is genuinely wrong, pin it anyway and open a
separate change for the fix. Fixing it inside the pinning phase destroys the
baseline you came for.

A split answer, two places answering one question with a capability one of
them lacks, is pinned twice: each answerer's current behaviour as usual, and
one further test that drives every answerer with the same input, marked
`xfail(strict=True)` with a reason naming a decision record,
`agent-ready scaffold decision <slug>`, whose `review-by` is the expiry and
whose `enforced-by` is the test id. While the answers differ it reports
xfail, never a pass, so the pin never records the split as passing; that
report is its red run, and it has no green run here. Once the answers agree
it passes, which strict mode fails, so the change that fixes the split
removes the marker and closes the record in the same commit, and the
decisions check fails if the expiry passes unmet. The fix is a change, never
part of this phase.

The project's existing tests are a corpus: harvest them first, because a
fixture the author of a change also wrote tests the shape the author assumed.
Where behaviour depends on input the project cannot commit, a device dump or a
customer's file, the pin records the limitation rather than simulating the
input, and the change that needs the input waits for real data.

Where a module's tests are a pull request's worth of work, pin one module per
pull request, over weeks. On a small package the whole phase may be one
session; the ceiling is what one review can read, not the calendar.

## Questions you must ask

1. Is this order right? I ranked by what is least protected relative to what it
   would cost, not by tier and not by size.
2. For each behaviour that looks like a bug: is it a bug, or is something
   downstream relying on it?
3. Is any of this scheduled to be deleted? Do not pin what is leaving. A zone
   whose intent is `restructuring` is not leaving: its behaviour stays, and is
   pinned.

## Approval

The human approves each pull request. A pinned zone gets `pinned = YYYY-MM-DD`
in its `[tool.template.zones]` entry, so phase 4 and the handover can read what
is covered without opening the tests. Stop here: the next phase is a new session, and `agent-ready status` resumes it.
