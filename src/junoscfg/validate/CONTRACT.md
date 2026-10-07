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

## Precedent

- `junoscfg.validate.xsd_fixes` — the registry shape, one `XsdFix` per
  correction with its category, description and applies_to.
