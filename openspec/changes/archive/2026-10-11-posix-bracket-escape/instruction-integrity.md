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
- Fix route step 2, 2026-10-11: proposal (9 lines) and metadata approved under the owner's unattended-run instruction of 2026-10-11; committed c29bc24.
- Fix route step 3, 2026-10-11: regression test `tests/unit/convert/test_field_validator.py::TestPatternValidation::test_a_literal_bracket_in_a_posix_bracket_expression` and repair committed f84532d, a2edf23 (the test first raised the warning as an error, which the lane gate does not read as a failure; it now records warnings and asserts none). Caps: 2 files, 30 lines. `agent-ready lane --base master` exit 0 (fails at the merge base, passes at head). Evidence: all 263 shipped `_patterns` parse to the same `re` program as before, 2 respelled (#49, #83), none warns; device-evidence checks 3,664 passed, 5 xfailed; before/after over `tests/data/device/manifest.json`: 0 of 96 conversions differ, base stderr carries the `field_validator.py:206` FutureWarning once, head none (PROC-F1 is the same root cause and closes here). Full checkpoint at a2edf23: every check passed, 7,559 passed, 37 skipped, 18 xfailed; coverage 92.95 %. Resume point: STOP-R, the orchestrator's lightweight fresh-agent review (C2), then `review.md`, metrics and the archive-ready commit.
- STOP-R resolved, 2026-10-11: the fresh-agent review (base 50b0a10, head f4062eb) returned APPROVE. Applying the orchestrator's rulings: F1 and F2 were applied to `proposal.md` as records only, and the F1 specification challenge stays pending the owner with a recorded interim action. F3 was deferred to ledger follow-up T5. No code or test changed, so the full check at a2edf23 stands. Metrics were captured for 50b0a10 to a2edf23. Resume point: the orchestrator's merge, bump and archive (task 3.3).
