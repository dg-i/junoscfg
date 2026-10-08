# Phase 3 — Design

## Outcome

`design.md` for a `feature` or `new-dependency` change: the decisions, the
reuse ladder walked to its verdict, and the risks. Other types skip this
phase; lines added never trigger it, because they are unknowable here.

## The reuse ladder

Walk it in order and stop at the first rung that holds:

1. a helper this repository already has, found through the slice or the
   search the intent phase states; where the layering forbids the import and
   no later rung answers, move the helper to the first answerer's layer or
   one below and import it back, with `tach.toml`, the expose list and both
   contracts updated and the move's cost in the design, never the bottom by
   default and never a local copy;
2. the standard library;
3. an established library that passes the dependency policy;
4. build it;
5. only when the functionality is an entire external tool, a command-line
   tool through a thin adapter, with a presence check and a toolbox entry.

At most three candidates, one line each: name, coverage, gap, maintenance
signal with its lookup date, verdict. Search with your own web access where the
session has it; say so where it does not. A system tool needs a maintained
wrapper with a bundled binary, else a wrapper or a subprocess adapter plus a
presence check.

## Decisions

Alpha hard-codes the one choice and names it in a decision record:
`agent-ready scaffold decision <slug>` writes the record with its fields as
sentinels, `agent-ready decisions` fails until they are answered, and
`agent-ready render decisions` refreshes the index. A new dependency in alpha
is a trial entry in `[tool.template.toolbox.trial]` with a `review-by` date,
confirmed into the approved list or removed at the beta transition; in beta
and release it is this type with this design, and the approved entry carries
purpose, minimum version, and licence.

## Stage

Alpha: one choice, no option, no abstraction with one implementation. The
symbol index reports a base class with one subclass and an enum with one
member; both are findings here. One Python version and one platform. The gap
a candidate leaves goes into the delta as REMOVED, so spec, tests, and code
lose it in one change. Beta accepts a candidate only when the gap shows through
no named surface. Release closes the gap or rejects the candidate.

## Questions you must ask

1. Does the candidate's gap touch a named surface?
2. Is this dependency load-bearing, or here for one call?

## Approval

The human approves the design and the toolbox entry.
