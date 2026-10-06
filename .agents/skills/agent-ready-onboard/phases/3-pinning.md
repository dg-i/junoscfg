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
public surface; under release, everything exposed.

Use the application's existing test and acceptance environment, including its container route and domain checks. Preserve separate fast and acceptance commands. For each module in that order, write tests that record what it does now,
including the behaviour that looks wrong. A characterization test is not an
assertion that the behaviour is correct; it is a record that it was this before
you touched it.

A test counts as pinning once it has been seen to fail: write it, break what it
guards, watch it go red, restore, watch it go green. Where the tests run in a
container over a bind mount, or against any other copy of the tree, a mutation
result counts only once the mutated file was read back through the same path
the tests use. Commit after the red run was read, never before: a commit
message that claims a result not yet established is the one false statement in
this phase that nobody will catch later.

Where the current behaviour is genuinely wrong, pin it anyway and open a
separate change for the fix. Fixing it inside the pinning phase destroys the
baseline you came for.

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
is covered without opening the tests.
