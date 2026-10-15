`--path --relative` output in `json` and `yaml-new` now spells presence flags and list-entry
key order as absolute output does: a `{}` or `true` flag in a selected list, and a selected
`{}`, is written `[null]` (it was written `{}` or `true`), and `name` leads each selected list
entry. The configuration is the same; only the text changes. Annotations such as
`"@": {"inactive": true}` are unchanged.
