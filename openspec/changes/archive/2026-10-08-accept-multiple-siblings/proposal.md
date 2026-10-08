## Why

Set validation falsely rejects compact Junos commands that assign multiple
sibling settings on one line, although device evidence confirms the compact
and expanded forms are equivalent. Repeating every grammar alternative made
parsing impractical and also accepted unknown tokens.

## What Changes

- Generate isolated, metadata-guided grammar for oneliner named lists and flat
  positional containers, repeating keyworded siblings without repeating bare
  value alternatives.
- Keep expanded one-setting-per-line forms valid and reject unknown tokens.
- Cover compact and expanded NTP server and maximum-prefixes commands in both
  generated and shipped validators, and remeasure parse performance.
- Remove the resolved sibling cases from the recorded over-rejections and
  update affected validation documentation and counts.

## Capabilities

### New Capabilities

- `validation/set-command-validation`: Valid Junos set commands, including
  equivalent compact and expanded sibling forms, validate without widening
  unknown-token acceptance or imposing impractical parse cost.

### Modified Capabilities

None; this is the first specification for set-command validation.

## Non-goals

- Bracketed `[ a b ]` value-list tokenization.
- General repetition for every generated grammar rule.
- Conversion semantics, which already accept these compact forms.

## Impact

Grammar generation, the shipped grammar artifact, validation tests and corpus,
documentation counts, changelog, and minor version. No new dependencies or
configuration overrides.
