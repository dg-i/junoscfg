<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Effective stack and conflicts C1–C5 in `instruction-integrity.md`: no owner batch (C1); type `bug`
  with a MODIFIED delta (C2); `.github/workflows/corpus.yml` removed whole (C3); no failing-first
  test, the removal is proved as below (C4); the decision record stays as written (C5).
- Authority: `docs/decisions/2026-10-11-retire-jvd-from-per-change-verification.md` (accepted).
- No version bump on the branch (`docs/how-to/run-a-batch-of-changes.md`, Version and merge).

## Requirements

- `validation/set-command-validation`, MODIFIED "A keyed entry takes exactly its key values": the
  phase-5 stop clause names the device-captured set lines under `tests/data/device/` (covering
  lines of `grammar-corpus.json`; every line with `--device-grammar`) instead of "any corpus or
  `--jvd` line"; every scenario kept, one scenario "Lines a device printed" added for the test
  that already enforces it.

## Evidence

- Base 284715b: `pytest --collect-only -q` collects 7,621 tests, 8 of them in
  `tests/corpus/test_jvd_corpus.py`, all skipped without `--jvd`
  (`SKIPPED [8] ... needs --jvd`). `pytest --markers` lists `jvd`; `pytest --help` lists `--jvd`.
- `grep -rn "jvd_data\|test_jvd_corpus\|jvd_corpus\|JUNOSCFG_JVD"` over `tests/ tools/ src/
  .github/ docs/ README.md`: the only importers of `tests/support/jvd_data.py` are
  `tests/conftest.py` and `tests/corpus/test_jvd_corpus.py`. `tests/corpus/test_set_corpus.py`
  does not import it; its `jvd_derived_data*` glob reads the private device captures for
  `--device-grammar` and stays.
- `.github/workflows/corpus.yml` has one job, `jvd`; the template (`../agent-ready-python`) ships
  only `ci.yml` and `update.yml`, so a template refresh does not restore it.
- Coverage: `[tool.coverage.run] source_pkgs = ["junoscfg"]`; test-support code is not measured,
  and the removed tests never ran in the default suite. Floor 91.47 unaffected by construction.

## Non-goals

- `tests/data/device/` (its `jvd/` captures, LICENSE, NOTICE, sources, manifest entries) and
  every test over it; `tools/import_device_captures.py`, `tools/device_grammar_corpus.py`.
- Historical JVD figures in test docstrings, archived changes, reviews and decision records.
- No product code, CLI option or public name changes.

## Acceptance criteria

- The delta's `Tests:` ids all exist (`agent-ready reconcile` exit 0) and pass.
- Removal proved by: `pytest --collect-only -q` collects 7,613 (7,621 − 8) with no
  `test_jvd_corpus` node; `pytest --markers` lists no `jvd`; `pytest --jvd` exits with
  "unrecognized arguments: --jvd"; `grep -rni jvd` over `tests/ tools/ src/ .github/ docs/
  README.md pyproject.toml` (archives excluded) shows only device-evidence hits, historical
  docstrings and decision/review records.
- The one full checkpoint passes, coverage floor included.
- Independent challenge evidence: none required (economy, normal floor).

## Performance expectations

None, because no runtime code changes; the default suite loses only 8 skipped tests.
Before/after comparison over `tests/data/device/` is not needed: no runtime code, reader, writer,
schema, grammar or anonymizer path changes.

## Outstanding decisions

None, because the decision record and the owner's request settle what is removed.

## Execution and checkpoint

- Assurance preference: economy
- Risk floor: normal (yellow zone `schema`, no security/trust boundary, no migration, no declared
  break, no named public surface, one domain)
- Roles required: Builder; Finalizer (orchestrator). No Test/Challenge, no fresh Reviewer.
- Resume point: phase 4 (no new tests; reconcile green), then phase 5.

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established: base 284715b, commits cc5c121 (preflight), 53818cc (proposal); approved under
  the owner's unattended-run instruction of 2026-10-11.
