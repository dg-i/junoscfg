## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

No symbol is removed. `read_platform` and `STAGING_PLATFORM` are added;
`promote_staged` gains an optional `platform` argument with a default.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. Four are added in `tests/test_schema_naming.py`, which is
deliberately not marked `schema`: they build a few bytes of XML in a temp
directory and would otherwise be skipped by default along with the tests that
need a real dump.

## Docs

`private_test_data/README.md` gains the capture command and the reason the
platform cannot come from the dump.
