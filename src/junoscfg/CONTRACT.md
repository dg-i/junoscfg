# junoscfg — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Not an implementation module: every name delegates to `convert` or `validate`,
except `validate_structured`, which composes them (`convert.structured_set_lines`
then set validation) because `validate` may not import `convert` (change
structured-one-line-blocks, C4). Other logic here is logic the Ansible
collection cannot reach except through one function signature.

## Invariants

- `convert_config`, `validate_config`, `Format` and `FieldValidationError` are
  what
  [https://github.com/dg-i/ansible-collection-junos-config](https://github.com/dg-i/ansible-collection-junos-config)
  imports; removing or changing one
  is a declared break — enforced by `agent-ready stage griffe`.
- `validate_xml` needs a cleaned `junos-validated.xsd` that nothing in this
  package produces: a raw NETCONF dump does not compile — enforced by
  `tests/unit/validate/test_validator.py::TestValidateXmlNeedsACleanedXsd`.

## Precedent

- `junoscfg.convert_config` — the one entry point; a new format pair is a member
  of `_SUPPORTED_CONVERSIONS`, never a new public function. A new format is a
  `Format` member and a row of `junoscfg.convert.FORMAT_IMPLEMENTATIONS`.
