## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime (Claude Code, Opus 5.5, offline) | Tools, filesystem | Highest | yes | Isolated worktree; no network, no device calls, no push |
| Organisation policy (DG-i) | All output | Highest | yes | Synthetic values only; no credentials or personal data in records |
| Owner instruction 2026-10-15 via Orchestrator | YAML-JSON-001 with modification | Owner | yes | Add `yaml-new` beside unchanged `yaml`; prepare, not perform, the rename; unattended; local merge, archive, tag; no push |
| AGENTS.md, ARCHITECTURE.md | Repository | Repository | yes | One-IR rule, evidence hierarchy, doors, docs checklist, version rule |
| agent-ready-change skill and phases | Workflow | Skill | yes | Standard lane, tests first, full checkpoint, fresh Reviewer |
| docs/how-to/run-a-batch-of-changes.md | Evidence procedure | Repository | yes | Device-evidence checks, before/after comparison, PYTHONDONTWRITEBYTECODE |
| convert, src/junoscfg, validate, display CONTRACT.md; tests/CONTRACT.md | Modules, tests | Repository | yes | Writer purity, IR rules, catalogue rows, package doors |
| docs/BACKLOG.md YAML-JSON-001; openspec/specs/conversion/* | Approved specs, backlog | Specs | yes | Proposed direction; existing writer and format requirements unchanged |
| Device captures tests/data/device/ | Evidence | Evidence | yes | Empty-container spelling differs by device release (below) |

Unavailable: the production consumer repository (ansible-collection-junos-config) is not
checked out; its usage is taken from ARCHITECTURE.md section 3, not measured.

## Conflicts

| ID | Sources and contradiction | Classification | Safe action and owner | Effect |
|---|---|---|---|---|
| C1 | Batch how-to puts worktrees in ../junoscfg-wt; owner says /private/tmp | automatically resolved by precedence | Builder; /private/tmp/junoscfg-yaml-new-format, branch change/yaml-new-format | Location only |
| C2 | Backlog proposes new normalized `yaml` plus legacy `yaml-old`; owner keeps `yaml`, adds `yaml-new`, defers the rename | automatically resolved by precedence | Builder; additive format, rename prepared and documented | No break now |
| C3 | Backlog: retain YAML metadata cleanup and scalar leaf-list promotion; owner: yaml-new is the identical object to Junos JSON | automatically resolved by precedence | Builder; yaml-new reads as JSON reads; legacy `yaml` keeps both; migration via `-i yaml -e yaml-new` applies them once | Consumer effect recorded for the rename change |
| C4 | Batch how-to: Builders do not bump, archive on branch then fast-forward; owner: Builder merges --no-ff, archives and bumps on master (as 332523c) | automatically resolved by precedence | Builder | Finalisation order |
| C5 | Phase 1 needs a declared-break entry per touched named surface; the change is additive | automatically resolved by precedence | Builder; entries say "Not a break", as 2026-10-11-group-wildcards-pass did; AGENTS.md makes it a patch | Patch bump |
| C6 | convert/CONTRACT.md: "YAML and XML apply leaf-list normalization, JSON keeps its shapes" names YAML generically | repository/skill correction | Builder; contract names `yaml` and says `yaml-new` keeps JSON's shapes | Contract edit |
| C7 | tach.toml: widening an interface is a reviewed human decision; owner asks for one name-to-implementation table that the surface also reads | automatically resolved by precedence | Builder adds one exposed name; Reviewer scrutinises | One expose entry |
| C8 | JSON writer rewrites `{}` to `[null]`; the QFX5120 25.2R2-S1.5 capture spells 15 such statements `{}`, the vMX 23.2R2-S7.5 capture of the same source `[null]` | specification/test disagreement | Owner instruction: keep JSON behaviour for yaml-new (equivalence); record a path-scoped device question | No new device claim |

## Assurance

- Standing preference: economy (pyproject.toml `[tool.template.assurance]`, record
  docs/how-to/run-a-batch-of-changes.md#assurance).
- Mandatory risk floor: high. Named public surfaces `consumer` and `cli` change
  additively; cross-domain (conversion and validation). Zones conversion, schema
  (validator) and surface, all yellow; anonymize not touched.
- Required roles: Builder; independent Test/Challenge (fresh agent); fresh isolated
  Reviewer at least as capable as the Builder; Finalizer (Builder, bounded). SKILL.md Roles.

## Execution checkpoint

Base 332523c6aa9576930ee7afe35226d5e4bdd2930d (master, v0.28.15). Standard lane,
type feature. Command: `uv run --locked --group dev --with griffe --with tach
--with towncrier --with vulture agent-ready check --set full`; schema tiers only if
selected. Cadence: invitation already pending; no new assessment. Integration: merge
--no-ff into master, archive commit with patch bump, `uv lock`, VERIFICATION.md note,
activation park, annotated tag; no push.

## Owner decision batch

None blocking. Decisions taken from the owner instruction and safe defaults are in
proposal.md and design.md; the device question (C8) is recorded, not asked.

## Delta log

- Initial preflight: consistent after C1 to C8. Resume: phase 1 proposal.
