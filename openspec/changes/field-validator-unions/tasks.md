## 1. Tests

- [x] 1.1 The existing suite is the regression guard: 1,437 tests pass
  unchanged, so neither escape loosened a case a test pins.

## 2. Implementation

- [x] 2.1 A `nokeyword` leaf's enum is advisory.
- [x] 2.2 `ipaddr-or-interface` accepts either form.

## 3. Verification

- [x] 3.1 Juniper's jvd corpus, 1,535 files and 4,945,686 lines: field warnings
  53,326 to 217, conversion unchanged at 1,500 files. The 35 that do not
  convert are documentation carrying prose, section labels such as `AN3:`, and
  the `show configuration | no-more` prompt — not Junos configuration.
- [x] 3.2 Of the 217 remaining, 199 name a `$VARIABLE` placeholder.
- [x] 3.3 The three real device configurations tested this session convert with
  zero field warnings, from many.
