# Capture change metrics

Run `uv run --locked --group dev agent-ready metrics <change> --base-sha
<full-commit-id> --head-sha <full-code-commit-id>` after committing the code and before merging or
archiving the live change. The two IDs identify Git commit objects, including
after a later squash. The command reads their committed trees, not the worktree.
Commit `metrics.md` and `metrics.json` with the change. OpenSpec moves both
files into the archive. Every JSON field identifies its status, value or null
reason, SHA pair, UTC capture time, and source.

Runtime logs are optional and never searched for automatically. Import a
Codex exec JSONL log or Claude Agent SDK stream-json log with
`--session-log PATH --runtime codex|claude --session-binding PATH`. The binding
is a separate operator declaration:

```json
{
  "schema_version": 1,
  "runtime": "codex",
  "format": "exec-jsonl",
  "session_id": "native-session-id",
  "change": "my-change",
  "base_sha": "full-base-commit-id",
  "head_sha": "full-code-commit-id",
  "log_sha256": "sha256-of-exact-jsonl-bytes",
  "first_line": 1,
  "last_line": 5,
  "phase": "implement",
  "binding_kind": "operator_declared"
}
```

`phase` may be null. Bounds are inclusive, 1-based JSONL lines containing
complete turns or one complete Claude invocation. The log hash establishes
which bytes were selected; attribution to the change is the operator's claim.
The supported format values are `exec-jsonl` for Codex and `stream-json`
for Claude. Other well-formed formats remain unmeasured. Native usage is
runtime-reported token use, not billing or prefix/work allocation. The event
formats cannot establish complete file reads or retries.

An optional `--human-effort PATH` accepts exactly this JSON shape:

```json
{
  "schema_version": 1,
  "change": "my-change",
  "base_sha": "full-base-commit-id",
  "head_sha": "full-code-commit-id",
  "entries": [
    {
      "phase": "review",
      "minutes": 25,
      "artifacts_read": ["openspec/changes/my-change/spec.md"]
    }
  ]
}
```

Each phase and artifact identifier is nonempty. Minutes are finite,
nonnegative numbers; an explicit zero is a reported observation. Empty
`entries` means no observation. The importer rejects unknown fields,
identity mismatches, booleans, negative or nonfinite minutes. It records the
path and SHA256 of the exact input bytes and never invents a value.

## Observe OpenSpec artifact readership for one release

Use this protocol before proposing that an OpenSpec artifact type be deleted.
The observation is bounded by two consecutive release tags on the target
branch. For the simplification roadmap, the baseline is `v0.14.0`; observation
does not begin until that tag exists, and it closes at the next release tag.
Both tagged trees must have no live OpenSpec change directories, so a change
cannot straddle the cohort boundary.

Record the exact files read in the `distinct files read per phase, by artefact
type` row of each change's `metrics.md`. Use one JSON object whose top-level
keys are phases, whose next-level keys are artifact types, and whose values are
sorted lists of repository-relative paths:

```json
{"implement":{"proposal":["openspec/changes/example/proposal.md"],"tasks":["openspec/changes/example/tasks.md"]}}
```

Record observed reads only. Do not reconstruct them from the final diff or the
workflow's expected reading order. A participant who cannot supply a complete
phase observation leaves that phase unmeasured. Native session logs may add
positive evidence, but their event formats cannot establish complete file
reads and therefore cannot turn an unmeasured row into a zero-reader result.

At the closing tag, select the cohort from metrics files first added between
the tags:

```bash
baseline=v0.14.0
closing=vNEXT
git rev-parse --verify "$baseline^{commit}"
git rev-parse --verify "$closing^{commit}"
git merge-base --is-ancestor "$baseline" "$closing"
test -z "$(git ls-tree -d --name-only "$baseline:openspec/changes" | grep -vx archive)"
test -z "$(git ls-tree -d --name-only "$closing:openspec/changes" | grep -vx archive)"
git diff --no-renames --diff-filter=A --name-only "$baseline" "$closing" -- \
  'openspec/changes/archive/*/metrics.md'
```

Replace `vNEXT` with the actual next release tag. The observation is ready for
analysis only when the cohort is nonempty and every cohort file has a valid
JSON value instead of `UNMEASURED` in the readership row. Audit the exact
closing tree, not the current checkout:

```bash
git diff --no-renames --diff-filter=A --name-only "$baseline" "$closing" -- \
  'openspec/changes/archive/*/metrics.md' |
while IFS= read -r metrics_file; do
  value=$(git show "$closing:$metrics_file" | awk -F '|' \
    '$2 ~ /distinct files read per phase/ {gsub(/^ +| +$/, "", $3); print $3}')
  printf '%s\t%s\n' "$metrics_file" "$value"
done
```

Make incompleteness fail explicitly and validate every recorded value as a
nonempty JSON object:

```bash
cohort=$(git diff --no-renames --diff-filter=A --name-only "$baseline" "$closing" -- \
  'openspec/changes/archive/*/metrics.md')
test -n "$cohort"
printf '%s\n' "$cohort" |
while IFS= read -r metrics_file; do
  value=$(git show "$closing:$metrics_file" | awk -F '|' \
    '$2 ~ /distinct files read per phase/ {gsub(/^ +| +$/, "", $3); print $3}')
  test -n "$value"
  test "$value" != UNMEASURED
  printf '%s' "$value" | jq -e 'type == "object" and length > 0' >/dev/null
done
```

Classify each recorded path by the artifact type named in the JSON object and
count distinct paths and changes with at least one read. An artifact type is a
deletion candidate only if all of these conditions hold:

1. Every change and every phase in the release cohort has an explicit
   observation; `UNMEASURED`, a missing phase, invalid JSON, or an empty cohort
   makes the whole result incomplete.
2. The artifact type existed in at least one cohort change and has zero
   recorded agent and human readers across the complete cohort.
3. No current skill, gate, decision, or repository instruction names that
   artifact as required input or evidence.

Open a separate `agent-ready-change` proposal for candidates that satisfy all
three conditions. Include the two tag commits, cohort file list, per-type
counts, and coverage audit. If no type qualifies—or coverage is incomplete—do
not propose a deletion; record that result and run another observation period
if the maintenance question remains valuable.
