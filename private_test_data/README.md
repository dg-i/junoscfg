# Private Test Data

Place private/real-world router configurations here for integration testing.
All files in this directory (except this README) are gitignored.

## Device XSD dumps

Dumps live in `schemas/`. They drive two things: `pytest --regen-schema`,
which rebuilds the bundled artifacts, and the schema-backed test tier, which
runs only when a dump is present.

Capture one with:

```bash
echo "<rpc> <get-xnm-information> <type>xml-schema</type> <namespace>junos-configuration</namespace> </get-xnm-information> </rpc>" \
  | ssh -Csp 830 router.example.com netconf > private_test_data/schemas/new.xsd
```

Stage it as `schemas/new.xsd`; `tests/schema_data.promote_staged()` reads the
Junos version out of it and renames it to `<version>.xsd`, appending `-2` and
so on if that name is taken. Syncing several devices is the point — each one
emits only the features it has, so one dump is never the whole schema.

`JUNOSCFG_XSD_SOURCE` overrides the location for `--regen-schema`. A legacy
`*.xsd` directly in this directory is still found.

## Running the schema-backed tests

```bash
uv run pytest tests/ --schema          # all of them, against every synced dump
uv run pytest tests/test_schema_data.py --schema -k 23.2R2
```

Without `--schema` those tests are skipped and the rest of the suite runs in
full against the committed artifacts. Parsing a dump takes minutes, and the
fixtures are parametrised over every file in `schemas/`, so narrow with `-k`.

## Juniper's jvd corpus

`pytest --jvd` runs the tests marked `jvd` against Juniper's published
Validated Designs. It clones `github.com/Juniper/jvd` into `jvd/` here on first
use, shallowly. Set `JUNOSCFG_JVD_PATH` to reuse a clone you already have:

```bash
JUNOSCFG_JVD_PATH=~/src/jvd uv run pytest tests/ -q --jvd
```

The corpus is not vendored: it is someone else's repository, about five million
lines, and a stale copy would be worse than none.
