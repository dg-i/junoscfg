## 1. Tests

- [x] 1.1 `tests/test_regen_source.py`: the train from the metadata; the
  shipped train chosen over a newer dump; none, two, a prefix-only match and
  an empty directory are errors; the override wins and must exist; a legacy
  dump beside the directory counts. Seen to fail at import first.

- [x] 1.2 From the review: a service train counts, an empty override is an
  error, an override without a release is an error, a lookup renames
  nothing, a directory named like a dump is ignored, the error names each
  dump with its release, and a real `--collect-only` run stops with exit 7.

## 2. Implementation

- [x] 2.1 `shipped_release_train`, `XsdSourceError`, `find_xsd_source` with
  explicit inputs so the tests are hermetic; `pytest_sessionstart` passes the
  environment in, regenerates before collection, exits 7 on an error.
- [x] 2.2 Help text, `AGENTS.md` step 2 at 100 lines, developer guide,
  private README.
- [x] 2.3 Version 0.10.1 in four places.

## 3. Verification

- [x] 3.1 A missing override: nothing collected, exit 7, the message names it.
- [x] 3.2 The real default resolves to the 25.2R2 QFX5120 dump.
- [x] 3.3 `pytest --regen-schema` end to end, 220 s: 1,555 passed, the 25.2R2
  dump picked unnamed, every artifact byte-identical but the metadata's
  timestamp, which was restored.
- [x] 3.4 Full suite 1,562 passed; the end-to-end run repeated through the
  session-start hook after the review.
