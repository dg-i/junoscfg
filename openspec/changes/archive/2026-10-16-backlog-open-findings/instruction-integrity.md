<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and organisation policy | every action: no credentials, personal data or de-anonymised values | 1 | yes | documents only; nothing pushed; no device or external system contacted |
| Runtime: Claude Code, model `claude-opus-5-5`, a Builder subagent of the coordinator session the owner instructs directly | tool access | 2 | yes | Builder in this session; the coordinator dispatches a fresh Reviewer; the Builder does the bounded finalization after the verdict |
| Skill `agent-ready-change` (`SKILL.md`, docs lane, `types/docs.md`) and the `agent-ready` lane gate | lanes, phases, gates | 3 | yes | docs lane: `skip_specs: true`, `docs-plan.md`, document suffixes only outside the change folder |
| `AGENTS.md`, `ARCHITECTURE.md`, `pyproject.toml` `[tool.template.*]`, `docs/how-to/run-a-batch-of-changes.md` | house rules, stage (beta), versioning, worktrees | 4 | yes | worktree `/private/tmp/junoscfg-backlog-open-findings`, branch `change/backlog-open-findings`; patch bump at merge; tag, no push; synthetic values only |
| Owner request 2026-10-16, relayed verbatim by the coordinator: "add the found issues to the BACKLOG" | scope, approval | 5 | yes, relayed | the pending findings of own-crash-fixes (v0.28.23) and device-validation (v0.28.24) go into `docs/BACKLOG.md`; each records "Owner ruling 2026-10-16: backlog" and keeps the recorded interim behaviour |
| Coordinator brief 2026-10-16 | entry list, IDs, exclusions, hand-off | 6 | yes | eleven new entries, four extended entries, P1, P2, P3, A5 and R2-A2 not backlogged; stop before review |
| Archived reviews `openspec/changes/archive/2026-10-16-own-crash-fixes/review.md`, `openspec/changes/archive/2026-10-16-device-validation/review.md` | the findings and their interim rulings | 7 | yes | the authoritative source of every entry |
| Observed: `master` 716a9d1 (v0.28.24), clean apart from the untracked `.agents/skills/openspec-*` folders (left alone) | tree state | 8 | yes | no other live change edits `docs/BACKLOG.md` |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Both reviews say "nothing is backlogged without the owner"; the owner's ruling reaches the Builder through the coordinator, not first-hand | automatically resolved by precedence | coordinator: it relays the owner's words verbatim; the edit only records findings and changes no behaviour, so it is reversible; the Reviewer and the owner see the entries before merge | entries are written; each cites the ruling as relayed |
| C2 | `.agent-ready/activation.json` must change to admit this change, but the docs-lane gate refuses a `.json` product edit | automatically resolved by precedence (lane gate) | Builder: commit the activation on `master` and merge `master` into the branch, as input-trust-rule did (e5cb8cb, 1afcd29) | the branch diff holds only documents |
| C3 | own-crash-fixes review TC7 says a key holding NEL, LS or PS reads back with a space; a probe at 716a9d1 shows that only NEL does in the position probed, LS and PS read back unchanged | specification/test disagreement (evidence only) | Builder: the entry records the executed observation beside the review's wording; no behaviour depends on it | YAML-BREAKS-001 states both |
| C4 | device-validation A3 names `required`, `enum` and `pattern` failures; the shipped JSON and YAML schemas hold none of these keywords (counted at 716a9d1), and no probed input reached the generic message | specification/test disagreement (evidence only) | Builder: VALIDATE-MESSAGES-001 records the code path and the count, and asks the selecting change to find a reachable input first | the entry stays, marked as reachable only through a schema that has such keywords |
| C5 | `docs/BACKLOG.md` links to files outside `docs/`; `mkdocs build --strict` already reports 48 such warnings on master; the brief requires a link to each archived review | automatically resolved by precedence (owner brief and the existing BACKLOG convention) | Builder: new links follow the existing convention; QA checks that every new warning is a BACKLOG link of that class and that its target exists | QA criterion "no new warning class" instead of "no new warning" |
| C6 | `docs/VERIFICATION.md` has a pending cadence invitation | automatically resolved by precedence (skill: unattended batches defer the invitation to job end) | coordinator: invite at job end; this change touches no verification path | no verification edit |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy
- Standing record: `pyproject.toml#tool.template.assurance` (`record = docs/how-to/run-a-batch-of-changes.md#assurance`), key `default`; no zone owns `docs/`, recorded as `surface` as input-trust-rule did
- Required roles: Builder. The risk policy adds no role below the floor; the coordinator dispatches a fresh isolated Reviewer anyway, which the policy permits
- Application policy: docs lane; one full checkpoint before review and the canonical one before merge
- Mandatory risk floor: not high. No red zone, no trust-boundary or security work, no migration, no declared break, no named-surface change, not cross-domain. Unwaivable: `agent-ready fields`, `caps`, `lane`, `openspec validate --strict`, markdownlint, the full checkpoint

## Owner decision batch

None, because the owner's ruling is the approved intent and the brief settles every entry, its ID and the exclusions.

## Delta log

- Preflight, 2026-10-16: docs lane; C1 to C6 resolved. Base 716a9d1. Resume point: phase 1.
- Phases 1 to 5, 2026-10-16: no new instruction; resume point phase 6 (review by a fresh Reviewer the coordinator dispatches).
