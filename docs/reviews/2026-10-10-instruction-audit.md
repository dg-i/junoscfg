# Instruction audit, 2026-10-10

Garden job 5, `agent-ready-garden instructions`, run in mode `full`: no mode
was given, and no `instructions-swept` baseline exists, so `full` applies
either way. Nothing was repaired and no pull request was opened; every
finding below needs the owner's decision. `instructions-swept` is unchanged.

## Run

| Item | Value |
|---|---|
| Mode | `full` (mode argument absent; baseline absent) |
| Baseline | none: `instructions-swept` is not set under `[tool.template.garden]`; agent-ready-checks 0.15.10 does not read that key (the template's unreleased working tree does) |
| Target | `01efe859064034787fd03c48de750a2bf3cdc473` on `change/agent-guidance-gates-and-contracts` |
| Working tree at the target | the owner's uncommitted `mkdocs.yml` edit (`/reviews/*.md` under `not_in_nav`) and the untracked identifier-key-fields review; read as evidence only, left untouched |
| Runtime, provider | Claude Code, model `claude-fable-5-1`, auto mode; Codex not available in this session |
| Date | 2026-10-10 |
| Tools | agent-ready 0.15.10 (locked), openspec 1.13.0 (both `npx` and the PATH copy), uv, git |

### Discovery methods

- `git ls-files` filtered for instruction-shaped paths (`AGENTS.md`, `CLAUDE.md`,
  contracts, `.agents/`, `.github/`, `openspec/`, `.agent-ready/`, hooks).
- Directory listings of `.claude/`, `.agents/`, `.agent-ready/` and `~/.claude/`
  (agents, commands, skills, plugins, settings, memory).
- `diff -rq .agents/skills .claude/skills`; per-file diffs of the three OpenSpec
  skill copies; diff of the local garden job against the template working tree.
- Read-only checks: `agent-ready skills`, `budget`, `caps`, `fields`,
  `decisions`, `gates`, `toolbox`, `status`, `lane`, `stage`,
  `render {codeowners,toolbox,levers,stage,decisions} --check`,
  `openspec validate --specs`, strict validation and `status` of both live changes.
- Existence checks for every path and test id named by `AGENTS.md`,
  `ARCHITECTURE.md`, the six contracts and `template.toml`: all resolve.

### Exclusions, with reasons

| Excluded | Count | Reason |
|---|---|---|
| `openspec/changes/archive/*` | 48 folders | history; never applied again; jobs 1 and 2 read them |
| `openspec/specs/**/spec.md` | 11 | validated with OpenSpec (11 passed); spec-versus-contract contradictions are job 1's |
| `openspec/changes/identifier-key-fields/{codemap.md,specs/**}` | 7 | generated slice and applied deltas; strict validation passed |
| `changelog.d/*` | 65 | towncrier fragments, not instructions |
| decision records not cited by any instruction read | 3 | `replace-docs-generator`, `superseded-device-measurements`, `reject-raw-set-brackets`; job 3 reads them |
| explanatory architecture pages | 3 | `conversion-bugfix-guide`, `schema-internals`, `design-decisions`: pointed to for "why", not rules |
| template how-tos | 2 | `hosting.md`, `remove-agent-ready.md`; `capture-change-metrics.md` read in its head only |
| `~/.claude/skills/synced/`, plugin skill bodies | 1 dir, 1 plugin | listed, not read |
| `graphify-out/`, `scratchpad/`, `.venv/`, caches | - | not instruction sources |

### Blind spots

- GitHub branch protection and required-review settings: not queryable here;
  `docs/how-to/work-with-agents.md` says the template cannot verify them either.
- The Codex runtime's actual loading of `.agents/skills`: inferred from
  `agent-ready skills` parity (passes), not observed.
- Nine of the twelve vendored `openspec-*` bodies were compared by diff against
  their regenerated copies, not read line by line (apply, archive, explore were).
- `docs/architecture/developer-guide.md`: Principles, Design patterns, Testing
  architecture and Extension guide read; the remaining mechanics sections not.
- `~/.claude/skills/graphify/SKILL.md`: first 60 lines only.
- Protected prompt text (platform, organisation, runtime) is described by class.

### Counts

| Class | Count |
|---|---|
| Sources discovered | 319 (121 read, 54 compared mechanically, 5 protected classes, 139 excluded as listed above) |
| Read | 121 files: 101 repository, 20 user-level |
| Compared mechanically | 54 gitignored-but-loaded files (30 mirror, 12 `source-command-opsx-*`, 12 `.claude/commands/opsx/*`) |
| Protected but semantically considered | 5 classes |
| Inaccessible | 0 claimed |

## Observable instruction surface

Precedence is the runtime's known order. Between repository sources the
repository declares no order; where one source is applied over another below,
the source of that reading is named.

| Source | Scope | Precedence | Loading path | Status |
|---|---|---|---|---|
| Platform and harness instructions | every action; confirmation before destructive or outward-facing actions; autonomy rules | 1 | system prompt | protected |
| Organisation policy (DG-i) | output content: no credentials, personal data, de-anonymisation | 1 | organisation block of the system prompt | protected |
| Runtime: auto-mode guidance, deferred tools, agent roster, MCP server instructions (Claude Docs) | tool choice, agent types, docs tool calls | 2 | session | protected |
| `~/.claude/settings.json` | model, effort, plugins, auto-mode allow/deny and environment facts | 2 | user settings | read |
| `~/.claude/CLAUDE.md` | graphify trigger | 2 (user) | user instructions | read |
| `~/.claude/skills/graphify/SKILL.md` | graph build and query | 3 when invoked | user skill | read (head) |
| `~/.claude/agents/junoscfg-{spec-writer,test-writer,implementer,reviewer,finalizer}.md` | one phase each of a change, when spawned | 3 when spawned | user agent profiles | read |
| Memory: `MEMORY.md` and 11 memory files | recorded owner feedback and project state | 5 (owner, as recorded) | project memory | read |
| `.agents/skills/agent-ready-change/*` (14 files) | every change: lanes, phases, roles, asking, stage | 3 when invoked | `.agents/skills`, mirrored to `.claude/skills` | read |
| `.agents/skills/agent-ready-garden/*` (6) | scheduled document maintenance | 3 (this run) | same | read |
| `.agents/skills/agent-ready-onboard/*` (9) | onboarding phases | 3 when invoked | same | read |
| `.agents/skills/agent-ready-refresh/SKILL.md` | template updates | 3 when invoked | same | read |
| `.agents/skills/openspec-*/SKILL.md` (12, vendored, generated by openspec 1.13.0) | OpenSpec change lifecycle commands | 3 when invoked | same | read (frontmatter; bodies diffed, 3 read) |
| `.claude/skills/source-command-opsx-*` (12, gitignored) and `.claude/commands/opsx/*.md` (12, gitignored) | the same commands as `/opsx:*` | 3 when invoked | Claude Code only | compared |
| `CLAUDE.md` | bridge `@AGENTS.md` | 4 | Claude Code root | read |
| `AGENTS.md` (100 lines, at cap) | house rules, verification, versions, docs checklist, test data | 4 | Codex root; Claude via bridge | read |
| `ARCHITECTURE.md` | goals, constraints, scope, cross-cutting rules, evidence hierarchy | 4 (pointer from `AGENTS.md`) | read on demand | read |
| `src/junoscfg/{,display/,convert/,validate/,anonymize/}CONTRACT.md`, `input.CONTRACT.md` | module invariants and precedents | 4 (pointer) | read before editing a module | read |
| `pyproject.toml` `[tool.template.*]` | caps, stage, surfaces, zones, domains, toolbox, garden | 4; enforced by checks | read by agent-ready | read |
| `.agent-ready/template.toml` | checks tag, local hook policy | 4; enforced by `fields` | read by agent-ready | read |
| `tach.toml` | layers and expose lists | 4; enforced by `tach check` | read by tach | read |
| `.pre-commit-config.yaml` | the fast hook set | 4; enforced on commit | pre-commit | read |
| `.github/workflows/ci.yml`, `publish.yml`, `CODEOWNERS` (generated) | CI gates, publishing, review routing | 4; enforced by hosting | GitHub | read |
| `openspec/config.yaml`, `openspec/schemas/agent-ready/schema.yaml` and 12 templates | change-folder artefacts and their instructions | 4; enforced by `openspec validate` | OpenSpec | read |
| `docs/architecture/developer-guide.md` | pipeline mechanics, test tiers, "Principles" | 4 (pointer from `AGENTS.md` for verification) | read on demand | read (sections) |
| `docs/how-to/settle-a-schema-question.md` | device evidence rules | 4 (pointer) | read on demand | read |
| `docs/how-to/work-with-agents.md`, `solo-review.md` | human workflow and review policy | 4 | read on demand | read |
| `docs/TOOLBOX.md`, `docs/decisions/index.md` (generated), 5 decision records | approved tools; decisions in force | 6 | read on demand | read |
| `openspec/changes/agent-guidance-gates-and-contracts/*` (4 files) | the live docs change: preflight C1-C10, proposal, metrics | 6 (approved artefacts) | OpenSpec | read |
| `openspec/changes/identifier-key-fields/*` | the completed, unarchived bug change | 6 | OpenSpec | read (5 files) |
| `private_test_data/README.md` | device dumps, captures, corpus rules | 4 | read on demand | read |
| `docs/reviews/2026-10-10-identifier-key-fields-agent-guidance.md` (untracked) | the owner's review that motivates the live change | evidence only | working tree | read |
| `.gitignore`, `.ignore`, `.copier-answers.yml`, `mkdocs.yml` | what is tracked, searched, templated, published | 4 | tools | read |

### Enforced repository state at the target

| Check | Result |
|---|---|
| `agent-ready skills`, `budget`, `decisions`, `gates`, five `render --check` | pass |
| `agent-ready caps` | pass; three vendored `openspec-*` skills over 300 lines, reported only |
| `agent-ready toolbox` | pass; three licence strings unverified, reported only |
| `agent-ready fields` | **fails**: `openspec/changes/identifier-key-fields/.openspec.yaml: assurance is not answered`; solo and `file://` template_url lines are reports |
| `agent-ready status` | phase 3 outstanding: zone `audit` has no `pinned` date |
| `agent-ready lane` | notes the two uncommitted owner files; evaluates base..HEAD only |
| `agent-ready stage` | `stage towncrier`: no fragment on this branch yet |
| `openspec validate --specs` | 11 passed |
| `openspec validate <change> --strict` | both live changes valid; identifier-key-fields: three ADDED requirements already exist in main specs (expected after the pre-merge application; archive must use `--skip-specs`) |
| `openspec status` | identifier-key-fields 6/8: `instruction-integrity` and `evidence-freeze` absent; agent-guidance 3/7 |
| Skill mirror | `.agents/skills` and `.claude/skills` identical apart from the vendored `source-command-*` copies |

## Findings

Each finding separates evidence (what the sources say or the checks print)
from inference (what follows). None qualifies for automatic correction.

### F1. The identifier-key-fields change fails the fields gate on this branch

- Evidence: `agent-ready fields` exits 1 with `assurance is not answered` for
  `openspec/changes/identifier-key-fields/.openspec.yaml`; `openspec status`
  shows `instruction-integrity` and `evidence-freeze` absent. The change was
  created 2026-10-09; the template refresh to v0.7.8 (commit `2a3e025`,
  2026-10-10) introduced `assurance` and the two artefacts; phase 0 says the
  owner confirms the value.
- Scope: this branch and any branch carrying the folder; `fields` runs in both
  check sets, so `agent-ready check` fails until it is answered.
- Inference: a template-introduced field met an existing live change. Nothing
  in the skill says what a change created before the field does.
- Consequence: the full checkpoint for the live docs change cannot pass while
  the folder sits beside it.
- Recommendation: the owner writes the value the change actually ran under
  (its review was a fresh Fable session with Test/Challenge work, which matches
  `maximum-assurance`), and decides whether to backfill the two artefacts or
  archive the change first.
- Decision owner: the repository owner. Automatic correction: no, the value is
  owner-confirmed by rule.

### F2. Solo review policy and the assurance policy disagree on when a fresh review is required

- Evidence: `docs/how-to/solo-review.md`: "For every change, and without
  exception for a change touching the `anonymize` red zone: 1. Have a fresh
  agent session read the proposal, the specs, the tests and the diff".
  `agent-ready-change/SKILL.md` Sessions: "`economy` adds neither role below
  that floor; `balanced` adds Test/Challenge work for behavioural changes and a
  Reviewer for yellow zones", and phase 6: "economy omits it below the floor.
  Record an omission". The skill also says the preference "cannot waive a
  mandatory risk control".
- Scope: every change. Precedence between a repository how-to and the
  template skill is not declared anywhere.
- Inference: under `economy`, or `balanced` outside a yellow or red zone, the
  skill records a review omission where the repository policy requires a
  fresh review. The review of 2026-10-10 asks to keep the fresh-session rule.
- Consequence: two agents can both be right and produce different review
  records for the same change.
- Recommendation: state the floor once, in `solo-review.md` (and a line in
  `AGENTS.md` if room): "a fresh review on every change is this repository's
  mandatory floor; `economy` does not waive it". The live docs change already
  edits `solo-review.md` and could carry the line.
- Decision owner: the repository owner. Automatic correction: no, meaning.

### F3. The developer guide's "Principles" contradict ARCHITECTURE.md and the declared stage

- Evidence, five items in `docs/architecture/developer-guide.md`:
  1. "Field validation prints warnings to stderr ... always report issues to
     stderr or through `FieldValidationResult.warnings`" versus
     `ARCHITECTURE.md` section 8: "Library calls never write those events to a
     terminal. The CLI renders their stable text to stderr".
  2. "converters fall back to hardcoded constants or heuristics" and the
     Design patterns row "name-based constant lookups provide safe fallback
     behavior" versus section 8: "A fallback that is not documented is a
     defect" and "the correction goes into the schema model, never into a
     runtime workaround".
  3. "Pre-1.0.0 (current state), breaking changes are acceptable with
     documentation" versus `AGENTS.md` Stage: "beta ... a removal is deprecated
     first" and `[tool.template.stage]` (`name = "beta"`, `break-bumps`,
     `declared-break` required by phase 1).
  4. The admonition "For AI coding agents ... treat these five principles as
     hard constraints" makes a mechanics guide a competing policy source.
  5. "For the full list of development commands, see the project CLAUDE.md":
     `CLAUDE.md` is the one-line bridge and `AGENTS.md` holds no command list.
- Scope: anyone reading the guide, which `AGENTS.md` names for verification
  and the pipelines. Precedence: the repository declares none; the live
  change's preflight (C7) and the owner's review apply `ARCHITECTURE.md` over
  the guide. Items 1 and 2 are already owner-visible as C7 and are a declared
  non-goal of the live change; items 3 to 5 are new.
- Consequence: an agent that reads the guide first writes to stderr from a
  library path, keeps a runtime fallback, or removes a public name without
  deprecation, each against the system rule.
- Recommendation: a follow-up docs change replaces the Principles block with
  pointers to `ARCHITECTURE.md`, drops the admonition, and repoints item 5 at
  `AGENTS.md` Verification or the guide's own Testing section.
- Decision owner: the repository owner. Automatic correction: no, meaning
  changes; item 5 has two plausible targets.

### F4. Three copies of the OpenSpec command skills, drifting, with no declared precedence against `agent-ready-change`

- Evidence: tracked vendored `.agents/skills/openspec-*` (12, `generatedBy:
  1.13.0`); gitignored `source-command-opsx-*` in both skill trees (12, loaded
  by Claude Code, listed in this session); gitignored `.claude/commands/opsx/*`
  (12, `/opsx:*`). The archive copies differ by 82 lines: the vendored body
  reports "Synced to main specs" only when its verification step passed, the
  regenerated copy prints that line unconditionally; explore differs by 148
  lines. All three prescribe archive with an inline spec sync and `/opsx:ff`
  or `/opsx:propose` generating design, specs and tasks in one step.
  `agent-ready-change` phase 7: main specs are applied before merge and the
  folder is archived with `--skip-specs` so the delta is never "applied a
  second time"; phase 3 limits design to `feature` and `new-dependency`.
  `AGENTS.md` says only "How to run a change: the agent-ready-change skill".
  `openspec validate identifier-key-fields --strict` already prints "Archive
  would refuse this delta ... already exists" for three specs.
- Scope: any session where a user or agent invokes `/opsx:*`,
  `/openspec-*` or the regenerated copies. Precedence: none declared.
- Inference: `/opsx:archive` on the identifier-key-fields change would either
  refuse or re-sync; `/opsx:propose` would write artefacts the lane gate
  does not expect.
- Consequence: duplicate ownership with material drift risk and a precedence
  ambiguity on the most consequential command (archive).
- Recommendation: one line in `AGENTS.md` naming `agent-ready-change` as the
  governing workflow and the `openspec-*` skills as vendored helpers used only
  through the commands it names; or remove the vendored skills and commands
  (decision 2026-10-06-raise-always-loaded-budget measured them at about
  1,300 tokens per session). Separately, a runtime correction: delete the
  regenerated `source-command-opsx-*` directories locally; `.gitignore` says
  they reappear on unrelated `openspec archive` runs.
- Decision owner: the repository owner. Automatic correction: no, the vendored
  bodies belong to their upstream and the precedence line is a rule.

### F5. Phase 4 says Hypothesis is approved; the toolbox says nothing

- Evidence: `phases/4-tests.md`: "Hypothesis is approved in the toolbox
  already, so the change that writes the first pair adds it to the dev group
  without a design". `pyproject.toml` `[[tool.template.toolbox.approved]]`,
  `docs/TOOLBOX.md` and `uv.lock` carry no hypothesis entry. The template seed
  table does. Already owner-visible as C6 of the live change, declared out of
  its scope.
- Scope: the first change that writes a round-trip property test.
  Precedence: the phase file is template-owned; the toolbox is this
  repository's.
- Consequence: an agent either adds a dependency the toolbox never approved
  or stalls on a design the phase says is unnecessary.
- Recommendation: add a trial or approved entry through the toolbox process
  (purpose, minimum version, MPL-2.0 licence), or record that here the first
  pair needs a `new-dependency` design, and raise the seed-versus-brownfield
  gap with the template.
- Decision owner: the repository owner (toolbox); the template maintainer
  (phase wording). Automatic correction: no, a dependency decision.

### F6. `work-with-agents.md` describes one phase per session; the skill now runs a continuous Builder

- Evidence: `docs/how-to/work-with-agents.md` line 3: "Every change runs
  through the `agent-ready-change` skill, one phase per session".
  `agent-ready-change/SKILL.md` (v0.7.8): "One continuous Builder ...
  progresses automatically across every non-decision boundary ... do not ask
  the owner to relay phase output".
- Scope: humans and agents reading the how-to. The how-to is
  application-owned; the skill is template-owned and newer.
- Consequence: a reader expecting a stop after every phase waits for a relay
  the skill forbids.
- Recommendation: reword to the continuous Builder with owner approval at
  decision boundaries (intent, spec freeze, tests, merge).
- Decision owner: the repository owner. Automatic correction: no, meaning.

### F7. The local hook policy cites a superseded decision and a hook that does not exist

- Evidence: `.agent-ready/template.toml` `[local-policy.hooks-979f...]`
  `reason`: "mypy runs in CI as reported-not-enforced under
  docs/decisions/2026-10-06-adopt-mypy-strict.md". That record carries
  `status: superseded`, `superseded-by: 2026-10-08-enforce-interface-type-checking`,
  under which CI runs blocking strict mypy over eight files (`ci.yml`, "mypy
  (stable interfaces)"). `.pre-commit-config.yaml` carries the comment "The
  type hook takes the whole package ... parallel mypy processes contend on one
  cache" above the deptry hook; no mypy hook exists.
- Scope: the refresh skill, which reads the policy to suppress a repeated
  hook recommendation; readers of the hook file.
- Consequence: the policy's conclusion (no mypy hook) still holds, but its
  stated reason is false, and the next refresh re-argues it from stale text.
- Recommendation: reword the reason to cite the accepted record and
  "blocking over eight stable-interface files"; delete or move the hook
  comment.
- Decision owner: the repository owner, who signed the policy. Automatic
  correction: no, the reason is an owner-signed decision text.

### F8. Stale comment in `[tool.template.stage]`

- Evidence: `pyproject.toml`: "A break on either surface raises the minor,
  which replaces the current patch-bump-for-everything rule in AGENTS.md".
  `AGENTS.md` Version Management already states the minor-on-break rule.
- Consequence: none in effect; a reader looks for a rule that no longer
  exists.
- Recommendation: drop the clause after "minor".
- Decision owner: the repository owner. Automatic correction: no, a comment's
  meaning.

### F9. The garden instruction job is a local edit of a template-owned skill, ahead of a release

- Evidence: commit `01efe85` added `jobs/5-instructions.md` and changed
  `SKILL.md` in `.agents/skills/agent-ready-garden/`, which the refresh skill
  calls template-owned. The pinned template v0.7.8 has no job 5. The template
  working tree (`agent-ready-python`, unreleased commits "Add periodic agent
  instruction audit", "Fit instruction audit within shipped cap") carries a
  job 5 whose `changed` mode differs from the local one (it starts from
  changed instruction sources; the local copy reads the whole repository diff)
  and a different stopping rule in `SKILL.md`. `instructions-swept` has a
  home in the template's unreleased `template_tables.py` under
  `[tool.template.garden]`; agent-ready-checks 0.15.10 does not know it.
  `SKILL.md` "Read this file and the one job file ... Do not read the others"
  sits beside job 5's `full`, which inventories every skill.
- Consequence: the next `agent-ready update` raises a conflict on these
  files; which wording is canonical is undecided; the audit's own baseline
  key cannot be set by a check that reads it.
- Recommendation: decide which copy is canonical, release the template, then
  refresh; add a clause letting the audit job read the other job files.
- Decision owner: the owner as template maintainer. Automatic correction: no,
  ownership and wording.

### F10. User-level auto-mode environment facts belong to another repository

- Evidence: `~/.claude/settings.json` `autoMode.environment` names a
  different repository as the trusted repo and `main` as the default branch,
  and lists that repository's sensitive paths. The block is user-global, so
  it is read in sessions here, where the repository is junoscfg and the
  default branch is `master`. (Contents not reproduced.)
- Scope: auto-mode permission judgement in every session on this machine.
- Consequence: a scope error at the user layer; permission reasoning may treat
  this repository as outside the trusted repo or misread its default branch.
- Recommendation: a runtime/operator correction, not a pull request: scope the
  block per project or generalise it.
- Decision owner: the user. Automatic correction: no, outside the repository
  and semantic.

### F11. The five Claude agent profiles encode the pre-refresh orchestration

- Evidence: `~/.claude/agents/junoscfg-{spec-writer,test-writer,implementer,
  reviewer,finalizer}.md` (2026-10-09) each run "exactly one phase" and load
  `agent-ready-change`; the refreshed skill says "One continuous Builder owns
  specification refinement, implementation, and accepted fixes" and "never a
  provider's session or delegation feature as the policy". The reviewer
  profile matches phase 6; the split Builder roles do not. The memory file
  for the pilot records them as its mechanism. Nothing in the repository
  references them; they are listed as spawnable in this session.
- Consequence: a provider divergence outside version control; a session that
  spawns them runs a role split the skill no longer describes.
- Recommendation: retire them, or realign them to Builder, Reviewer and
  Finalizer and record them in `work-with-agents.md` as the Claude adapter.
- Decision owner: the user. Automatic correction: no, outside the repository.

### F12. Two stale comments around the vendored copies and the hook file

- Evidence: `.gitignore`: the `source-command-*` skills "break the
  vendored-skills, caps and markdownlint globs", while `vendored-skills` now
  lists `source-command-*`. `.pre-commit-config.yaml` header: "and
  `agent-ready\n# phase 4 may write it where it is missing": an unclosed
  backtick, most likely meaning the onboarding skill's phase 4.
- Consequence: none in effect.
- Recommendation: fix with F4 and F7 respectively.
- Decision owner: the repository owner. Automatic correction: no, each has
  two plausible corrections.

### Observations, not findings

- `agent-ready status` reports zone `audit` without a `pinned` date while
  `onboarded = 2026-10-06`; `status` is a report, not a gate.
- `display/CONTRACT.md` names `junoscfg.display.constants.load_schema_tree`
  as a precedent pointer; `work-with-agents.md` names the same dotted path as
  the example of a refused import. A pointer is not an import; effects agree.
- Phase 2 and garden job 1 call `openspec` bare while the skill says to
  invoke it only through `npx ... @1.13.0`; the PATH copy is 1.13.0 today, so
  effects agree.
- `AGENTS.md` and `work-with-agents.md` give the full check as
  `uv run --locked agent-ready check --set full`; the skill and CI add
  `--group dev --with griffe --with tach --with towncrier --with vulture`.
  The check supplies tach and pre-commit itself; both spellings ran here.
- Three `openspec-*` skills exceed the 300-line report-only cap; three
  toolbox licences are unverified strings. Both are reported, not failed.

## Correction boundary

No finding is an exact mirror mismatch (the mirror is identical), an
unambiguous broken pointer with one existing target (every named path and
test id resolves; the two stale pointers each have two targets), a
mechanically incorrect generated bridge (`CLAUDE.md` is `@AGENTS.md`; all
five `render --check` pass), or a spelling defect with one meaning-preserving
fix. Therefore: no automatic correction, no pull request.

## Finish

`instructions-swept` stays unset: the key has no reader in the pinned checks
(F9) and every semantic finding above awaits the owner. The findings are
durably visible in this file.
