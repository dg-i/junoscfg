## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

No symbol is removed. `_RESERVED_RULE_NAMES` is added, private.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. Sixteen test functions are added across the two commits
(13 in `998915f`, 3 in `4c633d5`): four in `test_grammar_generator.py`, the
rest the schema-backed tier in `test_schema_data.py`.

## Docs

`docs/guide/validation.md` lost a promise: `4c633d5` removed "JSON, YAML, set
and structured validation work out of the box", which had not been true since
the 24.4 migration, and replaced it with a notice. No document described
rule-name generation itself.
