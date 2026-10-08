## 1. Tests

- [x] 1.1 An undeclared namespace prefix raises `ValueError`, not a traceback.
- [x] 1.2 The same element inside its `<rpc-reply>` still converts.
- [x] 1.3 Seen to fail with the catch removed; tree restored.

## 2. Implementation

- [x] 2.1 Catch `XMLSyntaxError` in `xml_to_yaml` and raise `ValueError`.

## 3. Verification

- [x] 3.1 The CLI reports `Error: Invalid XML: ...` where it printed a stack.
- [x] 3.2 A real `show configuration | display xml` capture from bordergw0206
  converts to the seven set lines the device itself would emit, `undocumented`
  wrapper stripped.
