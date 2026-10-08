# junoscfg.input — contract

Interface: `__all__` in `input.py`, module entry and expose list in `tach.toml`.

## Not for

Not format detection and not parsing. `normalize()` strips comments and
line-continuations so a parser sees clean text; deciding which parser runs is
`convert.input`'s job.

## Invariants

- Comment stripping never removes content inside a quoted value — enforced by
  `tests/test_input.py::TestRemoveComments::test_preserves_inline_content`.

## Precedent

- `junoscfg.input.normalize` — the single entry point every input path calls
  before parsing.
- `junoscfg.input.find_unsupported_set_brackets` — the shared lexical boundary
  for raw set conversion and validation; callers consume its line-numbered
  diagnostics instead of scanning independently.
