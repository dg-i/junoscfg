## Why

`tests/conftest.py` looked for the device XSD at `PROJECT_ROOT.parent / "xsd" /
"config-24.4.xsd"` — a directory *beside* the repository, which existed on one
machine and nowhere else. So in any clean clone `--regen-schema` found nothing.

Worse than the path: it then called `pytest.skip()` from a session-scoped
autouse fixture, which skips **every** test. Measured on a clone without the
XSD: `pytest --regen-schema` reported **1414 skipped, exit 0**.

`AGENTS.md` tells you to rerun with `--regen-schema` after XSD or schema
changes. That command reported success having tested nothing.

## What Changes

- Find the XSD by `JUNOSCFG_XSD_SOURCE`, else the newest `*.xsd` in
  `private_test_data/` — already gitignored and already documented as the home
  for real device data, which an XSD dump is.
- Warn instead of skipping. Without an XSD the suite runs in full against the
  committed artifacts and says it could not regenerate. With one, it
  regenerates exactly as before.
- Document the capture command in `private_test_data/README.md`.

## Capabilities

### New Capabilities

None; this makes an existing developer command work outside one machine.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Committing an XSD. It is operator data and tens of megabytes, and it is
  per-device and per-release.

## Impact

`tests/conftest.py` and `private_test_data/README.md`. No source, no public
name, no version bump: nothing a caller of the package can observe changes.
`pytest --regen-schema` goes from skipping 1414 tests to running them.
