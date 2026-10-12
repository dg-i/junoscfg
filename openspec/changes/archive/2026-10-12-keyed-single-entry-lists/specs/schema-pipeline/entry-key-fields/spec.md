## ADDED Requirements

### Requirement: Device-backed keyed singletons use the existing list model
WHEN a singleton schema type declares a positional identifier for a keyed entry THEN the corrected schema model SHALL represent the entry as a list without losing children or key order; ordinary containers, unkeyed homogeneous nodes and positional value leaves SHALL retain their classification. The bounded baseline is port-mirroring routing-instance, SRGB label-range and IS-IS attribute-group. This does not promise that multiple entries load on a device.
Tests: `tests/unit/convert/test_convert_roundtrip.py::TestKeyedSingletonMetadata::test_device_backed_slots_are_lists`, `tests/unit/convert/test_convert_roundtrip.py::TestKeyedSingletonMetadata::test_ordinary_containers_keep_their_classification`

#### Scenario: Three named paths
- **WHEN** bundled metadata resolves those paths at root and grouped copies
- **THEN** each is a keyed list with its original children and positional metadata

#### Scenario: Negative controls
- **WHEN** metadata resolves transport-class, snmp, trace filename and port-mirroring family
- **THEN** none becomes a list from its name or homogeneous flag alone

### Requirement: Named definitions retain their emitted descendant and depth context
WHEN named schema types are reused THEN JSON/YAML schema generation SHALL reuse a definition only for compatible emitted descendant shape and effective depth context, retain compatible separately allocated subtree reuse, register recursive definitions before emitting children, preserve the established depth cutoff and produce deterministic resolvable references. Leaf/presence gates, key properties, folded switch spellings and groups array semantics SHALL remain context-correct. This changes no source cardinality or accepted device syntax.
Tests: `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_a_corrected_descendant_array_is_admitted_in_its_own_context`, `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_an_uncorrected_context_never_borrows_object_array_allowance`, `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_equal_separately_allocated_subtrees_share_a_definition`, `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_every_ref_resolves_and_the_draft_schema_is_valid`, `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_a_real_named_cycle_closes_and_keeps_nested_constraints`, `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_deep_first_reuse_cannot_weaken_a_shallow_definition`, `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_different_depths_share_a_definition_when_emitted_shapes_match`, `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_the_same_tree_produces_deterministic_definitions`, `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_the_existing_depth_cutoff_is_preserved`, `tests/unit/validate/test_schema_generator.py::TestNamedDefinitionContexts::test_semantic_child_gates_do_not_share_incompatible_definitions`

#### Scenario: Same named parent with different corrected descendants
- **WHEN** ordinary and corrected singleton descendants occur beneath the same named parent type in either encounter order
- **THEN** each context admits its own array/object shape and the ordinary context rejects borrowed object-array allowance

#### Scenario: Deep and shallow named contexts
- **WHEN** a named parent is first reached near the cutoff and then at a shallow path
- **THEN** shallow child constraints are preserved, while equal emitted shapes at different depths share a definition

#### Scenario: Cyclic and compatible named graphs
- **WHEN** a real named graph is cyclic or compatible deep-copied subtrees occur
- **THEN** recursion closes on a registered definition, compatible shapes remain deduplicated, and every reference resolves deterministically
