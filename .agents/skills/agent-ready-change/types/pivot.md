# Type pivot

A pivot retires a concept on main. The proposal justifies it: the comparison
needed real use, or the loser already shipped. It completes in one change and
is never deferred, because residue reproduces itself.

## retires.md

`openspec instructions retires --change <slug>` prints the template. List what
retires: the concept's terms in the delimited block, its symbols, its
dependencies, the requirements it satisfied, its tests and fixtures, its docs.
`agent-ready retired` prints each term's occurrence count at the merge base
beside it, so a term too common to ban is visible to the human approving the
proposal. A term whose shape needs a regex goes under `Patterns:` in the
Decision section of the pivot's decision record, which cites this file by
path. A part of a definition the diff removes that still occurs in the tree
and is not a term is exempted with a reason, `- <identifier>: <reason>` after
the terms block. You draft the list; the human approves it with the proposal.

## What the change does

- The delta carries the REMOVED section for every requirement the concept
  satisfied, and ADDED for what replaces it.
- Every test on the list is deleted, never rewritten to assert the absence of
  the retired surface. No fixture stays that no test reads.
- The retired import is banned from then on: list it under `bans` in the
  decision record's front-matter and run `agent-ready render levers`, which
  renders the entry into the banned-api table with a message naming the
  record. A later pivot over the same import adds its own record; a pivot
  that reinstates the concept supersedes the record, which lifts the ban.
- The toolbox gains a rejected entry with the date where a tool retires, and
  the decision record states the observed reason the loser lost, never
  "switched to".
- A README that names the concept is updated in the same change.

## The gate

The retired terms occur nowhere in tracked text outside the homes where
history is allowed: decision records, the toolbox rejected list, the
changelog, the banned-api entries, and the change folder. vulture, the
unused-argument rules, deptry, and jscpd are clean. The gate derives the
removed symbols from griffe at the merge base and fails when the change
removes a symbol the list does not name or names one still there; run it as
`agent-ready retired` before the pull request, and read its hits as the list
of what the pivot has not yet finished.

## Stage

In alpha the rename to the settled name happens inside the pivot. In beta and
release a pivot runs through the deprecation path: the decorator first, a
decision record whose `review-by` is the removal release, the removal after.

## Approval

The human approves the retires list with the proposal.
