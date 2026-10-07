## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

None removed. `_make_crypt_hash` keeps its name and `_pseudo_field` is added,
both private.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

None retired. Four assertions that pinned the leak are rewritten to pin its
absence; the tests themselves remain.

## Docs

None. No document described the salt handling.
