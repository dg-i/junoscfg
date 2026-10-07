- minimise the exported surface from observed usage: unchanged. `_coerce_value`
  is private; no public name is added or removed.
- the deprecation policy, stated: not engaged. The `api` and `cli` surfaces keep
  their names and signatures. JSON and YAML derived from XML input change
  shape — numeric leaves become strings and `ieee-802.3ad` becomes `802.3ad` —
  which is a bug fix bringing one path into line with the other two, not a
  surface break. Set and structured output are untouched.
