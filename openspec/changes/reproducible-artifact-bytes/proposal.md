## Why

`open_artifact_write` let gzip stamp the current time into every header, so
regenerating identical content produced different bytes. Every regeneration
was a diff in git, and a byte comparison of a rebuilt artifact could fail for
reasons nothing in the schema explains. The schema replacement that follows
this change rebuilds the artifacts and has to be able to diff them.

## What Changes

- The writer opens `gzip.GzipFile` with `mtime=0` behind a text wrapper.
  Identical content written to the same path now gives identical bytes; the
  decompressed text is unchanged, so every reader behaves as before.
- One regression test: the header's MTIME field is zero and the artifact
  reads back through `read_artifact_text`.
- The shipped artifacts are not rewritten. Their bytes change when they are
  next regenerated, which the next change does on purpose.

## Capabilities

### New Capabilities

None; the same writer, with a header that no longer carries the clock.

### Modified Capabilities

None; no requirement changes, so `.openspec.yaml` sets `skip_specs: true`.

## Non-goals

- Regenerating or replacing the shipped artifacts, or choosing their release.
- Reproducibility of what the generators emit beyond the gzip container.

## Impact

`src/junoscfg/display/constants.py`, one function, and one test in
`tests/test_artifact_resolution.py`. Fix lane; patch bump to 0.7.1. The
downstream Ansible collection reads artifacts and never writes them.
