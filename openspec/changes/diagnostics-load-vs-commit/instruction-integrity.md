<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

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
