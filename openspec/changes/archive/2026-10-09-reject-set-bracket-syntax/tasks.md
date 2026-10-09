## 1. Tests

- [x] 1.1 Add reviewed conversion, validation, API, CLI, corpus, structured-input,
  and version acceptance tests; confirm the new rejection behavior is red.

## 2. Implementation

- [x] 2.1 Add one quote- and comment-aware raw-set bracket detector to the
  shared input kernel and expose it through the package door.
- [x] 2.2 Enforce the detector before raw set conversion can construct an IR.
- [x] 2.3 Convert detector findings into normal per-line `SetValidator` errors.
- [x] 2.4 Update interface metadata and contracts for the shared dependency.
- [x] 2.5 Document the user contract and accepted deferred-design decision.
- [x] 2.6 Apply the required 0.13.0 minor-version bump in all three locations.
- [x] 2.7 Run the focused grammar and conversion tests until green.
- [x] 2.8 Run the locked full `agent-ready` check once before review.
