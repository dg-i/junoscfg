<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Immutable platform constraints (harness, organisation policy DG-i) | every action; no credentials, personal or operator data in output | 1 | yes | tests use the `AGENTS.md` test-data values; nothing from `private_test_data/` enters a tracked file |
| Runtime (Claude Code, model `claude-opus-5-5`, unattended Builder subagent of the nightly orchestrator) | tool access; roles | 2 | partial: the Builder cannot be its own Test/Challenge or Reviewer | the orchestrator runs those roles as fresh agents at STOP-T and STOP-R (builder brief) |
| Invoked skill `agent-ready-change` (`SKILL.md`, phase files) | lanes, phases, roles, gates | 3 | yes | one task, so `batches.md` is not loaded; the lane follows the caps (C3) |
| Repository `AGENTS.md`, `ARCHITECTURE.md` (§8 layering), `tests/CONTRACT.md`, `src/junoscfg/convert/CONTRACT.md`, `tach.toml`, `tools/check_test_doors.py`, `pyproject.toml` `[tool.template.*]` | house rules, test placement and doors, stage `beta`, version rules | 4 | yes | fix at the owning layer (`convert/output/json_output.py`); contract tests reach only `junoscfg` and `junoscfg.cli` (C4); version and changelog move with the code (C3, C5) |
| Owner instructions: `private_test_data/makeover-work/builder-brief.md` and its intake answers of 2026-10-11, the mission `private_test_data/niglty_makeover_propmt.md`, the plan `private_test_data/makeover-ledger.md` row 2, the orchestrator's task message | IDs ARCH-C11 and ARCH-C15; assurance; integration; unattended approvals | 5 | yes | assurance `balanced`; branch `change/json-writer-pure`; fast-forward into local `master`, archive, tag, never push; ARCH-C15 stays INTENTIONAL, `_native_groups` keeps its output shape |
| Approved specifications and decisions: `openspec/specs/conversion/*` (no writer-purity requirement exists), `docs/decisions/2026-10-09-scope-compatibility-to-production-consumer.md` | what the conversion doors promise | 6 | yes | `junoscfg.convert.from_dict` is a secondary door below the `consumer` surface; the first writer requirement is written here |
| Acceptance and contract tests: `tests/contract/test_format_matrix.py` (row `groups` in `tests/support/shapes.py` pins the native list), `tests/unit/convert/test_convert_roundtrip.py` | the oracle | 7 | yes | extended, never weakened; no test asserts writer purity today |
| Observed behaviour on `d1e804e` (`private_test_data/makeover-work/c11_mutation.py`, synthetic values) | the four writers through `from_dict` | 8 | yes | the JSON writer rewrites the caller's IR: `ssh: true` and `ssh: {}` become `[null]`, `class: ["super-user"]` becomes `"super-user"`, a nested group entry is normalized in place; YAML, set and structured leave it unchanged. The set reader itself gives `ssh: {}`, so `to_dict` then `from_dict(..., "json")` changes the IR a caller holds |
| Device evidence: `tests/data/device/jvd/vmx-23.2R2-S7.5/mdr1_acx7509.json.gz`, `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.json.gz`, `tests/data/device/synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.json.gz` | native JSON `groups` | evidence, above the schema model | yes | the device writes `"groups": [ {"name": ...} ]` with no `group` wrapper, while `interfaces`, `routing-instances` and `vlans` keep theirs: ARCH-C15 is INTENTIONAL |
| Knowledge graph `graphify-out/` (`graphify query` on the writers and `_normalize_presence_flags`) | map only | below source | yes, noisy | confirmed in source: `from_dict` is called only by `pipeline_result` inside `src/`, as its last step |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Mission prompt "dedicated `codex/` branches" versus owner intake 8 "`change/<slug>`, not `codex/`" | automatically resolved by precedence | Builder: the later, explicit owner answer wins | branch `change/json-writer-pure` |
| C2 | Skill phase approvals by the owner versus an unattended run | automatically resolved by precedence | Builder: each approval reads "approved under the owner's unattended-run instruction of 2026-10-11" | phases progress without a relay |
| C3 | Plan row 2 and the task message "fix lane if it fits its caps" versus the fix lane's caps (two files, thirty lines outside the change folder, `agent-ready lane`) and `AGENTS.md` (bump in the same commit as the code: `pyproject.toml`, `src/junoscfg/__init__.py`, `uv.lock`) and the brief (a changelog fragment) | automatically resolved by precedence (the skill: "a fix that exceeds those caps is retyped `bug`") | Builder: type `bug`, standard lane, with a delta | at least six files outside the folder; phases 1 to 7 |
| C4 | Task message "prefer a writer-family contract law in `tests/contract/`, if the contract structure supports it" versus `tests/CONTRACT.md` and `tools/check_test_doors.py` (contract and corpus tests import only `junoscfg` and `junoscfg.cli`) | automatically resolved by precedence (the task's own condition) | Builder: the named surfaces never hand a writer an IR the caller owns (`pipeline_result` reads a fresh one), so the law cannot be stated through them; it lives at the owning door, `tests/unit/convert/test_convert_roundtrip.py`, as one test parametrised over every writer and over every catalogue source's IR (`tests/support/shapes.py`), plus the hand-built spellings | every writer is checked, not only JSON |
| C5 | Lane gate: any edit of `src/junoscfg/__init__.py` needs a `declared-break: consumer` entry, versus the brief's lesson "a declared break on `consumer`/`cli` takes a MINOR bump" | automatically resolved by precedence (`AGENTS.md`: a break on a named surface raises the minor, "everything else is a patch") | Builder: no behaviour of a named surface changes (`convert_config` builds its IR and `from_dict` is its last step), so the entry states that the file changes only `__version__` and that this is not a break; patch 0.16.1, as the `test-architecture` change recorded for its version-only edit (0.15.2 to 0.15.3) | version 0.16.1; the Reviewer may challenge it |
| C6 | Inventory sketch "one recursive function that returns a new tree instead of three in-place passes" versus the smallest fix that keeps one rule | not a source conflict; design choice recorded | Builder: the JSON writer copies the IR once on entry and normalizes its own copy; the three passes and `_native_groups` keep their output. Rewriting the passes is a refactor no requirement needs | smaller diff, same guarantee |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Owner-confirmed preference: balanced (owner intake answer 1, 2026-10-11)
- Mandatory risk floor: not high. One domain (`conversion`), yellow zones only (`conversion`; `surface` for the version string), no security or trust boundary, no migration, no declared break. Under `balanced`: the change is behavioural (`from_dict` no longer rewrites its input), so independent Test/Challenge after phase 4 (STOP-T); the zone is yellow, so a fresh Reviewer after phase 5 (STOP-R). Every acceptance test fails on the merge base; one full check before review; `agent-ready lane`, `fields`, `reconcile`; OpenSpec strict validation.

## Owner decision batch

None asked: the owner is asleep and the run is unattended. Intake answers 1–8 settle assurance, integration and challenges; C3–C5 are settled by repository rules.

## Delta log

<!-- Append later instructions or evidence and their consistency result. -->

- Initial preflight: consistent; C1–C6 resolved. Approved under the owner's unattended-run instruction of 2026-10-11.
