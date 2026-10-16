## 1. Intent

- [x] 1.1 Record bounded preflight and owner-approved intent.

## 2. Implementation

- [x] 2.1 Add the JSON probe source and teach the importer JSON sources and a capture awaiting the device.
- [x] 2.2 Document the probe and its capture in tests/data/device/README.md; prepare the changelog fragment and admission inventory.

## 3. Review and evidence

- [x] 3.1 Re-import byte-identical apart from the new source; simulated capture imports.
  Evidence: the importer, PRIVATE=private_test_data, TARGET=a scratch copy of master's
  tests/data/device: `diff -r` shows only `synthetic/sources/json-null-probes.json.gz`,
  byte-identical to the committed one, and prints `awaiting capture, skipped`. Against a
  scratch PRIVATE: awaiting keeps the source (rc 0); four or one rendering without a date
  stops with `set its date in CAPTURED` (rc 1); dated imports the four renderings with
  that date in the manifest (rc 0); dated without xml stops `missing ['xml']` (rc 1).
- [x] 3.2 Fresh lightweight review; resolve findings.
  Evidence: `review.md`, approve with corrections at a1b75ba; both findings resolved at
  219e5ff and 4eae44e and confirmed by the same Reviewer.
- [x] 3.3 Canonical full check; record command and HEAD.
  Evidence: the canonical command at 2d4d9780cc754658b39387fc10b09b866d297229, "every
  check passed", 351 s; suite 13496 passed, 22 xfailed, 37 skipped; schema-25.2 tiers
  selected by the new `.json.gz` under tests/data/device, after `tools.schema_verification
  prepare` with physical dumps. Earlier attempts stopped before any test: two ready
  changes (own-crash-fixes, device-validation) not yet in this worktree's inventory copy,
  capacity above max-builders, and a planned-path conflict on `.agent-ready/activation.json`
  (each branch must carry the shared copy); the parallel session parked both for this run.
  One run before the schema runtime was prepared passed the suite and failed the tiers.
- [ ] 3.4 Validate strictly, archive, bump the patch version, merge locally and tag without pushing.
