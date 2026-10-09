## Why

The CLI reference repeats Click option declarations by hand, so every option
change requires a second edit and can leave documentation silently stale. The
published API site also exposes dozens of implementation-module pages even
though the repository promises imports only through package doors.

## What Changes

- Generate the command-and-option reference deterministically from the Click
  command tree and fail a test when the committed page is stale.
- Keep explanations and worked examples in the authored guide while moving the
  mechanically derivable reference to its own generated page.
- Publish API documentation only for the supported `junoscfg`,
  `junoscfg.display`, `junoscfg.validate`, `junoscfg.anonymize`, and
  `junoscfg.audit` package doors.
- Delete the now-unpublished internal-module API pages and update links that
  encouraged submodule imports.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- None. This change affects generated documentation and publication scope, not
  CLI or Python runtime behavior.

## Non-goals

- Do not change command names, options, defaults, help text, or exit behavior.
- Do not change any package-door exports.
- Do not replace the MkDocs stack; that remains governed by the existing
  time-bound decision.

## Impact

The documentation guide, API navigation, internal API pages, generator tooling,
and documentation freshness tests change. Runtime packages and dependencies do
not change.
