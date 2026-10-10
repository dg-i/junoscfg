# conversion/meta-tags Specification

## Purpose
A Junos meta tag (`inactive`, `protect`, …) marks exactly the statement the
device marks, whichever format the configuration arrives in, so one
configuration gives one IR and every writer renders the tag where the device
would accept it.

## Requirements

### Requirement: An inactive leaf from XML reaches the IR set and structured input give

WHEN XML input carries `inactive="inactive"` on a leaf element, with a value
or as a presence flag, THEN the system SHALL hold the leaf's value (`[null]`
for a presence flag) as it holds an active leaf's value and SHALL mark it with
the sibling `@<name>` key `{"inactive": true}`, the IR set, structured and
device JSON input give for the same statement.
An empty tagged element is an empty container, `{"@": {...}}`, only where the
tree names a container, as set and structured input give; set and structured
output keep a tag on a flag spelled by its value (`disable`).
Tests: `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/unit/display/test_to_yaml.py::TestInactiveLeaf::test_an_inactive_presence_flag_matches_set_input`, `tests/contract/test_format_matrix.py::TestAStructuredTagLeadsItsLine::test_no_tag_follows_a_word`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines[an-inactive-vlan-id-xml]`

#### Scenario: Single inactive leaf

- **WHEN** `<unit><name>751</name><vlan-id inactive="inactive">751</vlan-id></unit>`
  under `interfaces interface xe-0/0/0` is converted by `convert_config` from
  XML, and the same statement is converted from set
  (`set … unit 751 vlan-id 751`, `deactivate … unit 751 vlan-id`) and from
  structured (`inactive: vlan-id 751;`), and from JSON in the device's
  shape (`"vlan-id": "751", "@vlan-id": {"inactive": true}`; the device
  writes the number 751, which JSON input keeps as a number, a recorded
  follow-up)
- **THEN** all four give `"vlan-id": "751"` and `"@vlan-id": {"inactive": true}`
  on the unit, and set output is `set … unit 751 vlan-id 751` followed by
  `deactivate … unit 751 vlan-id`

#### Scenario: Inactive unit holding an inactive leaf

- **WHEN** `<unit inactive="inactive">` holds `<vlan-id inactive="inactive">751</vlan-id>`
- **THEN** XML, set and structured input give one IR: the unit entry carries
  `"@": {"inactive": true}` and the leaf its sibling `@vlan-id`

#### Scenario: Inactive presence flag

- **WHEN** `<no-redirects inactive="inactive"/>` under `system` is converted from XML
- **THEN** the IR is `"no-redirects": [null], "@no-redirects": {"inactive": true}`,
  as `set system no-redirects` with `deactivate system no-redirects` gives

#### Scenario: Tagged flag spelled by its value

- **WHEN** `<disable inactive="inactive"/>` under an interface is converted from
  XML, set (`deactivate interfaces xe-0/0/0 disable`) or JSON
- **THEN** all give `"disable": [null], "@disable": {"inactive": true}`, and set
  and structured output keep the tag (`deactivate … disable`, `inactive: disable;`
  on its own line, also under a container such as `protocols lldp`)

#### Scenario: Empty tagged container

- **WHEN** `<lldp inactive="inactive"/>` under `protocols` is converted from XML
- **THEN** the IR is `"lldp": {"@": {"inactive": true}}`, as `set protocols lldp`
  with `deactivate protocols lldp` gives

#### Scenario: CLI

- **WHEN** `junoscfg convert -i xml -e set` reads the single-inactive-leaf XML
- **THEN** it prints no `vlan-id vlan-id` line and exits 0

### Requirement: An inactive leaf-list is inactive as a whole

WHEN every value of a leaf-list carries `inactive="inactive"` in XML input THEN
the system SHALL hold the values as a list and mark the leaf-list once with the
sibling `@<name>` key. WHEN only some of its values carry it THEN the system
SHALL refuse the input with `ValueError` naming the element, because Junos has
no per-value tag (the CLI rejects `deactivate policy-options community C1
members 64496:2`) and widening the tag would deactivate active values.
Tests: `tests/unit/display/test_to_yaml.py::TestInactiveLeaf::test_an_inactive_leaf_list_takes_one_marker`, `tests/unit/display/test_to_yaml.py::TestInactiveLeaf::test_a_partly_inactive_leaf_list_is_refused`

#### Scenario: Every value inactive

- **WHEN** `<members inactive="inactive">64496:1</members><members inactive="inactive">64496:2</members>`
  appear under `policy-options community C1`
- **THEN** the IR holds `"members": ["64496:1", "64496:2"]` and
  `"@members": {"inactive": true}`

#### Scenario: Some values inactive

- **WHEN** only `<members inactive="inactive">64496:2</members>` of the two is tagged
- **THEN** XML conversion raises `ValueError` naming `members`, and no IR is built
