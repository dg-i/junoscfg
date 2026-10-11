## Why

Decision `2026-10-11-retire-jvd-from-per-change-verification` (accepted, owner request) retired the
JVD tier: the Juniper corpus clone and `--jvd` are no longer used for any change's verification or
any claim about output. Their code still ships in the test suite and a nightly CI job still runs it,
and a main spec still tells phase 5 to report `--jvd` lines. The decision assigns their removal to
this change, typed `bug` as the owner asked.

## What Changes

- Removes the `--jvd` pytest option, its skip logic and the `jvd_corpus` fixture
  (`tests/conftest.py`), and the `jvd` marker (`pyproject.toml`).
- Removes `tests/corpus/test_jvd_corpus.py` and `tests/support/jvd_data.py` with its
  `BROKEN_FILES` exception; nothing else imports them.
- Removes `.github/workflows/corpus.yml`: its only job ran the tier.
- Rewrites the stale documentation of the tier: developer guide (test layout, CI nightly row, the
  jvd opt-in tier and its paragraph), `docs/how-to/work-with-agents.md`, `tests/CONTRACT.md`.
- No override, fallback, parameter or environment read is added; `JUNOSCFG_JVD_PATH` goes with
  `jvd_data.py`, its only reader (searched: `grep -rn "JUNOSCFG_JVD\|jvd_data\|jvd_corpus"`).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `validation/set-command-validation`: "A keyed entry takes exactly its key values" names the
  device-captured set lines under `tests/data/device/` instead of `--jvd` as what phase 5 stops on.

## Non-goals

- The committed device evidence (`tests/data/device/`, its `jvd/` captures, licence, notice and
  manifest entries) and every test over it stay.
- Historical figures in test docstrings and archived changes that cite the JVD corpus stay.
- No product code, CLI option or public name changes; not a break on `consumer` or `cli`.

## Impact

Tests, CI and documentation only. The default suite is unchanged: the removed tests were skipped
without `--jvd`. Coverage measures `src/junoscfg` only, so the floor is unaffected.
