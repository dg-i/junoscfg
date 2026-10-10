# junoscfg.validate — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Two pipelines share this directory: the build-time XSD pipeline and the runtime
validators. They are separate domains in `pyproject.toml`; do not let a runtime
validator import an `xsd_*` module.

## Invariants

- Schema corrections live in `xsd_fixes.py` as Python, never edited into the
  generated artifacts, so they survive regeneration — enforced by
  `tests/test_xsd_fixes.py::TestFixRegistry::test_all_fixes_have_metadata`.
- `ArtifactBuilder` and `JunosValidator` resolve lazily through `__getattr__`:
  importing this package must not pull lxml or the schema artifacts.
- Any `maxOccurs` other than 1 makes a list, however the dump bounds it
  — enforced by `tests/test_xsd_parser.py::TestCardinality::test_a_numeric_max_occurs_is_list` and `tests/test_xsd_parser.py::TestCardinality::test_unbounded_is_list`.

## Precedent

- `junoscfg.validate.xsd_fixes` — the registry shape, one `XsdFix` per
  correction with its category, description and applies_to.
- `junoscfg.input.find_unsupported_set_brackets` — the lower-layer lexical
  boundary set validation reports through normal `ValidationError` results.
