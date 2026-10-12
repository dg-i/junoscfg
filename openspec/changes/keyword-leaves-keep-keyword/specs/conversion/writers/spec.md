## ADDED Requirements

### Requirement: Writers retain keyworded leaves and nested triggers

WHEN any of the Set, structured, JSON, YAML or XML readers supplies keyworded timeout, limit, path or filename leaves or nested optical trigger content THEN each of the Set, structured, JSON and YAML writers SHALL preserve the independently specified IR; Set output SHALL retain each required keyword. Genuine positional traceoptions filenames and maximum-prefixes limits SHALL retain their supported spelling. Existing event-options trigger after/count behavior SHALL remain supported without claiming device Set equivalence.
Tests: `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`

#### Scenario: A keyworded timeout is retained

- **WHEN** a radius-server has timeout 10 or IS-IS overload has timeout 300
- **THEN** rendered Set and structured output retains timeout and readers recover that leaf

#### Scenario: An unrelated trigger retains its nested content

- **WHEN** otn-options trigger oc-los holds hold-time up 100
- **THEN** writers retain oc-los, hold-time and up 100

### Requirement: Flattening never silently discards richer child shapes

WHEN a flat-dict container carries a nested mapping or a list with values THEN the Set and structured writers SHALL preserve all child content by normal traversal rather than emitting a truncated flattened statement.
Tests: `tests/unit/convert/test_convert_roundtrip.py::TestAFlatHintPreservesRicherContent::test_nested_content_is_not_discarded`

#### Scenario: A flat hint encounters a nested child

- **WHEN** a container marked flat-dict contains nested child hold-time up 100
- **THEN** both writers retain that complete child independently of the hint
