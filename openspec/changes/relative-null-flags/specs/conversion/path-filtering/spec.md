## ADDED Requirements

### Requirement: A relative selection spells presence flags and entry key order as absolute output does

WHEN a configuration path is selected with `relative=True` (CLI `--path --relative`) and
written as `json` or `yaml-new` THEN the system SHALL write the selection's presence flags
and list-entry key order as the absolute output writes them at the corresponding place: a
`{}` or `true` flag anywhere in the selection, and a selected `{}` or `true`, is `[null]`; a
flag inside a list (`[true]`) follows absolute output (`[[null]]`), whose device spelling
stays open (NEW-R2); `name` leads every selected list entry; an `@` annotation's values are
left as written. The selection is the value under its last path key: `junoscfg.convert.
from_dict(value, "json", wrap=False)` spells a bare `{}` as `[null]`. Relative output stays
unchanged by this requirement in what it does not name: the set reader's `groups` wrapper
(`{"group": [...]}` relative, a list absolute) and schema-context scalar-leaf coercion
(`"class": ["super-user"]` stays a list relative). The writer leaves the selection it is
given unchanged.
Tests: `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_is_spelled_as_absolute_output_spells_it`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_annotation_in_a_selected_list_stays_boolean`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_the_scenarios_are_written_as_specified`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_selected_group_list_from_set_input`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_anonymized_selection_is_spelled_alike`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_bare_selection_is_left_unchanged`

#### Scenario: A selected list holding an empty-container flag

- **WHEN** `system.syslog.host` holds `{"explicit-priority": {}, "name": "198.51.100.9"}` and is written as relative JSON
- **THEN** that entry is written `{"name": "198.51.100.9", "explicit-priority": [null]}`, as the absolute output holds it

#### Scenario: A selected empty container

- **WHEN** `system.services.netconf.ssh` holds `{}` and is written as relative JSON or yaml-new
- **THEN** the output is `[null]`, as the absolute output holds `"ssh": [null]`

#### Scenario: A deactivated entry in a selected list

- **WHEN** a selected `system.syslog.host` entry holds `"@": {"inactive": true}`
- **THEN** the annotation stays `{"inactive": true}`, so the entry stays deactivated
