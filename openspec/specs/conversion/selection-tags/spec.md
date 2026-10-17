# conversion/selection-tags Specification

## Purpose
A `--path` selection writes the tags that give its statements their meaning: absolute output
keeps the selected statement's own tags and those along its path, as the device prints them,
and relative output notes each tag it cannot write instead of writing a line the device
refuses.

## Requirements

### Requirement: An absolute selection keeps the tags of the selected statement and along its path

WHEN a path is selected with `relative=False` (CLI `--path` without `--relative`) THEN the
system SHALL hand the writer the annotations the IR holds for the selected statement and along
its path, as the selection of the whole configuration holds them: the selected key's `@<key>`
beside it (a leaf's, leaf-list's or flag's `inactive`, `protect`, `active`, `operation`,
comment or any other meta key, or a list's own comment, a key holding a dot included), each
step's `@<key>` beside it, and each ancestor container's own `@` (the configuration's own `@`
aside). A container and a list entry hold their tags inside the selected value. Every writer
then writes the tags as the parent selection writes them, from every reader: the output reads
back as the IR holding only the selected statement and these annotations, and loads with the
same meaning, so a statement inside a deactivated or protected container is written inside
it. The QFX5120 25.2R2-S1.5 prints a leaf under a deactivated route with the route's
`deactivate` line, `"@": {"inactive": true}` in JSON and `inactive="inactive"` in XML, and
under a deactivated `routing-options static` with `deactivate routing-options static` (probe
C3). Equivalent, not identical: junoscfg writes no bare `set routing-options static` beside
the tag. The display text filters (`filter_json_by_path`, `filter_yaml_by_path`) share the rule.
Tests: `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_absolute_leaf_selection_keeps_its_tags`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_leaf_selection_reads_as_its_statement_alone`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_tagged_entry_or_container_at_the_path_end_keeps_its_tags`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_leaf_selection_keeps_every_meta_key`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_dotted_flag_keeps_its_tags`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_anonymized_leaf_selection_keeps_its_tags`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_absolute_selection_keeps_its_ancestors_tags`, `tests/unit/display/test_display_filters.py::TestFilterDictByPath::test_a_selected_leaf_keeps_its_annotation`, `tests/unit/display/test_display_filters.py::TestFilterDictByPath::test_the_text_filters_keep_a_selected_leafs_annotation`, `tests/unit/display/test_display_filters.py::TestFilterDictByPath::test_a_selection_keeps_its_ancestors_annotations`, `tests/unit/cli/test_cli.py::TestPathOptions::test_path_keeps_a_selected_leafs_tags`, `tests/unit/cli/test_cli.py::TestPathOptions::test_path_keeps_an_ancestors_tag`, `tests/corpus/test_device_renderings.py::TestAnAbsoluteSelectionKeepsItsTags::test_every_tagged_statement_keeps_its_tags`, `tests/corpus/test_device_renderings.py::TestAnAbsoluteSelectionKeepsItsTags::test_a_selection_keeps_every_annotation_along_its_path`, `tests/corpus/test_device_probes.py::TestASelectionLoadsAsTheDevicePrintsIt::test_the_selection`

#### Scenario: A deactivated host name

- **WHEN** `set system host-name r1`, `deactivate system host-name` and `set system domain-name example.net` are converted with `--path system.host-name`
- **THEN** set writes `set system host-name r1` and `deactivate system host-name`, structured writes the leaf `inactive:`, and json, yaml and yaml-new hold `"@host-name": {"inactive": true}`, as `--path system` writes them

#### Scenario: A deactivated leaf-list

- **WHEN** `deactivate system domain-search` tags a two-value leaf-list selected as `system.domain-search`
- **THEN** every writer keeps the tag, as the parent selection writes it

#### Scenario: A tagged list entry or container at the path end

- **WHEN** `interfaces.interface` holds a deactivated entry, or `system.syslog` is deactivated, and the path ends there
- **THEN** the tag is written as before this change

#### Scenario: A device's commented list and deactivated flag

- **WHEN** the device captures' `access.radius-server` (a list with its comment beside it) or `routing-options.forwarding-table.chained-composite-next-hop.ingress.l3vpn` (a deactivated flag) is selected absolute
- **THEN** the output holds the comment or the tag, as the parent selection writes it

#### Scenario: A host name under a deactivated system

- **WHEN** `set system host-name r1` and `deactivate system` are converted with `--path system.host-name`
- **THEN** set writes `set system host-name r1` and `deactivate system`, structured writes `inactive: system host-name r1;` (which reads back as those two lines), and json, yaml and yaml-new hold `"@": {"inactive": true}` inside `system`

#### Scenario: The probe's route under a deactivated static

- **WHEN** the probe's route lines and `deactivate routing-options static` are converted with `--path routing-options.static.route`
- **THEN** the set output reads as the same configuration as the device's display set

### Requirement: A relative selection notes each tag it cannot write

WHEN a path is selected with `relative=True` THEN every writer SHALL drop a tag at or above the
path that its output cannot write and SHALL give one note, "N tag(s) at or above the selected
path dropped: relative output writes what lies below the path": in `set` and `structured` a
tag on the selected statement itself or on an ancestor; in `json`, `yaml-new` and `yaml` a tag
beside a key of the path (`@host-name`, a per-value tag of a selected leaf-list included) or on
an ancestor, while a selected container's own `@` is part of the value they write. No writer
SHALL write a bare verb (`deactivate`, `protect`, `activate`, `delete` with no path): the
QFX5120 25.2R2-S1.5 refuses one at an edit level ("syntax error, expecting <statement>,
<attribute-name>, <flag-value>, or <identifier>", probe SC1). This reverses the bare command
the approved path-filtering requirement prescribed (owner ruling 2026-10-17), and the note
counts only, so an anonymized conversion quotes nothing. A comment beside a key of the path or
on an ancestor, which json, yaml-new and yaml write absolute, is dropped with its own note, "N
comment(s) at or above the selected path dropped: ..."; set and structured output write no
comment in any selection.
Tests: `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_leaf_selection_notes_its_tags`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_selection_notes_every_tag_it_drops`, `tests/unit/cli/test_cli.py::TestPathOptions::test_a_relative_path_notes_a_dropped_tag`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_leaf_selection_notes_its_comment`, `tests/corpus/test_device_renderings.py::TestRelativeSelections::test_a_relative_selection_is_the_absolute_one_without_its_path`

#### Scenario: A tagged leaf selected relative

- **WHEN** the deactivated, protected `system.host-name` is selected relative and written as set
- **THEN** the output is `set r1` and the note counts two tags; no bare line is written

#### Scenario: A deactivated container selected relative

- **WHEN** `set system syslog file f any any` and `deactivate system syslog` are written with `--path system.syslog --relative`
- **THEN** set writes `set file f any any` and structured the `file f` block, each with the note; json, yaml-new and yaml hold `"@": {"inactive": true}` in the value and give no note

#### Scenario: A statement below a deactivated ancestor selected relative

- **WHEN** `set system host-name r1` and `deactivate system` are written with `--path system.host-name --relative`
- **THEN** every writer writes the value alone and gives the note
