## Context

Three conversion-path layers currently write directly to stderr: field
validation in the pipeline, anonymization debug tracing in its walker, and
dropped-delete notes in the structured renderer. The existing string APIs and
CLI output must remain stable while ownership of those messages moves outward.

## Reuse ladder

| Candidate | Coverage | Gap | Maintenance signal, lookup date | Verdict |
|---|---|---|---|---|
| `FieldValidationResult` | Already carries structured field errors and warnings | Does not represent anonymization or renderer notes, and has no converted output | Repository-owned and heavily tested, checked 2026-10-09 | Reuse its data when constructing general diagnostics |
| Standard-library frozen dataclasses and callback protocols | Immutable results plus dependency-inverted message collection | Requires small repository types and optional sinks | Python standard library across supported versions, checked 2026-10-09 | Use |

## Decisions

- Define frozen `Diagnostic` and `ConversionResult` values in the conversion
  package, where the unified pipeline owns their lifecycle.
- Make `pipeline_result()` the implementation and keep `pipeline()` as a thin
  string-returning wrapper; mirror that shape at the top-level package door.
- Pass an optional diagnostic callback down to anonymization and output
  rendering so lower layers never import the conversion package or globalize
  capture state.
- Store source, severity, message, and optional path, with one renderer method
  that reproduces the existing terminal text.
- Have the CLI render returned diagnostics before converted stdout.

## Risks

- Debug diagnostics may contain original sensitive values, exactly as the old
  debug stderr did; they remain opt-in through anonymization debug level.
- Legacy library callers lose incidental stderr output by design and migrate
  to the structured-result APIs when they need it.
- Optional callback parameters are additive, but every package door and
  interface declaration must expose the new result APIs coherently.
