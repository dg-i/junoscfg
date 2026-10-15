## ADDED Requirements

### Requirement: A relative selection is spelled as absolute output spells it

WHEN a configuration path is selected with `relative=True` (CLI `--path --relative`) and
written as `json` or `yaml-new` THEN the system SHALL write the selection's presence flags
and list-entry key order as the absolute output for the same path writes them at that path:
a `{}` or `true` flag in a selected list, a selected `{}` and a selected `true` are each
`[null]`, and `name` leads every selected list entry. Schema-context scalar-leaf coercion of
a relative selection is not covered by this requirement.
Tests: `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_is_spelled_as_absolute_output_spells_it`

#### Scenario: A selected list holding an empty-container flag

- **WHEN** `system.syslog.host` holds `[{"any": {}, "name": "198.51.100.9"}]` and is written as relative JSON
- **THEN** the output is `[{"name": "198.51.100.9", "any": [null]}]`, as the absolute output holds at that path

#### Scenario: A selected empty container

- **WHEN** `system.services.netconf.ssh` holds `{}` and is written as relative JSON or yaml-new
- **THEN** the output is `[null]`, as the absolute output holds `"ssh": [null]`
