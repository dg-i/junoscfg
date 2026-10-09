## Reader and task

- Reader: contributors deciding where a change belongs and which architectural
  constraints it must preserve.
- Task: distinguish durable layering and packaging constraints from transient
  repository measurements without being sent to stale figures.

## Authoritative sources

| Claim | Source |
|---|---|
| Generated schema artifacts ship with the package in compressed form | `src/junoscfg/validate/data/*.gz`, `[tool.hatch.build.targets.wheel]` in `pyproject.toml` |
| The import graph is acyclic and follows the declared layer direction | `tach.toml`, verified by `uv run --locked --group dev tach check` |
| `display` is the shared kernel rather than presentation-only code | imports in `.agent-ready/codemap/map.json` after `agent-ready codemap build`, plus `src/junoscfg/display/CONTRACT.md` |
| Exact file sizes, line counts, and edge counts are transient measurements | the checked-in source and artifact files; no repository record reproduces the old import-edge count |

## Affected documents

- `ARCHITECTURE.md`: the authoritative home for system-wide trade-offs,
  layering, generated-artifact policy, and dependency direction.

## Documentation QA

- Links and anchors: run the repository Markdown hook through the full
  `agent-ready` checkpoint; expect no dead fragment or Markdown failure.
- Commands and examples: inspect the diff; expect no user command or example to
  be added or changed.
- Referenced paths: run `test -d src/junoscfg/validate/data` and
  `uv run --locked --group dev agent-ready codemap check`; expect the artifact
  directory and fresh index pointers to resolve.
- Terminology: compare the edited layering paragraph with `AGENTS.md`,
  `tach.toml`, and `src/junoscfg/display/CONTRACT.md`; expect “shared kernel,”
  zone names, and dependency direction to agree.
- Diátaxis placement: inspect the diff; expect explanatory architectural
  rationale to remain in `ARCHITECTURE.md`, not move into a how-to or contract.
- Rendered output: run the repository Markdown hook through the full
  `agent-ready` checkpoint and inspect the edited sections as rendered
  Markdown; expect intact lists, code fences, links, and headings.
