## MODIFIED Requirements

### Requirement: A relative selection is written as absolute output writes it, without its path

WHEN a configuration path is selected with `relative=True` (CLI `--path --relative`) THEN
the system SHALL write what the absolute output writes at that path, without the path:
`json` and `yaml-new` the Junos JSON object's value at the path (`groups` holds its entries
there), with presence flags, key order, single-leaf coercion and annotation booleans as
written there, and `yaml` the IR's value; `set` and `structured` the absolute statements
without the words the path is written as (a list name the schema hides has none; a key no
statement names, an annotation key or `junoscfg:unplaced`, is passed over), so a selected
list writes its entries' statements and
a selected leaf its value. A selection whose statement is its path alone (a flag, `null`)
writes `set` in set output and nothing in structured output. A tag at or above the path
that the output cannot write follows `conversion/selection-tags`: it is dropped with a note,
never written as a bare verb (owner ruling 2026-10-17). The writer leaves the IR it is given
unchanged; `junoscfg.convert.from_dict(value, fmt, wrap=False)`, the secondary door for a bare
value, keeps its meaning (presence flags and key order as under its last path key). A flag
inside a list (`[true]`) follows absolute output (`[[null]]`), whose device spelling stays
open (NEW-R2).
Tests: `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_is_spelled_as_absolute_output_spells_it`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_annotation_in_a_selected_list_stays_boolean`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_the_scenarios_are_written_as_specified`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_selected_group_list_from_set_input`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_anonymized_selection_is_spelled_alike`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_keeps_its_schema_context`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_list_name_the_schema_hides_is_not_written`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_selected_groups_is_the_list_of_groups`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_entry_named_like_a_hidden_list_keeps_its_name`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_selected_list_writes_its_statements`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_annotation_selection_keeps_its_booleans`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_annotation_selection_in_set_and_structured`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_every_tag_below_a_selection_is_written_below_it`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_yaml_new_selection_is_measured_as_written`, `tests/unit/convert/test_convert_api.py::TestJunosYamlWriter::test_a_cycle_below_a_relative_path_is_refused_on_write`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_the_kept_statements_key_writes_its_statements`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_anonymized_list_selection_in_set`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_relative_leaf_preserves_output`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_relative_output_is_the_subtree_without_the_path`, `tests/corpus/test_device_renderings.py::TestRelativeSelections::test_a_relative_selection_is_the_absolute_one_without_its_path`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_bare_selection_is_left_unchanged`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_selection_below_its_path_is_left_unchanged`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_bare_value_keeps_its_meaning`

#### Scenario: A selected list holding an empty-container flag

- **WHEN** `system.syslog.host` holds `{"explicit-priority": {}, "name": "198.51.100.9"}` and is written as relative JSON
- **THEN** that entry is written `{"name": "198.51.100.9", "explicit-priority": [null]}`, as the absolute output holds it

#### Scenario: A selected empty container

- **WHEN** `system.services.netconf.ssh` holds `{}` and is written as relative JSON or yaml-new
- **THEN** the output is `[null]`, as the absolute output holds `"ssh": [null]`

#### Scenario: A deactivated entry in a selected list

- **WHEN** a selected `system.syslog.host` entry holds `"@": {"inactive": true}`
- **THEN** the annotation stays `{"inactive": true}`, so the entry stays deactivated

#### Scenario: A single leaf given as a list

- **WHEN** a `yaml` file gives `class: [super-user]` and `system.login` is written as relative JSON
- **THEN** the user's `class` is `"super-user"`, as the absolute output holds it

#### Scenario: A list whose name the schema hides

- **WHEN** `interfaces` holding `ge-0/0/0` is written as relative set
- **THEN** the lines read `set ge-0/0/0 ...`, never `set interface ge-0/0/0 ...`

#### Scenario: A selected list in set and structured output

- **WHEN** `system.login.user` holding user `admin` is written as relative set
- **THEN** the line is `set admin class super-user`, never a Python repr

#### Scenario: An annotation selection

- **WHEN** `system.@` holding `{"inactive": true}` is written as relative JSON
- **THEN** the output is `{"inactive": true}`, as the absolute output holds it

## REMOVED Requirements

### Requirement: An absolute selection keeps the tags of the selected statement

**Reason**: Moved to `conversion/selection-tags`, which holds every tag rule of a selection,
widened to the tags along the path (probe C3) and with its relative half reversed (owner
ruling 2026-10-17).
**Migration**: None; `conversion/selection-tags` keeps its scenarios and tests.
