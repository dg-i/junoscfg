# junoscfg.convert

Unified conversion-pipeline package door.

`FORMAT_IMPLEMENTATIONS` maps each format name (`junoscfg.Format`'s values) to the
implementation that reads and writes it: `"yaml"` to `"ir-yaml"` (the IR as YAML),
`"yaml-new"` to `"junos-yaml"` (the Junos JSON object as YAML), `"json"` to
`"junos-json"`. `to_dict`, `from_dict` and `junoscfg.validate_config` dispatch
through it; the planned rename of `yaml` edits this table
([decision record](../decisions/2026-10-15-yaml-new-before-renaming-yaml.md)).

::: junoscfg.convert
