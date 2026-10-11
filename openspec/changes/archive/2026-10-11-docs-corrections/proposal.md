## Why

The user guides teach Junos the device refuses. `docs/guide/validation.md` names
`set system location dc-a` as valid configuration the set grammar wrongly rejects, and
`docs/guide/annotations.md` uses `location dc-a` in its JSON, YAML, curly and set examples. The
device takes keyworded children under `system location` (`location building <name>`), the main
spec `validation/set-command-validation` records the bare value as invalid as on the device
(vMX 23.2R2-S7.5), and the test lists it as correctly rejected (NEW-C7).

## What Changes

- `docs/guide/validation.md`, the set-validation warning: the structural-only sentence says what
  the merge of same-named rules does (a line may pass with a child the bundled model has only at
  another position of that name, shown on `family inet6 labeled-unicast per-prefix-label`); the
  over-rejection sentence names the share of device lines and the corpus record instead of a count
  a live change moves; `set system location dc-a` appears as malformed input the test refuses,
  beside the device's spelling `set system location building "B 2"`.
- `docs/guide/annotations.md`: every `location dc-a` becomes `domain-name example.net`, a leaf both
  captured devices print as written; the console outputs are rerun at the checked head.

Reader: a user validating or converting Junos with junoscfg; task: trust the guide's examples to
load on a device and know what set validation can and cannot catch. Sources: `docs-plan.md`.

## Capabilities

### New Capabilities

### Modified Capabilities

None: documents only, `skip_specs: true`.

## Non-goals

- NEW-C8 (`docs/architecture/developer-guide.md`): live Builder #7 lists that file (preflight C2).
- NEW-C14 (`.pre-commit-config.yaml`): not a document; the docs lane refuses it (preflight C3).
- The test's `OVER_REJECTED` classification (NEW-R20, probe P14): a test edit, outside this lane.

## Impact

Two user-guide pages; no code, test, configuration or spec. Every console output is rerun with
`junoscfg convert` at the checked head; every validator claim with `validate_set`
(`private_test_data/makeover-work/docs-corrections/probe_validate.py`, not tracked).
