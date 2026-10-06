# junoscfg — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Not an implementation module: every name here delegates to `convert` or
`validate`. Logic added here is logic the Ansible collection cannot reach
except through this one function signature.

## Invariants

- `convert_config`, `validate_config`, `Format` and `FieldValidationError` are
  what `dg-i/ansible-collection-junos-config` imports; removing or changing one
  is a declared break — enforced by `agent-ready stage griffe`.
- `validate_xml` cannot work on the bundled artifacts: no XSD ships. Pinned, not
  fixed, by
  `tests/test_characterization.py::TestValidateXmlNeedsAnXsdNobodyShips`.

## Precedent

- `junoscfg.convert_config` — the one entry point; a new format pair is a row in
  `_CONVERTERS`, never a new public function.
