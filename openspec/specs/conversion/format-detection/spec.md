# conversion/format-detection Specification

## Purpose
Classify configuration text once while preserving the formats each caller is
allowed to infer when the user does not name one explicitly.

## Requirements

### Requirement: Classify supported configuration syntax by parsed content

WHEN non-empty configuration text is submitted for format detection THEN the
system SHALL classify valid JSON, XML, YAML, display set, and structured input
from content, prefer JSON for text valid as both JSON and YAML, parse-confirm
brace-prefixed YAML rather than assuming JSON, and reject empty input.

Tests: `tests/unit/display/test_format_detection.py::TestFormatDetection::test_characterization_matrix`

#### Scenario: Unambiguous supported formats

- **WHEN** the input is valid JSON, XML, block YAML, display set, or structured configuration
- **THEN** the classifier returns the corresponding format

#### Scenario: Flow-style YAML starts with a brace

- **WHEN** brace-prefixed input fails JSON parsing but succeeds as a YAML mapping
- **THEN** the classifier returns YAML

#### Scenario: JSON is also valid YAML

- **WHEN** brace-prefixed input parses successfully as both JSON and YAML
- **THEN** the classifier returns JSON

#### Scenario: Empty input

- **WHEN** the input contains no non-whitespace content
- **THEN** the classifier raises a format-detection error

### Requirement: Apply an explicit accepted-format policy per caller

WHEN conversion, validation, or audit requests automatic format detection THEN
the system SHALL use its declared accepted-format policy, with conversion and
audit accepting JSON, XML, YAML, set, and structured while validation continues
to distinguish only set from structured.

Tests: `tests/unit/display/test_format_detection.py::TestDetectionPolicies::test_each_caller_policy`

#### Scenario: Conversion and audit policy

- **WHEN** conversion or audit receives any of the five supported formats without an explicit input format
- **THEN** it uses the classifier's five-format result

#### Scenario: Validation policy remains narrow

- **WHEN** top-level validation receives input without an explicit format
- **THEN** it classifies display set as set and every other non-empty input as structured
