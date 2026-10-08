## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

None in `src/`. In `tests/conftest.py`, `find_xsd_source` keeps its name and
returns a path or raises `XsdSourceError` where it returned None.

## Dependencies

None added or removed.

## Requirements

None; `skip_specs: true`.

## Tests and fixtures

None retired; `tests/test_regen_source.py` added. The session fixture
`_regenerate_schema_artifacts` is replaced by `pytest_sessionstart`, and its
warning-and-carry-on path by a stop with the reason.

## Docs

`AGENTS.md` step 2, compacted within its cap; the tier table and usage list
in `docs/architecture/developer-guide.md`; `private_test_data/README.md`.
