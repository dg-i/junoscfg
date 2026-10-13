# Observe OpenSpec artifact readership

Application-owned extension to [change metrics](capture-change-metrics.md).

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
