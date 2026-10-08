## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired, though `enable-disable` stops appearing in output.

## Symbols

No symbol is removed. `_is_statement_name` is added, private.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. `TestStatementNameNokeywordLeaf` adds four, covering the
switch, an ordinary presence statement, a `freeform-nk` leaf and a positional
one, so the three populations are pinned apart.

## Docs

None. No document described the JSON key chosen for a nokeyword leaf.
