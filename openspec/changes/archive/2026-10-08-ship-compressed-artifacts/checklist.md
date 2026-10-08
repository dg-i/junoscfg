- minimise the exported surface from observed usage: `junoscfg.display` gains
  `find_artifact`, `read_artifact_text` and `open_artifact_write`, all three
  reached across modules and so added to `__all__` and `tach.toml`'s expose
  list, which `agent-ready interfaces` holds in step.
- the deprecation policy, stated: not engaged. The artifacts a user generated
  before this still load, and `schema generate` now writes the compressed form
  — a caller that hardcodes `junos-set.lark` rather than resolving it will not
  find it, which is why every reader in the package was moved to the helper.
