## Why

Anonymization claims success while addresses, names and descriptions leave as
written. The walker never sees a universal statement below the root, the
siblings of a transparent child (`interface-range`), or a list held by a
container that is no list; the IP rule ignores `host`, `hostname`,
`ipprefix-only` and untyped leaves and crashes on `from interface ge-0/0/0.0`;
`apply-groups` is anonymized twice; and the public `anonymize()` passes every key
it cannot place, while the pipeline refuses them (ARCH-C05, NEW-R5, ANON-P1,
ANON-P2, NEW-C11, NEW-A-N1/N2/N3/N6, NEW-A-S2, NEW-R8).

## What Changes

- The walker resolves children through `junoscfg.display.schema_child`, walks a
  transparent container's other children against the container, and each entry
  of a list a container holds.
- The IP rule answers by type: an address, host, `areaid`, free-text or untyped
  leaf takes a value that parses as an address; `_IP_NAMED_LIST_PARENTS` goes.
- `GroupRule` claims `apply-groups` and `apply-groups-except` wherever they
  stand; `_replace_apply_groups` goes.
- **BREAKING** (`consumer`, `cli`), owner answer 5: content the walk cannot place
  (an unknown key, a value of a shape its node does not take, a statement kept
  whole) has its address-shaped words replaced and is named, by schema path, in
  `AnonymizeResult.unplaced` and a conversion warning. Neither door refuses it
  any more; an anonymized run withholds the text of `UNPLACED` messages.
- Field validation walks transparent siblings against their container and each
  entry of such a list (NEW-A-S2).
- `apply_revert` restores rewritten words in keys too.
- No override, fallback or parameter is added.

## Capabilities

### New Capabilities

- `anonymization/placed-values`: what the walker reaches, the IP rule's type answer, group references, content the walk cannot place, messages of an anonymized run.

### Modified Capabilities

- `anonymization/keyed-entries`: "No value anonymized before escapes" admits explained additions.
- `conversion/entry-keys`: the record is no longer refused by anonymization.
- `validation/keyed-entries`: an entry without its key field is not refused by anonymization.
- `schema-pipeline/universal-statements`: inside `apply-flags`, no address passes an anonymized run.

## Non-goals

- NEW-R1, NEW-R3, NEW-R4 (change 5b); the `<*>` wildcard (ANON-P3, change 6);
  addresses inside strings and revert by substring (ANON-P5, NEW-A-N4/N5/N7,
  change 7); escaped quotes (ANON-P4, change 8); keyed homogeneous containers
  (OPEN-21, change 11).

## Impact

`anonymize/` (walker, `__init__`, `rules/ip.py`, `rules/group.py`, `revert.py`),
`convert/__init__.py`, `convert/field_validator.py`, docs, version. Reproduce:
`private_test_data/makeover-work/repro_*.py`; measurement:
`private_test_data/makeover-work/anonymize-every-placed-value/`.
