<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and organisation policy | every action: no credentials, personal data or de-anonymised values in output | 1 | yes | tracked text holds synthetic values only; nothing is pushed, no external system contacted |
| Runtime: Claude Code, model `claude-opus-5-5`, Builder subagent of the batch orchestrator (lane D, wave 1), scratchpad | tool access | 2 | yes | the orchestrator runs the independent Reviewer; this Builder stops at STOP-R |
| Skill `agent-ready-change` (`SKILL.md` fix lane, phase 0, `batches.md`) | lanes, gates | 3 | yes | fix lane, type `fix`: ten-line proposal, one regression test failing on the merge base, caps 2 files / 30 lines, `skip_specs: true` |
| `AGENTS.md`, `ARCHITECTURE.md`, `tests/CONTRACT.md`, `src/junoscfg/convert/CONTRACT.md`, `pyproject.toml` `[tool.template.*]`, `docs/how-to/run-a-batch-of-changes.md` | house rules, zones, stage (beta), worktree, device-evidence checks, versioning | 4 | yes | worktree `../junoscfg-wt/posix-bracket-escape`; device-evidence checks and the before/after comparison apply (a `convert/` path); no version bump on the branch |
| Owner instructions, 2026-10-11: the nightly makeover intake (`private_test_data/makeover-work/builder-brief.md`) | scope, approvals, no questions | 5 | yes | every approval recorded as "approved under the owner's unattended-run instruction of 2026-10-11" |
| Orchestrator task for ledger row #20 (DEV-V5 = NEW-A4; PROC-F1 if the same root cause) | scope, stop points | 5 (relays the owner) | yes | one failure mode; a lightweight fresh-agent review is required before finalizing (C2) |
| Main specs under `openspec/specs/` | behaviour | 6 | yes | no requirement names the pattern dialect; no delta (`skip_specs: true`) |
| Tests under `tests/` | the oracle | 7 | yes | no test is weakened; one regression test added |
| Observed: `git status` clean on `master` 50b0a10; shipped `_patterns` #49 and #83 warn `Possible nested set at position 4` when compiled after `_posix_to_python_re` (scan of all 263 patterns, `private_test_data/makeover-work/posix-bracket-escape/scan.py`) | behaviour | 8 | yes | the failure mode this fix closes |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Skill "ask once" and owner approval of the proposal versus the owner's unattended-run instruction of 2026-10-11 (no questions, owner away) | automatically resolved by precedence | Builder: the ledger row and the inventory evidence are the approved intent | no owner batch |
| C2 | Standing preference `economy` adds no Reviewer below the high-risk floor versus the orchestrator's ruling that a solo fix-lane change takes a lightweight fresh-agent review | automatically resolved by precedence | Orchestrator runs the Reviewer; the preference may add assurance, never remove it | Builder stops at STOP-R; `review.md` comes from that Reviewer |
| C3 | Inventory leads offer two owning layers ("when translating, or at artifact build") versus `AGENTS.md` "fix at the owning layer" | automatically resolved by precedence | Builder: the schema artefacts keep the XSD's POSIX pattern as written (generator paths are serialized and out of lane); the dialect translation belongs to the one consumer that compiles it, `convert/field_validator.py` | no serialized path is touched |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy
- Standing record: `pyproject.toml#tool.template.assurance` (`record = "docs/how-to/run-a-batch-of-changes.md#assurance"`), matched key `default`; `zones` is empty, no declared break, no trust boundary
- Zone: `conversion` (yellow), path `src/junoscfg/convert/field_validator.py`
- Mandatory risk floor: not high (yellow zone, no security or trust-boundary work, no migration, no declared break, no named public surface change, one domain). Added by the orchestrator: a lightweight fresh Reviewer (C2). Unwaivable: the one full checkpoint, `agent-ready fields`, `caps`, `lane`, `openspec validate --strict`

## Owner decision batch

None, because the owner asked for no questions (C1) and the evidence fixes the repair: the match semantics stay those of today, only the dialect spelling changes.

## Delta log

- Initial preflight, 2026-10-11: consistent with the ledger row and inventory leads; approved under the owner's unattended-run instruction of 2026-10-11. Resume point: phase 1 (fix-lane route step 2).
