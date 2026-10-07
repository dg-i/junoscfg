## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

No symbol is removed. `find_artifact`, `read_artifact_text` and
`open_artifact_write` are added to the kernel and exposed.

## Dependencies

No dependency is added: `gzip` is in the standard library.

## Requirements

No requirement is retired; this change sets `skip_specs: true`.

## Tests and fixtures

No test is retired. Eight are added, two seen to fail under mutation. Four
existing tests named artifacts by their plain filename and now resolve them,
which is what they should always have done; two characterization pins that
asserted the written filenames are rewritten rather than deleted, as a pin that
records changed behaviour should be.

## Docs

`docs/guide/cli.md` describes `--artifacts` as a validation option, which has
been too narrow since v0.6.31; corrected here along with a note that generated
artifacts are compressed.
