## Why

A statement the schema could not place went through the set reader's
nokeyword catch-all: the unknown token became that leaf's value, the rest of
the line was dropped, and the result validated. `set interfaces ge-0/0/0
nonsense alpha beta gamma` became `"enable-disable": "nonsense"` with no word
said. That hid the defective 24.4R0 artifacts for five months: every
`hop-limit` line took it. Owner's decision: the private plan of 2026-10-08.

## What Changes

- A `set` line is never cut. A nokeyword leaf takes one token only when the
  line ends there or a sibling follows; otherwise, and when a schema node has
  no type the reader knows, the statement is kept whole as one key, as the
  unknown-token path always did. Set output renders it back unchanged.
- Field validation reports a key the schema does not name, so it reaches
  stderr by default and fails `--strict` through the door the field validator
  already uses. The keys readers write by rule are exempt by that rule: a list
  entry's key, `_`-prefixed values, `@` attributes, universal statements and a
  folded switch's spelling. **BREAKING** on `api` and `cli`: errors where
  there were none.
- The jvd tier counts unmodelled statements on their own axis, beside the
  value-warning budget it already enforces.
- The mandatory check accepts a folded switch's spelling: `watchdog enable`
  satisfies `enable-disable`. The warning was false and unseen, because the
  pipeline prints warnings only beside an error, which an unplaced statement
  now is.
- Anonymization refuses a configuration with an unplaced statement. The
  anonymizer never rewrites a key the schema does not name, so the statement
  would leave verbatim, address and all, where the reader used to drop it.

## Capabilities

### New Capabilities

None; a defect in how the reader and the validator treat the unknown.

### Modified Capabilities

None at spec level; `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Modelling what the count surfaces: `bridge-domains`, 85% of it on jvd, is
  one wrapper missing from the transparent-container fix; its own change.
- Two pre-existing drops, recorded as known defects: the leaf path joins a
  trailing switch spelling into the value (`mtu 9000 disable`), and a meta
  command such as `deactivate system nonsense alpha` deactivates `system`.
- A fourth channel out of the library; the architecture calls the existing
  three a defect.

## Impact

Before, on 25.2R2: the catch-all fires on no line of three real devices nor
of jvd's 2,222,948 set lines, only on malformed input; the unknown-token path
on 7 device lines and 69,122 jvd lines in 407 shapes. After: 69,165 reported
on jvd, 1.4% of its lines, and 69 valid lines with two positional values now
kept whole; value warnings 233 to 521, the difference being mandatory-field
warnings the pipeline prints only beside an error, pre-existing and now
visible. The jvd tier passes both axes. Minor bump to 0.9.0.
