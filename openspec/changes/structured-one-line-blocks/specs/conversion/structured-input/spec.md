## Purpose

Structured (curly-brace) text is read by one token lexer, so a configuration
means the same whatever its layout, and nothing the text holds vanishes without
a word: it becomes a statement, a refusal, or a warning.

## ADDED Requirements

### Requirement: Structured text is read by tokens, not lines

WHEN structured text puts several statements, a block's braces, or a closing
brace and the next statement on one line THEN the reader SHALL read the same
statements, with the same tags, as the text laid out one statement per line;
`{`, `}`, `;` and a bracket list are tokens wherever they stand outside quotes
(a template's `${NAME}` stays inside its word), and format detection SHALL classify such text as structured, a tagged one-liner
included.
Tests: `tests/unit/display/test_set_converter.py::TestTheLexerReadsTokensNotLines::test_one_line_text_reads_as_its_lines`, `tests/unit/display/test_set_converter.py::TestTheLexerReadsTokensNotLines::test_tags_and_quoted_values_read_exactly`, `tests/unit/convert/test_structured_input.py::TestABlockOnOneLine::test_every_door_converts_it`, `tests/unit/convert/test_structured_input.py::TestABlockOnOneLine::test_auto_detection_reads_it_as_structured`, `tests/unit/display/test_format_detection.py::TestFormatDetection::test_each_format_is_recognised`

#### Scenario: A block on one line

- **WHEN** `class-of-service { forwarding-classes { class fc0 queue-num 0; } }` is converted
- **THEN** the IR holds the forwarding class, as the multi-line text gives it,
  and `junoscfg audit unused` reports what the multi-line text gives it

#### Scenario: Two statements and a following block on one line

- **WHEN** `system { host-name router1; domain-name example.net; } interfaces { ge-0/0/0 { description uplink; } }` is converted
- **THEN** `host-name` is `router1`, `domain-name` is `example.net`, and the interface block is kept

#### Scenario: A tagged one-liner without a format

- **WHEN** `system { inactive: host-name router1; }` reaches `junoscfg` with no `-i`
- **THEN** it is read as structured, never as the YAML mapping it also parses as

### Requirement: A comment is never part of a statement

WHEN a `#` comment or a `/* */` comment, on one line or several, holds `;`,
`{`, `}` or a quote THEN the reader SHALL skip it whole; a `#` or `/*` inside a
quoted value is part of the value.
Tests: `tests/unit/display/test_set_converter.py::TestACommentIsNeverPartOfAStatement::test_a_comment_holding_a_delimiter`

#### Scenario: A trailing comment holding a semicolon

- **WHEN** `system { host-name router1; ## note; see ticket }` is read, or the same with `/* a; b */`
- **THEN** `host-name` is `router1`

### Requirement: Malformed structured text is refused

WHEN structured text closes a block it never opened, leaves a block, bracket
list, quote or comment open, ends a statement without `;`, lets a statement run
onto a later line (as prose or a CLI prompt above a dump does; no device writes
one), or opens a block with no name THEN conversion SHALL raise `ValueError`
naming the fault, its line and the line's text, and structured validation SHALL return an invalid result; no statement
of the text is converted silently in part. A `;` with no statement before it
(`;;`, `};`) carries nothing and is read as nothing.
Tests: `tests/unit/display/test_set_converter.py::TestMalformedTextIsRefused::test_it_raises`, `tests/unit/convert/test_structured_input.py::TestMalformedTextIsRefused::test_every_door_refuses_it`, `tests/unit/display/test_set_converter.py::TestAnEmptyStatementReadsAsNothing::test_a_stray_semicolon`

#### Scenario: A brace too many

- **WHEN** `system { host-name router1; } }` is converted, or audited
- **THEN** `ValueError` names the unmatched `}` and its line; the CLI exits 2

### Requirement: What yields no statement is reported, not silently dropped

WHEN a block holds no statement THEN each door SHALL report a warning naming
the block's path: `SetConverter.notes()`, a `warning` diagnostic of source
`structured-input` from `convert_config_result()` and `pipeline_result()`, the
`diagnostic_sink` of `to_dict()`, stderr of `junoscfg convert`, `junoscfg -v`
and `junoscfg audit unused`, and a warning of `validate_structured()` and
`validate_config()`. The device's `{ /* OMITTED */ }` placeholder, its curly
rendering of a statement under `apply-flags omit`, is reported as content the
device hid and is never written as configuration. What an empty block
configures on a device has no evidence yet (probe P6); the warning says it
holds no statement and claims nothing more.
Tests: `tests/unit/display/test_set_converter.py::TestWhatYieldsNoStatementIsReported::test_the_lexer_names_the_block`, `tests/unit/convert/test_structured_input.py::TestWhatYieldsNoStatementIsReported::test_every_door_reports_it`, `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet::test_only_the_recorded_lines_differ`, `tests/corpus/test_device_renderings.py::TestTheRecordExplainsItself::test_every_defined_class_has_a_recorded_line`

#### Scenario: The device's placeholder

- **WHEN** the vMX and QFX5120 captures' curly holds `system { /* OMITTED */ };` under group `GR-OMIT`
- **THEN** no set line holds `OMITTED`, the class `omitted-block-emitted` is gone from `known-differences.json`, and conversion warns that `groups GR-OMIT system` hides its content

### Requirement: The schema-free set writer of the lexer is deprecated

WHEN a caller uses `SetConverter.to_set()` THEN it SHALL emit a
`DeprecationWarning` naming `convert_config(..., from_format=Format.STRUCTURED,
to_format=Format.SET)` and removal in the next minor release. It keeps its
schema-free route, which places a one-line statement's tag on its last node;
it reads with the token lexer, so one-line text now yields its lines.
Tests: `tests/unit/display/test_set_converter.py::TestToSetIsDeprecated::test_it_warns_and_keeps_its_output`

#### Scenario: A caller of the deprecated writer

- **WHEN** `SetConverter("system {\n host-name router1;\n}").to_set()` is called
- **THEN** it warns and returns `set system host-name router1`
