Add the format `yaml-new`: the Junos JSON object written and read as YAML, equivalent to
`json` (`Format.YAML_NEW`, `-i`/`-e yaml-new`, `audit -i yaml-new`,
`validate_config(format="yaml-new")`). `yaml` is unchanged. Convert an existing YAML file
with `junoscfg convert -i yaml -e yaml-new`; a later release will rename `yaml-new` to
`yaml` and `yaml` to `yaml-old`, with deprecation first.
