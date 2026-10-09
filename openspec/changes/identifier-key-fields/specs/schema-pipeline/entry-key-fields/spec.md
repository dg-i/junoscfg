## Purpose

The structure tree names the fields that key a list entry, in the order the
dump declares them, so no reader, writer or validator keeps its own answer to
what keys an entry.

## ADDED Requirements

### Requirement: The parser keeps a list's identifier elements

WHEN a complexType's sequence holds elements flagged `identifier` beside a
trailing `xsd:choice` THEN the parser SHALL keep each identifier as a child of
the node, in declared order ahead of the choice's children, and SHALL record
the identifier names on the node, in that order, as its entry keys.
Tests: `tests/test_xsd_parser.py::TestIdentifierElementsAreKept::test_two_identifiers_beside_a_comment_only_choice`, `tests/test_xsd_parser.py::TestIdentifierElementsAreKept::test_one_identifier_other_than_name`, `tests/test_xsd_parser.py::TestIdentifierElementsAreKept::test_a_name_identifier_records_no_keys`

#### Scenario: Two identifiers beside a choice of comments only

- **WHEN** a type declares `list-type` and `list-name` as identifiers and its
  choice holds only the undocumented and comment references
- **THEN** the node has the children `list-type` and `list-name`, the keys
  `(list-type, list-name)`, and is no longer a childless presence list

#### Scenario: One identifier other than name

- **WHEN** a type declares `address` as its identifier beside a choice of
  `exact` and `orlonger`
- **THEN** the node keys on `(address,)` and keeps `exact` and `orlonger`

#### Scenario: The identifier is name

- **WHEN** the one identifier is `name`
- **THEN** the node records no entry keys, and its entries stay keyed `name`

### Requirement: The structure tree carries the keys as k

WHEN a node keyed by anything but the single field `name` is written to the
structure tree and read back THEN the tree SHALL carry its keys as an ordered
list under `k` and SHALL restore the same keys on read; `k` SHALL be omitted
where the one key is `name`, and `fe` SHALL carry only the position `p`.
Tests: `tests/test_artifact_builder.py::TestStructureTreeRoundTrip::test_ordered_entry_keys_survive`, `tests/test_artifact_builder.py::TestStructureTreeRoundTrip::test_a_flat_entry_carries_only_its_position`

#### Scenario: Round trip

- **WHEN** a node keyed `(list-type, list-name)` and a `route-filter` keyed
  `(address,)` at position `first` are written and read back
- **THEN** both keep their keys in order, the second keeps position `first`,
  and neither tree entry holds `fe.k`

### Requirement: One kernel helper answers an entry's keys

WHEN any site needs the fields that key a list's entries THEN it SHALL call
`entry_keys()` from `junoscfg.display` on the list's tree node, which SHALL
answer the node's `k` as a tuple, else `("name",)`; no module under
`src/junoscfg/` SHALL read `fe.k`, a `values-only` position, a `_v<n>` entry
key, a literal `community-name`, or `ENTRY_KEY_OVERRIDES`, which stays
exported, read by no module, until a later minor release removes it.
Tests: `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_the_helper_answers_k_then_name`, `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_no_module_keeps_its_own_key`

#### Scenario: The helper's answers

- **WHEN** the node carries `k` `["list-type", "list-name"]`, or `["address"]`,
  or no `k`
- **THEN** the helper answers `("list-type", "list-name")`, `("address",)`,
  `("name",)`

#### Scenario: The source holds no second answer

- **WHEN** the source tree under `src/junoscfg/` is scanned
- **THEN** only the definition and the export of `ENTRY_KEY_OVERRIDES` name
  it, and none of the other retired spellings is read

### Requirement: The bundled tree carries the declared keys

WHEN the bundled structure tree, regenerated from the shipped release's dump,
is walked THEN every `control-as-list-type` slot SHALL carry the children and
keys `list-type`, `list-name`; every `attributes-match` SHALL be keyed
`from-event-attribute`, `condition`, `to-event-attribute-value`; every
`route-filter` SHALL be keyed `address` and every `prefix-list-filter`
`list_name`, both at position `first`; the community action list under `then`
SHALL be keyed `community-name`; and no node SHALL carry `values-only`.
Tests: `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_the_bundled_tree_carries_the_declared_keys`

#### Scenario: The AS-list slots

- **WHEN** the tree is walked for `as-path-neighbors`, `as-path-origins` and
  `as-path-transits`
- **THEN** all 24 slots, at the root, in logical systems, in groups and in
  grouped logical systems, with and without a `term`, carry both keys

#### Scenario: The flat-entry lists

- **WHEN** the tree is walked for the lists `_fix_flat_entry_keys` marks
- **THEN** each carries the keys its dump declares and `fe` holds only `p`
