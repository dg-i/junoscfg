## 1. Tests

- [x] 1.1 Rewrite `test_rename_root_renames_and_sorts_keys` as
  `test_rename_root_preserves_key_order`: the renamed root comes first and
  `system` precedes `firewall`, as in `examples/router1.conf`.

## 2. Implementation

- [x] 2.1 `sort_keys=False` at `cli.py` addvars and rename-root.
- [x] 2.2 `sort_keys=False` in `format_output` and in the `_kw` dict that
  `format_output_with_offset` shares across its three documents.
- [x] 2.3 Confirm no `yaml.dump` in the package still lacks it.
