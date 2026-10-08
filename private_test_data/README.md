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
Junos version out of it and renames it to `<release>.xsd`, appending `-2` and
so on if that name is taken.

Then rename it by hand to record which box it came from, by convention
`<release>_<platform>.xsd` — `23.2R2-S7.5_vmx.xsd`. Anything ending `.xsd` is
picked up, so the suffix costs nothing.

**The platform cannot be read out of the dump**, which is why nothing tries. A
NETCONF XSD is release-wide: it describes everything a Junos release supports
across the product line, so every dump names every platform (ACX, EX, MX, PTX,
QFX, SRX, vMX) as enum values for hardware-specific configuration. Feature
depth says the same — `unified-edge` is 1,771 nodes in both a vMX's 23.2R2 dump
and the bundled 24.4R0, and `virtual-chassis` is 63 in all of them. What varies
is the release. `show version` is the only source, and it is not in the file.

Worth recording, because matching matters: validating a config against the dump
pulled from that same device left 1 rejected line of 3,369, against 12 for the
bundled 24.4R0.

`JUNOSCFG_XSD_SOURCE` overrides the location for `--regen-schema`. A legacy
`*.xsd` directly in this directory is still found.

## Device captures

`captures/` holds pairs of files, `<name>.conf` beside `<name>.json`: a subtree
as `show configuration <path>` prints it, headed by a line naming that path,
and the same subtree as the device rendered it through `| display json`. The
device is the oracle, with no schema in the judging; `tests/test_device_truth.py`
converts the fragment and compares the set of JSON paths. Pairs here run on
the machine that holds them and are skipped elsewhere; a pair the owner is
content to publish moves to `tests/data/captures/` unchanged.

Capture one with, on the device:

```text
show configuration groups <g> policy-options
show configuration groups <g> policy-options | display json
```

Save the first as `<name>.conf` with this exact first line, the path as the
device took it:

```text
## show configuration groups <g> policy-options
```

and the second as `<name>.json`. Strip any secret before saving. Only element
paths are compared, and only element paths are printed on a failure.

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
