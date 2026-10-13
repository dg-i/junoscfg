<!-- Maintained by the agent-ready template. Local edits can conflict with updates.
See docs/how-to/template-ownership.md before editing; review every update diff. -->

# Type stage-up

The owner decides to move the stage; this change executes the move. Its
proposal names the stage left and the stage entered, and a decision record
states what flipped; `[tool.template.stage]` states only what is.

## The gate half

Each is a single edit CI can fail, so each is done before the pull request:

- every toolbox trial entry confirmed into the approved list or removed;
- `towncrier check --compare-with origin/main` passing, with `changelog.d/`
  created and a fragment for this change, from beta on;
- one characterization test per named surface;
- a `version` field on every data and config surface;
- one `docs/how-to/` page per named surface, from beta on;
- for release: a CI matrix matching the declared matrix, a migration entry
  per named surface, the deprecations in flight derived from the decorator at
  the previous tag, and at least one page under each Diátaxis directory.

Then `uv run --locked --group dev agent-ready render levers`, which rewrites the lever blocks of
`pyproject.toml` for the new stage, and for beta `vulture src --make-whitelist
> .agent-ready/vulture-whitelist.py`, the dead-code baseline that growth is
measured against from then on.

## The advisory half

`checklist.md`, copied from `openspec/schemas/agent-ready/templates/`
because it is a stage-up's artefact alone and OpenSpec's `status` never lists
it, one line per item with the owner's answer, so the garden audits a file
rather than re-deriving a judgment: the exported surface
minimised from observed usage, as the brownfield expose derivation does, and
the deprecation policy stated. Every item is answered before the change
archives: `uv run --locked --group dev agent-ready fields` fails an unanswered one, and the archive step's
precondition holds here as for every change.

## Backwards

A stage moves backwards only through the gate's own escape hatch: a `stage-up`
change whose `.openspec.yaml` carries a declared-break entry for every named
surface,
which takes the red column, and whose decision record names what is withdrawn
and from whom. `uv run --locked --group dev agent-ready fields` fails a lowered name that arrives without
them. An area being replaced rather than demoted keeps its promise and leaves
the named surfaces, with `being-replaced` on its zone.

## Approval

The stage owners, through the CODEOWNERS rule on `pyproject.toml`, and the
red column where a break is declared.
