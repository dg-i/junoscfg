## Why

The batch how-to merged in v0.20.2 names the serialized paths, the schema tier and the owner's
assurance preference, but `pyproject.toml` still carries the template's empty lists and a
placeholder record, and the page is not in the site navigation. The docs lane could not carry
either (`batch-process-rules` C1, C2).

## What Changes

- `[tool.template.batch] serialized-paths`: `xsd_fixes.py`, `grammar_generator.py`,
  `validate/data/**`, `tests/data/device/known-differences.json` (owner rule 1).
- `[tool.template.batch] expensive-tiers`: `schema`, over the parser and generator paths, command
  `uv run --locked pytest --schema tests/corpus/test_schema_data.py -q` (owner rule 3).
- `[tool.template.assurance] record` cites the how-to's Assurance section (owner rule 8); the
  values stay `economy`, the high-risk floor is the skill's.
- `mkdocs.yml` nav lists the how-to; the how-to says where `pyproject.toml` mirrors it.

## Capabilities

### New Capabilities

### Modified Capabilities

None: configuration and navigation, `skip_specs: true`.

## Non-goals

- No change to `max-builders` (3), zones or domains; no runtime code, test or behaviour.

## Impact

Read by the `agent-ready-change` workflow at phase 0 and by the batch Orchestrator; no check
reads these keys today. Strict MkDocs builds the page in the nav.
