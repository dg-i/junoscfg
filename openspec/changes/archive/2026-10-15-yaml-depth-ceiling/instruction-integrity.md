## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime (Claude Code, Opus 5.5, offline) | Tools, filesystem | Highest | yes | Isolated worktree `/private/tmp/junoscfg-yaml-depth-ceiling`; no network, no device calls, no push |
| Organisation policy (DG-i) | All output | Highest | yes | Synthetic values only; no credentials or personal data in records |
| Owner rule 2026-10-15, as relayed in the Orchestrator's task brief | YAML safeguards, this batch | Owner (relayed) | yes | "I do not want to fix PyYAML problems; if this is a genuine junoscfg problem fix it, if not leave it. This applies to the yaml safeguards we have discussed as well." |
| Owner rulings 2026-10-15 on the alias-cycles review, as relayed in the same brief | yaml-new doors, legacy `yaml` input | Owner (relayed) | yes | SC-2 size bound removed (SC-C moot), the consequence documented: junoscfg assumes its YAML input is not hostile, a caller handling untrusted YAML bounds it first; SC-A replaced by a fixed 64-level ceiling on the expanded document at reader, writer and `validate_config`, refusal naming kind and path, stop and report if 64 does not cover the corpus with margin; cycle refusal kept; SC-B left, not backlogged; C5 legacy `yaml` input refuses a cycle and depth past 64 with the path, valid legacy output byte-identical, bomb expansion left; records, specs, changelog adjusted; break decision recorded |
| AGENTS.md, ARCHITECTURE.md | Repository | Repository | yes | Kernel door imports, equivalent-not-identical output, docs checklist, version rule, test data conventions, beta stage rules, 200-line ARCHITECTURE.md cap |
| agent-ready-change skill, batches.md and phases | Workflow | Skill | yes | First of two independent changes (batches.md: Task 2, relative selections, has another zone, outcome and proposal); standard lane, design phase, tests first, one full checkpoint, fresh Reviewer |
| docs/how-to/run-a-batch-of-changes.md, docs/how-to/verification-evidence.md | Evidence procedure | Repository | yes | Device and catalogue base-versus-head comparison, readiness declaration |
| src/junoscfg/input.CONTRACT.md, src/junoscfg/convert/CONTRACT.md, tests/CONTRACT.md, tach.toml | Modules, tests | Repository | yes | `find_non_json_value` stays the shared kernel boundary |
| openspec/specs/conversion/junos-json-yaml, validation/junos-json-yaml | Approved specs | Specs | yes | The alias requirement (two interim bounds) is what the rulings replace; "`yaml` SHALL keep its reader and writer unchanged" meets C5 |
| docs/decisions/2026-10-15-yaml-new-expands-aliases-within-a-bound.md | Decision record | Decisions | yes | Superseded by a new record; status `superseded`, `superseded-by` set |
| Archived review `openspec/changes/archive/2026-10-15-yaml-new-alias-cycles/review.md` (SC-2, SC-A, SC-B, SC-C, C5) | Evidence | Evidence | yes | The pending decisions this change closes |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Decision record 2026-10-15-yaml-new-expands-aliases-within-a-bound keeps denial-of-service protection; the relayed rulings remove the size bound | automatically resolved by precedence | Builder supersedes the record with a new one, not an appended note | One new record, the old one `superseded` |
| C2 | Spec "Each format name selects its implementation": `yaml` keeps its reader unchanged; the C5 ruling changes the `yaml` reader | automatically resolved by precedence | Builder modifies the requirement to except the cycle and depth refusal | Spec delta |
| C3 | C5 ruling says "legacy `yaml` input"; the owner rule fixes only genuine junoscfg problems. `yaml` validation (`validate_yaml`) has no junoscfg recursion: PyYAML loads, jsonschema judges (base probe: a cycle is an invalid result, no crash) | automatically resolved by precedence | Builder checks the `yaml` reader only (convert, audit, CLI); `yaml` validation unchanged | Recorded in spec and guide |
| C4 | Brief: worktree under `/private/tmp`, Builder merges `--no-ff` and archives on master; batch how-to says `../junoscfg-wt` and Orchestrator merges | automatically resolved by precedence | Builder | Location and finalisation order |
| C5 | Found at base, outside the rulings: the `yaml` reader raises `AttributeError` on a mapping key that is not a string (`_strip_meta_keys`, `k.startswith`), a crash in junoscfg's own code | owner decision required | Not acted on (the rulings name only cycle and depth); reported with a recommended default | None here |
| C6 | Found at base, outside the rulings: JSON input nested about 2,000 deep raises `RecursionError` in `_normalize_annotations` (junoscfg's own recursion); the yaml-new writer's part (about 500 deep, `input.py:visit`) is fixed here by the ceiling | owner decision required | Not acted on (not a YAML door); reported with a recommended default | None here |
| C7 | Device question C8 (QFX5120 25.2R2-S1.5 and `[null]` for `system services netconf ssh`) | owner decision required | Not ruled; not acted on | Reported |
| C8 | A later Orchestrator message asked for a repository-wide input-trust rule in ARCHITECTURE.md; recording it as an owner instruction was refused by the runtime's permission check | runtime/operator correction | Not acted on; left for the owner to confirm first-hand | ARCHITECTURE.md gets only the YAML facts the brief names |

## Assurance

- Standing preference: economy
- Standing record: `pyproject.toml` `[tool.template.assurance]`, record
  docs/how-to/run-a-batch-of-changes.md#assurance; key matched: `default` (economy).
- Required roles: Builder; independent Test/Challenge (fresh agent); fresh isolated
  Reviewer at least as capable as the Builder; Finalizer (Builder, bounded).
- Mandatory risk floor: high. Named surfaces (`consumer`: `convert_config`,
  `validate_config`; `cli`) change what they accept, in both directions; cross-domain
  (conversion and validation).

## Execution checkpoint

Base `adb6fb7b5b624765a494b8a1d535972d08ac265b` (master, v0.28.18). Standard lane, type
feature (design phase). Command: `uv run --locked --group dev --with griffe --with tach
--with towncrier --with vulture agent-ready check --set full --base adb6fb7`; physical
schema dumps copied into the worktree; `tools.schema_verification prepare` before it if the
schema tiers are selected. Evidence folder: `private_test_data/makeover-work/yaml-depth-ceiling/`.
Cadence: invitation pending; no new assessment. Integration: merge `--no-ff`, archive commit
with the version bump, VERIFICATION.md note, activation park, annotated tag; no push.

## Owner decision batch

None blocking: the relayed rulings cover SC-2, SC-A, SC-B, SC-C and C5; C5 to C8 above are
reported, not asked.

## Delta log

- Initial preflight: consistent after C1 to C8. Resume: phase 1 proposal.
