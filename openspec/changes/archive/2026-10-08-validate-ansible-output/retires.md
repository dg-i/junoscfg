## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

No symbol is removed. `_child_reference` gains a keyword-only `spliced`
argument, defaulted, and stays private.

## Dependencies

No dependency is added or released by this change.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. Four commands move out of the expected-rejection list in
`tests/test_set_corpus.py`, and the `groups` and `freeform` cause codes go with
them.

## Docs

`docs/guide/validation.md` drops `set groups` and `apply-macro` from the list of
known over-rejections and updates the accept count.
