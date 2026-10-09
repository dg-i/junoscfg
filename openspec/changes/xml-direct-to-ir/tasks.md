## 1. Verification

- [x] 1.1 Run XML/YAML conversion, IR parity, and malformed-XML tests before
  implementation.
- [x] 1.2 Confirm the public XML-to-YAML output and XML-to-IR value types are
  pinned independently.

## 2. Change

- [x] 2.1 Extract the existing XML walker result into a supported helper exposed
  through the display package door.
- [x] 2.2 Make XML input consume that dict directly, normalize leaf-lists at the
  common input boundary, and update its contract and architecture documentation.
- [x] 2.3 Add the changelog fragment and run focused tests, including the
  device-derived private XML capture and the production consumer contract.

  Evidence after review correction: 186 focused repository tests passed; the
  JSON regression proves schema loading is bypassed and scalar shapes are
  retained, while the private XML capture kept
  canonical IR SHA-256
  `0c8b63bb622e3722820c613f2d66c3a6051dd6c9621b524de12a575028098a89`;
  the collection's 33 tests passed against this checkout.
- [x] 2.4 Run the locked full repository check.

  Passed at `23bae69` with 1,631 tests passed and 72 skipped using
  `uv run --locked --group dev --with griffe --with tach --with towncrier
  --with vulture agent-ready check --set full --base
  codex/implement-simplification-roadmap`.

## 3. Review and evidence

- [x] 3.1 Complete the fresh-session review and write `review.md`.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
