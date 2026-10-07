## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired. `_source_text` was never a term, only an undeclared
attribute, and it is replaced by the declared `source_text`.

## Symbols

- `AnonymizeConfig._source_text`, which existed only as a dynamically attached
  attribute and never as a declared field.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. The characterization pin is rewritten, which is what a fix
does to the pin it invalidates.

## Docs

None. No document described `_source_text`.
