## Why

`junoscfg convert -e json` wrote output that `junoscfg convert -v -i json`
rejected: eight errors on `examples/router1.set`, and 51, 17 and 38 on three
real device configurations. Four causes -- the entry key a named list writes,
the `[null]` a presence flag writes, the bare container statement, and
`apply-groups`, which is in all three devices and in no NETCONF XSD. Counts
and shapes are in `tasks.md`.

Found by fresh-agent review of eleven open changes, none of which caused it.
No test converted a configuration then validated the result, so all eleven
passed the suite and all four gates.

## What Changes

- `schema_generator` models what the converters actually write, and takes the
  universal statements from the kernel rather than a flag the shipped tree
  lacks. List alternatives become `anyOf`; `oneOf` demands exactly one branch
  and a container now matches the array one too.
- `tests/test_round_trip_validates.py` is the missing test: every shape, both
  formats, seen to fail under four separate mutations.
- `grammar_generator` gives either-order nodes their own rule. The shape was
  decided per node and written per merged rule, so 6 qualifying nodes handed
  it to 1,050 that did not: `set interfaces mtu 9192 ge-0/0/0` validated.
- `_value_token` and `field_validator` read one kernel type table.
  `field_validator`'s copy held bare XSD names where the tree stores prefixed
  ones, so **integer validation never fired**; its nokeyword enum escape now
  asks whether the enum is a fragment, keeping the 4,342 that are and
  enforcing the 26 closed Junos enums that are not.
- A chosen artifacts directory holding none reports an error rather than the
  `None` conversion dereferenced into a traceback; malformed YAML likewise.
- `private_test_data/` leaves the sdist: 98 MB and 2,627 files, real device
  XSD dumps among them, down to 2.3 MB.

## Capabilities

### Modified Capabilities

None; `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- **Closing the quotable-value widening.** Measured, not claimed: scoping by
  type tightened 1,225 slots and moved the mutation measure 70.4% to 70.3%,
  because 124,227 of 179,773 leaves carry no type at all.
- Regenerating from an XSD; everything here rebuilds from the shipped tree.
