<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and organisation policy | every action: no credentials, personal data or de-anonymised values | 1 | yes | documents only; nothing pushed, no external system contacted |
| Runtime: Claude Code, model `claude-opus-5-5`, the coordinator session the owner instructed directly | tool access | 2 | yes | Builder and Finalizer in one session; a fresh Reviewer subagent |
| Skill `agent-ready-change` (`SKILL.md`, docs lane) and `agent-ready-checks` lane gate | lanes, phases, gates | 3 | yes | docs lane: `skip_specs: true`, `docs-plan.md`, document suffixes only |
| `AGENTS.md`, `ARCHITECTURE.md` (200-line cap), `pyproject.toml` `[tool.template.*]` | house rules, stage (beta), versioning | 4 | yes | worktree `/private/tmp/junoscfg-input-trust-rule`; patch bump at merge; tag, no push |
| Owner instruction, 2026-10-15, first-hand in the coordinator session | scope, approval | 5 | yes | "whoever writes malicious Juniper config can do far worse than wrecking the junoscfg process, so this must be trusted input; therefore I do not want to fix yaml bugs here. Please put this in the ARCHITECTURE.MD as well and continue with this decision"; and, asked whether the coordinator should add the rule itself after the yaml-depth-ceiling Builder merged, "ok" |
| Observed: `master` 037e012 (v0.28.20) clean apart from untracked `.agents/skills/openspec-*` (left alone, owner undecided) | tree state | 8 | yes | no live change edits these files |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | The yaml-depth-ceiling Builder refused to record the rule (its conflict C8): a security-relaxing rule relayed by an agent message had no first-hand owner confirmation | resolved by the owner | the owner gave the rule first-hand in this session and approved this session adding it | the rule is recorded here, not relayed |
| C2 | `src/junoscfg/input.py` docstring and `tests/unit/input/test_input.py` docstring say "YAML input is not hostile" versus the docs-lane gate, which refuses `.py` | automatically resolved by precedence (lane gate) | Builder: left as is; the narrower YAML wording stays true under the rule | no code edit |
| C3 | `openspec/specs/conversion/junos-json-yaml/spec.md` says YAML "is not hostile" versus `skip_specs: true` | automatically resolved by precedence | Builder: left; the spec's sentence is a case of the rule | no spec edit |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy (`pyproject.toml#tool.template.assurance`, keys `default` and `trust-boundary`)
- Zone: none owns these paths; recorded as `surface`
- Mandatory risk floor: high, because the change records a trust-boundary policy. A fresh isolated Reviewer at least as capable as the Builder reviews it; for a docs-only change the Reviewer's challenge of every claim against the owner's words and the code stands in for Test/Challenge, since there is no behaviour to test
- Unwaivable: one full checkpoint, `agent-ready fields`, `caps`, `lane`, `openspec validate --strict`, markdownlint, strict MkDocs build

## Owner decision batch

None: the owner's instruction is the approved intent.

## Delta log

- Preflight, 2026-10-15: docs lane; C1–C3 resolved. Intent, docs plan and freeze approved under the owner's first-hand instruction of 2026-10-15. Resume point: phase 5.
