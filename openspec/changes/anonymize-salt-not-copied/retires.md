## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

None removed. `_make_crypt_hash` keeps its name; `_pseudo_salt` is added.

## Dependencies

None.

## Requirements

None; `skip_specs: true`.

## Tests and fixtures

None retired. Four assertions that pinned the leak are rewritten to pin its
absence; the tests themselves remain.

## Docs

None. No document described the salt handling.
