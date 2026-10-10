## Purpose

Structured text is validated statement by statement as conversion reads it, in
the input's own tokens, so the validation doors agree with each other and with
what the device accepts in curly form.

## ADDED Requirements

### Requirement: Curly text is validated as the conversion walk reads it

WHEN structured text is validated through `validate_structured()`,
`validate_config()` (format given or detected), or `junoscfg -v -i structured`
THEN each statement the conversion walk reads SHALL be validated as one set
line spelled in the input's own tokens: a one-line statement the walk reads as
several sibling statements is split where each sibling starts, a tag is not a
line of its own, and no token passes through the set writer first. A block on
one line is validated, never passed as empty.
Tests: `tests/contract/test_every_door.py::TestStructuredTextValidatesAsConversionReadsIt::test_every_door_agrees`, `tests/unit/convert/test_structured_input.py::TestTheSetLinesOfAStatement::test_the_walk_splits_at_each_sibling`

#### Scenario: The device's one-line container statement

- **WHEN** curly `hold-time up 2000 down 0;` under an interface is validated (vMX curly prints it so; its display set prints two lines)
- **THEN** every door reports it valid, as it reports the two set lines valid

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
next minor release, and give the verdict it gave before: the `validate` package
cannot reach the conversion walk, so these doors keep the schema-free route.
Tests: `tests/unit/validate/test_structured_validator.py::TestTheStructuredDoorsAreDeprecated::test_each_warns_and_keeps_its_verdict`

#### Scenario: The facade's structured door

- **WHEN** `JunosValidator().validate_structured("system {\n host-name router1;\n}")` is called
- **THEN** it warns and returns a valid result
