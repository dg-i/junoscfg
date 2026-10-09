## Findings

1. **Relative leaf filtering regressed for set and structured output.** Moving
   selection ahead of rendering means a leaf path passes a scalar to the
   renderer. The set and structured renderers assumed a dict and raised
   `AttributeError`, while the pre-change API returned `set <value>` and an
   empty structured result respectively. **Resolved:** the output door and
   renderers now accept selected scalar subtrees, and a four-format regression
   test pins the existing results.
2. **The new pipeline arguments and output wrapping switch were undocumented.**
   The public docstrings did not describe `path`, `relative`, `wrap`, or the
   relative-without-path error. **Resolved:** the affected API docstrings and
   developer guide now describe those behaviors.

## Already provided

- The acceptance test spies on the renderer and proves wrapped and relative
  subtrees are selected before rendering, while missing paths bypass it.
- The recorded locked full checkpoint passed every repository gate and the
  complete application suite before the review correction.

## Specification challenges

None. Both corrections preserve the approved path-filtering behavior.

## Review prompts

- Path text is caller-controlled but only navigates an already parsed dict; it
  does not introduce a filesystem, command, or template trust boundary.
- A valid relative leaf path was the incompatible input missed by the original
  acceptance test; it is now covered across all four output formats.
- The shared blind spot was testing only container subtrees. Direct comparison
  with the pre-change branch exposed the scalar-rendering regression.
- No second filtering path was added to the conversion pipeline. The exported
  legacy filters remain compatibility utilities for direct callers only.

## Verdict

Ready after correction, subject to the focused and locked full gates being
rerun because runtime code and tests changed after the previous checkpoint.
