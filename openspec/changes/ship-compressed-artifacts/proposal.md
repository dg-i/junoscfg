## Why

The bundled artifacts are 34.5 MB and the package 38 MB. They are JSON and a
Lark grammar, so they compress to **2.1 MB** — the two JSON schemas alone give
back 20 MB at a 5% ratio.

That matters beyond download size. The owner wants a user to be able to
generate a schema from their own device's XSD and point junoscfg at it, and a
35 MB set per release makes carrying more than one unattractive. Compression
is the lever that makes several releases cheap; it is not a packaging detail.

## What Changes

- Every artifact ships gzipped. `junos-structure-tree.json.gz` and the rest.
- Two kernel helpers beside the resolver landed in v0.6.31: `find_artifact`
  takes the compressed form if present and the plain one if not, and
  `read_artifact_text` decompresses by suffix. `open_artifact_write` is their
  pair for the three generators.
- Seven read sites and six write sites go through them, rather than each
  deciding. Seven call sites each making the same decision is how
  `resolve_artifacts_dir` came to be needed.
- A directory of plain artifacts still works. A developer who ran
  `schema generate` last week keeps their set, and `--artifacts` pointed at it
  behaves as before.

## Capabilities

### New Capabilities

None; the same artifacts, stored smaller.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Dropping any artifact. The two JSON schemas are 20 MB raw and 1.0 MB packed;
  at that size there is no reason to make JSON and YAML validation optional.
- A cache directory or a `--release` flag. `--artifacts` and
  `JUNOSCFG_ARTIFACTS` already select a set, and since v0.6.31 they do so for
  the whole tool.

## Impact

`src/junoscfg` goes 38 MB to **5.2 MB**, the artifacts 34.5 MB to 2.1 MB.
Loading the 13.8 MB structure tree costs 0.19s. Eight tests; two seen to fail
under mutation. The downstream Ansible collection's 33 tests pass with
byte-identical filter output.
