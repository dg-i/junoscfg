# junoscfg.convert — contract

Interface: `__all__` in `__init__.py`, module entry and expose list in `tach.toml`.

## Not for

Not a place for a direct format-to-format shortcut. Every conversion goes
through the dict IR, and a second path for a pair that already has one is the
duplicate `ARCHITECTURE.md` section 1 calls a defect.

## Invariants

- Every supported pair round-trips through the IR without losing content —
  enforced by
  `tests/test_convert_consistency.py::TestJsonRoundTripConsistency::test_roundtrip_preserves_content`.
- XML input has no parser of its own; it bridges through `xml_to_yaml()` —
  enforced by `tests/test_integration.py::TestExampleRoundtrip::test_xml_to_set_high_match`.
- One configuration yields one IR whatever format it arrived in — enforced by
  `tests/test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr`.

## Precedent

- `junoscfg.convert.output.dict_walker.WalkOutput` — the strategy every new
  output format implements instead of walking the IR again.
- `junoscfg.input.find_unsupported_set_brackets` — the lower-layer lexical
  boundary raw set readers apply before constructing the IR.
