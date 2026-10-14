# tests — contract

Where a test goes, which door it uses, and what it asserts.

## Layers

| Directory | Holds | Imports from |
|---|---|---|
| `unit/<package>/` | one file per source module of `src/junoscfg/<package>/` (`cli/` for `cli.py`, `input/` for `input.py`) | any package door in `tach.toml` |
| `contract/` | a law every member of a family keeps — every reader, writer, anonymize rule, validation door — parametrised over a catalogue | `junoscfg`, `junoscfg.cli` |
| `corpus/` | evidence, strongest first: device captures, the set corpus, schema dumps (`--schema`), goldens | `junoscfg`, `junoscfg.cli` |
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
- **Assert meaning**: the IR, accept or reject, a round trip to the same IR,
  and for set output the device's display set; never the byte layout.
- **Evidence ranks**: a device capture (`tests/data/device/`) outranks
  anything written by hand or by junoscfg; a disagreement is junoscfg's.
- **Paths** come from `tests/support/paths.py`; never `__file__` arithmetic or
  the working directory.
- **Shipped artifacts** come from the session fixtures `bundled_tree`,
  `bundled_validator` and `bundled_set_validator` in `conftest.py`; minimal
  ones from `tests/support/artifacts.py`.
- **Strict xfail only**, with the reason naming the follow-up change.

## Which tests a change runs

A change under `src/junoscfg/<package>/`, code or package data, runs its unit
tests, the unit tests of its transitive importers, and `tests/contract/`.
Existing tooling modules run their transitive test consumers across tools and all
tests, including imported test helpers. Consumers in shared support or root
fixtures run the full suite; nested fixtures run their directory. Unknown loaders
or malformed/unreadable dependency sources run the full suite. Deleted/unmapped
tools, tooling configuration, `tach.toml` and the pre-commit configuration run
`tests/tooling/`. Shared
`tests/data/`, `tests/support/`, `tests/conftest.py`, the package root,
shipped artifacts, `pyproject.toml` and the lock run the full default suite.
A changed test selects itself; a conftest or deleted test selects its nearest
existing containing test directory. Covered descendants are omitted from the
selection. The hook always invokes the selector, including deletion-only
commits, and lists a moved file's old path. A test reads any other repository
file through a constant path from `PROJECT_ROOT` (or a path constant from
`tests/support/paths.py`), never a working-directory path: that file, or a
directory named that way, then selects the module (only the module, when the read
is inside a test function). A computed path or the bare root outside
`tests/tooling/` makes the module a reader of every such file. Other configuration
also runs `tests/tooling/`; documents and change records nobody reads select no
tests. `tools/affected_tests.CONTRACT.md` has the exact rule. The full set adds
branch coverage.
