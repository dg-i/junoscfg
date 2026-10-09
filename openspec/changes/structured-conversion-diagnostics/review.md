## Findings

1. **The new lower-layer diagnostic sinks were absent from their public
   docstrings.** `from_dict()` and `anonymize()` accept caller-owned sinks, but
   generated API documentation did not explain ownership or rendering.
   **Resolved:** both package-door docstrings now document the optional sink.

## Already provided

- Acceptance tests prove both legacy package doors still return strings and
  both opt-in doors return the same immutable result shape.
- Library and CLI calls exercise the same dropped-delete event, proving stderr
  is silent in-process and the CLI retains its previous wording.
- An anonymization debug case independently proves sensitive debug events use
  the returned diagnostic channel instead of process stderr.
- The locked full checkpoint passed 1,622 tests with 18 skipped.

## Specification challenges

None.

## Review prompts

- Configuration and anonymization values are caller-controlled. Diagnostics
  retain the old debug content but cross no new boundary; only the caller can
  choose to render them.
- Strict validation still raises, non-strict conversion still returns output,
  and missing filtered paths retain any diagnostics accumulated beforehand.
- The shared blind spot was checking the new top-level APIs without checking
  documentation of the callback seam used by lower layers; generated API docs
  now cover it.
- `pipeline_result()` is the only conversion implementation. The string API is
  a wrapper, and callbacks are transport seams rather than alternate capture
  implementations or global state.
- The test counts reproduce the recorded checkpoint. The stated CLI stability
  is pinned by existing CLI tests plus the new identical-wording assertion.

## Verdict

Ready to merge after the documentation correction and fast gate. No runtime
behavior changed after the recorded full checkpoint.
