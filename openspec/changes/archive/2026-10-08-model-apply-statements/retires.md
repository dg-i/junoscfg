## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

`_fix_apply_statements` is added to the fix registry, raising the registered
count. No symbol is removed. `_strip_apply_groups`, `_inside_quotes` and the
`_validate_line` early return all stay: they are the bridge until the
artifacts carry the nodes, and removing them now would break set validation.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. Fifteen are added, eight seen to fail under mutation. Two
of them pin the `set_validator` bridge as still load-bearing, so that the day
the artifacts carry the nodes they fail together and point at the code to
delete.

## Docs

`docs/architecture/developer-guide.md` and `schema-internals.md` carry the
updated fix counts. `set_validator.py`'s module docstring names the bridge.
