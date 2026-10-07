## 1. Tests

- [x] 1.1 Rewrite `TestXmlAndStructuredInputDisagreeOnTheIr` as
  `TestXmlAndStructuredInputAgreeOnTheIr`, asserting the two IRs are equal for
  the whole fixture, plus the alias and the string typing individually.
- [x] 1.2 Update the three `test_to_yaml.py` assertions that expected ints.
- [x] 1.3 Keep the assertion that set output from both paths still agrees, so
  the thing that masked the defect stays pinned.

## 2. Implementation

- [x] 2.1 Wrap `local_name` in `resolve_key_alias` on the XML path.
- [x] 2.2 `_coerce_value` returns the text unchanged.
- [x] 2.3 Record the parity rule in `ARCHITECTURE.md` section 8 and in
  `src/junoscfg/convert/CONTRACT.md`.
