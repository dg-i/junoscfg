## 1. Tests

- [x] 1.1 `xsd_fixes` declares the four statements on the root, each flagged
  `universal`, with the right node kinds.
- [x] 1.2 `artifact_builder` round-trips the `u` flag through
  `_BOOL_FLAG_KEYS`, in both directions.
- [x] 1.3 `grammar_generator` emits one `universal_statement` rule and every
  rule references it.
- [x] 1.4 `schema_generator` names them per container.
- [x] 1.5 End-to-end on the real 427,978-node tree, without shipping it.
- [x] 1.6 Two tests assert the `set_validator` bridge is still load-bearing;
  they flip together the day the artifacts carry the nodes.
- [x] 1.7 Eight of the fifteen seen to fail under mutation.

## 2. Implementation

- [x] 2.1 `_fix_apply_statements`, Group D.
- [x] 2.2 `u` in `_BOOL_FLAG_KEYS`, one entry each side thanks to the
  symmetric writer landed in v0.6.28.
- [x] 2.3 `universal_statement` in the grammar generator.
- [x] 2.4 One `patternProperties` entry per container in the JSON schema.
- [x] 2.5 `set_validator`'s docstring names the bridge and what retires it.

## 3. Verification

- [x] 3.1 The four statements appear in no NETCONF XSD — not as element, ref
  or substring — in 21.4R0, 23.2R2, 23.4R2 or 25.2R2.
- [x] 3.2 Regenerating from 23.2R2-S7.5 was measured and rejected. jvd
  conversion unchanged at 1,500 of 1,535 files and 4,945,686 lines, but field
  warnings went 217 to 3,254 (0.044 to 0.658 per 1k), over the 0.5 budget
  `test_jvd_corpus.py` enforces. 3,001 of the 3,037 extra are one enum:
  `evpn ip-prefix-routes encapsulation` lacks `srv6` before 24.4, and the
  corpus writes `encapsulation srv6` 22,304 times across 7 files.
- [x] 3.3 The same regeneration also opened 6 new real-device rejections
  (`protocols uplink-failure-detection`, absent from a vMX dump) while closing
  20 (`hop-limit`, `analyzer`). Net 21 to 7, at the cost above.
- [x] 3.4 Declaring once rather than per-container: +242 bytes and +98 KB
  against +24 MB on the structure tree and +0.6 MB on the grammar.
- [x] 3.5 Nothing ships: `src/junoscfg/validate/data/` is untouched and still
  24.4R0. All four measurements unchanged.
