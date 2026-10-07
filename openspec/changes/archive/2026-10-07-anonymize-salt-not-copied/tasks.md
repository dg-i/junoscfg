## 1. Tests

- [x] 1.1 `TestSaltIsNotCopied`: the salt is replaced for all three crypt
  formats, at the original length and in the crypt64 alphabet; `rounds=N`
  survives while the salt after it does not; the replacement is deterministic.
- [x] 1.2 Update the four tests that asserted `startswith("$6$abc$")` and
  friends. They were asserting the leak, so they now assert its absence —
  prefix kept, original salt absent, salt and body lengths preserved.

## 2. Implementation

- [x] 2.1 Add `_pseudo_salt()`: crypt64 characters derived from the same HMAC,
  at the original salt's length.
- [x] 2.2 Parse `rounds=N$` as a parameter before splitting off the salt, so
  the real salt is replaced rather than dropped.
- [x] 2.3 Pass the derived salt into `_make_crypt_hash` instead of the original.

## 3. Verification

- [x] 3.1 Full suite: 1400 passed.
- [x] 3.2 Confirmed the three formats emit a replaced salt of the right length
  and alphabet, and that `$5$rounds=5000$realsalt$` keeps the rounds field.
