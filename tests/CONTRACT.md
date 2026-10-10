# tests — contract

Where a test goes, which door it uses, and what it asserts.

## Layers

| Directory | Holds | Imports from |
|---|---|---|
| `unit/<package>/` | one file per source module of `src/junoscfg/<package>/` (`cli/` for `cli.py`, `input/` for `input.py`) | any package door in `tach.toml` |
| `contract/` | a law every member of a family keeps — every reader, writer, anonymize rule, validation door — parametrised over a catalogue | `junoscfg`, `junoscfg.cli` |
| `corpus/` | evidence, strongest first: device captures, the set corpus, jvd (`--jvd`), schema dumps (`--schema`), goldens | `junoscfg`, `junoscfg.cli` |
| `tooling/` | CI, regeneration, generated documents | as needed |
| `support/` | helpers, paths and catalogues; no tests | any package door |

## Rules

- **Placement.** A test lives with the behaviour's owner. A law that holds for
  a whole family is one parametrised contract test and a catalogue row, never
  a copy per member.
- **A fix adds a row or a unit test at the owning layer**, never a class named
  after the change, the bug, a phase or a review round. Provenance (change id,
  device evidence such as `deactivate5.txt`, owner answer) goes in the
  docstring.
- **Names describe behaviour**: `TestAnInactiveLeafKeepsItsValue`,
  `test_a_numeric_list_type_is_rejected`.
- **Doors.** Import names from a package door, never a submodule or an
  underscore name, and reach no private attribute; `tools/check_test_doors.py`
  enforces it, and an exception there carries its reason.
- **Assert meaning**: the IR, accept or reject, a round trip to the same IR.
  Byte layout only where a requirement declares it (name-keyed lists).
- **Paths** come from `tests/support/paths.py`; never `__file__` arithmetic or
  the working directory.
- **Shipped artifacts** come from the session fixtures `bundled_tree`,
  `bundled_validator` and `bundled_set_validator` in `conftest.py`; minimal
  ones from `tests/support/artifacts.py`.
- **Strict xfail only**, with the reason naming the follow-up change.

## Which tests a change runs

A change under `src/junoscfg/<package>/` runs `tests/unit/<package>/` and
`tests/contract/`; the pre-commit hook selects exactly that. A change to
`tests/support/`, `conftest.py`, `src/junoscfg/__init__.py` or the artifacts
runs everything. The full set adds `corpus/`, `tooling/` and branch coverage.
