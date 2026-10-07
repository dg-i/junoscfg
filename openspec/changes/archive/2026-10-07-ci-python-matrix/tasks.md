## 1. Tests

- [x] 1.1 No new unit tests: this change *is* test infrastructure. Verified by
  running the exact command the matrix job runs,
  `uv run --python X --with pytest --with lxml --no-dev pytest tests/ -q`, on
  the floor and the ceiling: 1397 passed on both.
- [x] 1.2 Verified the derivation against the real `pyproject.toml`: it emits
  `["3.10","3.11","3.12","3.13","3.14"]`.
- [x] 1.3 Verified the mismatch guard fires by simulating a floor raised to
  3.12 while the classifiers still start at 3.10.

## 2. Implementation

- [x] 2.1 Add the `versions` job: derive the matrix from the
  `Programming Language :: Python :: X.Y` classifiers, cross-check the lowest
  against the `requires-python` floor, fail on disagreement, emit JSON.
- [x] 2.2 Add the `tests` job: `fail-fast: false` across the derived matrix,
  installing the package, pytest and lxml only.
- [x] 2.3 Leave the `full` job on one interpreter; `agent-ready-checks`
  needs 3.11+ and the gates do not vary by interpreter.
- [x] 2.4 Give the mypy step an explicit `src tests` target. It had none, so it
  exited on an argparse usage error and reported nothing — invisible because
  the step is `continue-on-error`.
