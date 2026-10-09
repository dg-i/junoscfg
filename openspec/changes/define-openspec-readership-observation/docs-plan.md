## Reader and task

- Reader: repository maintainer evaluating OpenSpec maintenance cost.
- Task: observe one complete release cohort, audit evidence coverage by
  artifact type, and decide whether any type is eligible for a deletion
  proposal without interpreting missing telemetry as zero readership.

## Authoritative sources

| Claim | Source |
|---|---|
| Metrics are captured against immutable base and head commits before archive. | `.agents/skills/agent-ready-change/phases/7-archive.md` |
| Runtime logs require an operator binding and are never discovered automatically. | `docs/how-to/capture-change-metrics.md` |
| Native runtime formats cannot establish complete file-read coverage. | `docs/how-to/capture-change-metrics.md` |
| Machine evidence records status, value, reason, provenance, and SHA pair. | Archived `openspec/changes/archive/*/metrics.json` files |
| A release boundary is a reachable `v{version}` Git tag. | `AGENTS.md` version-management rules |
| The roadmap requires one release of observation before a deletion proposal. | `docs/roadmaps/2026-10-08-junoscfg-simplification.md` |

## Affected documents

- `docs/how-to/capture-change-metrics.md`: existing operational home for
  capture inputs, provenance, limitations, and evidence interpretation.
- `docs/roadmaps/2026-10-08-junoscfg-simplification.md`: authoritative status
  of the seven simplification tasks and the release-long hold point.

## Documentation QA

- Links and anchors: run `uv run --locked --group docs mkdocs build --strict`;
  expect a successful build with no broken links.
- Commands and examples: execute the documented tag-boundary and `jq`
  coverage commands against this repository; expect valid output and no JSON
  parse errors.
- Referenced paths: verify every repository path in the new section with
  `test -e`; expect all static paths to exist.
- Terminology: inspect for consistent use of `measured`, `unmeasured`,
  `observation cohort`, `baseline tag`, `closing tag`, and `deletion
  candidate`; never use `unread` as a synonym for `unmeasured`.
- Diátaxis placement: keep operational steps in the metrics how-to and only
  status/hold-point text in the roadmap.
- Rendered output: inspect the built metrics how-to navigation and headings;
  expect the protocol to be reachable under Working with Agents and tables and
  code blocks to render without warnings.
