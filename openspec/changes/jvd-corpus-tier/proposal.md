## Why

Three defects reached a release this session that every committed fixture
missed, and all three were found by pointing junoscfg at Juniper's published
Validated Designs: a `nokeyword` leaf's enum being enforced (53,326 field
warnings), `ipaddr-or-interface` validated as IP-only, and a oneliner list's
keyword order. `examples/router1.set` is 61 lines that I wrote; the harvested
`tests/data/set_corpus.txt` is 116 commands from this repository's own tests.
Neither can say much about Junos.

`github.com/Juniper/jvd` is about 1,500 configurations and five million lines
across QFX, ACX, MX, PTX and SRX — the only breadth of that kind this project
can reach.

## What Changes

- `tests/jvd_data.py` finds a clone, or makes a shallow one under gitignored
  `private_test_data/jvd/`. `JUNOSCFG_JVD_PATH` reuses an existing checkout.
- A `--jvd` flag, a `jvd` marker and a session fixture in `tests/conftest.py`,
  mirroring the `--schema` tier that already exists. Skipped by default.
- `tests/test_jvd_corpus.py`: one session-scoped pass converting every file,
  with a conversion-rate floor, an assertion that every failure is a file that
  is not configuration, and a field-warning budget per thousand lines. Plus one
  guard per defect the corpus found, each taking its example from the corpus.
- The tier table in `docs/architecture/developer-guide.md`, which listed three
  tiers and omitted `--schema`, now lists five.

## Capabilities

### New Capabilities

None; this is test infrastructure.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Vendoring the corpus. It is someone else's repository under its own licence,
  it is large, and a stale copy would be worse than none.
- Running it in CI. It needs the network and three and a half minutes, and the
  decision belongs to whoever owns the CI budget.
- Pinning a revision. The corpus is upstream and moves; the assertions are
  thresholds so that someone else's commit cannot fail this build.

## Impact

`tests/` only; no runtime code changes. The default suite is unchanged at 1,437
tests. `--jvd` adds seven tests and about three and a half minutes, measured at
1,535 files and 4,945,686 lines. Each of the three regression guards was seen
to fail with its fix reverted.
