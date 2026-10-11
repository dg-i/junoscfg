<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and organisation policy | as in `archive/2026-10-11-batch-process-rules/instruction-integrity.md` | 1 | yes | nothing pushed; synthetic values only |
| Runtime: Claude Code, `claude-opus-5-5` | tools, subagents | 2 | yes | none |
| Skill `agent-ready-change` v0.9.0, checks 0.15.11 | lanes and gates | 3 | yes | standard lane, type `refactor` (C1) |
| `AGENTS.md`, `pyproject.toml` `[tool.template.*]`, the how-to merged in v0.20.2 | house rules, batch and assurance tables | 4 | yes | the how-to names the lists this change mirrors |
| Owner task 2026-10-11 (rules 1 and 8, "add it to `mkdocs.yml` nav"), unattended, no questions | scope | 5 | yes | approved intent; same batch as `batch-process-rules` (its C1, C2) |
| Tests, observed behaviour | oracle | 7–8 | yes | no test reads `[tool.template.batch]` or `[tool.template.assurance]` (upstream checks source searched: no reader) |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Owner "a rule that needs executable configuration gets its own change of the proper type" versus checks 0.15.11 knowing no `maintenance` type | automatically resolved by precedence | Builder: type `refactor` with `skip_specs: true` (no behaviour, no requirement); template follow-up TF5 of the previous change | standard lane artefacts |
| C2 | Owner rule 8 "economy for a yellow-zone change ..., the high-risk floor otherwise" versus the table's keys | automatically resolved by precedence | as `batch-process-rules` C5: values stay `economy`, the floor is the skill's; only `record` changes, to the how-to's Assurance section | none |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy
- Standing record: `docs/how-to/run-a-batch-of-changes.md#assurance` as set by this change (before it: `pyproject.toml#tool.template.assurance`), matched key `default`
- Mandatory risk floor: not high (no red zone, break, trust boundary, public surface or cross-domain work). Unwaivable: the one full checkpoint, `fields`, `caps`, `lane`, OpenSpec validation, strict MkDocs. No Test/Challenge or Reviewer is required; review omission is recorded in `review.md`.

## Owner decision batch

None, because the owner asked for no questions and rules 1 and 8 name the values.

## Delta log

- Initial preflight: consistent.
