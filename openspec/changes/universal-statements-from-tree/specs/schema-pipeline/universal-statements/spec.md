## Purpose

The statements Junos accepts at every hierarchy level are declared once, on the
structure tree's root, and every layer reads them from there through one kernel
helper, so no module keeps its own list of their names or shapes.

## ADDED Requirements

### Requirement: One helper resolves a universal statement at every level

WHEN a reader, writer or validator walking the structure tree meets a key the current node's children do not name THEN it SHALL resolve that key through `junoscfg.display.schema_child(node, key, root)`. The helper SHALL answer the node's own child first, then the root's universal statement of that name (`junoscfg.display.universal_statements(root)`), else nothing. The set, curly and XML readers, leaf-list normalization, the set, structured and JSON writers and field validation SHALL use the helper, so a nested `apply-groups`, `apply-groups-except`, `apply-flags` or `apply-macro` is read, written and validated against its node. The JSON-schema generator SHALL name exactly the statements the tree declares. No module SHALL keep its own copy of their names, except the kernel's compatibility floor, the schema fix that declares them, and the anonymize and audit walkers, which give a group reference its meaning.
Tests: `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_a_nested_statement_resolves_to_the_roots_node`, `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_the_nodes_own_child_comes_first`, `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_a_key_nothing_declares_resolves_to_nothing`, `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_the_helper_is_a_kernel_door`, `tests/unit/validate/test_schema_generator.py::TestUniversalStatementsReachEveryContainer::test_the_tree_is_authoritative`, `tests/unit/convert/test_field_validator.py::TestAUniversalStatementIsValidatedWithItsNode::test_nested_statements_are_clean`, `tests/unit/convert/test_field_validator.py::TestAUniversalStatementIsValidatedWithItsNode::test_a_bare_nested_statement_is_unplaced`, `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/tooling/test_universal_statement_names.py::TestUniversalStatementsComeFromTheTree::test_no_module_keeps_their_names`, `tests/tooling/test_universal_statement_names.py::TestUniversalStatementsComeFromTheTree::test_the_scan_sees_each_retired_reading`

#### Scenario: A statement below the root

- **WHEN** `system`, an interface or a BGP group holds `apply-groups`, `apply-groups-except`, `apply-macro` or `apply-flags`
- **THEN** `schema_child` answers the root's node for it, and field validation checks it against that node and reports nothing for a valid one
- **WHEN** XML or YAML holds a nested `apply-groups` with one group
- **THEN** it reads as a list of that group, as set input and the top level already read it (catalogue row `universal-statements-below-the-root`)
- **WHEN** JSON or YAML holds a nested `apply-groups` with no group (`null`, `[null]`, `true`)
- **THEN** field validation reports it `UNPLACED`, as any leaf without its value

#### Scenario: The tree decides which statements are universal

- **WHEN** a tree's root flags only `apply-groups` universal
- **THEN** the JSON schema names `apply-groups` at every container and no other name from the floor

### Requirement: A tree that declares none runs on a compatibility floor

WHEN the tree's root flags no child universal THEN `universal_statements` SHALL answer the floor `junoscfg.display.UNIVERSAL_STATEMENTS`: the four statements with the nodes the bundled tree declares for them. When the root flags any child, the helper SHALL answer only those. A tree that flags none is a structure tree built before 0.8.0, or one built without the schema fixes. The floor SHALL retire when the artifact loader refuses such a tree, after one minor release that warns. Until then a tripwire test SHALL fail if the bundled artifacts declare anything but the floor, or are answered from it.
Tests: `tests/unit/display/test_universal_statements.py::TestTheFloorIsForATreeThatDeclaresNone::test_a_tree_declaring_none_gets_the_floor`, `tests/unit/display/test_universal_statements.py::TestTheFloorIsForATreeThatDeclaresNone::test_a_tree_declaring_some_gets_only_those`, `tests/unit/display/test_universal_statements.py::TestTheFloorIsForATreeThatDeclaresNone::test_the_bundled_tree_never_runs_on_the_floor`, `tests/unit/display/test_universal_statements.py::TestTheFloorIsForATreeThatDeclaresNone::test_an_old_tree_reads_and_writes_them`, `tests/unit/validate/test_schema_generator.py::TestUniversalStatementsReachEveryContainer::test_a_tree_without_the_flag_still_names_the_kernel_four`

#### Scenario: Artifacts built before 0.8.0

- **WHEN** conversion runs on a structure tree whose root holds no `apply-*` node
- **THEN** set input reads `apply-groups`, `apply-macro` and `apply-flags omit` as it does on the bundled tree, and set output writes them back

#### Scenario: The bundled artifacts

- **WHEN** the bundled tree is loaded
- **THEN** its root declares exactly the floor's four nodes, and the helper answers the tree's own nodes, never the floor

### Requirement: A flag helper reads the node, never a name

WHEN `get_transparent_child`, `is_transparent_list_key`, `is_positional_key` or `is_flat_dict` is asked about a key the tree does not place THEN it SHALL answer no flag. The helpers SHALL take the node only and keep no table of element names. Content the tree does not place SHALL be written with every keyword it holds, and field validation SHALL report it `UNPLACED` as before.
Tests: `tests/unit/convert/test_convert_api.py::TestUnplacedContentKeepsItsKeywords::test_every_keyword_is_written`, `tests/unit/convert/test_convert_api.py::TestUnplacedContentKeepsItsKeywords::test_it_is_still_reported`, `tests/tooling/test_universal_statement_names.py::TestUniversalStatementsComeFromTheTree::test_no_module_keeps_their_names`

#### Scenario: Unplaced content with a flagged name

- **WHEN** JSON holds `{"bogus-container": {"timeout": "5", "limit": "7", "interfaces": {"interface": [{"name": "ge-0/0/0", "description": "x"}]}}}`
- **THEN** set output writes `set bogus-container timeout 5`, `set bogus-container limit 7` and `set bogus-container interfaces interface ge-0/0/0 description x`, where it wrote `set bogus-container 5` and dropped `interface`, and each unknown key is reported `UNPLACED`

### Requirement: apply-flags is the container the device writes

WHEN set, curly, JSON, YAML or XML input holds `apply-flags omit` or `apply-flags replace` at any level THEN every reader SHALL read `{"apply-flags": {"omit": [null]}}` (or `replace`), field validation SHALL report nothing, set output SHALL write `set … apply-flags omit`, curly output SHALL write `apply-flags omit;`, and the grammar SHALL accept the set line. The device writes `omit` so in set, XML and JSON (`tests/data/device/synthetic/{vmx-23.2R2-S7.5,qfx5120-25.2R2-S1.5}/junoscfg-oracle.{set,xml,json}.gz`, group `GR-OMIT`). `replace` has the set and curly spellings the grammar already accepted; its JSON and XML shape is inferred from `omit` and awaits probe P8. Any other word under `apply-flags` SHALL be kept whole and reported `UNPLACED` by the set and curly readers, reported `UNPLACED` by field validation from JSON, YAML and XML, and rejected by the grammar.
Tests: `tests/unit/convert/test_set_input.py::TestApplyFlagsIsAContainerOfFlags::test_a_flag_reads_as_the_device_writes_it`, `tests/unit/convert/test_set_input.py::TestApplyFlagsIsAContainerOfFlags::test_another_word_is_kept_whole_and_reported`, `tests/unit/convert/test_field_validator.py::TestAUniversalStatementIsValidatedWithItsNode::test_an_unknown_flag_under_apply_flags_is_unplaced`, `tests/unit/validate/test_xsd_fixes.py::TestGroupDMissingElements::test_apply_flags_is_the_devices_container_of_flags`, `tests/corpus/test_shipped_artifacts.py::TestTheShippedArtifactsModelTheApplyStatements::test_an_apply_statement_validates`, `tests/corpus/test_shipped_artifacts.py::TestTheShippedArtifactsModelTheApplyStatements::test_an_apply_statement_is_rejected`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/contract/test_round_trip_validates.py::TestTheConverterOutputValidates::test_the_rendering_validates`

#### Scenario: The device's group GR-OMIT

- **WHEN** `set groups GR-OMIT system apply-flags omit`, its curly, JSON, YAML or XML spelling is read
- **THEN** the IR holds `"apply-flags": {"omit": [null]}` under `system`, nothing is reported, strict conversion passes, and set output is the device's line (catalogue row `apply-flags-omit-as-the-device-writes-it`)

#### Scenario: At the top and with another word

- **WHEN** `set apply-flags omit` is read
- **THEN** the IR holds `{"apply-flags": {"omit": [null]}}`, not the leaf `"omit"`
- **WHEN** `set apply-flags bogus` or `set system apply-flags bogus` is read, or JSON holds `"apply-flags": {"bogus": [null]}`
- **THEN** it is reported `UNPLACED`, and `validate_config` rejects the set line
