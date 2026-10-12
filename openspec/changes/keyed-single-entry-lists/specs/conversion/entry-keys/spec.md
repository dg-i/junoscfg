## ADDED Requirements

### Requirement: A keyed singleton retains its entry and its tag through every format
WHEN supported keyed singleton configuration arrives through set, structured, XML, JSON or YAML THEN every reader SHALL retain an entry array and every writer SHALL preserve its children and entry metadata through the same IR. Set inactive output SHALL name the entry path once without repeating the key or naming the key leaf.
Tests: `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/contract/test_format_matrix.py::TestASecondWriterKeepsTheIr::test_every_second_writer`

#### Scenario: Inactive port-mirroring entry
- **WHEN** routing-instance with name and IP address is inactive
- **THEN** all readers keep one entry with @ inactive and set writes one entry deactivate

#### Scenario: Range and attribute-group
- **WHEN** SRGB has start/end or attribute-group has name and metric
- **THEN** the complete one-entry array survives every reader/writer

### Requirement: Known containers do not borrow the name entry fallback
WHEN a known schema container has a child named name THEN the shared writer SHALL traverse its children rather than consume name as an entry key; an absent schema SHALL retain the documented legacy fallback. Writers SHALL leave caller IR unchanged.
Tests: `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/unit/convert/test_convert_roundtrip.py::TestKnownContainerNames::test_name_and_siblings_are_written_separately`, `tests/unit/convert/test_convert_roundtrip.py::TestKnownContainerNames::test_an_unknown_schema_retains_the_entry_fallback`

#### Scenario: Transport-class
- **WHEN** transport-class has two name entries and auto-create
- **THEN** both entries and the sibling survive without a dict being emitted as a key

#### Scenario: Keyworded name
- **WHEN** corrected-schema snmp has name and location
- **THEN** both render separately and round-trip; this control makes no device acceptance claim
