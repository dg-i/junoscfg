## 1. Verification

- [x] 1.1 The delta's `Tests:` ids exist (`agent-ready reconcile` exit 0); no new test, a removal adds no behaviour (C4). Focused run: `pytest -q tests/corpus/test_set_corpus.py tests/unit/validate/test_grammar_generator.py::TestKeyedEntryTakesExactlyItsKeys tests/contract/test_every_door.py::TestAKeyedEntryTakesExactlyItsKeys tests/tooling`: 389 passed, 1 skipped, 5 xfailed, 18.2 s.
- [x] 1.2 Removal proved: `pytest --collect-only -q` 7,613 (base 7,621, less the 8 skipped jvd tests); `pytest --markers` lists no `jvd`; `pytest --jvd` exits 4, "unrecognized arguments: --jvd"; `git grep -ni jvd -- tests tools src .github docs README.md pyproject.toml ':!tests/data/device'` shows only device-evidence code (`test_device_renderings.py`, `import_device_captures.py`, the private `jvd_derived_data*` globs), historical docstrings, decision and review records.

## 2. Change

- [x] 2.1 Remove the `--jvd` option, its skip logic and the `jvd_corpus` fixture (`tests/conftest.py`), and the `jvd` marker (`pyproject.toml`).
- [x] 2.2 Remove `tests/corpus/test_jvd_corpus.py`, `tests/support/jvd_data.py` (`BROKEN_FILES`) and `.github/workflows/corpus.yml` (its only job ran the tier).
- [x] 2.3 Remove the tier from `docs/architecture/developer-guide.md` (tests/corpus row, CI nightly row, jvd tier row and paragraph), `docs/how-to/work-with-agents.md` (CI nightly row), `tests/CONTRACT.md` (corpus row).
- [x] 2.4 Towncrier fragment `changelog.d/+retire-jvd-tier.removal.md`; no version bump (merge-time versioning).

## 3. Review and evidence

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.
