## Why

`convert_config(path=...)` renders the complete configuration and reparses or
rescans that output with four format-specific filters. The dict IR already
contains the subtree and is the one conversion boundary.

## What Changes

- Add optional `path` and `relative` filtering to the unified pipeline.
- Filter the dict IR after validation/anonymization and before rendering.
- Make `convert_config()` pass its existing options into the pipeline.
- Preserve all exported format-specific filters during beta.

## Capabilities

### New Capabilities

- `conversion/path-filtering`: format-independent subtree selection at the IR boundary.

### Modified Capabilities

- None.

## Non-goals

- Removing or deprecating existing public filter helpers in this release.
- Changing path syntax, missing-path output, or relative rendering semantics.

## Impact

The public pipeline gains optional keyword arguments and the existing dict
filter becomes available through the display package door; existing calls and
`convert_config()` output remain compatible.
