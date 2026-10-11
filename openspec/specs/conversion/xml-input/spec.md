# conversion/xml-input Specification

## Purpose
XML input is read by one walker, `junoscfg.display.xml_to_dict`, which every
door that takes XML shares. An element's text is the value the device wrote,
so XML reads to the configuration the device's other renderings hold.

## Requirements

### Requirement: An XML leaf's text is its value as written

WHEN an XML element without child elements carries text that is not only
whitespace THEN `junoscfg.display.xml_to_dict` SHALL read that text unchanged as
the leaf's value, leading and trailing spaces included, for a single leaf, each
value of a leaf list, and an entry's key; WHEN the text is only whitespace THEN
it SHALL be the value only on a leaf the structure tree says takes a value, and
elsewhere (a presence flag, a container, an element outside the tree) the
element SHALL read as it does without text. Every door that reads XML
(`xml_to_dict`, `xml_to_yaml`, `convert_config` and `convert_config_result`
with `Format.XML`, `junoscfg convert`) SHALL give the same values, and set
output SHALL write the device's own line.
Tests: `tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText::test_spaces_around_a_value_are_kept`, `tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText::test_whitespace_alone_is_a_value_only_where_the_tree_takes_one`, `tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText::test_every_door_writes_the_devices_line`

#### Scenario: A value with a trailing space

- **WHEN** `<allow-commands>^show </allow-commands>` under `system login class OPS` is read
  (the device's rendering, `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.xml.gz`,
  vMX 23.2R2-S7.5)
- **THEN** the IR holds `"^show "`, JSON and YAML output hold `"^show "`, and set output is
  `set system login class OPS allow-commands "^show "`, the line the device displays

#### Scenario: Spaces in a leaf list and an entry key

- **WHEN** `<members> 64496:1</members><members>64496:2 </members>` or `<name> OPS </name>` is read
- **THEN** each value keeps its spaces

#### Scenario: A flag or container written across lines

- **WHEN** `<passive>\n</passive>` (a presence flag) or an empty container is pretty-printed
  across lines
- **THEN** the flag reads as `[null]` and the container as it reads without the line break

#### Scenario: Whitespace alone on a value leaf

- **WHEN** `<description> </description>` is read
- **THEN** the description is `" "`
