# validation/structured-validation Specification

## Purpose
Structured text is validated statement by statement as conversion reads it, in
the input's own tokens, so the validation doors agree with each other and with
what the device accepts in curly form.

## Requirements

### Requirement: Curly text is validated as the conversion walk reads it

WHEN structured text is validated through `validate_structured()`,
`validate_config()` (format given or detected), or `junoscfg -v -i structured`
THEN each statement the conversion walk reads SHALL be validated as one set
line spelled in the input's own tokens (`junoscfg.convert.structured_set_lines()`):
a one-line statement the walk reads as several sibling statements is split
where each sibling starts, a tag is not a line of its own, and no token passes
through the set writer first. A statement whose last leaf the walk read without
its value SHALL be invalid, whatever the set grammar says of the split line. A
block on one line is validated, never passed as empty; what yields no
statement is a warning on every door. The walk and the grammar both come from
the `artifacts_dir` given; a directory without the structure tree the walk
reads raises `SchemaLoadError` (CLI exit 3), as a missing grammar does. None of
these doors warns of a deprecation.
Tests: `tests/contract/test_every_door.py::TestStructuredTextValidatesAsConversionReadsIt::test_every_door_agrees`, `tests/unit/convert/test_structured_input.py::TestTheSetLinesOfAStatement::test_the_walk_splits_at_each_sibling`, `tests/unit/convert/test_structured_input.py::TestTheRecommendedDoorsAreNotDeprecated::test_no_deprecation_reaches_their_caller`, `tests/unit/convert/test_structured_input.py::TestValidationReadsOneArtifactsDirectory::test_the_walk_and_the_grammar_come_from_it`

#### Scenario: The device's one-line container statement

- **WHEN** curly `hold-time up 2000 down 0;` under an interface is validated (vMX curly prints it so; its display set prints two lines)
- **THEN** every door reports it valid, as it reports the two set lines valid

#### Scenario: A sibling without its value

- **WHEN** curly `hold-time up 2000 down;` is validated
- **THEN** every door reports it invalid, although the set grammar takes the
  split line `hold-time down` as `hold-time` with the value `down`

#### Scenario: No acceptance or rejection the writer would add

- **WHEN** curly `description a b c;` or `overload timeout 300;` is validated
- **THEN** the first is invalid and the second valid, as their set lines are,
  although the writer would quote the one and drop `timeout` from the other

#### Scenario: A one-line block

- **WHEN** `system { bogus-statement 1; }` is validated
- **THEN** every door reports it invalid

### Requirement: The validate package's structured doors are deprecated

WHEN a caller uses `StructuredValidator.validate()` or
`JunosValidator.validate_structured()` THEN each SHALL emit a
`DeprecationWarning` naming `junoscfg.validate_structured()` and removal in the
next minor release. They keep their schema-free route through
`SetConverter.to_set()`, because the `validate` package cannot reach the
conversion walk, but they read with the token lexer, so their verdict changes
where it reads differently: a block on one line is validated (`system {
bogus-statement 1; }` becomes invalid), a brace too many is invalid, and the
device's `/* OMITTED */` placeholder is valid with a warning. A one-line
statement of siblings and a `protect:` line stay rejected there.
A multiword terminal statement tagged `inactive`, `protect`, or `delete` SHALL
return an invalid result containing the path-free `to_set()` refusal; it never
reaches set validation. Public `junoscfg.validate_structured()` remains the
schema-aware replacement.
Tests: `tests/unit/validate/test_structured_validator.py::TestTheStructuredDoorsAreDeprecated::test_each_warns_and_keeps_its_schema_free_route`, `tests/unit/validate/test_structured_validator.py::TestTheStructuredDoorsAreDeprecated::test_the_new_lexer_changes_a_verdict`, `tests/unit/display/test_terminal_tag_refusal.py::TestTerminalMetadataRequiresTheSchema::test_deprecated_validation_reports_the_refusal`

#### Scenario: The facade's structured door

- **WHEN** `JunosValidator().validate_structured("system {\n host-name router1;\n}")` is called
- **THEN** it warns and returns a valid result

#### Scenario: Refused terminal metadata

- **WHEN** either deprecated validation door receives a multiword terminal inactive/protect/delete statement
- **THEN** it returns invalid with the replacement conversion named, rather than claiming schema-free conversion succeeded
