# junoscfg.anonymize — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Not reversible without the mapping. `apply_revert` needs the file
`export_mapping` wrote; nothing here can undo an anonymization from the output
alone.

## Invariants

- The same input and the same salt produce the same output, every run —
  enforced by `tests/test_anonymize/test_ip_rule.py::TestIpRuleTransform::test_deterministic_with_same_salt`
  and the matching `test_deterministic` in each other rule's tests.
- `networks=["auto"]` silently does nothing through the Python API, because
  `_source_text` is attached only by the CLI. Pinned, not fixed, by
  `tests/test_characterization.py::TestNetworksAutoNoOpsThroughThePythonApi`.

## Precedent

- `junoscfg.anonymize.rules.ip.IpRule` — the rule shape: `matches()` then
  `transform()`, both taking the shared signature.
