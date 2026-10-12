# schema-pipeline/entry-key-fields Specification

## Purpose
The structure tree keeps every child a list declares, in order, and names the
fields that key its entries, so no site keeps its own answer to either.

## Requirements

### Requirement: The parser keeps every element a sequence declares

WHEN a complexType's sequence declares identifier elements and `xsd:choice`
groups THEN the parser SHALL keep every element, `name` included, as a child
of the node in declared order, and SHALL record as the node's key fields, in
declared order, each identifier element and each choice whose every element is
an identifier (`<flag>identifier</flag>` or `<identifier/>`), such a choice as
one field whose alternatives are its elements. Any `maxOccurs` but 1 is a list.
Tests: `tests/unit/validate/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_two_identifiers_beside_a_comment_only_choice`, `tests/unit/validate/test_xsd_parser.py::TestCardinality::test_a_numeric_max_occurs_is_list`, `tests/unit/validate/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_one_identifier_other_than_name`, `tests/unit/validate/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_name_is_a_key_child`, `tests/unit/validate/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_a_second_choice_is_kept`, `tests/unit/validate/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_an_identifier_choice_is_one_key_field`

#### Scenario: Two identifiers beside a choice of comments only

- **WHEN** a type declares identifiers `list-type`, `list-name` and a choice of
  comments only
- **THEN** it has those children, the keys `(list-type, list-name)`, and is no
  childless presence list

#### Scenario: A key, an identifier choice, an action choice

- **WHEN** a type declares `address`, an `<identifier/>` choice of `exact` and
  `orlonger`, then a choice holding `accept` and `reject`
- **THEN** the keys are `(address, (exact, orlonger))`, the five children kept
  in that order

#### Scenario: An identifier choice first, and name

- **WHEN** one type declares an `<identifier/>` choice of `add` and `delete`,
  then `community-name`, and another the one identifier `name`
- **THEN** the first is keyed `((add, delete), community-name)`, the second
  `("name",)` with the child `name`

#### Scenario: A list the XSD bounds by a number

- **WHEN** `forwarding-classes class` declares `maxOccurs="16"`
- **THEN** it is a list, keyed `name` (challenge A, owner decision)

### Requirement: A simpleContent key keeps anonymization type knowledge

WHEN an identifier leaf's type is an inline `simpleContent` extension THEN the
parser SHALL record its extension base as anonymization type knowledge and the
structure tree SHALL preserve it separately from the `tr` field strict field
validation consumes. JSON/YAML schema generation, field validation and grammar
generation SHALL not treat that hint as a validation type.
Tests: `tests/unit/validate/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_a_simple_content_key_keeps_anonymization_type_only`, `tests/unit/convert/test_field_validator.py::TestIPAddressValidation::test_anonymization_type_does_not_validate_a_template_value`

#### Scenario: IP prefix key and template value

- **WHEN** a route-filter `address` extends `ipprefix`
- **THEN** its structure-tree leaf carries `ipprefix` for anonymization, while
  a synthetic template value in that key gains no IP-validation warning

### Requirement: The structure tree carries the keys and the declared order

WHEN a list node is written to the structure tree and read back THEN the tree
SHALL keep its children in declared order and carry its key fields as an
ordered list under `k`, a field of alternatives as a nested list, omitted only
where the keys are `("name",)`, and SHALL restore both on read; no node SHALL
carry `fe`.
Tests: `tests/unit/validate/test_artifact_builder.py::TestStructureTreeRoundTrip::test_ordered_entry_keys_survive`, `tests/unit/validate/test_artifact_builder.py::TestStructureTreeRoundTrip::test_declared_child_order_survives`, `tests/unit/validate/test_artifact_builder.py::TestStructureTreeRoundTrip::test_no_node_carries_fe`

#### Scenario: Round trip

- **WHEN** nodes keyed `(list-type, list-name)`, `(address, (exact, orlonger))`
  and `("name",)` are written and read
- **THEN** each keeps keys and child order; only the first two carry `k`

### Requirement: One kernel helper answers an entry's keys

WHEN any site needs the fields that key a list's entries, or the children a
statement inside it names, THEN it SHALL read `entry_keys()` or
`statement_children()` through `junoscfg.display`; no module under
`src/junoscfg/` SHALL read `fe`, `values-only`, a `_v<n>` key, a literal
`community-name`, `FLAT_ENTRY_ELEMENTS`, `ENTRY_KEY_OVERRIDES` or
`get_flat_entry_config`, and the last two SHALL be banned imports.
Tests: `tests/unit/display/test_entry_keys.py::TestEntryKeys::test_the_helper_answers_the_key_tuple`, `tests/unit/display/test_entry_keys.py::TestStatementChildren::test_statement_children_drop_the_key_fields`, `tests/tooling/test_entry_key_spellings.py::TestEntryKeysComeFromTheTree::test_no_module_keeps_its_own_key`

#### Scenario: The helper's answers

- **WHEN** the node carries `k` `["list-type", "list-name"]`, or `["address",
  ["exact", "orlonger"]]`, or no `k`
- **THEN** the helper answers `("list-type", "list-name")`, `("address",
  ("exact", "orlonger"))`, `("name",)`

#### Scenario: The source holds no second answer

- **WHEN** the source tree under `src/junoscfg/` is scanned
- **THEN** no retired spelling is read, and `pyproject.toml` bans the two names

### Requirement: The bundled tree carries the declared keys

WHEN the bundled tree, regenerated from the shipped release's dump, is walked
THEN `control-as-list-type` SHALL carry the keys `list-type`, `list-name`;
`attributes-match` its three fields; the three filter lists their address or
`list_name` then the match-type choice, actions as children; `then community`
its action choice then `community-name`; and `o` SHALL stand where the dump
flags `oneliner`, and on those filter lists (owner decision, phase 5).
Tests: `tests/unit/display/test_entry_keys.py::TestEntryKeys::test_the_bundled_tree_carries_the_declared_keys`, `tests/unit/validate/test_artifact_builder.py::TestTheOneLineFlag::test_the_one_line_flag_follows_the_dump`, `tests/corpus/test_schema_data.py::TestEntryKeysOnTheDump::test_the_as_list_slots_carry_both_keys`

#### Scenario: The AS-list slots

- **WHEN** the tree is walked for the three `as-path-*` lists
- **THEN** all 24 slots, at the root, in logical systems, in groups and in
  grouped logical systems, with and without a `term`, carry both keys

#### Scenario: Two lists named community

- **WHEN** the tree is walked for `then community` and `policy-options community`
- **THEN** the first is keyed (action choice, `community-name`), the second `name`

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
