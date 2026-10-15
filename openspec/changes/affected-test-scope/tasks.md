## 1. Verification

- [x] 1.1 Add focused narrowing, conservative fallback and repository-reader regressions;
  observe them failing on the previous selector (2d43f0c, c55f076, 4bc64ce).

## 2. Change

- [x] 2.1 Implement dependency- and reader-based selection and document the contracts.
- [x] 2.2 Adopt reviewed template v0.14.4 through the supported updater with the
  application CI preserved (bd6c8a8).

## 3. Review and evidence

- [x] 3.1 Pass cheap gates, then one canonical full checkpoint on a stable snapshot;
  record the command and checked HEAD here (`agent-ready check --set full`
  canonical command at e20ed29: every check passed, 175 s).
- [x] 3.2 Measure equivalent workflows including setup, hooks and failed attempts.
- [x] 3.3 Complete the risk-required fresh isolated review and resolve binding findings.
- [x] 3.4 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.5 Finalizer synchronizes the reviewed main specification, archives, bumps the
  patch version, integrates locally and tags without pushing.
