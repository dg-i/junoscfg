# conversion/curly-meta-tags Specification

## Purpose
Curly-brace (structured) configuration carries Junos tags (`inactive:`,
`protect:`, `replace:`, `delete:`) at the head of a line. Reading it, a tag
marks the node the device marks; writing it, a tag leads the line of the node
it marks, so what junoscfg writes reads back as the same configuration.

## Requirements

### Requirement: A tag on a curly statement marks the node the statement starts

WHEN structured input carries `inactive:`, `protect:`, `replace:` or `delete:`
before a statement or a block opener THEN the reader SHALL mark the node that
statement starts and no other: a list entry, which ends after its key fields
(the rest of a one-line entry is its content); a leaf or leaf-list, never its
value; a container; and for an unkeyed `homogeneous` container, which never
carries a tag, the child that follows it in the same statement (on a line of
its own, `inactive: family {` tags `family` itself, which is reported). Where a
list keyword stands alone on its line and its entries follow as lines of the
block (`source-prefix-list { PL1; }`), a tag on the keyword marks the whole
list and a tag on an entry's line marks that entry. A tag that would mark only
some values of a leaf or of `apply-groups`, or one data line of `apply-macro`,
is not widened: the leaf is refused with `ValueError`, as XML input refuses it,
and the macro line is kept whole and reported. The schema walk that reads set input SHALL apply
this rule; no curly statement is flattened to set text first.
Tests: `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/unit/convert/test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_every_tag_on_a_one_line_entry`, `tests/unit/convert/test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_a_transparent_list_entry`, `tests/unit/convert/test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_an_entry_keyed_by_two_fields`, `tests/unit/convert/test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_set_input_still_marks_the_last_node`, `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir[a-tag-on-a-bare-list-keyword-structured]`, `tests/unit/convert/test_meta_tags.py::TestATagOnOneValueOfALeafListIsRefused::test_a_per_value_tag_in_curly_is_refused_as_in_xml`, `tests/unit/convert/test_meta_tags.py::TestOnlyTagsCountAsTags::test_uneven_tags_on_apply_groups_are_refused`, `tests/unit/convert/test_meta_tags.py::TestATagDoesNotGrowOverActiveConfiguration::test_a_tag_on_apply_macro_data_does_not_tag_the_macro`, `tests/unit/convert/test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_stacked_curly_tags_mark_one_entry_in_either_order`

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

#### Scenario: Entry inside its list's block

- **WHEN** `source-prefix-list { inactive: PL1; PL2; }` sits under a firewall term's `from`
- **THEN** the entry `PL1` carries the tag, as `deactivate … source-prefix-list PL1`
  gives; `inactive: source-prefix-list {` would tag the whole list

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
A tagged leaf-list keeps its tag on the bracket line (`inactive: members [ … ];`).
A list tagged as a whole is written as its keyword's tagged block with the
entries inside, never collapsed (`inactive: name-server { 192.168.0.1; }`), as
the device writes `inactive: routing-instance { R1 {…} }`.
Tests: `tests/unit/convert/test_meta_tags.py::TestStructuredOutputPutsATagFirst::test_an_inactive_family_inet`, `tests/unit/convert/test_meta_tags.py::TestStructuredOutputPutsATagFirst::test_a_tagged_child_is_not_joined`, `tests/contract/test_format_matrix.py::TestASecondWriterKeepsTheIr::test_every_second_writer`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/unit/validate/test_artifact_builder.py::TestHomogeneousFlag::test_the_tree_carries_it`

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
