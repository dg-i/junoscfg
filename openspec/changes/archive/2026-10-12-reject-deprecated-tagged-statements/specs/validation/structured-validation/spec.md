## MODIFIED Requirements

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
