## Purpose

A value in a set or curly statement is one token. How a writer spells it, and how a reader reads
a quoted one, follows the leaf's type in the schema, never the look of the value, so the output
loads on the device as the same configuration from every input format.

## ADDED Requirements

### Requirement: A policy-algebra value is written as the device's token

WHEN a writer (set, structured) writes a value of a leaf typed `policy-algebra` that is one device
token, an expression in parentheses (`( P-A )`, `( P-A && P-B )`) or a quoted name
(`"( P-A )"`), read from any format (set, structured, JSON, YAML, XML), THEN the system SHALL write
it as it is, with no quotes added or removed; any other value of such a leaf (a plain name) SHALL be
quoted only where any value must be. The device writes `import ( P-A )` bare and keeps a quoted
name's quotes in its own XML and JSON (`<import>"( P-A )"</import>`), vMX 23.2R2-S7.5 and QFX5120
25.2R2-S1.5 `junoscfg-oracle` and vMX `synthetic-probes` captures (DEV-4, DEV-6).
Tests: `tests/unit/display/test_value_format.py::TestAValueIsSpelledByItsLeaf::test_a_policy_algebra_token_is_written_as_it_is`, `tests/unit/display/test_value_format.py::TestAValueIsSpelledByItsLeaf::test_a_plain_name_is_quoted_only_where_it_must_be`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/contract/test_format_matrix.py::TestEveryWriterKeepsTheIr::test_the_output_reads_back_as_the_ir`, `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet::test_only_the_recorded_lines_differ`

#### Scenario: A one-term expression

- **WHEN** `import ( P-A )` on a BGP neighbor is read from set, structured, JSON, YAML or XML and written as set
- **THEN** the output is `set protocols bgp group G neighbor 192.168.1.2 import ( P-A )`, not `"( P-A )"`, a policy name

#### Scenario: The device's quoted name from XML or JSON

- **WHEN** the device's `<import>"( P-A )"</import>` or `"import": ["\"( P-A )\""]` is written as set or structured
- **THEN** the value is written `"( P-A )"`, never `""( P-A )""`

### Requirement: A reader keeps the quotes of a policy name that reads as an expression

WHEN set or structured input quotes a value of a leaf typed `policy-algebra` whose text starts with
`(` (`import "( P-A && P-B )"`) THEN the system SHALL keep the quotes in the IR, as the device's
XML and JSON hold it (vMX 23.2R2-S7.5 `synthetic-probes.{xml,json}.gz`), so every writer writes a
policy name, not an expression; WHEN it quotes any other value of such a leaf (`import "P-1"`)
THEN the reader SHALL read it without its quotes, as before (what the device holds for such a
name is open, probe P12) (DEV-5).
Tests: `tests/contract/test_format_matrix.py::TestEveryReaderGivesTheShapeIr::test_the_source_reads_as_the_ir`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/contract/test_format_matrix.py::TestASecondWriterKeepsTheIr::test_every_second_writer`

#### Scenario: A quoted name from set input

- **WHEN** `set protocols bgp group G neighbor 192.168.3.1 import "( P-A && P-B )"` is converted to JSON and to set
- **THEN** the JSON holds `"import": ["\"( P-A && P-B )\""]` and the set output is the input line

#### Scenario: A quoted plain name

- **WHEN** `set protocols bgp group G import "P-1"` is converted to JSON
- **THEN** the JSON holds `"import": ["P-1"]`

### Requirement: A quote inside a value is escaped

WHEN a writer (set, structured) quotes a value that holds `"` THEN the system SHALL write each
inner `"` as `\"`, as the device writes `description "uplink to sw1 \"core\""`, and SHALL write
`\` as it is, as the device writes the login message `"...only.\nAll access is logged."` (vMX
23.2R2-S7.5 and QFX5120 25.2R2-S1.5 `junoscfg-oracle.set.gz`); the output reads back as the same
value through every reader (DEV-7, NEW-C6, ANON-P4). How the device writes `\\`, a backslash
before a quote, or a trailing backslash is open (probe P11).
Tests: `tests/unit/display/test_value_format.py::TestAValueIsSpelledByItsLeaf::test_a_quote_inside_a_value_is_escaped`, `tests/unit/display/test_value_format.py::TestAValueIsSpelledByItsLeaf::test_a_backslash_is_written_as_it_is`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`, `tests/contract/test_format_matrix.py::TestASecondWriterKeepsTheIr::test_every_second_writer`, `tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_the_mapping_restores_the_set_output`

#### Scenario: A description with an escaped quote

- **WHEN** `set interfaces ge-0/0/0 description "uplink to sw1 \"core\""` is read from set, or the same value from structured, JSON, YAML or XML, and written as set
- **THEN** the output is that line, and structured output writes `description "uplink to sw1 \"core\"";`

#### Scenario: Quoting text around the escape

- **WHEN** a value with an escaped quote sits in a one-line curly block, beside comments holding `;`, `{`, `}` and quotes, in a template `${SITE}`, in prose, or beside address-form words (`10.255.0.1:100`, `target:198.51.100.1:5`, `host:198.51.100.2`, `lo_198.51.100.3`)
- **THEN** every reader reads the one value and every writer writes it back as the same value

#### Scenario: Revert of an anonymized set output

- **WHEN** the device example is anonymized to set and reverted with its mapping
- **THEN** the reverted set output reads to the IR the plain set output reads to

### Requirement: The leaf's type, not the value's look, decides

WHEN a value that looks like a policy expression (`( A && B )`) sits on a leaf not typed
`policy-algebra` (a description), THEN the system SHALL quote it as any value holding a space, so
it reads back as the same text; a `$junos-…` variable stays quoted (DEV-V7, recorded as the class
`junos-variable-quoted`).
Tests: `tests/unit/display/test_value_format.py::TestAValueIsSpelledByItsLeaf::test_an_expression_on_another_leaf_is_quoted`, `tests/unit/display/test_value_format.py::TestAValueIsSpelledByItsLeaf::test_a_junos_variable_stays_quoted`, `tests/contract/test_format_matrix.py::TestSetOutputIsTheDeviceLines::test_the_set_lines`

#### Scenario: An expression in a description

- **WHEN** `set interfaces ge-0/0/0 description "( P-A && P-B )"` is converted to set
- **THEN** the output keeps the quotes
