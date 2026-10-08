## 1. Tests

- [x] 1.1 Reproduce the blank-salt test's false failure by forcing a legitimate
  `secrets.token_hex` collision at the owning boundary.
- [x] 1.2 Replace the probabilistic assertion with a deterministic test that
  proves every blank salt invokes automatic generation and uses the returned salt.

## 2. Implementation

- [x] 2.1 Refresh CODEOWNERS and stage levers with the project-locked supported
  render commands, preserving junoscfg-owned Ruff policy.
- [x] 2.2 Document targeted implementation tests, measured tier costs, the
  pre-review/review-correction/final-checkpoint cadence, and local base behavior.
- [x] 2.3 Remove the governance job's duplicate application-suite run while
  retaining its dependency on the complete Python-version matrix.
- [x] 2.4 Bump the patch version and add the changelog fragment.
- [x] 2.5 Run cheap structural checks, focused tests, one authoritative full
  pre-review checkpoint, a fresh read-only review, correction checks, and a
  conditional final full checkpoint only for later runtime-relevant edits.
