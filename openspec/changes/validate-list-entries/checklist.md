- minimise the exported surface from observed usage: nothing exported changes.
  `junoscfg.display.__all__` and `tach.toml` are untouched; the change is
  inside `_container_schema` and two artifacts.
- the deprecation policy, stated: engaged on `api` and `cli`, declared in
  `.openspec.yaml` with migrations. `validate_json`, `validate_yaml` and `-v`
  report invalid where they reported valid for three shapes the schema always
  claimed to reject; the field validator and the set grammar rejected the same
  content all along. Minor bump to 0.11.0.
- measured before loosening and before tightening: six probes must reject and
  seven shapes must validate, all pinned; `required` dropped on the evidence of
  the three fragments the first attempt broke, not by assumption.
- the first attempt's lesson applied: artifacts regenerated and hash-checked
  after every generator change, and every count re-taken after the design
  settled, before anything is recorded.
