## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

No symbol is removed. `_IP_OR_NAME_TYPES` is added, private.
`ipaddr-or-interface` moves out of `_IP_ANY_TYPES` into it.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired and none is added: the corpus that demonstrates this is
`github.com/Juniper/jvd`, which is not vendored here, and no committed fixture
exercises either shape. That gap is the reason the defect survived.

## Docs

None. No document described field-level enum or type handling.
