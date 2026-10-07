## 1. Tests

- [x] 1.1 `tests/test_set_corpus.py` records four fewer rejections; the pinned
  list is what proves nothing else regressed.
- [x] 1.2 The nine adversarial commands are still rejected.

## 2. Implementation

- [x] 2.1 Splice a child the parent is transparent over.
- [x] 2.2 Strip `apply-flags` and `apply-macro` as well as `apply-groups`.
- [x] 2.3 A named list's entry name is `QUOTED_OR_VALUE`.
- [x] 2.4 Rebuild `src/junoscfg/validate/data/junos-set.lark`.

## 3. Verification

- [x] 3.1 The collection's example playbook runs under ansible-core 2.21.5 and
  renders `router1.conf` and `router2.conf`; both now validate clean, from
  seven errors each.
- [x] 3.2 Corpus 100 to 104 of 116; nine of nine adversarial rejected;
  4.2s compile, 4 ms a line.
- [x] 3.3 The collection's 33 tests pass and its four filters produce output
  byte-identical to junoscfg 0.6.8, before any of this session's work.
