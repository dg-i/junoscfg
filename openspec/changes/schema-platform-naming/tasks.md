## 1. Tests

- [x] 1.1 A recorded platform reaches the name.
- [x] 1.2 The marker is consumed, so it cannot leak to the next dump.
- [x] 1.3 Without a marker the release stands alone.
- [x] 1.4 An explicit argument beats the marker.

## 2. Implementation

- [x] 2.1 `read_platform`, taking the last word so `Model: vmx` pipes in.
- [x] 2.2 `promote_staged(platform=...)`, falling back to the marker.

## 3. Verification

- [x] 3.1 Established that the platform is not in the dump: every one names
  every platform, and `unified-edge` is 1,771 nodes in both a vMX's 23.2R2 and
  the bundled 24.4R0 while `virtual-chassis` is 63 in all three.
- [x] 3.2 `23.2R2-S7.5-vmx.xsd` renamed from the `show version` model.
- [x] 3.3 1,451 tests pass; the four new ones run without `--schema`.
