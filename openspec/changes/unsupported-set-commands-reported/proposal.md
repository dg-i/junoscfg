## Why
Raw set conversion silently discards commands it cannot interpret, producing a different configuration without an error. OPEN-7 reproduction is confirmed on base 8066ce3a3f41af0b379d9d5a8e5b964eb1f3bd33.

## What Changes
- Refuse visible raw set lines outside the existing set/deactivate/protect/delete/activate dispatch, including bare commands, before IR construction.
- Reuse the shared lexical input boundary and physical-line/comment view for conversion and validation; command-refusal messages contain line numbers without source values.
- **BREAKING**: consumer and CLI conversion formerly returned partial output; they now raise InputError/ValueError or exit 2. Validation remains invalid and reports the same lexical reason per line.
- Document annotate, insert and replace-pattern as unsupported; feature support (#24) is deferred by the owner.

## Capabilities

### New Capabilities
None, because this tightens the existing raw-set-input capabilities.

### Modified Capabilities
- `conversion/raw-set-input`: unsupported command refusal independent of field validation and strictness.
- `validation/raw-set-input`: shared unsupported command diagnostics without changing supported path grammar.

## Non-goals
- Implement editing commands, comment round trips, grammar expansion or device feature semantics.
- Change bracket rejection, supported metadata commands, schema data, root package or CLI implementation.
- Remove existing APIs or add an override, fallback, option, environment read or dependency.

## Impact
Owned input kernel and raw set reader, validation adapter if needed, distinct acceptance test, existing set/annotations references and changelog. Preserve set/deactivate/protect/delete/activate, quoted values, blank/comment input and bracket precedence. Migrate scripts by supplying canonical display set input or removing unsupported interactive commands explicitly; no silent ignore option. Approved under owner unattended-run instruction of 2026-10-11 and rejection-only continuation.
