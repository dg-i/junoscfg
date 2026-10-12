# junoscfg.input — contract

## Not for

Not format detection or parsing; `convert.input` chooses the parser.

## Invariants

- Comment stripping preserves quoted content — enforced by
  `tests/unit/input/test_input.py::TestRemoveComments::test_preserves_inline_content`.
- Unsupported raw set commands are refused before normalization or IR construction
  with value-free physical-line diagnostics — enforced by
  `tests/unit/convert/test_set_commands.py::test_unsupported_commands_are_refused`.

## Precedent

- `normalize` is the raw set normalizer; structured text uses `display.SetConverter`.
- `find_unsupported_set_brackets` and `find_unsupported_set_commands` are the
  shared lexical boundaries consumed by raw set conversion and validation.
- `iter_visible_set_lines` retains physical lines and content after leading comments.
- `InputError` carries `lineno` for refusals whose callers must withhold source text.
