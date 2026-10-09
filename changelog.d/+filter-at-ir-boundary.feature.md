Apply conversion path filtering once at the shared dict IR boundary before
rendering, while preserving existing path and relative output semantics,
including relative paths that select a single leaf.
