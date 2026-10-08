## 1. Tests

- [x] 1.1 The pair the bridge named went red on the new tree, as designed:
  `TestTheApplyGroupsStripperIsStillLoadBearing` (both) and the three in
  `TestTheApplyFixReachesARealGrammar`. Nothing else in 1,518 moved on the
  artifacts alone; removing the bridge then moved the corpus pin by four
  lines, `apply-groups` after a leaf value, recorded as correctly rejected.
- [x] 1.2 `TestTheShippedGrammarModelsTheApplyStatements` replaces them at the
  validator: the four statements at depth and at the top, a description that
  mentions them, and the bracket form pinned as the documented `brackets` limit.
- [x] 1.3 `TestTheBundledTreeCarriesTheApplyStatements` replaces the grammar
  substitute: the four root nodes carry `universal`, the fix has nothing left
  to add, and the shipped grammar takes and rejects what the substitute pinned.

## 2. Implementation

- [x] 2.1 `junoscfg schema generate` from the 25.2R2-S1.5 dump, 195 s; all
  five hashes changed, every gzip header time-free.
- [x] 2.2 The bridge removed from `set_validator.py`; docstring rewritten.
- [x] 2.3 Docs: validation.md, schema-internals.md, cli.md, ARCHITECTURE.md,
  settle-a-schema-question.md; two test docstrings.
- [x] 2.4 Version 0.8.0 in four places; break declared for api and cli.

## 3. Verification, re-taken on the installed set

- [x] 3.1 Three devices: 21 to 1 rejected, of 6,998 then 7,002 set lines; only
  `chassis dump-on-panic`. The review reproduced both figures on its own build.
- [x] 3.2 Device truth, `firewall family inet6`: 0 missing, 0 extra (was 1, 3);
  `policy-options` 57 of 57 both times.
- [x] 3.3 Corpus 10 of 116 rejected on the artifacts alone, the same ten; 14
  once the bridge went, the four it hid. jvd 1,500 of 1,535, 233 warnings,
  0.047 per 1k: unchanged. Grammar load 4.6 s. Artifacts 2.48 MB.
- [x] 3.4 Full suite green: 1,518 passed, 71 skipped, 2 xfailed; pre-commit, openspec
  validate and fields clean; `agent-ready check` fails only the branch-wide
  griffe and lane items that predate this change.
