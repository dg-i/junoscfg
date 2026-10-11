# Review

Fresh isolated Reviewer (general-purpose subagent, model `claude-opus-5-5`, no Builder context),
reviewed `a1cbae2..db38a5e` after the full checkpoint passed at db38a5e. Added by the Builder
above the `economy` preference (preflight, Assurance). Verdict: **APPROVE WITH FIXES**.

## Findings and dispositions

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | major | AGENTS.md Version Management changed beyond the proposal's scope, C2 said the old rule held | accepted: proposal and C2 now record merge-time versioning for every change (owner rule 5) |
| 2 | major | AGENTS.md lost the pointer to the developer guide's per-path extras; the how-to did not link the pre-review table | accepted: AGENTS.md keeps "Per-path extras: developer guide, Testing Architecture"; the how-to intro links the table |
| 3 | major | Assurance section omitted security, migration and named-surface high-risk triggers and pushed zone-less changes onto the floor | accepted: the section quotes the skill's floor list; economy for every change below it |
| 4 | minor | `[--anonymize]` inside a copyable zsh block | accepted: one command form, `--anonymize` explained after it; commands use an absolute `$w` |
| 5 | minor | "Checks 1 to 5 run in the default suite" | accepted: "Checks 2 to 5" |
| 6 | minor | decision said nobody runs `--jvd`; the nightly CI job does | accepted |
| 7 | minor | merge steps omitted the rebase full rerun and regenerate-only conflict resolution | accepted |
| 8 | minor | no commit step before the second `--regen-schema` | accepted |
| 9 | minor | check 4 omitted the JSON shapes the strict xfails name | accepted |
| 10 | minor | "a directory created later stays local" holds only for top-level entries | accepted: reworded; the `.claude/skills` regeneration step added (found by the first full check) |
| 11 | minor | how-to archive order contradicted C3 | accepted: archive commit on the branch, then fast-forward and tag |
| 12 | minor | "oracle checks" and "device-evidence checks" both used | accepted: "device-evidence checks" in every product document, named in the how-to intro |
| 13 | minor | source (a) omitted `synthetic-probes` | accepted |
| 14 | nit | duplicated facts (Builder count, bump rule, schema commands) | accepted: the how-to points at `max-builders` and AGENTS.md; the developer-guide row links the how-to's schema tier |
| 15 | nit | gitignored names (`compare-template.py`, EVIDENCE_BLOCKED, T1–T4) | not changed: they are batch artefacts on this machine; T4 commits the script as a shared tool |
| 16 | nit | template lacked `sensitive_patterns`; keys omitted the source | accepted (gitignored script; 1,152 conversions recorded, no exception) |

## Specification challenges

None.

## Confirmation

The same Reviewer re-read `db38a5e..417e969`: findings 1–14 and 16 CONFIRMED, 15 not changed
with the rationale accepted, no new finding; it ran the how-to's comparison block as written
("0 of 1152 conversions differ", head 42.6 s) and `mkdocs build --strict` (passed). Verdict
APPROVE. A later Builder fix, `417e969..c8086a5` (the regeneration check excludes the
timestamped `junos-schema-meta.json.gz`, found by the schema-tier QA run), returned to the same
Reviewer: CONFIRMED, verified in the regeneration worktree, verdict APPROVE.
