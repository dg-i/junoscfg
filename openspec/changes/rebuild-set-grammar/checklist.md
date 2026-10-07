- minimise the exported surface from observed usage: `read_structure_tree` is
  added to `artifact_builder`, beside the `write_structure_tree` it inverts. It
  is not in any `__all__` or expose list; `_deserialize_node` and
  `_BOOL_FLAG_KEYS` are private.
- the deprecation policy, stated: not engaged. No public name or signature
  changes. `junoscfg -v` on set and structured input changes from raising
  `SchemaLoadError` to validating, which no caller could have depended on.
