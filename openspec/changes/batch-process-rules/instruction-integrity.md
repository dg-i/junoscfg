<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and organisation policy | every action: no credentials, personal data or de-anonymised values in output; confirm outward-facing actions | 1 | yes | tracked text holds synthetic values only; nothing is pushed |
| Runtime: Claude Code, model `claude-opus-5-5`, subagents, scratchpad | tool access, isolated subagents | 2 | yes | fresh isolated Reviewer available as a subagent |
| Skill `agent-ready-change` v0.9.0 (`SKILL.md`, `batches.md`, phases, `types/docs.md`) and the lane gate of `agent-ready-checks` 0.15.11 | lanes, phases, batch orchestration, gate rules | 3 | yes | docs lane; the gate accepts only `.md/.rst/.txt` and images outside the change folder (C1, C2) |
| `AGENTS.md`, `ARCHITECTURE.md`, `pyproject.toml` `[tool.template.*]`, `docs/architecture/developer-guide.md` | house rules, caps (`AGENTS.md` 100 lines), zones, stage | 4 | yes | AGENTS.md stays under its cap; pointers, not detail |
| Owner instructions, 2026-10-11 (the pasted task "Persist the batch/parallel process rules"; later in the session "continue unattended") | scope, rules 1–8, boundaries, done-when; "do not ask the owner questions" | 5 | yes | approved intent for this batch; no question round (C4) |
| Claude memory: `nightly-makeover-run`, `writes-only-in-private-test-data`, `device-oracle-test-data` | earlier owner answers | 5, older | yes | superseded where the 2026-10-11 task differs (C6, C7, C8) |
| Decisions `docs/decisions/*.md`, main specs | what is promised today | 6 | yes | `2026-10-10-commit-device-captures-as-the-oracle` keeps the jvd clone as the opt-in tier; this change's record narrows its role |
| Tests under `tests/` | the oracle | 7 | yes | the survey of checks 1–6 below decides (a) or (b) per check and the follow-ups |
| Observed: `git status`, `git worktree list`, upstream `../agent-ready-python` tags | tree state, upstream release | 8 | yes | upstream latest release is v0.9.0, already installed (a1cbae2): no refresh to run |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Owner "add it to `mkdocs.yml` nav" in this docs change versus the docs-lane gate, which refuses any non-document suffix (`mkdocs.yml`) | automatically resolved by precedence | Builder: the nav entry moves to the batch's second change, `batch-process-config` (type `refactor`), merged right after this one; template follow-up TF1 asks the docs lane to accept the site nav file | the page is outside the nav for the interval between the two merges |
| C2 | Owner rules 1 and 8 need `pyproject.toml` (`[tool.template.batch]`, `[tool.template.assurance]`); version bump lines live in `pyproject.toml` and `src/junoscfg/__init__.py`; the docs lane refuses both | automatically resolved by precedence | Builder: `serialized-paths`, the `schema` expensive tier and the assurance `record` go to `batch-process-config`; the patch bump of each change goes into its archive commit (owner rule 5, merge-time versioning), outside the gated pull-request range | AGENTS.md "bump in the same commit as the code" holds: a docs change has no code commit |
| C3 | Owner "on clean `master`" versus the main checkout: staged, uncommitted edits to `.agents/skills/agent-ready-garden/*` that are not this session's | automatically resolved by precedence | Builder: work only in `../junoscfg-wt/batch-process-rules`; never stage, commit or revert the garden edits; archive commits are made on the change branch and `master` is fast-forwarded, so no commit in the main checkout can sweep them in | none on the deliverables |
| C4 | Skill "the human approves the proposal" and "ask once" versus owner "do not ask the owner questions" and the owner being away | automatically resolved by precedence | Builder: the owner's 2026-10-11 task is the approved intent; every judgement call it delegates (the `--jvd` fate) is decided in the decision record with its reasons | no owner batch |
| C5 | Owner rule 8 "if upstream supports it" versus `[tool.template.assurance]` (v0.9.0): supported, but its keys are `default`, `zones[<name>]`, `declared-break`, `trust-boundary`; "cross-domain" has no key | automatically resolved by precedence | Builder: cross-domain, red zone, declared break and trust boundary are all in the skill's mandatory high-risk floor, so `economy` everywhere plus the floor is exactly the owner's rule; `batch-process-config` points `record` at this change's decision record. A change outside every zone takes `default = economy`, read as the owner's "economy" because the floor alone carries "otherwise" | this change: `economy` |
| C6 | Memory `nightly-makeover-run` intake 1 "assurance balanced" versus owner rule 8 (2026-10-11) | automatically resolved by precedence (later owner instruction) | Builder: the standing preference applies; the owner's continuation prompt says "balanced, unless the persisted standing preference applies" | `economy` below the floor |
| C7 | Memory intake 8 "work in the main checkout" versus owner rule 4 (worktrees) | automatically resolved by precedence | Builder: worktree `../junoscfg-wt/<slug>` | none |
| C8 | Owner rule 4 "`private_test_data/` is symlinked into each worktree" versus `private_test_data/` being a tracked directory (`.gitignore`, `README.md`): linking the directory itself would show both tracked files deleted | repository/skill correction | Builder: link every entry of the main checkout's `private_test_data/` into the worktree's directory except the two tracked files; the how-to writes down that command | worktree tree stays clean |
| C9 | Owner "Builder and Reviewer briefs" versus where they live: `private_test_data/makeover-work/{builder,roles}-brief.md` (gitignored) and the tracked Reviewer report list in `docs/how-to/solo-review.md` | automatically resolved by precedence | Builder: edit the tracked `solo-review.md` in this change; trim the gitignored briefs outside the change (owner done-when) | none |
| C10 | Owner rule 3 checks 1, 3, 5 and 6 versus the tests: no committed test covers check 1 or 6, and 3 and 5 only partly (survey in `docs-plan.md`) | specification/test disagreement | Builder: the how-to records the present commands and coverage per check; each gap becomes a test-only follow-up (T1–T4) listed in the makeover ledger, never part of this change | the docs state the gaps, not a coverage that does not exist |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy
- Standing record: `pyproject.toml#tool.template.assurance`, matched key `default` (`zones` has no `surface` entry; this change edits no zone path, declares no break, crosses no trust boundary); the owner's 2026-10-11 rule 8 is the same value (C5)
- Mandatory risk floor: not high (no red zone, no break, no trust boundary, no named public surface, one domain-free documentation slice). Unwaivable: the one full checkpoint, `agent-ready fields`, `caps`, `lane`, OpenSpec validation, markdownlint and strict MkDocs build. The Builder adds one fresh isolated Reviewer because every later change reads these instructions; that adds assurance and waives nothing.

## Owner decision batch

None, because the owner asked for no questions (C4) and every rule in the task is either explicit or delegated to the decision record; the `--jvd` fate is decided there.

## Delta log

- Initial preflight: consistent; C1, C2 move the nav, configuration and version lines to `batch-process-config` and the archive commits; C10 makes T1–T4 ledger follow-ups.
