## Purpose

A Junos meta tag (`inactive`, `protect`, …) marks exactly the statement the
device marks, whichever format the configuration arrives in, so one
configuration gives one IR and every writer renders the tag where the device
would accept it.

## ADDED Requirements

### Requirement: An inactive leaf from XML reaches the IR set and structured input give

WHEN XML input carries `inactive="inactive"` on a leaf element with a value
THEN the system SHALL hold the leaf's value as it holds an active leaf's value
and SHALL mark it with the sibling `@<name>` key `{"inactive": true}`, the IR
set and structured input give for the same statement.
Tests: `tests/test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr::test_an_inactive_leaf_reaches_one_ir`, `tests/test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr::test_an_inactive_unit_and_leaf_reach_one_ir`, `tests/test_cli.py::TestInactiveXmlLeaf::test_set_output_deactivates_the_leaf`

#### Scenario: Single inactive leaf

- **WHEN** `<unit><name>751</name><vlan-id inactive="inactive">751</vlan-id></unit>`
  under `interfaces interface xe-0/0/0` is converted by `convert_config` from
  XML, and the same statement is converted from set
  (`set … unit 751 vlan-id 751`, `deactivate … unit 751 vlan-id`) and from
  structured (`inactive: vlan-id 751;`)
- **THEN** all three give `"vlan-id": "751"` and `"@vlan-id": {"inactive": true}`
  on the unit, and set output is `set … unit 751 vlan-id 751` followed by
  `deactivate … unit 751 vlan-id`

#### Scenario: Inactive unit holding an inactive leaf

- **WHEN** `<unit inactive="inactive">` holds `<vlan-id inactive="inactive">751</vlan-id>`
- **THEN** XML, set and structured input give one IR: the unit entry carries
  `"@": {"inactive": true}` and the leaf its sibling `@vlan-id`

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
Tests: `tests/test_to_yaml.py::TestInactiveLeaf::test_an_inactive_leaf_list_takes_one_marker`, `tests/test_to_yaml.py::TestInactiveLeaf::test_a_partly_inactive_leaf_list_is_refused`

#### Scenario: Every value inactive

- **WHEN** `<members inactive="inactive">64496:1</members><members inactive="inactive">64496:2</members>`
  appear under `policy-options community C1`
- **THEN** the IR holds `"members": ["64496:1", "64496:2"]` and
  `"@members": {"inactive": true}`

#### Scenario: Some values inactive

- **WHEN** only `<members inactive="inactive">64496:2</members>` of the two is tagged
- **THEN** XML conversion raises `ValueError` naming `members`, and no IR is built
