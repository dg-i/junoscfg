Remove the secondary `junoscfg.display.to_yaml.json_to_yaml()` helper and
`junoscfg.convert.output.xml_output` module. Direct importers should use
`convert_config(..., from_format=Format.JSON, to_format=Format.YAML)` and
`junoscfg.convert.from_dict()` respectively. The production consumer and
supported conversion behavior are unchanged.
