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
- `validate_xml` needs a cleaned `junos-validated.xsd` that nothing in this
  package produces: a raw NETCONF dump does not compile — enforced by
  `tests/test_characterization.py::TestValidateXmlNeedsACleanedXsd`.

## Precedent

- `junoscfg.convert_config` — the one entry point; a new format pair is a row in
  `_CONVERTERS`, never a new public function.
