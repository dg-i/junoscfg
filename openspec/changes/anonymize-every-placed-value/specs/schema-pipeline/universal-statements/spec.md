## MODIFIED Requirements

### Requirement: One helper resolves a universal statement at every level

WHEN a reader, writer or validator walking the structure tree meets a key the current node's children do not name THEN it SHALL resolve that key through `junoscfg.display.schema_child(node, key, root)`. The helper SHALL answer the node's own child first, then the root's universal statement of that name (`junoscfg.display.universal_statements(root)`), else nothing. The set, curly and XML readers, leaf-list normalization, the set, structured and JSON writers and field validation SHALL use the helper, so a nested `apply-groups`, `apply-groups-except`, `apply-flags` or `apply-macro` is read, written and validated against its node. A universal statement SHALL never be resolved inside a universal statement: `apply-flags` holds its flags and `apply-macro` its pairs, so `apply-flags apply-groups G1` is reported `UNPLACED` by every reader and rejected by the grammar, which adds the universal statements to no rule that only a universal statement reaches. The JSON-schema generator SHALL name exactly the statements the tree declares. No module SHALL keep its own copy of their names, except the kernel's compatibility floor, the schema fix that declares them, the anonymizer's group rule and the audit walker, which give a group reference its meaning; the anonymize and audit walkers resolve the statements through the helper too.
Tests: `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_a_nested_statement_resolves_to_the_roots_node`, `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_the_nodes_own_child_comes_first`, `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_nothing_resolves_inside_a_universal_statement`, `tests/unit/convert/test_set_input.py::TestApplyFlagsIsAContainerOfFlags::test_no_universal_statement_inside_apply_flags`, `tests/unit/convert/test_field_validator.py::TestAUniversalStatementIsValidatedWithItsNode::test_a_universal_statement_inside_apply_flags_never_passes`, `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_a_key_nothing_declares_resolves_to_nothing`, `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_the_helper_is_a_kernel_door`, `tests/unit/display/test_universal_statements.py::TestOneHelperResolvesThem::test_a_nodes_own_statement_wins_in_every_reader`, `tests/corpus/test_device_renderings.py::TestEveryDoorReadsTheDevicesUniversalStatements::test_every_door_reads_the_devices_universal_statements`, `tests/corpus/test_device_renderings.py::TestEveryDoorReadsTheDevicesUniversalStatements::test_the_captures_hold_universal_statements`, `tests/unit/convert/test_convert_api.py::TestLeafListPromotion::test_a_nested_json_scalar_universal_leaf_list_is_a_list`, `tests/unit/validate/test_schema_generator.py::TestUniversalStatementsReachEveryContainer::test_the_tree_is_authoritative`, `tests/unit/convert/test_field_validator.py::TestAUniversalStatementIsValidatedWithItsNode::test_nested_statements_are_clean`, `tests/unit/convert/test_field_validator.py::TestAUniversalStatementIsValidatedWithItsNode::test_a_bare_nested_statement_is_unplaced`, `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/tooling/test_universal_statement_names.py::TestUniversalStatementsComeFromTheTree::test_no_module_keeps_their_names`, `tests/tooling/test_universal_statement_names.py::TestUniversalStatementsComeFromTheTree::test_the_scan_sees_each_retired_reading`, `tests/unit/anonymize/test_walker.py::TestTheWalkerReachesEveryPlacedValue::test_a_universal_statement_below_the_root`

#### Scenario: A statement below the root

- **WHEN** `system`, an interface or a BGP group holds `apply-groups`, `apply-groups-except`, `apply-macro` or `apply-flags`
- **THEN** `schema_child` answers the root's node for it, and field validation checks it against that node and reports nothing for a valid one
- **WHEN** XML or YAML holds a nested `apply-groups` with one group, as every device XML capture does
- **THEN** it reads as a list of that group, as set input, the top level and the device's own JSON do (catalogue row `universal-statements-below-the-root`; every capture's set, curly and XML door against its JSON)
- **WHEN** JSON holds a nested `apply-groups` with one group as a scalar
- **THEN** it stays the scalar it was: JSON keeps its supplied shapes (ARCH-C10), a carry-forward to change 13 pinned by a strict xfail, not an answer
- **WHEN** a node declares its own child named like a universal statement
- **THEN** every reader reads that child, never the root's statement
- **WHEN** JSON or YAML holds a nested `apply-groups` with no group (`null`, `[null]`, `true`)
- **THEN** field validation reports it `UNPLACED`, as any leaf without its value

#### Scenario: Not inside a universal statement

- **WHEN** `set system apply-flags apply-groups G1`, `set system apply-flags apply-flags omit`, their curly or JSON spelling, or `apply-macro M1 peer 203.0.114.7` inside `apply-flags` is read
- **THEN** it is reported `UNPLACED`, written back as read, rejected by `validate_config`, strict conversion raises, and an anonymized run converts it with the address replaced and its schema path named in a warning, no message carrying the address (owner answer 5, spec anonymization/placed-values)

#### Scenario: The tree decides which statements are universal

- **WHEN** a tree's root flags only `apply-groups` universal
- **THEN** the JSON schema names `apply-groups` at every container and no other name from the floor

