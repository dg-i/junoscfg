---
status: accepted
scope: ["openspec/changes/archive/**/review.md"]
enforced-by: none
review-by: 2027-04-06
---

# Device figures recorded before the 25.2R2 artifacts are superseded

## Context

Eleven changes reviewed between 2026-10-07 and 2026-10-08 quote rejection
counts for three real device configurations, taken against the bundled
24.4R0 artifacts. The assessment of 2026-10-08 found those artifacts
defective: `firewall family inet6 filter term from hop-limit` and
`forwarding-options analyzer` fail only against them across seven releases,
and the dump they came from no longer exists. 20 of the 21 rejections quoted
as junoscfg's residue were the artifacts' fault.

## Decision

The eleven reviews are archived as written. Their real-device figures are
superseded by the ones in `ship-25-2r2-artifacts` (v0.8.0): 1 rejected set
line of 7,002 across the three devices, `chassis dump-on-panic`, which no
release's XSD models. Each review carries a one-line pointer here rather than
a re-measurement against a schema that was being replaced.

## Consequences

A reader of an archived review knows which of its numbers to trust. Nothing
is re-measured eleven times, and nothing is rewritten in a record the owner
already accepted. The device-truth tier added in v0.9.1 is where a future
figure of this kind is taken from, with no schema in the judging.
