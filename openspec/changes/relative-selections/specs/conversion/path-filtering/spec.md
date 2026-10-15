## RENAMED Requirements

- FROM: `### Requirement: A relative selection spells presence flags and entry key order as absolute output does`
- TO: `### Requirement: A relative selection is written as absolute output writes it, without its path`

## MODIFIED Requirements

### Requirement: Filter the shared IR before rendering

WHEN a caller supplies a non-empty configuration path to the unified conversion
pipeline THEN the system SHALL select that path from the dict IR before invoking
the target renderer, handing it the IR rebuilt along the path (and, for a relative
selection, the path's keys), and return an empty string only when a key on the path is
absent (a path stepping into a list or a leaf names no key): a path whose value is `null`
selects it. A path is split at its dots and matched against the keys present: the exact
key first, and a key holding a dot (`ieee-802.1`, `inet.0`) by the shortest join of steps
with which the rest of the path resolves, so no path that selected a value selects another.
Tests: `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_pipeline_filters_ir_before_rendering`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_path_to_null_selects_it`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_key_holding_a_dot_is_selected`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_the_exact_key_wins_over_a_dotted_one`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_path_through_a_list_or_a_leaf_selects_nothing`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_path_not_in_the_configuration_gives_no_output`

#### Scenario: Wrapped subtree

- **WHEN** `path="system"` and `relative=False`
- **THEN** the renderer receives only the IR hierarchy rooted at `system`

#### Scenario: Relative subtree

- **WHEN** `path="system"` and `relative=True`
- **THEN** the renderer receives the IR hierarchy rooted at `system` and the path `["system"]`, and writes what lies below it

#### Scenario: Missing subtree

- **WHEN** the requested path is absent
- **THEN** conversion returns an empty string without invoking the renderer

#### Scenario: A key holding a dot

- **WHEN** `path="class-of-service.classifiers.ieee-802.1"` selects the `ieee-802.1` classifiers
- **THEN** the output holds them, where it was empty

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
writes `set` in set output and nothing in structured output; a tag on the selected
statement itself is a bare command in set output (`deactivate`) and, in structured output,
dropped with a note. The writer leaves the IR it
is given unchanged; `junoscfg.convert.from_dict(value, fmt, wrap=False)`, the secondary door
for a bare value, keeps its meaning (presence flags and key order as under its last path
key). A flag inside a list (`[true]`) follows absolute output (`[[null]]`), whose device
spelling stays open (NEW-R2).
Tests: `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_is_spelled_as_absolute_output_spells_it`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_annotation_in_a_selected_list_stays_boolean`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_the_scenarios_are_written_as_specified`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_selected_group_list_from_set_input`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_anonymized_selection_is_spelled_alike`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_keeps_its_schema_context`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_list_name_the_schema_hides_is_not_written`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_selected_groups_is_the_list_of_groups`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_entry_named_like_a_hidden_list_keeps_its_name`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_selected_list_writes_its_statements`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_annotation_selection_keeps_its_booleans`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_annotation_selection_in_set_and_structured`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_every_tag_below_a_selection_is_written_below_it`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_yaml_new_selection_is_measured_as_written`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_the_kept_statements_key_writes_its_statements`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_anonymized_list_selection_in_set`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_relative_leaf_preserves_output`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_relative_output_is_the_subtree_without_the_path`, `tests/corpus/test_device_renderings.py::TestRelativeSelections::test_a_relative_selection_is_the_absolute_one_without_its_path`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_bare_selection_is_left_unchanged`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_selection_below_its_path_is_left_unchanged`, `tests/unit/convert/test_convert_roundtrip.py::TestNoWriterChangesTheIrItIsGiven::test_a_bare_value_keeps_its_meaning`

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
