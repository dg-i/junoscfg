<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Historical effective instruction stack (source 5ae3ad7; superseded below)

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and organisation policy (DG-i) | every action: no credentials, personal or operator data in output | 1 | yes | tracked text holds the `AGENTS.md` test-data values only; nothing from `private_test_data/` enters a tracked file; nothing is pushed, no external system contacted |
| Runtime: Claude Code, model `claude-opus-5-5`, unattended Builder subagent of the batch orchestrator (row #16, lane C, wave 2) | tool access, roles | 2 | partial: the Builder cannot be its own Test/Challenge or Reviewer | the orchestrator runs those roles; this Builder stops at STOP-T and STOP-R |
| Skill `agent-ready-change` (`SKILL.md`, `batches.md`, phase files) | lanes, phases, roles, gates | 3 | yes | standard lane, type `bug` |
| `AGENTS.md`, `ARCHITECTURE.md`, `tests/CONTRACT.md`, `src/junoscfg/convert/CONTRACT.md`, `pyproject.toml` `[tool.template.*]`, `docs/how-to/run-a-batch-of-changes.md` | house rules, zones, domains, stage `beta`, worktree, device-evidence checks, versioning | 4 | yes | worktree `../junoscfg-wt/diagnostics-load-vs-commit`, branch `change/diagnostics-load-vs-commit`; the device-evidence checks and the before/after comparison apply (paths under `convert/`); no version bump on the branch; no serialized path |
| Owner instructions, 2026-10-11: `private_test_data/makeover-work/builder-brief.md` (intake answers), `builder-kickoff.md`, the mission `private_test_data/niglty_makeover_propmt.md` (device-ledger bullet "`radius-server` without `secret` is valid at load time but mandatory at commit; diagnostics must state the actual boundary"; open issue 16 "Reconcile strict field validation with load-time versus commit-time Junos requirements") and the ledger row #16 (DEV-V3, NEW-B7 = NEW-C2, OPEN-16) | scope, approvals, no questions | 5 | yes | every approval reads "approved under the owner's unattended-run instruction of 2026-10-11" |
| Orchestrator task for row #16 | lane, overlap rule | 5 (relays the owner) | yes | lane C; live Builders #7, #8, #9: their `files.txt` are read before editing, and an overlap stops the change |
| Approved specifications: `openspec/specs/conversion/diagnostics` ("WHEN conversion produces field-validation messages ... the system SHALL carry them as diagnostics") | what a conversion reports | 6 | yes | today's gating contradicts it (C2) |
| Guides: `docs/guide/cli.md` "Field Validation" ("It runs by default during conversion, printing warnings to stderr"); `docs/guide/validation.md` table row "Mandatory fields ... Reported as warnings" | documented behaviour | 6 | yes | the documented promise this change makes true |
| Tests: `tests/unit/convert/test_field_validator.py::TestTheExampleConfigurationValidates` (pin `RADIUS_SECRET` = "Missing mandatory field 'secret'") | the oracle | 7 | yes | the pin moves to the reworded message (C3), never weakened |
| Observed on `40173ba`: `private_test_data/makeover-work/c-open16{,b,c}.out` and `diagnostics-load-vs-commit/probe_mandatory.out` | behaviour | 8 | yes | a conversion reports the mandatory warning only when an unrelated error exists; the message does not name the commit boundary |
| Knowledge graph `graphify-out/` | map only | below source | yes | confirmed in source: `convert/__init__.py::_convert` extends diagnostics with `(*result.errors, *result.warnings)` inside `if not result.valid`; `convert/field_validator.py::_check_mandatory` is the one producer of field warnings |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Skill phase approvals and "ask once" versus the owner's unattended-run instruction (no questions, owner away) | automatically resolved by precedence | Builder: the ledger row, the mission text and repository evidence are the approved intent; each approval is recorded as given under the unattended-run instruction | no owner batch |
| C2 | Spec `conversion/diagnostics` and `docs/guide/cli.md` (field-validation warnings are carried as diagnostics and printed) versus observed behaviour (warnings reach the diagnostics only when `result.valid` is false) | specification/test disagreement, resolved by precedence (the approved spec and guide outrank observed behaviour) | Builder: the code is the defect (NEW-B7 = NEW-C2); warnings are always carried; `strict` raises on errors only, as its docstring and the CLI help already say | code change; the spec gains an explicit requirement and scenario so the gating cannot return |
| C3 | DEV-V3 and the mission ("diagnostics must state the actual boundary") versus the pinned message "Missing mandatory field 'secret'" | automatically resolved by precedence (owner instruction outranks a test pin) | Builder: reword the message to name the boundary; the pin follows the new wording; severity stays warning (device evidence: the vMX and QFX5120 loaded `access profile PROF-1 radius-server ...` without `secret`, `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.set.gz`, vMX 23.2R2-S7.5, and `tests/data/device/synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.set.gz`, QFX5120 25.2R2-S1.5) | test pin updated with the code, not loosened |
| C4 | OPEN-16 inventory lead "an optional `--commit-check`/strict level may escalate" versus the batch rule "fix at the owning layer" and stage `beta` (a new option is a feature on the `cli` surface) | automatically resolved by precedence | Builder: no new option; `strict` keeps raising on errors only (load-time verdicts) and never on a commit-time warning; recorded as a non-goal | proposal non-goal |
| C5 | OPEN-16 note "set validation has no field validation at all" (`validate_set`, `validate_config`, `junoscfg convert -v`) versus `ARCHITECTURE.md` and `docs/guide/validation.md`, which give schema validation (grammar, JSON Schema) and field validation separate doors | automatically resolved by precedence | Builder: unchanged; the validation guide already names field validation as the conversion's (and `validate_ir`'s) check. Adding field validation to `validate_config` would change a door the production consumer imports | proposal non-goal |
| C6 | Live Builders #7 (`docs/architecture/developer-guide.md`, `tests/contract/test_every_message.py`), #8 (S lane) and #9 versus the paths this change needs | consistent | Builder: the developer guide's sentence on mandatory warnings (line 520) is left alone; `files.txt` written after phase 2 and checked against every live `files.txt` | no overlap planned |
| C7 | Domain declaration: every edited source file lies under `src/junoscfg/convert/` (domain `conversion`), and `convert/field_validator.py` is also a path of domain `validation`; the change alters what field validation says about device acceptance (validation's purpose) and what a conversion reports (conversion's) | automatically resolved by precedence (the skill's high-risk floor; where the floor's reach is uncertain the stronger reading is taken, as the preference can add assurance and cannot remove it) | Builder: `domains: [conversion, validation]`; the change is cross-domain, so the high-risk floor applies | STOP-T after phase 4, STOP-R after phase 5 |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy
- Standing record: `pyproject.toml#tool.template.assurance` (`record = "docs/how-to/run-a-batch-of-changes.md#assurance"`), matched key `default`; `zones` is empty; no declared break (`declared-break` entries state "Not a break"), no trust boundary
- Zone: `conversion` (yellow): `src/junoscfg/convert/__init__.py`, `src/junoscfg/convert/field_validator.py`
- Mandatory risk floor: high, because the change is cross-domain (C7). Required whatever the preference: independent Test/Challenge after phase 4 (STOP-T) and a fresh Reviewer at least as capable as the Builder after phase 5 (STOP-R); every acceptance test fails on the merge base; one full check before review; `agent-ready fields`, `caps`, `lane`, `reconcile`; `openspec validate --strict`

## Owner decision batch

None, because the owner asked for no questions (C1) and the evidence settles both halves: the device loads the configuration without the mandatory statement (captures cited in C3), and the approved spec and guide already promise that warnings are reported (C2).

## Delta log

<!-- Append later instructions or evidence and their consistency result. -->

- Initial preflight, 2026-10-11: consistent; C1–C7 resolved. Approved under the owner's unattended-run instruction of 2026-10-11. Resume point: phase 1.
- Phase 1, 2026-10-11: proposal and lane fields approved under the owner's unattended-run instruction of 2026-10-11. `openspec validate` waits for the phase-2 delta (a bug carries one). Resume point: phase 2.
- Phase 4, 2026-10-11: acceptance tests written (15 fail on the base `40173ba` for the reason the delta names, none passes there); test data moved to a capture line not touched by DEV-3 (evidence-freeze delta log). The high-risk floor requires independent Test/Challenge: STOP-T. Approved under the owner's unattended-run instruction of 2026-10-11.

## Current migration preflight — 2026-10-12

- Current base: `13b2cc73fd42fb44d1c69121b73d9b9fa61677cd`; historical base `40173ba8ec6c0664ea3590b5a3b14786fcf22629` and STOP-T `5ae3ad7d8074cf40a1c8feaf0129c075f59e0950` preserved in the verified private bundle and logs. Rebase changed planning/tests only; product implementation has not started.
- Runtime: Codex continuous Builder under root orchestration, isolated diagnostics worktree; independent Test/Challenge and fresh Reviewer remain required. Historical provider/model entries above do not describe this run.
- Installed checks `0.16.1` revision `6e833710f7b0df04e8612defaf34ed861d124908`, template `0.10.2` revision `3064189f740d3ff6cd2d54c537b1fc245f755005`; Strategy A `strategy-a/1` enabled. Local `.agent-ready/activation.json` parses equal to common Git operator inventory; checkpoint `73a0097848033ddf79804d3fecead7108c8cf63e`. Branch/change stay PARKED until root admission. No shared inventory edit by Builder.
- Owner qualified-warning ruling approves exactly `may be required at commit; the configuration loads without it`. Automatically resolved by precedence: supersedes unconditional historical wording, changes wording assertions only; severity/strict/output/non-goals remain approved. Root owns admission and material rulings.
- Owner schema schedule `OWNER-SCHEMA-SCHEDULE-2026-10-12` supersedes canonical full/per-change real-schema requirements for this makeover. Automatically resolved by precedence: do not launch canonical full or real schemas now. Supported substitute before review is fast plus exact configured ordinary command `uv run --locked pytest tests/ -q --cov --cov-report=term:skip-covered`; assertions/floor remain. Only root executes final selected physical 25.2R2-S1.5 schema at makeover end.
- Owner authorizes unattended local migration and completion; no phase questions, network, push, publish, device contact or Claude control. Sibling/common-Git/cache writes use sandbox escalation. Main/shared inventory/version/tag/archive belong to root. No new dependency, override, fallback or environment read.
- Standing assurance `economy` from `docs/how-to/run-a-batch-of-changes.md#assurance`; cross-domain conversion/validation unchanged high-risk floor. No material unresolved owner decision.
- Contracts reread: `ARCHITECTURE.md`, convert contract, tests contract, batch guide and current phases 0/1/2/4. Knowledge graph absent in this worktree; source and current generated codemap supply bounded context. Unknown usage/efficiency remains UNMEASURED.
- Next incomplete phase: independent phase-4 Test/Challenge after current-base red and baseline comparisons; no implementation until root ruling.
