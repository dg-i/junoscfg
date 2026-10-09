## Purpose

Select one configuration subtree consistently before rendering it into any
supported output format.

## ADDED Requirements

### Requirement: Filter the shared IR before rendering

WHEN a caller supplies a non-empty configuration path to the unified conversion
pipeline THEN the system SHALL select that path from the dict IR before invoking
the target renderer, return an empty string when it is absent, and preserve the
existing relative and path-wrapped output semantics.

Tests: `tests/test_convert_api.py::TestPathFiltering::test_pipeline_filters_ir_before_rendering`

#### Scenario: Wrapped subtree

- **WHEN** `path="system"` and `relative=False`
- **THEN** the renderer receives only the IR hierarchy rooted at `system`

#### Scenario: Relative subtree

- **WHEN** `path="system"` and `relative=True`
- **THEN** the renderer receives the contents below `system`

#### Scenario: Missing subtree

- **WHEN** the requested path is absent
- **THEN** conversion returns an empty string without invoking the renderer
