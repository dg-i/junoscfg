## 1. Verification

- [x] 1.1 Acceptance tests written before implementation and observed failing at `cb04f69`
  (105 failed plus one collection error, all for the intended reasons;
  `private_test_data/makeover-work/device-probe-fixes/red-run.txt`): the sanitized probe record
  and its corpus tests, the verb rule, the shared walk, every-door verb rows, ancestor tags,
  the relative note, per-value notes, the probe's undocumented rows.
- [x] 1.2 Independent Test/Challenge (high risk floor): M1, M2, S1 to S8, N1 to N10 and S-1 to
  S-5 dispositioned in `review.md`; the additions written and observed failing at `94e28f6`
  (151 failed; `red-run-2.txt`): every probe record sanitized and its values synthetic,
  relative text against the untagged configuration, per-value and anonymized notes, the
  undocumented rows of groups and their negatives, the S4 walk rows, the set reader's refusal
  of a list keyword, the literal keywords, commit-check warnings, the alias giving no note.

## 2. Change

- [x] 2.1 Kernel: `junoscfg.input.set_tokens` and `set_token_value` (moved from the set
  reader); `junoscfg.display.meta_target` and `read_entry_key`, the read-only walk of what a
  verb line names (a homogeneous list whole, another list's keyword refused); the path filter
  keeps the annotations along an absolute path.
- [x] 2.2 Conversion: the set reader places a tag by the walk and refuses a list's bare
  keyword and a leaf's value with an error naming them; `Below` drops a tag at or above a
  relative path, every writer notes it by one text (`tags_above` for json, yaml-new and
  yaml); the walker notes per-value leaf-list tags; the set writer takes a diagnostic sink;
  each writer's note source is named after it.
- [x] 2.3 Validation and schema: `SetValidator` judges a verb line by the walk and the tree
  beside its grammar, and names several statements on one line unsupported; the grammar
  writes `=`, `+` and `-` as keywords; five `_UNDOCUMENTED` rows; artifacts regenerated with
  `--regen-schema` from the 25.2R2 dump (44 fixes, grammar compile unchanged at 9.5 s); the
  widened one-line grammar measured (12,416 containers, +27 % grammar, +2.2 s compile) and
  not taken (owner rule 2026-10-17).
- [x] 2.4 Records and docs: ARCHITECTURE.md section 8 rule and decision
  2026-10-17-set-input-is-a-device-export; the unsupported list in `docs/guide/conversion.md`;
  `docs/guide/validation.md`; contracts; BACKLOG entries closed, narrowed or added
  (WHOLE-LIST-TAGS-001); `grammar-corpus.json` regenerated (no rejection);
  `expected-findings.json` class `mandatory-commit-refuses`; changelog fragments; the
  main-spec test ids of the two renamed tests (their MODIFIED text lands at phase 7).
- [x] 2.5 Evidence: `tools/compare_device_outputs.py` over the 96 capture conversions: 0 of 96
  differ (`base.json`, `head.json`); unit, contract, corpus and tooling suites green.

- [x] 2.6 Review round 1 (Merge after fixes) fixes: B1 `system dump-on-panic` a flag, one IR
  from every reader, with the every-reader probe law; B3 records say conversion reads one-line
  statements; A1 `family` tags refused by `-v` and dropped with a note by set output; A2, A5 to
  A8 record corrections; A3 measurement provenance; A4 the relative comment note, device
  questions in BACKLOG DEVICE-EVIDENCE; S-6 owner ruling recorded; artifacts regenerated.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it. Fresh Reviewer (coordinator-dispatched): Merge after fixes on `16a1fe9` (B1 to B3, A1 to A8), Merge on `a2e63dd` (R2-A1 recorded, R2-A2 to BACKLOG JSON-NUMBER-IR-001); review.md.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head. Base `ec62908ecdb5b9d624ed085392b9eafdb1338bdf`, head `8cf02f963c4a39ac6ff1d4cee488c8df6d3bb9ba`.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits. Main specs applied at `a385689` (validate --strict and --specs pass); merge, archive with v0.28.26 and the tag follow.
