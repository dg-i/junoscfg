<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and organisation policy | every action: no credentials, personal data or de-anonymised values in output | 1 | yes | tracked text holds synthetic values only; nothing is pushed, no external system contacted |
| Runtime: Claude Code, model `claude-opus-5-5`, Builder subagent of the batch orchestrator (lane D, wave 1b), scratchpad | tool access | 2 | yes | the orchestrator runs the independent Reviewer; this Builder stops at STOP-R |
| Skill `agent-ready-change` (`SKILL.md` fix lane, phase 0, `batches.md`) | lanes, gates | 3 | yes | fix lane, type `fix`: ten-line proposal, one regression test failing on the merge base, caps 2 files / 30 lines, `skip_specs: true` |
| `AGENTS.md`, `ARCHITECTURE.md`, `tests/CONTRACT.md`, `src/junoscfg/display/CONTRACT.md`, `pyproject.toml` `[tool.template.*]`, `docs/how-to/run-a-batch-of-changes.md` | house rules, zones, stage (beta), worktree, versioning | 4 | yes | worktree `../junoscfg-wt/audit-key-keywords`; no version bump on the branch; `audit/` is not a path the device-evidence checks name, the before/after comparison is run anyway as blast-radius evidence |
| Owner instructions, 2026-10-11: the nightly makeover intake (`private_test_data/makeover-work/builder-brief.md`) | scope, approvals, no questions | 5 | yes | every approval recorded as "approved under the owner's unattended-run instruction of 2026-10-11" |
| Orchestrator task for ledger row #21 (OPEN-12) | scope, stop points, coordination | 5 (relays the owner) | yes | one failure mode; no serialized path; a lightweight fresh-agent review is required before finalizing (C2); live Builders #7 and #8 checked through their `files.txt` and diffs |
| Main specs under `openspec/specs/` (`audit/keyed-references`) | behaviour | 6 | yes | the spec names which key field is the reference, not how the entry path is spelled; no delta (`skip_specs: true`) |
| Tests under `tests/` | the oracle | 7 | yes | no test is weakened; one regression test added |
| Observed: `git status` clean on `master` 87ac8f7; `collect_occurrences` writes `virtual-link 10.255.255.1 0.0.0.2` and `route-filter 10.0.0.0/8 upto` where the set writer writes `virtual-link neighbor-id 10.255.255.1 transit-area 0.0.0.2` and `route-filter 10.0.0.0/8 upto /24` (`private_test_data/makeover-work/audit-key-keywords/repro.py`) | behaviour | 8 | yes | the failure mode this fix closes |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Skill "ask once" and owner approval of the proposal versus the owner's unattended-run instruction of 2026-10-11 (no questions, owner away) | automatically resolved by precedence | Builder: the ledger row and the inventory evidence are the approved intent | no owner batch |
| C2 | Standing preference `economy` adds no Reviewer below the high-risk floor versus the orchestrator's ruling that a solo fix-lane change takes a lightweight fresh-agent review | automatically resolved by precedence | Orchestrator runs the Reviewer; the preference may add assurance, never remove it | Builder stops at STOP-R; `review.md` comes from that Reviewer |
| C3 | Inventory lead "ask the display kernel for an entry's written key tokens (the same helper the set writer uses)" and `AGENTS.md` "fix at the owning layer" versus the batch coordination rule (live S-lane Builder #8 lists `src/junoscfg/display/__init__.py` and `src/junoscfg/convert/output/dict_walker.py`, which a shared helper would edit) and the fix-lane caps | automatically resolved by precedence | Builder: the audit walker asks the display kernel's `key_is_positional`, the rule the set writer applies, and keeps its own token loop; moving the writer's `_entry_key` into `display` is recorded as a follow-up, not done here | no overlap with a live Builder; two copies of the token loop remain (recorded in the proposal) |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy
- Standing record: `pyproject.toml#tool.template.assurance` (`record = "docs/how-to/run-a-batch-of-changes.md#assurance"`), matched key `default`; `zones` is empty, no declared break, no trust boundary
- Zone: `audit` (yellow), path `src/junoscfg/audit/walker.py`
- Mandatory risk floor: not high (yellow zone, no security or trust-boundary work, no migration, no declared break: the audit scripts change from device-invalid to the writer's spelling, which the named surfaces promise; one domain). Added by the orchestrator: a lightweight fresh Reviewer (C2). Unwaivable: the one full checkpoint, `agent-ready fields`, `caps`, `lane`, `openspec validate --strict`

## Owner decision batch

None, because the owner asked for no questions (C1) and the device evidence fixes the spelling: `virtual-link neighbor-id 10.255.255.1 transit-area 0.0.0.2` is what the device accepts and the writer prints (device probe, vMX 23.2R2-S7.5: `tests/contract/test_every_door.py` row `virtual-link-keys-without-keywords` records the keyless spelling rejected).

## Delta log

- Initial preflight, 2026-10-11: consistent with the ledger row and inventory lead (inventory-c OPEN-12), extended within the same failure mode to a key choice's value (`route-filter ... upto /24`), which the audit drops the same way; approved under the owner's unattended-run instruction of 2026-10-11. Resume point: phase 1 (fix-lane route step 2).
