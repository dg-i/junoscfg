## 1. Verification

- [x] 1.1 Phase-4 acceptance tests written and failing before the change (177 failed at 6f8018f).
- [x] 1.2 Owner-approved rewrites (phase-4 question 1): the attributes-match, flat-entry and `fe` tests rewritten to the keyed form, intent kept.
- [x] 1.3 Owner question 3: the `o` digest pin replaced by a test of the rule (`o` where the dump flags `oneliner`, and on the filter lists the fix names).
- [x] 1.4 Owner question 4: `test_name_keyed_lists_keep_name` compares the generated schema by dict equality.
- [x] 1.5 Owner question 8: the grammar rejects a numeric `list-type`; seen failing before the grammar change.
- [x] 1.6 The proposal's identifier counts reproduced by a test on the dump.
- [x] 1.7 Device round 4 (owner-approved): R, S and T in `tests/data/captures/keyed-entries-route-filter.*` and the T tests; a key keyword goes either side of the positional values.

## 2. Change

- [x] 2.1 Parser keeps every element a sequence declares and records the key fields.
- [x] 2.2 Structure tree carries `k`; `fe`, `values-only`, `_v<n>` and `_fix_attributes_match_oneliner` retired; fix counts in the docs.
- [x] 2.3 Kernel `entry_keys()` (and `entry_key_names()`); `ENTRY_KEY_OVERRIDES`, `get_flat_entry_config`, `FLAT_ENTRY_ELEMENTS` removed and banned.
- [x] 2.4 Set reader, set and structured writer, field validator, schema generator, grammar generator, audit walker and fixture, anonymize walker, XML reader read `entry_keys()`.
- [x] 2.5 Artifacts regenerated with `--regen-schema`, committed separately.
- [x] 2.6 Docs: keyed-entries convention, validation guide, API page.
- [x] 2.7 Version 0.15.0 and the towncrier fragment.
- [x] 2.8 Full check, declared-break measurement, collection test suite.
  - Full check at 4305435: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` exit 0, "every check passed" (1838 passed, 93 skipped, 1 xfailed).
  - Declared break: 2,558 of 10,792 list-entry objects in the regenerated JSON schema carry no `name` property (0.14.0: 0 of 8,394).
  - Collection 347715a against this checkout: 33 passed.

## 3. Review and evidence

- [x] 3.1 Complete the fresh-session review and write `review.md`.
  - Re-review of the fix pass `fc22c57..HEAD` at d8717de, fresh session: see `review.md` "Phase-6 re-review"; every decision probed, one Low finding (11), no challenge open.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.

## 4. Fix pass on the phase-6 review (owner decisions)

- [x] 4.1 Challenge A: any `maxOccurs` but 1 is a list; a nokeyword leaf never overwrites a present, different value.
- [x] 4.2 Challenge B: keyword key fields read in either order, written in declared order; grammar agrees (device probe round 5).
- [x] 4.3 Challenge C: closed enum only for `k` key fields; a `name` key's enum is open.
- [x] 4.4 Finding 4: entries indexed by key tuple. `ma4_mx204.conf` (233,512 lines): 65.6 s at fc22c57, 4.5 s after; master's code 12.5 s on the same machine.
- [x] 4.5 Finding 5: an entry without a key field from JSON, YAML or XML is reported unplaced.
- [x] 4.6 Finding 6: a bare `apply-groups` is reported unplaced.
- [x] 4.7 Finding 7: `set system location dc-a` is a correct rejection (device probe round 5); the grammar rejects it again.
- [x] 4.8 Finding 8: `entry_keys()` for the `k` test; one `statement_children()` in the kernel.
- [x] 4.9 Finding 9: one enum rule for every leaf; spec, changelog and plumbing.
- [x] 4.10 Finding 10 and question 7: the migration sentence; the pre-review list in the developer guide.
- [x] 4.11 `apply-macro` takes one to three values in reader and grammar (owner decision, device probe round 5).
- [x] 4.12 Artifacts regenerated twice with `--regen-schema` (after the parser change, after the grammar change), each committed separately.
- [x] 4.13 Corpus comparison against the frozen master baseline (`review_tools.py corpus|grammar|compare`, tag `fix1`, at d274595 + 7f998e9):

```
master: {"files": 1538, "lines": 4947067, "failed": 35, "unplaced": 69768, "other_field_warnings": 521}
branch: {"files": 1538, "lines": 4947067, "failed": 35, "unplaced": 68172, "other_field_warnings": 329}
files with MORE unplaced than master: 2; fewer: 161
   more  0 -> 1  .../srv6_core_edge/configuration/snips/evo/interfaces/cpe-attachment.conf
   more  0 -> 1  .../srv6_core_edge/configuration/snips/junos/interfaces/cpe-attachment.conf
files whose set output differs from master: 75
grammar sample: newly rejected 0, newly accepted 2
    OK  set class-of-service schedulers s0 drop-profile-map loss-priority any protocol any drop-profile dp0
    OK  set class-of-service forwarding-classes class LOW queue-num 1
```

  - The two files with one more unplaced statement are jvd templates whose
    `esi { $ESI_BYTES; $ESI_MODE; }` gives two values for the single node's
    nokeyword `identifier`; master wrote `$ESI_MODE` over `$ESI_BYTES` without a
    word, the branch keeps the second whole and reports it (challenge A).
  - Set output differs in 75 files, by category: 31 `prefix-segment algorithm`
    and 9 `forwarding-classes class`, now lists, write one child per line where
    master kept the line unplaced as written; 25 `$TEMPLATE` values master kept
    unplaced and verbatim, now placed and quoted by `format_value`; 9 a
    `deactivate` on a keyed entry master dropped or wrote without its key; 4
    `then community add <name>`, where master lost the name; 2 the `esi` case
    above; 2 order only. Each loads as the same configuration or is a
    statement master lost.
  - Other field warnings 329 against 521: 241 false `Missing mandatory field`
    on master (`queue-num`, `drop-profile`, `index`, ... under nodes the reader
    could not place) are gone; 49 are new, every one on a `$TEMPLATE` or
    `<placeholder>` value now placed and validated.
  - `pytest --jvd tests/test_jvd_corpus.py`: 8 passed, `TestFieldWarningBudget` included.

- [x] 4.14 Full check at 8d623a1: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` exit 0, "every check passed" (1892 passed, 45 skipped, 1 xfailed).
  - Declared break re-measured on the regenerated JSON schema: 2,560 of 11,547 list-entry objects carry no `name` property (fc22c57: 2,558 of 10,792; 0.14.0: 0 of 8,394); the 755 more are the declarations the dump bounds by a number.
  - Collection 347715a against this checkout, throwaway virtualenv, clone unmodified: 33 passed.
