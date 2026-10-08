## 1. Tests

- [x] 1.1 `TestGroupHUfdGroupTransparent`: the wrapper is flagged, BGP's
  `group` is not, an empty tree reports nothing applied.
- [x] 1.2 `TestUplinkFailureDetectionGroupIsAList`: the entry with its links,
  and an exact set round trip. The first seen to fail on the old artifacts.

## 2. Implementation

- [x] 2.1 The fix, registered after `transparent-containers`.
- [x] 2.2 Artifacts regenerated from the 25.2R2 dump; structure tree and
  metadata changed, grammar and both schemas byte-identical.
- [x] 2.3 Fix counts in the developer guide and schema internals, 42 and
  Group H 8; `test_schema_data`'s docstring records which releases fire.
- [x] 2.4 Version 0.10.0 in four places; break declared for api and cli.
- [x] 2.5 From the review: D and G rows of the two fix tables corrected to
  14 and 6, the wrapper list in `json_output._native_groups` extended, a
  deactivate round-trip test added.

## 3. Verification

- [x] 3.1 Three devices: unplaced 7 to 1; set rejections 1 of 7,002, unchanged.
- [x] 3.2 23.2R2: the fix does not fire; the statement is absent there.
- [x] 3.3 jvd: 69,686 field-validate lines, the 521 value warnings and
  69,165 unplaced of 0.9.0 to the line; no file in the corpus carries the
  statement, so nothing there could move.
- [x] 3.4 Full suite 1,544 passed; pre-commit clean.
- [x] 3.5 A device capture of the subtree, supplied the same day in structured,
  JSON and XML: the JSON shape is junoscfg's; the device-truth tier passes on
  it as a fourth pair.
