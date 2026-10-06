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
single source. Probe the pair once before trusting it: remove one exposed name
and watch each gate go red.

## Greenfield

One contract per skeleton module, written as the module is written.

## Brownfield — scope and order

Not every module at once. Start with touched, boundary-heavy, or high-exposure modules; the rest get a
contract on first touch. A contract written for a module nobody edits is a
document nobody reads.

Derive the `expose` list from observed cross-module usage, not from `__all__`.
Across surveyed projects `__all__` coverage ran from 0 of 70 modules to 262 of
289, so it cannot be relied on either way. Where it is near-total it is real
intent: reconcile your derived list against it and raise the difference rather
than silently overriding it.

## Questions you must ask

1. For each name I propose exposing that `__all__` does not list: is this
   public, or is it a leak somebody should stop relying on?
2. For each name in `__all__` that nothing imports: keep it as a promise to
   outside callers, or drop it?
3. For each module: is there an invariant people keep breaking? That is the line
   worth writing, and it needs a test id.

## Approval

The human approves each contract. A contract whose invariant names no check is
not approved; write the check or delete the line.
