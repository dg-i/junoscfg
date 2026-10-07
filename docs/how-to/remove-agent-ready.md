# Remove agent-ready from an application repository

Work on a clean branch. Record the application's native acceptance invocation
and the base commit before editing. In the rendered example, that invocation is
`./scripts/check`; use the real application's command where it differs.

```sh
git status --short
git switch -c remove-agent-ready
git rev-parse HEAD
git ls-files
rg -n --hidden 'agent-ready|template_update' .
```

Record the printed commit as `BASE` for rollback. Stop if the initial status is
dirty. Review the tracked inventory and matches for ownership; a text match
alone never authorizes deletion. Record any remote schedules you disable.

## Remove the shipped skills

Run each command only if that exact tracked path exists. Review customized or
renamed skills as application material and retain or convert them deliberately.

```sh
git rm -r -- .agents/skills/agent-ready-onboard
git rm -r -- .agents/skills/agent-ready-change
git rm -r -- .agents/skills/agent-ready-garden
git rm -r -- .agents/skills/agent-ready-refresh
git rm -r -- .claude/skills/agent-ready-onboard
git rm -r -- .claude/skills/agent-ready-change
git rm -r -- .claude/skills/agent-ready-garden
git rm -r -- .claude/skills/agent-ready-refresh
```

## Convert integration points

Review `.github/workflows/ci.yml`, `.github/workflows/update.yml`, and
`.gitlab-ci.yml`. Remove only template-owned jobs or invocations. A wholly
template-owned workflow may be removed with `git rm -- PATH` after the native
acceptance job exists. Keep mixed workflows and application CI. In GitLab
hosting settings, disable pipeline schedules targeting `template_update`;
removing YAML does not disable schedules. Disable separately configured cron or
Codex schedules only when they invoke template update. Retain other schedules.

Edit the hook configuration and the real native check adapter. Remove only
agent-ready hook entries or commands. Retain application hooks and useful ruff,
mypy, deptry and other checks. The rendered example uses `scripts/check`; use
the recorded adapter instead if its path differs. Preserve its executable mode
and any existing native hooks.

```sh
$EDITOR .pre-commit-config.yaml scripts/check
pre-commit validate-config
pre-commit install
```

Run the last two commands when pre-commit is installed; they validate and
refresh the retained setup. Do not remove the whole hook file or uninstall all
hooks.

Keep useful generated tool settings in `pyproject.toml`; remove only their
stage-lever marker lines. Transfer useful zone, domain, stage and cap
information to ordinary application documentation, then remove the
`[tool.template]` subtree. Remove only the check package dependency and its
`[tool.uv.sources]` entry, using the application's native dependency workflow.
For uv:

```sh
$EDITOR pyproject.toml
uv remove --group dev agent-ready-checks
uv lock
```

Inspect the resulting TOML. Keep the dev group, lockfile, unrelated tool
tables, and other dependencies.

Retain `AGENTS.md`, `CLAUDE.md`, and application instructions. Review the block
between `<!-- agent-ready:stage:begin -->` and
`<!-- agent-ready:stage:end -->`; keep useful policy as ordinary prose and
remove the markers and obsolete command references. Treat other generated
blocks, retirement inventories, ownership files, toolbox and decision indexes,
and graphs the same way: retain useful contents as application artifacts and
edit stale command links.

Source, tests, the native acceptance adapter, canonical executable specs,
OpenSpec specs, live changes and archive, contracts, `ARCHITECTURE.md`, docs,
decision records, budgets, baselines, `tach.toml`, and independent tools remain
by default. Keep `openspec/schemas/agent-ready` while live, historical or
configuration references use it. Migrating to another schema is a separate
change.

## Remove update metadata last

Copy useful `[local-policy.*]` decisions into application decision docs. Then:

```sh
git rm -- .copier-answers.yml .agent-ready/template.toml
```

Review any other `.agent-ready` contents individually; that directory may
contain application artifacts. Keep this guide and useful how-to docs as
application documentation.

## Verify and roll back

```sh
git diff HEAD --check
git diff HEAD --stat
git diff HEAD
rg -n --hidden 'agent-ready|template_update' .
./scripts/check
```

Substitute the recorded native acceptance command for the last line. Classify
remaining matches as documentation or history versus runnable references.
Review the full diff and the command result before merging.

On this dedicated clean branch, use the recorded `BASE` to restore only the
reviewed changed tracked paths:

```sh
git restore --source BASE --staged --worktree -- PATH...
```

Remove only new paths created during the removal, naming each explicitly.
Re-enable remote schedules only from the recorded list of settings.
