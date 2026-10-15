## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime (Claude Code, Opus 5.5, offline) | Tools, filesystem | Highest | yes | Isolated worktree; no network, no device calls, no push |
| Organisation policy (DG-i) | All output | Highest | yes | Synthetic values only; no credentials or personal data in records |
| Owner ruling 2026-10-15 on PO-2 / SC-1, relayed by the Orchestrator | This change | Owner | yes | yaml-new input refuses cycles only: a mapping or list reached twice through an alias is expanded, a cyclic alias is refused with its path; consistently at every door using `junoscfg.input.find_non_json_value` (reader, writer, `validate_config`); keep denial-of-service protection with a refusal naming kind and path, never the value; test a cycle and an alias bomb; an unstated rule (a numeric limit) is chosen conservatively, recorded as a specification challenge with its interim action and reported as pending; update every record of the alias policy; changelog records loosening as additive |
| Owner ruling 2026-10-15 on PO-3 and PO-4 | docs/BACKLOG.md | Owner | yes | Backlog entries in the existing style with the archived review's evidence, placed inside one of the batch's changes |
| AGENTS.md, ARCHITECTURE.md | Repository | Repository | yes | Kernel door imports, equivalent-not-identical output, docs checklist, version rule, test data conventions |
| agent-ready-change skill, batches.md and phases | Workflow | Skill | yes | Second change of the batch, after relative-null-flags (merged `19e13c5`, v0.28.17); standard lane, design phase, tests first, one full checkpoint, fresh Reviewer |
| docs/how-to/run-a-batch-of-changes.md, docs/how-to/verification-evidence.md | Evidence procedure | Repository | yes | Device before/after comparison, synthetic adversarial rows, readiness declaration |
| src/junoscfg/input.CONTRACT.md, src/junoscfg/convert/CONTRACT.md, tests/CONTRACT.md, tach.toml | Modules, tests | Repository | yes | `find_non_json_value` is the shared kernel boundary; interface widening is a reviewed decision |
| openspec/specs/conversion/junos-json-yaml, validation/junos-json-yaml | Approved specs | Specs | yes | The interim rule (refuse a mapping or list reached through an alias) is what the ruling replaces |
| docs/decisions/2026-10-15-yaml-new-before-renaming-yaml.md | Decision record | Decisions | yes | yaml-new is the Junos JSON object in YAML; untouched in meaning |
| Archived review `openspec/changes/archive/2026-10-15-yaml-new-format/review.md` (R2, SC-1, PO-2 to PO-4) | Evidence | Evidence | yes | The interim, its linear-time property, and the backlog evidence |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | batches.md: separate changes for unrelated outcomes; owner: put the PO-3/PO-4 backlog entries inside one of the changes | automatically resolved by precedence | Builder; the entries ride in this change, which already edits the yaml-new records | One docs/BACKLOG.md edit, no behaviour |
| C2 | Owner ruling: expand shared blocks; the trust boundary needs a bound the owner did not state | specification/test disagreement | Builder; interim bound chosen conservatively from the existing linear-time property, recorded as SC-2 with Decision pending; reported | Safe, reversible, additive later |
| C3 | Owner: worktree under `/private/tmp`, Builder merges `--no-ff` and archives on master; batch how-to says `../junoscfg-wt` and Orchestrator merges | automatically resolved by precedence | Builder | Location and finalisation order |
| C4 | tach.toml: widening an interface is a reviewed human decision; the kernel's return type becomes a named tuple exported beside `find_non_json_value` | automatically resolved by precedence | Builder adds one exposed name (`NonJsonValue`), as yaml-new-format C7 did; the Reviewer scrutinises | One expose entry |
| C5 | Pre-existing: legacy `yaml` input recurses on a cycle (`_strip_meta_keys`) and expands an alias bomb through every writer | owner decision required | Out of the ruling (`yaml` is not a `find_non_json_value` door); reported with a recommended default, not acted on | None here |
| C6 | Device question C8 (QFX5120 25.2R2-S1.5 and `[null]` for `system services netconf ssh`) | owner decision required | Not ruled; not acted on | Reported |

## Assurance

- Standing preference: economy
- Standing record: `pyproject.toml` `[tool.template.assurance]`, record
  docs/how-to/run-a-batch-of-changes.md#assurance; keys matched: `default`, `trust-boundary`
  (economy).
- Required roles: Builder; independent Test/Challenge (fresh agent); fresh isolated
  Reviewer at least as capable as the Builder; Finalizer (Builder, bounded).
- Application policy: AGENTS.md Verification; synthetic adversarial rows for text input.
- Mandatory risk floor: high. Trust-boundary input (YAML text from users), cross-domain
  (conversion and validation), named surfaces (`consumer`: `convert_config`,
  `validate_config`; `cli`) accept more input.

## Execution checkpoint

Base `87e14cd79eb4e0bd9b69d9990f882fe1beacfa77` (master, v0.28.17). Standard lane, type
feature (design phase). Command: `uv run --locked --group dev --with griffe --with tach
--with towncrier --with vulture agent-ready check --set full --base 87e14cd`; physical
schema dumps in the worktree and `tools.schema_verification prepare` before it if the
schema tiers are selected. Cadence: invitation pending; no new assessment. Integration:
merge `--no-ff`, archive commit with patch bump, VERIFICATION.md note, activation park,
annotated tag; no push.

## Owner decision batch

None blocking: the owner ruled on PO-2 to PO-4 and said how to treat an unstated bound (C2);
C4 to C6 are reported, not asked.

## Delta log

- Initial preflight: consistent after C1 to C6. Resume: phase 1 proposal.
