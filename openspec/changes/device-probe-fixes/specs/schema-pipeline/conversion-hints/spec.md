## MODIFIED Requirements

### Requirement: A rename keeps the device's element name

WHEN a schema fix renames an element to its CLI keyword (Group E: `end-range` to `to`,
`ieee-802.3ad` to `802.3ad`, the NAT rule `match`, SNMP `name`, the `ethernet-` speeds, the
`=`, `+` and `-` literals, `hello-padding-type` to `hello-padding`) THEN the node SHALL record
the element name the device writes in XML and JSON, the structure tree SHALL carry it (`x`),
the set grammar SHALL take the keyword, and the JSON schema SHALL name the element as the
device writes it; the IR SHALL hold the tree's key whichever reader gave it (set, curly, XML,
JSON, yaml-new, yaml), so one configuration has one IR; set and curly output SHALL write the
keyword, and JSON and yaml-new output the device's element name. JSON and yaml-new
validation SHALL take the element name, and the keyword as a permanent alias (what junoscfg
0.28.23 and earlier wrote, and what the JSON reader reads) only where the node records an
element name: the QFX5120 25.2R2-S1.5 loads JSON holding `"802.3ad"` and `"to"` as it loads
the element names (probe D3; owner ruling 2026-10-17, the alias is no longer deprecated). The
device prints `system-name`, `ethernet-1g` and `equal-literal`, `plus-literal` and
`minus-literal` with `community-name` in JSON and XML, and loads junoscfg's JSON holding them
(probe D2). No table outside the schema model SHALL repeat the renames.
Tests: `tests/unit/validate/test_xsd_fixes.py::TestARenameKeepsTheDevicesName::test_every_rename_records_the_element_name`, `tests/unit/validate/test_artifact_builder.py::TestStructureTreeRoundTrip::test_every_flag_the_tables_name_survives`, `tests/unit/validate/test_schema_generator.py::TestTheJsonSchemaNamesElementsAsTheDeviceWrites::test_json_takes_the_element_name_yaml_the_keyword`, `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/contract/test_round_trip_validates.py::TestTheConverterOutputValidates::test_the_rendering_validates`, `tests/contract/test_round_trip_validates.py::TestTheSchemaStillRejects::test_the_bundled_schema_rejects`, `tests/contract/test_round_trip_validates.py::TestTheKeywordOfARenameIsAnAlias::test_both_spellings_validate`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/corpus/test_device_probes.py::TestJunoscfgWritesTheDevicesJsonNames::test_the_json_object`, `tests/corpus/test_device_probes.py::TestEveryProbedRenderingReadsAsItsSet::test_the_rendering`

#### Scenario: A LAG member from JSON

- **WHEN** `{"ether-options": {"ieee-802.3ad": {"bundle": "ae0"}}}` under an interface is read
  from JSON, and `ether-options 802.3ad ae0` from set
- **THEN** both give one IR, set output writes `ether-options 802.3ad ae0`, JSON output writes
  `"ieee-802.3ad"`, and JSON validation accepts the JSON and field validation the IR

#### Scenario: An interface-range member range

- **WHEN** the device's JSON `"member-range": [{"name": "ge-0/0/2", "end-range": "ge-0/0/5"}]`
  is read and validated
- **THEN** no finding is reported and set output writes `member-range ge-0/0/2 to ge-0/0/5`

#### Scenario: IS-IS hello padding

- **WHEN** `set protocols isis interface ge-0/0/0 hello-padding strict` and the device's JSON
  `"hello-padding-type": "strict"` are read
- **THEN** both validate, give one IR, and set output writes `hello-padding strict`

#### Scenario: The keyword spelling the device loads

- **WHEN** the probe's keyword JSON (`"802.3ad"`, `"to"`) and its element JSON are read
- **THEN** both give one IR, whose set output is the device's two display set lines
