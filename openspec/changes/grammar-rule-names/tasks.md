## 1. Tests

- [x] 1.1 `TestRuleNamesAreValidLark`: names are lowercased, `start` does not
  collide, and every generated name matches Lark's rule pattern.
- [x] 1.2 `TestBundledGrammarCompiles`, marked `xfail(strict=True)` so it
  reports the moment regeneration fixes it.

## 2. Implementation

- [x] 2.1 Lowercase in `_safe_rule_name`.
- [x] 2.2 Add `_RESERVED_RULE_NAMES` and map `start` to `start_element`.

## 3. Verification

- [x] 3.1 Regenerated the grammar from a real 23.2R2 dump: 706 KiB, and
  `lark.Lark(...)` loads it. Before the fix the same input failed on
  `jnx_tel_RE_local_interfaces_stats`.
- [x] 3.2 Confirmed the defect predates onboarding by loading the grammar from
  commit a2edd22: it fails identically.
