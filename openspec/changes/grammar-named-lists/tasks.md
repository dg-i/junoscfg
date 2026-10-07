## 1. Tests

- [x] 1.1 Turn `TestNamedListKeysSurviveRuleMerging` and
  `TestTransparentListChildrenAreSpliced` from pins into regression guards.
- [x] 1.2 `TestContainerMayBeSetBare`, both bare and with content.
- [x] 1.3 `TestListEntryTakesSiblingsOnOneLine`: `set ntp server X version 4
  prefer` is one command, so the list repeats its alternatives.
- [x] 1.4 `TestUnknownTokensInsideANamedList`: the known over-acceptance,
  `xfail(strict=True)`, with a passing control.

## 2. Implementation

- [x] 2.1 `_rule_name_for`, suffixing `__list`; no element name produces a
  doubled underscore in the bundled 24.4R0 or in any of the three synced
  dumps, 23.2R2, 23.4R2 and 25.2R2, so the suffix cannot collide.
- [x] 2.2 Drop `_RuleInfo.has_non_list` and the branch reading it.
- [x] 2.3 Emit a nokeyword container's rule without its keyword.
- [x] 2.4 Make a non-list container's content optional.

## 3. Verification

- [x] 3.1 Rebuilt the grammar from the bundled 24.4R0 structure tree: 4,379
  rules, 670 of them `__list`, loads in 25s.
- [x] 3.2 `examples/router1.set`: 61 of 61 lines accepted, from 12.
- [x] 3.3 A 113-command corpus taken from this repository's own tests, not from
  the fixture I wrote: 99 accepted, from 23.
- [x] 3.4 Nine commands that must fail: five rejected, four accepted. All four
  are the bare-`VALUE` over-acceptance pinned in 1.4.
