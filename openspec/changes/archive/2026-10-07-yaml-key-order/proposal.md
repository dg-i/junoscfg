## Why

Every `edityaml` command alphabetised its output. `cli.py` called `yaml.dump`
without `sort_keys=False`, which PyYAML defaults to true — while the code
immediately above one of those calls reads:

```python
# Preserve key order by rebuilding dict
```

So the intent was explicit and the implementation defeated it two lines later.

Every YAML writer in `display/` and `convert/output/` passes
`sort_keys=False`. The `edityaml` and `cli` paths were the only ones that did
not, which is why `junoscfg -e yaml` and `junoscfg edityaml rename-root`
disagreed about the order of the same configuration.

`dg-i/ansible-collection-junos-config` pipes one into the other, so its
generated `group_vars` came out alphabetised relative to the configuration they
were read from — `firewall` first, `system` buried.

## What Changes

- Pass `sort_keys=False` at the five sites that lacked it: `addvars` and
  `rename-root` in `cli.py`, and the three `format_output*` helpers in
  `edityaml/ansibilize.py`.
- Rewrite the characterization test that pinned the sorting. It recorded the
  defect faithfully; the fix is expected to rewrite it rather than delete it.

## Capabilities

### New Capabilities

None; this makes one output path agree with every other.

### Modified Capabilities

No requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Changing the order junoscfg derives from a configuration. This only stops
  the YAML writer from re-sorting what it was given.

## Impact

`src/junoscfg/cli.py`, `src/junoscfg/edityaml/ansibilize.py`, and the
characterization test. Output of `edityaml addvars`, `rename-root`,
`ansibilize` and `ansibilize -P` changes: keys appear in configuration order
instead of alphabetically. Anyone diffing generated `group_vars` across this
version sees a reordering once.
