## ADDED Requirements

### Requirement: An absolute selection keeps the tags of the selected statement

WHEN a path is selected with `relative=False` (CLI `--path` without `--relative`) and ends at
a key whose annotation the IR holds beside it (`@<key>`: a leaf's, leaf-list's or flag's
`inactive`, `protect`, `active`, `operation`, comment or any other meta key, or a list's own
comment as the device writes it), a key holding a dot included, THEN the system SHALL hand
the writer that annotation beside the selected key, so every writer writes the statement's
tags as the selection of its parent writes them, from every reader: the output reads back as
the IR holding only the selected statement and its annotation, and loads with the same
meaning. A container and a list entry hold their tags inside the selected value and keep
them as before. A relative selection hands the writer the same IR and the path: a selected
leaf's tags are then a tag on the selected statement itself, written as the relative
requirement above says and as a selected container's are (a bare command in set output,
dropped with a note in structured output, the value alone in json, yaml and yaml-new), where
base dropped them silently (specification challenge SC1, pending owner decision). Tags of
an ancestor on the path are outside this requirement.
Tests: `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_absolute_leaf_selection_keeps_its_tags`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_leaf_selection_reads_as_its_statement_alone`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_tagged_entry_or_container_at_the_path_end_keeps_its_tags`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_leaf_selection_writes_its_tags_as_a_container_does`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_leaf_selection_keeps_every_meta_key`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_dotted_flag_keeps_its_tags`, `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_an_anonymized_leaf_selection_keeps_its_tags`, `tests/corpus/test_device_renderings.py::TestAnAbsoluteSelectionKeepsItsTags::test_every_tagged_statement_keeps_its_tags`, `tests/unit/display/test_display_filters.py::TestFilterDictByPath::test_a_selected_leaf_keeps_its_annotation`, `tests/unit/display/test_display_filters.py::TestFilterDictByPath::test_the_text_filters_keep_a_selected_leafs_annotation`, `tests/unit/cli/test_cli.py::TestPathOptions::test_path_keeps_a_selected_leafs_tags`

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

#### Scenario: A tagged leaf selected relative

- **WHEN** the deactivated, protected `system.host-name` is selected relative and written as set
- **THEN** the output is `set r1`, `deactivate`, `protect`, which put back under `system host-name` reads as the absolute output
