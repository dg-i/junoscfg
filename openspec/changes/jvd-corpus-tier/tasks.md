## 1. Tests

- [x] 1.1 `TestCorpusConverts`: the corpus is large enough to mean something, a
  conversion-rate floor, and every failure is a file that is not configuration.
- [x] 1.2 `TestFieldWarningBudget`, per thousand lines rather than a count.
- [x] 1.3 `TestShapesThatReachedARelease`, one guard per defect the corpus
  found.

## 2. Implementation

- [x] 2.1 `tests/jvd_data.py`: discovery, shallow clone, `JUNOSCFG_JVD_PATH`.
- [x] 2.2 `--jvd`, the `jvd` marker, skip-by-default and the session fixture.

## 3. Verification

- [x] 3.1 All seven pass against the real corpus in 202s.
- [x] 3.2 Each of the three regression guards was seen to fail with its fix
  reverted: the nokeyword enum escape, `ipaddr-or-interface`, and the
  either-order oneliner branch. The working tree was restored and checked.
- [x] 3.3 The default suite is unchanged: 1,437 passed, the jvd tests skipped.
