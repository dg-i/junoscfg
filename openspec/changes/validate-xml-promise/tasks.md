## 1. Tests

- [x] 1.1 `test_schema_generate_produces_what_validate_xml_needs`: run
  `schema generate`, then `validate_xml` against that directory — a valid
  document passes and an invalid one is rejected with a schema error.
- [x] 1.2 Update the two `test_artifact_builder.py` assertions that pinned
  five artifacts.
- [x] 1.3 Rewrite the characterization class and the module docstring: the
  defect pin becomes a working-behaviour pin.

## 2. Implementation

- [x] 2.1 Write `junos-validated.xsd` in `build_from_netconf_dump`.
- [x] 2.2 Write it in `build_from_xsd` too; both are reachable.
- [x] 2.3 Update `src/junoscfg/CONTRACT.md` to state the real constraint
  instead of recording a defect.
