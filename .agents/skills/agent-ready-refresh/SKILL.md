---
name: agent-ready-refresh
description: Bring a repository up to the current template and check versions. Run agent-ready update, resolve what Copier could not merge, work the checks that fail afterwards, and ask about the rest. Run it on the update pull requests the scheduled workflow opens, or by hand.
---

# Refresh

The template and the check package move on after onboarding. `agent-ready
update` is the one command that brings a repository to the newest template
release: it runs `copier update` with the answers a new question needs, moves
the check package to the tag that release names, refreshes the lockfile, and
reports the conflict markers Copier left and the checks that fail under the
new version. This skill works that report.

Invoke as `agent-ready-refresh`, on the update branch the scheduled workflow
opened or on a clean branch of your own. The update refuses a branch with
existing changes so its scoped recovery command cannot discard local edits.
Read this file only.

## Run the update

Run `uv run --locked --group dev agent-ready update --no-checks` from the
repository root. Use the current updater when the pinned copy predates the
required update behavior:
`uvx --from "git+<template_url>@<immutable-checks-commit>#subdirectory=checks"
agent-ready update --no-checks`. The source comes from `.copier-answers.yml`;
the reviewed target release supplies the check-package commit. Review the diff
and report, commit the exact update and receipt, then run
`uv run --locked --group dev agent-ready check --set full --base <update-base>`.
Full verification judges a committed snapshot; `--no-checks` defers it until
that snapshot exists and never waives it. A scheduled update needs the same
verification, with its local updater attestation reproduced as described below.
`--to <ref>` picks a
template ref other than the newest tag, and `--data key=value` changes a
recorded answer, which is how a repository whose remote is not GitHub stops
the workflows from shipping: `--data github_workflows=false`. The command
checks that the target release and its check-package tag are readable before
Copier changes files. `--data template_url=<url>` moves the Copier source and
the check-package source together; the update refreshes the dev minimum and
lockfile from the same release. If the source or tag cannot be read, the
application remains untouched. A failure after Copier names the files it
changed and gives a recovery command scoped to those files on the update
branch. Read that command before running it if the branch also carries local
edits.
The command
refuses `project_name`, `package_name`, `python_version`, and `mode`, because
Copier would re-render the seeds and delete the old package directory; those
are edited by hand. Where the question at the recorded release refuses a
recorded answer that the target accepts, the command renders the merge base
with the nearest value the old question takes, carried in a commit of the
answers file that is undone before the command returns, and keeps the
recorded answer, saying so in the report; the answers file is never edited
by hand for it. The report
names the template commit before and after, the check package tag before and
after, the files with conflict markers, and the failing checks. Nothing is
committed by the command. When you commit a resolution that touches
`.pre-commit-config.yaml`, stage that file first: pre-commit refuses to run
with its own configuration modified and unstaged.

A successful update records `.agent-ready/update-receipt.json`, binding its base,
immutable template/check references and exact changed file hashes. The updater
retains an identical attestation in the Git common directory. Commit that receipt
with the update. The lane accepts only that exact updater diff without a live
change; manual corrections invalidate it and need their own reviewed change.
Incoming tracked receipts alone are insufficient. A fresh clone or CI checkout
must reproduce the supported update from the recorded base to retain its own
attestation; copying an incoming attestation is not verification. This is local
updater provenance, not human approval or protection from local Git-directory
writers. The receipt never skips other checks. A beta/release refresh still includes
its required Towncrier fragment; include it in the reviewed update workflow.

## The rule that governs every finding

**The template owns its files; this repository owns everything else.** The
agent-ready skill bodies and the CI workflows are the template's.
The template owns `checks-tag` in `.agent-ready/template.toml`; this repository
owns its `[local-policy.<id>]` tables. The seeds it wrote once, `pyproject.toml`,
`.pre-commit-config.yaml`, `ARCHITECTURE.md`, `tach.toml`, the source and the
tests, are this repository's, and `copier update` never touches one that
exists. So
a conflict marker can only sit in a template-owned file, and it means one
thing: someone here edited what the template owns, and the template has since
changed the same lines.

Never resolve such a conflict on your own. Show both sides, say what the
template's change does and what the local edit did, and ask whether the local
edit still stands. If it does, the answer is a differently named copy or an
issue on the template, never a silent merge; if it does not, take the
template's side and say so in the pull request.

## Working the checks

A check that fails after the update is the template asking this repository for
something it did not need before. Work them the way `agent-ready-onboard`
does:

1. Derive what can be derived, and present it as a proposal with its evidence.
2. A field no evidence can fill, a sentinel `agent-ready fields` reports, is a
   question. Never fill it with a plausible guess.
3. One pull request per finding, never one sweeping rewrite: each is
   reviewable on its own and revertable on its own. Where the update branch
   itself has to go green first, keep the resolution commits small and name
   the finding each one closes.

Then `agent-ready scaffold template`, every time: it adds the tables, hook
file, tool sections, `tach.toml`, and ignore lines a release introduced where
this repository has none, keeps what it has, and names every key the
template's tables carry that a kept table lacks, which is how a change inside
a seed reaches a brownfield repository. `agent-ready caps --homes` adds the
artefact homes no cap here covers. The command prints the notes of every
release between the one this repository records and the target before it runs
them; read them first, since they name what a release asks of a repository.

For the hook file, compare the current bytes with the bytes used by the update
report before repeating a merge recommendation. A matching accepted local
policy is an already-decided recommendation. Scaffold still runs, and every
correctness check still applies. Changed hook bytes or a skill conflict need
their own decision.

Ask the way `agent-ready-onboard` does: in prose, never as a menu, in one
batch at the end, each question numbered and carrying the evidence and what
you would do. Use no asking mechanism that only one runtime has.

## Local policy

The update report names the exact `refresh.pre-commit.integration.v1` scope
and `hooks-` id when the current hook file differs from the incoming hook
recommendation. An owner may decide that the application's native adapter
covers it. Record that decision in `.agent-ready/template.toml` as
`[local-policy.<printed-id>]` with `scope`, a concrete `reason`, an issue URL
or `local-only: <reason>` as `upstream`, and a `review-by` date. The id is tied
to both hook files' exact bytes. The policy suppresses only this repeated
recommendation. It never suppresses checks, conflicts or expiry;
`agent-ready fields` fails when review is overdue or metadata is invalid.
For an exit from the template, use `docs/how-to/remove-agent-ready.md`.

## Stopping

Stop and report, rather than pushing on, when:

- a conflict needs a decision about a local edit, which is the human's;
- a finding is a cap raise or a stage move, both of which take a decision
  record only a human signs;
- the same failure repeats without new evidence or a changed hypothesis, which
  is more often a contract or spec problem than a merge problem.

Run `agent-ready caps` and `agent-ready skills` before pushing anything that
touches a capped document or a skill body. Both runtimes run the same checks
the same way; nothing in this skill depends on a feature only one of them has.

## Application-owned backlog and adoption

`docs/BACKLOG.md` is a preserved seed. Verify populated contents survive the update;
never reset them to the template example. If an issue tracker is declared, retain
one authoritative destination and the file's pointer. Apply
`docs/how-to/review-scope.md` when consolidating deferred findings with their IDs,
evidence and rulings. Align application-owned prompts and working guidance with
that policy in a separate reviewed adoption change. Record an ongoing batch's
remaining scope and resume from valid evidence without restarting completed phases.
