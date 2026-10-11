## Why

A Junos wildcard name (`groups GR-BGP protocols bgp group <*>`, `interfaces <ge-*>`) is a pattern
that selects names, not a name. The group rule replaces `<*>` by `group_<hash>`, so the anonymized
group selects no BGP group and defines a new one; the identity and community rules do the same at
their names, and the IP rule leaves `<203.0.114.7>` as written beside the neighbour it renames
(ANON-P3 = NEW-C12, strict xfail `test_a_wildcard_group_name_passes_the_group_rule`).

## What Changes

- A wildcard name whose pattern is only `*` passes every rule unchanged: it selects every name.
- Any other wildcard name keeps its brackets; the text inside is offered to the rules as a name of
  that place, so `<EBGP>` becomes `<group_…>` of group `EBGP`, `<203.0.114.7>` the neighbour's
  replacement, `<EBGP-*>` with `--anonymize-sensitive-words ebgp` `<word_…-*>`.
- A wildcard name that, anonymized, selects other names among those the configuration holds at its
  place, or whose text a rule claims and leaves as written, is reported by schema path:
  `AnonymizeResult.patterns` (a new field with a default) and an `anonymize:` warning naming the
  path and a count, never a value. Interim rule pending the owner (challenge S1).
- Revert restores a wildcard name exactly: the text inside its brackets is reverted.
- No override, fallback, parameter or environment read is added.
- Removes the test filters that hid the defect (mapping entries whose original starts with `<`).

## Capabilities

### New Capabilities

- `anonymization/wildcard-names`: requirement "A wildcard name is a pattern, not a name" (split
  from `anonymization/placed-values` in phase 7: that spec would pass its 200-line cap).

### Modified Capabilities

- None.

## Non-goals

- `apply-path` strings that name a group or hold `<*>` (NEW-A-N7, change 7).
- Pseudonyms that keep a wildcard's literal text selecting the same names (owner question S1).

## Impact

`anonymize/{walker,revert,__init__}.py`, `convert/__init__.py` (the warning), contract, CLI guide,
changelog, patch 0.20.1. Reproduce: `private_test_data/makeover-work/group-wildcards-pass/repro.py`.
