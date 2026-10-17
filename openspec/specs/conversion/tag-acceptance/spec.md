# conversion/tag-acceptance Specification

## Purpose
Which Junos tags each input carries into the IR, and which it refuses: XML
keeps `protect` as it keeps `inactive`, and a tag Junos never accepts -- on
`family` itself -- is reported from every input instead of passed on.

## Requirements

### Requirement: A tag on an unkeyed homogeneous container is reported

WHEN any input tags an unkeyed `homogeneous` container itself
(`deactivate … family`, `protect … family`, `<family inactive="inactive">`,
`"family": {"@": {"inactive": true}}`) THEN field validation SHALL report it
`UNPLACED`, set and structured output SHALL drop it and say so in one note on the
diagnostic sink ("N tag(s) dropped from a container Junos never tags (...): it is written
merged with each child"), and set validation SHALL report a verb line naming it invalid
(`junoscfg.display.meta_target` gives it the kind `merged`), because the device rejects it.
Set output repeated it as written, a line the device refuses (Reviewer A1, owner ruling
2026-10-17, change device-probe-fixes). The device evidence is `interfaces … unit … family`;
`family` under routing-instances, protocols, firewall and access follows by extension, and the
16 `tunnel encapsulation` nodes the same rule covers have no device evidence (BACKLOG
DEVICE-EVIDENCE, question 12). Only a
tag counts (`inactive`, `protect`, `operation`, `active`); metadata such as
`junos:group` on the container is not one. The device rejects it
(`missing argument`, `private_test_data/deactivate4.txt` and `deactivate6.txt`).
Tests: `tests/unit/convert/test_meta_tags.py::TestATagOnFamilyIsReported::test_every_input_reports_it`, `tests/unit/convert/test_meta_tags.py::TestATagOnFamilyIsReported::test_set_output_drops_it_with_a_note`, `tests/unit/convert/test_meta_tags.py::TestATagOnFamilyIsReported::test_structured_output_drops_it_with_a_note`, `tests/unit/convert/test_meta_tags.py::TestATagOnFamilyIsReported::test_set_output_drops_a_sibling_family_tag_from_json`, `tests/unit/convert/test_meta_tags.py::TestOnlyTagsCountAsTags::test_metadata_on_family_is_not_a_tag`, `tests/unit/convert/test_meta_tags.py::TestOnlyTagsCountAsTags::test_a_family_tag_written_twice_is_noted_once`, `tests/contract/test_every_door.py::TestEveryVerbNamesAStatementPath::test_every_door_agrees`, `tests/unit/display/test_meta_path.py::TestAMetaPathNamesWhatTheReaderTags::test_the_target`

#### Scenario: Every input

- **WHEN** set, XML, JSON, YAML and structured input (`inactive: family {` on
  its own line) each tag `family` under a unit
- **THEN** `convert_config_result` carries one `UNPLACED` diagnostic naming `family`

#### Scenario: Set output and validation

- **WHEN** `deactivate interfaces xe-0/0/0 unit 0 family` follows the family's `set` line
- **THEN** set output writes the `set` line alone with the note, and `-v` reports the
  `deactivate` line invalid

### Requirement: XML input keeps protect

WHEN XML input carries `protect="protect"` on an element THEN the IR SHALL mark
that node `"protect": "protect"`, the canonical spelling device JSON's
`"protect": true` normalizes to, so set output writes `protect …`.
Tests: `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`

#### Scenario: Protected route

- **WHEN** `<route protect="protect"><name>0.0.0.0/0</name><next-hop>10.0.0.1</next-hop></route>`
  is read, and the same route from set (`protect routing-options static route
  0.0.0.0/0`), structured (`protect: route 0.0.0.0/0 next-hop 10.0.0.1;`) and
  device JSON (`"@": {"protect": true}`)
- **THEN** all four give one IR
