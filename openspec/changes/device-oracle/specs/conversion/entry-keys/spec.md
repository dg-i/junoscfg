## MODIFIED Requirements

### Requirement: Writers follow the declared order

WHEN set or structured output renders a list entry THEN set output SHALL write
the keyword, the key values in declared order, each not `nokeyword` with its
keyword, a key choice as its keyword and value, then each other child on a line
of its own; structured output SHALL put an entry on one line exactly where the
node carries `o`. The device's structured static route and `attributes-match`
SHALL be pinned beside today's. Correctness is the device's display set
(`tests/corpus/test_device_renderings.py`), not byte identity with an earlier
release.
Tests: `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet::test_only_the_recorded_lines_differ`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/corpus/test_device_truth.py::test_name_keyed_set_lines_match_the_device`, `tests/corpus/test_device_truth.py::test_unexplained_structured_shapes_are_pinned`

#### Scenario: Device JSON and XML to set and structured

- **WHEN** the device-shaped AS-list, community, route-filter, source-address-filter
  and `attributes-match` entries are converted
- **THEN** each is one set line as the device displays it, and structured output
  writes `route-filter 198.51.100.0/24 exact accept;` and `community add COMM-A;`

#### Scenario: Name-keyed lists, as the device splits them

- **WHEN** static `route`, NTP `server` and `flag` entries with two children are set
- **THEN** each child is a line of its own (device probe, vMX 23.2R2-S7.5)
