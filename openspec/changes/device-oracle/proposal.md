## Why

The tests judged junoscfg against data it helped make: `router1.set` is its own
output, the set corpus was harvested from its own tests. Four devices (vMX,
EX4600, EX4100, QFX5120) printed nine configurations, five of them Juniper's
JVD, in curly, XML, JSON and set, and their renderings show 16 defect classes
no committed test found. Owner decisions, 2026-10-10; device facts from the
junoscfg-d9 session.

## What Changes

- `tests/data/device/`: the captures, gzipped, with a manifest, JVD's five
  unmodified sources and its Apache-2.0 licence and notice
  (`docs/decisions/2026-10-10-commit-device-captures-as-the-oracle.md`).
- `tests/corpus/test_device_renderings.py`: junoscfg's set rendering of every
  capture's every rendering equals the device's display set, less the lines
  `known-differences.json` records by class (defect, equivalent, open,
  device quirk); an unrecorded or vanished difference fails.
- The grammar corpus: 182 device lines covering every rule the 8,560 device
  lines use, plus every line the grammar rejects; all lines by hand
  (`--device-grammar`). `set_corpus.txt` retires; its negative cases stay.
- `router1` retires from the tests; `examples/` holds a device's renderings.
- Tools: `import_device_captures.py`, `device_differences.py`,
  `device_grammar_corpus.py`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None: test data and tests only.

## Non-goals

- Fixing the defects the devices show; each is a later change, and its fix
  shrinks the record.
- The jvd clone tier, which stays opt-in for breadth.

## Impact

Tests and test data; `examples/`; tools; docs. No product code.
