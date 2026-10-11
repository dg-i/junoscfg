<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and organisation policy | every action: no credentials, personal data or de-anonymised values in output; confirm outward-facing actions | 1 | yes | tracked text holds synthetic values only; nothing is pushed, no external system contacted |
| Runtime: Claude Code, model `claude-opus-5-5`, Builder subagent of the batch orchestrator, scratchpad | tool access | 2 | yes | the orchestrator runs any independent role; this Builder stops at STOP-T/STOP-R if the floor requires one |
| Skill `agent-ready-change` (`SKILL.md`, phases 0–5) and `agent-ready-checks` 0.15.11 | lanes, phases, gates | 3 | yes | standard lane, type `bug`; phase 3 not required (bug) |
| `AGENTS.md`, `ARCHITECTURE.md`, `tests/CONTRACT.md`, `pyproject.toml` `[tool.template.*]`, `docs/how-to/run-a-batch-of-changes.md` | house rules, zones, stage (beta), worktree, versioning | 4 | yes | worktree `../junoscfg-wt/retire-jvd-tier`; no version bump on the branch (merge-time versioning) |
| Owner instructions, 2026-10-11: the nightly makeover intake (`private_test_data/makeover-work/builder-brief.md`) and the request recorded in the decision record ("docs or bug") | scope, approvals, no questions | 5 | yes | approved intent; every approval recorded as "approved under the owner's unattended-run instruction of 2026-10-11" |
| Orchestrator task for `retire-jvd-tier` | the removal list, stop points | 5 (relays the owner) | yes | the files and requirement listed in the proposal |
| Decision `docs/decisions/2026-10-11-retire-jvd-from-per-change-verification.md` (accepted) | authority for the removal | 6 | yes | "Removing the tier's code is its own change, `retire-jvd-tier`, typed `bug`" |
| Main spec `openspec/specs/validation/set-command-validation/spec.md` | names `--jvd` in "A keyed entry takes exactly its key values" | 6 | yes | MODIFIED delta (C2) |
| Tests under `tests/` | the oracle | 7 | yes | no test other than the JVD tier's is removed or weakened |
| Observed: `git status` clean on `master` 284715b; `.github/workflows/corpus.yml` holds only the `jvd` job and is repository-owned (the template at `../agent-ready-python` ships `ci.yml` and `update.yml` only) | tree state | 8 | yes | the workflow file is removed whole (C3) |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Skill "the human approves the proposal" and "ask once" versus the owner's unattended-run instruction of 2026-10-11 (no questions, owner away) | automatically resolved by precedence | Builder: the owner's request and the accepted decision record are the approved intent | no owner batch |
| C2 | The owner asked for "docs or bug"; the docs lane refuses `.py`/`.yml`, and a main spec names `--jvd` | automatically resolved by precedence | Builder: type `bug`, standard lane, one MODIFIED requirement; `skip_specs` stays unset as the lane gate requires for `bug` | a delta and the bug route of phase 4 |
| C3 | Removing the JVD job leaves `.github/workflows/corpus.yml` with no job | automatically resolved by precedence | Builder: remove the file, as the orchestrator task directs when nothing else remains | no nightly workflow; `ci.yml` and `publish.yml` stay |
| C4 | Skill phase 4 asks for failing-first acceptance tests versus a removal, which adds no behaviour to test | specification/test disagreement | Builder: the delta's `Tests:` names existing tests; the freeze names what proves the removal (collect-only, `grep`, `pytest --jvd` refused) | no new test; no failing-first commit |
| C5 | Decision record front-matter `scope` lists files this change deletes | automatically resolved by precedence | Builder: the accepted record is left as written (it records what was retired); if a check refuses a missing scope path it is reported, not worked around | none expected |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy
- Standing record: `pyproject.toml#tool.template.assurance` (`record = "docs/how-to/run-a-batch-of-changes.md#assurance"`), matched key `default`; `zones` is empty, no declared break, no trust boundary
- Zone: `schema` (yellow). The change edits no zone path (tests, CI, docs, specs only); the requirement it modifies belongs to domain `validation`, whose set-validation code lives in the `schema` zone
- Mandatory risk floor: not high (yellow zone, no security or trust-boundary work, no migration, no declared break, no named public surface: `--jvd` is a pytest option of the test suite, neither `consumer` nor `cli`; one domain). No Test/Challenge and no fresh Reviewer required. Unwaivable: the one full checkpoint, `agent-ready fields`, `caps`, `lane`, `openspec validate --strict`

## Owner decision batch

None, because the owner asked for no questions (C1) and the accepted decision record lists what this change removes.

## Delta log

- Initial preflight, 2026-10-11: consistent with the decision record; approved under the owner's unattended-run instruction of 2026-10-11. Resume point: phase 1.
