# Phase 5 — Contracts

## Outcome

A contract for every module in scope, each within its 30-line cap, with
`__all__`, the `tach.toml` module entry, and the `[[interfaces]] expose` list
carrying the interface facts. `tach check` and `agent-ready interfaces` pass.

## What a contract is

Almost all of it is machine-checked, so the prose holds only three kinds of
line:

- an invariant, naming the check or test id that enforces it;
- a precedent pointer to a symbol, as a dotted path the generated index can
  resolve;
- where the module name plus `__all__` is genuinely ambiguous, one line saying
  what the module is *not* for.

Interface facts are never restated in prose. If `__all__` already says it, the
contract does not.

## Where a contract lives

A module that is a directory carries `CONTRACT.md` inside it. A module that is
a single file carries `<module>.CONTRACT.md` beside it, so a flat package of
seven modules has seven contracts, each sorting next to its code.
`agent-ready scaffold contract <path>` writes the right one with its three
sections as sentinels, and the shipped caps match both spellings.

## Two enforcers, one declaration

`tach check` enforces the expose list against member-path imports only.
`agent-ready interfaces` enforces it against names reached through a module
reference, and fails when `__all__` and the expose list disagree, so the two are
written together and `__all__`, the one a person editing the module sees, is the
single source.

Satisfying both enforcers is a refactor, not a documentation pass:
cross-package consumers move to the package door, while implementation modules
inside that package may import sibling submodules without bypassing another
package's contract. `__all__` may not exist yet to match an expose list against.
Two shapes make import cycles: a sibling that imports its own package back, and
a package `__init__` that imports a submodule which reaches back to it. A
sibling never imports its own package; a heavy
re-export, one that would pull a large dependency at import time, is a
module-level `__getattr__` rather than an eager import.

## Greenfield

One contract per skeleton module, written as the module is written.

## Brownfield — scope and order

Not every module at once. Start with touched, boundary-heavy, or high-exposure modules; the rest get a
contract on first touch. A contract written for a module nobody edits is a
document nobody reads.

Derive the `expose` list from observed cross-module usage, not from `__all__`:
`agent-ready scaffold contract <path> --expose-from-usage` writes the contract,
derives the list from what other modules take from the module, prints the
reconciliation against `__all__` and the line to paste, and declares the
`tach.toml` stanza where the module has none. Across surveyed projects
`__all__` coverage ran from 0 of 70 modules to 262 of 289, so it cannot be
relied on either way; where it is near-total it is real intent, so raise the
difference rather than silently overriding it.

A module that imports a moved helper carries a precedent pointer to it, and
`agent-ready codemap check` fails once that pointer no longer resolves, so
the next agent that reads the contract before editing meets the home.

## Questions you must ask

1. For each name I propose exposing that `__all__` does not list: is this
   public, or is it a leak somebody should stop relying on?
2. For each name in `__all__` that nothing imports: keep it as a promise to
   outside callers, or drop it?
3. For each module: is there an invariant people keep breaking? That is the line
   worth writing, and it needs a test id.

## Approval

The human approves each contract. A contract whose invariant names no check is
not approved; write the check or delete the line. Before the approval, probe
the pair once: remove one exposed name and watch each gate go red, which is the
only thing that proves the two are wired to the code rather than to each other.
Stop here: the next phase is a new session, and `agent-ready status` resumes it.
