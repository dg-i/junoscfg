# Review

Fresh agent session, read-only, against `v0.6.32`.

## Confirmed exact

Reader and writer do drive off the same two tables — best evidence is that the
*next* change added the `u` flag in one table line and it round-tripped.
`accepts-bracket` provably never shipped (74 `members` nodes, no flag keys on
any). `_fix_policy_algebra` provably matched nothing: 0 element names against
186/196/201/253 type references across four dumps. The bundled 427,978-node
tree round-trips byte-for-byte. All three new assertions bite.

## Findings

1. **The defect class is left live and undeclared.** Two halves, neither a
   stated non-goal:
   - Nothing ties a fix's flags to the writer tables. The new round-trip tests
     are driven off `_BOOL_FLAG_KEYS`/`_VALUE_FLAG_KEYS`, so they cover only
     flags already in the tables — and `accepts-bracket` failed precisely by
     being outside them. A new fix can still invent an unwritable flag.
   - **18 of 41 fixes report applied having changed nothing**, including
     `members-bracket`, the fix this change edited. The record indicts
     `_fix_policy_algebra` for exactly that, so the metadata's
     `fixes_applied: 38` is not a deadness signal for any of them.
   Accepted as-is: both are real, neither is caused by this change, and
   closing them is its own piece of work.
2. **It left a stale comment in shipped source.** Deleting
   `_fix_policy_algebra` falsified a comment `scope-policy-expression` had
   just added to `grammar_generator.py`. The record enumerates what it swept
   and misses this. **Fixed in v0.7.0.**
3. **`ALL_FIXES` is public and changed; no break declared.** `agent-ready
   stage griffe` fails on it. The checklist says "both private", true of the
   functions but not of the list they live in. Still open — see below.
4. `codemap.md` is stale against the symbol index.

## Resolution

The central claim — that the symmetry is real — holds and is well evidenced.
Finding 2 is fixed. Findings 1, 3 and 4 are recorded and left: 1 is separate
work, 3 and 4 are gate debt shared with `model-apply-statements`.

## Owner acceptance

The owner asked for the open changes to be archived (2026-10-08) and, shown
the findings in summary, chose to fix the blockers and the over-acceptance
before archiving. They did not review each finding individually. Everything
recorded as fixed was fixed in `v0.7.0` (`validate-own-output`); everything
recorded as accepted is accepted on that basis.

## Measurements superseded

Any real-device rejection figure above was taken against the bundled 24.4R0
artifacts, found defective on 2026-10-08 and replaced in v0.8.0. The numbers
that stand are in `ship-25-2r2-artifacts`; see
`docs/decisions/2026-10-08-superseded-device-measurements.md`.
