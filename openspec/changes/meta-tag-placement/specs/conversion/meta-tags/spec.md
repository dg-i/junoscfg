## ADDED Requirements

### Requirement: A tag on an unkeyed homogeneous container is reported

WHEN any input tags an unkeyed `homogeneous` container itself
(`deactivate … family`, `protect … family`, `<family inactive="inactive">`,
`"family": {"@": {"inactive": true}}`) THEN field validation SHALL report it
`UNPLACED`, set output SHALL repeat it as written, and structured output SHALL
drop it and say so on the diagnostic sink, because the device rejects it
(`missing argument`, `private_test_data/deactivate4.txt` and `deactivate6.txt`).
Tests: `tests/test_meta_tags.py::TestATagOnFamilyIsReported::test_every_input_reports_it`, `tests/test_meta_tags.py::TestATagOnFamilyIsReported::test_set_output_repeats_it`, `tests/test_meta_tags.py::TestATagOnFamilyIsReported::test_structured_output_drops_it_with_a_note`, `tests/test_meta_tags_challenge.py::test_set_output_repeats_a_sibling_family_tag_from_json`

#### Scenario: Every input

- **WHEN** set, XML, JSON, YAML and structured input (`inactive: family {` on
  its own line) each tag `family` under a unit
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
