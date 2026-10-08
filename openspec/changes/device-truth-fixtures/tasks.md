## 1. Tests

- [x] 1.1 `test_junoscfg_renders_what_the_device_renders`, one case per pair:
  3 passed on the shipped artifacts; 1 failed on the previous 24.4R0 set, on
  `hop-limit`, which is the test doing its job, with element paths only in
  the message.
- [x] 1.2 A list entry is told by its `name` or `address`: two terms against
  one, and a `then` moved between terms, both differ. Probed, not pinned.

## 2. Implementation

- [x] 2.1 The two pairs extracted from the capture into
  `private_test_data/captures/`, secrets stripped, each headed by its path;
  one synthetic pair under `tests/data/captures/` in the documentation ranges.
- [x] 2.2 Discovery over both directories; a missing directory is no error.
- [x] 2.3 `private_test_data/README.md` and the developer guide's tier table.
- [x] 2.4 Version 0.9.1 in four places.

## 3. Verification

- [x] 3.1 Full suite green with the pairs present, 1,539 passed; the private
  cases skipped with the pairs moved aside, the synthetic one still running.
- [x] 3.2 Pre-commit, openspec validate and fields clean.
