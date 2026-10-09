## Purpose

The structure tree keeps every child a list declares, in order, and names the
fields that key its entries, so no site keeps its own answer to either.

## ADDED Requirements

### Requirement: The parser keeps every element a sequence declares

WHEN a complexType's sequence declares identifier elements and one or more
`xsd:choice` groups THEN the parser SHALL keep every identifier, `name`
included, and the children of every choice as children of the node, in
declared order, and SHALL record the identifier names, in that order, as the
node's entry keys.
Tests: `tests/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_two_identifiers_beside_a_comment_only_choice`, `tests/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_one_identifier_other_than_name`, `tests/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_name_is_a_key_child`, `tests/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_a_second_choice_is_kept`, `tests/test_xsd_parser.py::TestEveryDeclaredChildIsKept::test_a_choice_declared_before_the_key_comes_first`

#### Scenario: Two identifiers beside a choice of comments only

- **WHEN** a type declares `list-type` and `list-name` as identifiers and its
  choice holds only the undocumented and comment references
- **THEN** the node has the children `list-type` and `list-name`, the keys
  `(list-type, list-name)`, and is no longer a childless presence list

#### Scenario: One key, two choices

- **WHEN** a type declares `address`, a choice of `exact` and `orlonger`, then
  a choice holding `accept` and `reject`
- **THEN** the node keys on `(address,)` and its children are `address`,
  `exact`, `orlonger`, `accept`, `reject` in that order

#### Scenario: A choice before the key, and name

- **WHEN** one type declares a choice of `add` and `delete`, then the
  identifier `community-name`, and another the one identifier `name`
- **THEN** `add` and `delete` precede `community-name` among the first's
  children, and the second has the child `name` and the keys `("name",)`

### Requirement: The structure tree carries the keys and the declared order

WHEN a list node is written to the structure tree and read back THEN the tree
SHALL keep its children in declared order and carry its keys as an ordered
list under `k`, omitted only where the keys are `("name",)`, and SHALL restore
both on read; no node SHALL carry `fe`.
Tests: `tests/test_artifact_builder.py::TestStructureTreeRoundTrip::test_ordered_entry_keys_survive`, `tests/test_artifact_builder.py::TestStructureTreeRoundTrip::test_declared_child_order_survives`, `tests/test_artifact_builder.py::TestStructureTreeRoundTrip::test_no_node_carries_fe`

#### Scenario: Round trip

- **WHEN** nodes keyed `(list-type, list-name)`, `(address,)` and `("name",)`,
  and a node with `add` declared before `community-name`, are written and read
- **THEN** each keeps its keys and child order, only the first two carry `k`,
  and none carries `fe`

### Requirement: One kernel helper answers an entry's keys

WHEN any site needs the fields that key a list's entries, or whether the node
declares a child before them THEN it SHALL read them from `entry_keys()` and
the tree node's child order through `junoscfg.display`; no module under
`src/junoscfg/` SHALL read `fe`, `values-only`, a `_v<n>` key, a literal
`community-name`, `FLAT_ENTRY_ELEMENTS`, `ENTRY_KEY_OVERRIDES` or
`get_flat_entry_config`, and the last two SHALL be banned imports.
Tests: `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_the_helper_answers_the_key_tuple`, `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_no_module_keeps_its_own_key`

#### Scenario: The helper's answers

- **WHEN** the node carries `k` `["list-type", "list-name"]`, or `["address"]`,
  or no `k`
- **THEN** the helper answers `("list-type", "list-name")`, `("address",)`,
  `("name",)`

#### Scenario: The source holds no second answer

- **WHEN** the source tree under `src/junoscfg/` is scanned
- **THEN** none of the retired spellings is read, and `pyproject.toml` bans
  `junoscfg.display.ENTRY_KEY_OVERRIDES` and
  `junoscfg.display.get_flat_entry_config`

### Requirement: The bundled tree carries the declared keys

WHEN the bundled structure tree, regenerated from the shipped release's dump,
is walked THEN every `control-as-list-type` slot SHALL carry the keys
`list-type`, `list-name`; every `attributes-match` the keys
`from-event-attribute`, `condition`, `to-event-attribute-value`; every
`control-route-filter-type` `address`, every `control-prefix-list-filter-type`
`list_name`, each with its actions; `then community` `community-name` after
its actions; `policy-options community` `("name",)`; and `o` SHALL be set on a
list with children exactly where the dump flags `oneliner` or `oneliner-plus`.
Tests: `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_the_bundled_tree_carries_the_declared_keys`

#### Scenario: The AS-list slots

- **WHEN** the tree is walked for `as-path-neighbors`, `as-path-origins` and
  `as-path-transits`
- **THEN** all 24 slots, at the root, in logical systems, in groups and in
  grouped logical systems, with and without a `term`, carry both keys

#### Scenario: Two lists named community

- **WHEN** the tree is walked for `then community` and `policy-options community`
- **THEN** the first is keyed `community-name`, declared after `add`, and the
  second is keyed `name`
