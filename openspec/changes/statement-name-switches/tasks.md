## 1. Tests

- [x] 1.1 `TestStatementNameNokeywordLeaf`: `disable` keys on the statement.
- [x] 1.2 The other three nokeyword populations are unchanged: an ordinary
  presence statement, `vlan-id` (`freeform-nk`) and a positional value.
- [x] 1.3 Seen to fail with the branch disabled; tree restored and rechecked.

## 2. Implementation

- [x] 2.1 `_is_statement_name`, reading the interned enum table through the
  cached `load_schema_tree()`.

## 3. Verification

- [x] 3.1 `{"disable": [null]}` round-trips to itself through structured.
- [x] 3.2 The structured rendering is byte-identical to the parent commit, so
  the oneliner oddity there is pre-existing.
- [x] 3.3 1,437 tests unchanged.
