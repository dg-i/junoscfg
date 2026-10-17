# junoscfg.input — contract

## Not for

Not format detection or parsing; `convert.input` chooses the parser.

## Invariants

- Comment stripping preserves quoted content — enforced by
  `tests/unit/input/test_input.py::TestRemoveComments::test_preserves_inline_content`.
- `find_non_json_value` walks no deeper than 64 levels and refuses a non-string key
  before what it holds, so a cycle, a deep alias chain or such a key is refused, never a
  crash; an alias bomb is expanded (decision 2026-10-15-configuration-input-is-trusted)
  — enforced by `tests/unit/input/test_input.py::TestFindNonJsonValue::test_a_value_past_64_levels_is_refused_at_its_path`
  and `tests/unit/input/test_input.py::TestFindNonJsonValue::test_without_scalars_a_key_that_is_not_a_string_is_refused`.
- Unsupported raw set commands are refused before normalization or IR construction
  with value-free physical-line diagnostics — enforced by
  `tests/unit/convert/test_set_commands.py::test_unsupported_commands_are_refused`.

## Precedent

- `normalize` is the raw set normalizer; structured text uses `display.SetConverter`.
- `find_unsupported_set_brackets`, `find_unsupported_set_commands` and `set_tokens`
  are the shared lexical boundaries consumed by raw set conversion and validation.
- `find_non_json_value` is the boundary yaml-new and JSON conversion and validation, the
  `xml` reader, and the `yaml` reader and validation (with `META_KEY_PREFIXES`) share
  (decision 2026-10-15-yaml-nests-at-most-64-levels).
- `iter_visible_set_lines` retains physical lines and content after leading comments.
- `InputError` carries `lineno` for refusals whose callers must withhold source text.
