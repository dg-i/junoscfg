## 1. Verification

- [x] 1.1 Run XML/YAML conversion, IR parity, and malformed-XML tests before
  implementation.
- [x] 1.2 Confirm the public XML-to-YAML output and XML-to-IR value types are
  pinned independently.

## 2. Change

- [ ] 2.1 Extract the existing XML walker result into a private helper exposed
  through the display package door.
- [ ] 2.2 Make XML input consume that dict directly and update its contract and
  architecture documentation.
- [ ] 2.3 Add the changelog fragment and run focused tests.
- [ ] 2.4 Run the locked full repository check.

## 3. Review and evidence

- [ ] 3.1 Complete the fresh-session review and write `review.md`.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
