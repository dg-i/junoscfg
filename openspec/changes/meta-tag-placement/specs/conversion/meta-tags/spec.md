## ADDED Requirements

### Requirement: A tag on a curly statement marks the node the statement starts

WHEN structured input carries `inactive:`, `protect:`, `replace:` or `delete:`
before a statement or a block opener THEN the reader SHALL mark the node that
statement starts and no other: a list entry, which ends after its key fields
(the rest of a one-line entry is its content); a leaf or leaf-list, never its
value; a container; and for an unkeyed `homogeneous` container, which never
carries a tag, the child that follows it in the same statement. The schema
walk that reads set input SHALL apply this rule; no curly statement is
flattened to set text first.
Tests: `tests/test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr::test_a_one_line_tagged_route_reaches_one_ir`, `tests/test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr::test_an_inactive_family_inet_reaches_one_ir`, `tests/test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_every_tag_on_a_one_line_entry`, `tests/test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_a_transparent_list_entry`, `tests/test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_an_entry_keyed_by_two_fields`, `tests/test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_set_input_still_marks_the_last_node`

#### Scenario: One-line entry

- **WHEN** `inactive: route ::/0 apply-groups [ G_LOC G_DEF ];` sits under
  `routing-options rib inet6.0 bgp-static`, or
  `inactive: route 0.0.0.0/0 next-hop 10.0.0.1;` under `routing-options static`
- **THEN** the route entry carries `"@": {"inactive": true}` and
  `apply-groups` or `next-hop` carries no tag, as the device's XML and JSON
  show; `protect:`, `replace:` and `delete:` mark the same entry

#### Scenario: Unkeyed homogeneous container

- **WHEN** `inactive: family inet {` opens a block under a unit
- **THEN** `inet` carries the tag and `family` none, as `<inet inactive="inactive">` gives

#### Scenario: Entry keyed by two fields

- **WHEN** `inactive: route-filter 198.51.100.0/24 exact accept;` sits under a term's `from`
- **THEN** the entry keyed `198.51.100.0/24 exact` carries the tag, `accept` none

#### Scenario: Set input is unchanged

- **WHEN** set input reads `deactivate routing-options static route 0.0.0.0/0 next-hop`
- **THEN** `next-hop` carries the tag and the route none

### Requirement: Structured output puts a tag at the head of its node's line

WHEN structured output writes a tagged node THEN the tag SHALL lead the line
that node starts, and the writer SHALL NOT join onto one line a node after the
first that carries a tag, so reading the output back gives the same IR. An
unkeyed `homogeneous` container is written merged with each child
(`family inet {`), decided by the schema's `homogeneous` flag rather than by a
list of names. Layout is otherwise free (`ARCHITECTURE.md` §1).
Tests: `tests/test_meta_tags.py::TestStructuredOutputPutsATagFirst::test_an_inactive_family_inet`, `tests/test_meta_tags.py::TestStructuredOutputPutsATagFirst::test_a_tagged_child_is_not_joined`, `tests/test_meta_tags.py::TestStructuredOutputPutsATagFirst::test_round_trips_keep_the_ir`, `tests/test_artifact_builder.py::TestHomogeneousFlag::test_the_tree_carries_it`

#### Scenario: Tag inside a merged line

- **WHEN** the IR marks `inet` under a unit's `family` inactive
- **THEN** structured output writes `inactive: family inet {`, never `family inactive: inet {`

#### Scenario: Tagged child of a collapsible parent

- **WHEN** a term's `then` holds only `accept`, and `accept` is inactive
- **THEN** structured output writes `then { inactive: accept; }` as a block

#### Scenario: Round trips

- **WHEN** each tagged shape of this capability goes set → structured → set
  and structured → set → structured
- **THEN** the IR after the round trip equals the IR before it

### Requirement: A tag on an unkeyed homogeneous container is reported

WHEN any input tags an unkeyed `homogeneous` container itself
(`deactivate … family`, `protect … family`, `<family inactive="inactive">`,
`"family": {"@": {"inactive": true}}`) THEN field validation SHALL report it
`UNPLACED`, set output SHALL repeat it as written, and structured output SHALL
drop it and say so on the diagnostic sink, because the device rejects it
(`missing argument`, `private_test_data/deactivate4.txt` and `deactivate6.txt`).
Tests: `tests/test_meta_tags.py::TestATagOnFamilyIsReported::test_every_input_reports_it`, `tests/test_meta_tags.py::TestATagOnFamilyIsReported::test_set_output_repeats_it`, `tests/test_meta_tags.py::TestATagOnFamilyIsReported::test_structured_output_drops_it_with_a_note`

#### Scenario: Every input

- **WHEN** set, XML, JSON and YAML input each tag `family` under a unit
- **THEN** `convert_config_result` carries one `UNPLACED` diagnostic naming `family`

### Requirement: XML input keeps protect

WHEN XML input carries `protect="protect"` on an element THEN the IR SHALL mark
that node `"protect": "protect"`, the canonical spelling device JSON's
`"protect": true` normalizes to, so set output writes `protect …`.
Tests: `tests/test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr::test_a_protected_one_line_route_reaches_one_ir`

#### Scenario: Protected route

- **WHEN** `<route protect="protect"><name>0.0.0.0/0</name><next-hop>10.0.0.1</next-hop></route>`
  is read, and the same route from set (`protect routing-options static route
  0.0.0.0/0`), structured (`protect: route 0.0.0.0/0 next-hop 10.0.0.1;`) and
  device JSON (`"@": {"protect": true}`)
- **THEN** all four give one IR
