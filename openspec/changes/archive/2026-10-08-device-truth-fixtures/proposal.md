## Why

Every test of conversion judges junoscfg against the schema it ships, so a
defect in the artifacts is invisible to all of them: the 24.4R0 set lacked
`hop-limit`, every such line converted to a fused key, and 1,518 tests were
green. A capture of a subtree beside the device's own `| display json` of it
is the one oracle that needs no schema, and it is what settled the question.
Nothing in the suite used it. Step 3 of the owner's plan of 2026-10-08.

## What Changes

- `tests/test_device_truth.py`: for every pair `<name>.conf` beside
  `<name>.json`, re-root the fragment along the path its first line names,
  convert structured to JSON, and compare the set of JSON paths with the
  device's, a list entry told by its name, `@` attributes aside; zero missing
  and zero extra, and a failure names element paths only.
- Pairs are looked for under `tests/data/captures/`, holding one synthetic
  pair so the helpers run on every clone, and the gitignored
  `private_test_data/captures/`, holding two from one group: `policy-options`
  and `firewall family inet6`. A pair the owner is content to publish moves
  to the first directory unchanged.
- The tier runs wherever it finds a pair and is skipped elsewhere; no flag,
  since a pair converts in milliseconds.
- `private_test_data/README.md` says how to capture one;
  `docs/architecture/developer-guide.md` lists the tier.

## Capabilities

### New Capabilities

None; a test tier, with no runtime behaviour.

### Modified Capabilities

None at spec level; `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Publishing the two pairs. They are one operator's configuration, and the
  plan is explicit that the owner says so first; the test is written so that
  the move is a rename.
- Comparing values. Paths settle whether junoscfg and the device agree on
  shape; values are the field validator's, and a device renders numbers as
  strings as junoscfg does.
- The third capture, `event-options policy`, whose device JSON does not parse.

## Impact

Two pairs, 57 and 32 device paths, both 0 missing and 0 extra on the 25.2R2
artifacts. Pointed at the previous 24.4R0 set with `JUNOSCFG_ARTIFACTS`, the
`firewall family inet6` pair fails on `hop-limit`, 1 missing and 3 extra,
which is the defect the assessment found. Patch bump to 0.9.1.
