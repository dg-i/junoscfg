# Review

Fresh agent session, read-only, against `v0.6.32`.

## Confirmed exact

1,535 files, 4,945,686 lines, 1,500 converted, 35 failures, 217 warnings — to
the digit. 53,326 before reproduces as 53,347 with both escapes reverted
(0.04% apart; the gap is later commits). 4,448 enum-bearing nokeyword leaves,
exact.

## Findings

1. **The escape silenced 26 genuinely closed Junos enums.** Of the 4,368 that
   reach it, 4,342 are fragments exactly as the proposal argues — 4,238
   `enable-disable`, 104 `*-name` carrying `['default']` — and 26 are not:
   `autorp-mode`, `dense-group-flags`, `transport`. `convert --strict` passed
   `set protocols pim rp auto-rp frobnicate`, which a device rejects. The
   fragment signature is mechanical, so they could have been kept.
   **Fixed in v0.7.0**: `enum_is_fragment` in the kernel keeps the 4,342 and
   enforces the 26.
2. **Neither escape had a biting test.** Mutating either fails **zero** tests
   in the committed suite — which the change's own `retires.md` admits. They
   were caught only by `tests/test_jvd_corpus.py`, and that tier was **red at
   HEAD**: the oneliner guard built `data/junos-set.lark` by hand and the
   artifacts had shipped gzipped. **Fixed in v0.7.0.**
3. **The jvd warning budget is loose.** `MAX_FIELD_WARNINGS_PER_1K_LINES = 0.5`
   permits 2,472 warnings at this corpus size against 217 observed — 11x
   slack. It catches the defect this change fixed (53,326 = 21x over) and
   would *not* have caught the `ipaddr-or-interface` one (215 warnings, well
   inside). Recorded; tightening it is separate work.
4. `tasks.md` 3.3 — "the three real device configurations convert with zero
   field warnings, from many" — does not reproduce: with both escapes
   reverted the three raise **one** warning in total. The jvd evidence carries
   this change; that line overstates.

## Resolution

The headline is true and the trade is justified for 4,342 of the 4,448 — but
not for all of them, and finding 1 is the kind of over-loosening that was the
point of reviewing this batch. Fixed, along with the broken tier that was the
only thing testing it at all. 3 and 4 recorded and left.

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
