## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

No symbol is removed. `tests/jvd_data.py` is new and test-only.

## Dependencies

No dependency is added. The clone uses `git`, which the project already
requires; `ensure_corpus` returns None rather than raising when it is absent,
and the fixture skips.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. Seven are added, all behind `--jvd`.

## Docs

`docs/architecture/developer-guide.md` replaces a three-tier table that omitted
`--schema` with a five-tier one. `private_test_data/README.md` gains the corpus
section.
