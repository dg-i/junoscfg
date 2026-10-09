## Why

The raw set reader accepts interactive bracket-list shorthand that canonical
Junos `| display set` never emits, then can build an incorrect IR from it.
Rejecting the unsupported spelling at the input boundary prevents silent
semantic corruption and records the intentional exception as decision
`2026-10-09-reject-raw-set-brackets`.

## What Changes

- **BREAKING** on `api` and `cli`: every raw set command rejects an unquoted
  `[` or `]` before IR construction, independent of validation and strictness.
- Validation reports the same complete, line-specific diagnostic as a normal
  per-line error; conversion raises `ValueError`. Quoted brackets and comments
  remain ordinary content.
- One shared quote-aware detector serves conversion and validation. The set
  corpus gains `INTENTIONALLY_UNSUPPORTED`, and the bare community-members
  command moves to the correctly rejected category.
- User documentation and an accepted decision explain the boundary; the beta
  API/CLI break raises the minor version in all three version locations.

## Capabilities

### New Capabilities
- `conversion/raw-set-input`: input-boundary handling and conversion guarantees
  for raw Junos set commands.
- `validation/raw-set-input`: line-oriented validation results for raw Junos
  set commands.

### Modified Capabilities
None; `openspec/specs/` has no existing capability to modify.

## Non-goals

- Removing shared bracket normalization or structured bracket-list support.
- Implementing schema-aware bracket-list expansion or resolving meta-command
  bracket semantics; the decision records that deferred design without a
  roadmap commitment.

## Impact

Set conversion, set validation, their public API and CLI doors, corpus tests,
validation documentation, decision records, and the package version change.
