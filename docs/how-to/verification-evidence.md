# Verification admission and evidence

Policy identifier: `strategy-a/1`. Readiness grants permission to run a command;
it is never evidence that the command succeeded. Keep the seven change phases,
assurance floor, independent Test/Challenge role and fresh isolated Reviewer.

## Activate deliberately

After updating and reviewing the local gates, record one operator activation
checkpoint. Inspect `git branch --list`, `git worktree list`, and every live
change, including parked work. Do not delete branches or infer approval from age.
Add `[tool.template.verification]` with `enabled = true` and
`policy = "strategy-a/1"` to `pyproject.toml`. Existing installations remain
inactive until this explicit edit. Ensure `.gitignore` includes
`.agent-ready/verification/`: ignore files are application-owned seeds and an
update preserves them. Commit the policy, ignore entry and assessment together.

Create `.agent-ready/activation.json` with these fields:

```json
{
  "policy": "strategy-a/1",
  "checkpoint": "FULL_IMMUTABLE_COMMIT_SHA",
  "actor": "operator identity",
  "authority": "owner activation decision reference",
  "captured_at": "2026-10-11T12:00:00+00:00",
  "branches": {"main": "parked", "change/example": "ready"},
  "changes": {"example": "ready"}
}
```

Run `agent-ready readiness --activate` after reviewing the inventory. It installs
one shared assessment in the Git common directory for every local worktree.
Local copies must match it; changing a local file alone never changes admission.
List every local branch and live change. The default branch can be parked while
an admitted change runs. Assess new branches and changes explicitly; update the
inventory and change state together. Parked work consumes no active slot but
remains inventoried and cannot run expensive verification. Ready branch and
change counts each respect `[tool.template.batch].max-builders`. Exact overlapping
planned paths or a shared `serialized-paths` group refuse simultaneous readiness.
Verification execution uses one shared lock across this application's worktrees,
a conservative bound within the configured capacity. A crashed lock blocks;
inspect its owner record before removing only the abandoned lock directory.

## Declare readiness

In the change's `.openspec.yaml` add:

```yaml
verification:
  state: ready
  planned-paths: [src/package/widget.py, tests/test_widget.py]
  dependencies: []
  changelog: 'none: internal preservation change'
  generated-records: []
```

Planned paths are exact relative filenames, including deletions and both sides of
renames. Every changed path outside the selected change folder must be declared.
Dependencies name archived change folders; generated records name required files.
Changelog names a fragment or `none:` with a concrete reason. Existing stage gates
still decide whether a fragment is required. Finish product tasks before
`## 3. Review and evidence` in `tasks.md`; review and metrics remain open.

`agent-ready readiness --base <base>` reports derived readiness without running
verification tools. `agent-ready check --set full --base <base>` refuses unready
work before codemap generation, hooks, or application tests. Focused native tests
and `check --set fast` remain available while editing. Commit product inputs
before the full checkpoint; an expensive checkpoint does not judge dirty work.

## Declare expensive work

Keep declarations in `tool.template.batch.expensive-tiers`. Each entry has a
unique `name`, `paths` globs, and a `command` argument list. Add:

- `inputs`: exact ignored schema/data inputs; tracked files are included already.
- `version-files`: exact files reporting external tool/runtime versions.
- `required-manifest`: JSON with unique `tests` and `shards` ID arrays.
- `result-manifest`: fresh JSON written by the command with completed IDs.
- `sentinel-command`: optional integrity command, always executed uncached.
- `stability-manifest`: optional JSON array of generated file paths; a cache miss
  runs the command twice and requires those files to be byte-identical.

Required tests are nonempty; shards may be empty. Coverage must match exactly:
missing, duplicate and unexpected IDs fail. The wrapper deletes the prior result
manifest before executing, so stale generated output cannot stand in for a pass.
Keep result manifests untracked and ignored so the command does not modify its
input snapshot. The application adapter owns truthful execution reporting and sharding; the
template checks its declared contract and does not implement domain schemas.

`check --set expensive` runs matching tiers. The full checkpoint includes them
and the existing application test adapter, or pytest when no adapter is declared.
Path selection includes renames and deletions. An invalidated checkpoint requires
a rerun even after review corrections; "one checkpoint" is not a maximum.

For junoscfg, a cheap dependency guard runs on lock/projection changes and
reports only its consistency obligation. The checked projection excludes only
the editable root package version; changing any other parsed lock data requires
refreshing it and selects real qualification. Missing/stale projections refuse
even under expensive-only checks and direct adapters. Routine real-schema tiers
qualify only the shipped schema. Assertion execution
has no stability manifest; the separate generation tier has one and runs public
generation twice. Its inputs include the assertion result and exported products,
so changed prerequisite bytes invalidate generation evidence. Generation outputs,
not assertion exports, are the integrity-authoritative retained artifacts.
The [schema qualification instructions](run-a-batch-of-changes.md#run-the-schema-tier-when-the-generators-change)
cover explicit older-release qualification and timing reports.

## Evidence identity and recovery

Evidence lives under `.agent-ready/verification/`. Each command records full
input identity, completion, exit status, timestamps, duration, provenance, output
path and hash, and result hashes. Failed or incomplete evidence cannot be reused.
Unknown, corrupt, missing, legacy or mismatched evidence is a miss. No automatic
legacy import exists. Preserve historical records under their historical rules.

Identity includes tracked source/test/configuration bytes, explicit ignored
inputs, manifests, lockfiles when tracked, comparison base, command/options,
selected declaration, check-package content and version, Python/platform identity,
executable bytes, external version files and a digest of the process environment.
Symlinks, submodules and missing declared files fail closed. Do not include secret
values in declarations; environment values are hashed, not copied into evidence.

Only fixed per-change `review.md`, `metrics.md`, `metrics.json`, `events.jsonl`
and `lifecycle.json` records are excluded from tracked input identity. The
activation inventory is evaluated separately on every admission. Other edits,
including tasks, can conservatively invalidate reuse. Never use this exclusion
for executable inputs. Tool versions that cannot be observed require an explicit
version file or no reuse; adapters must include every external input they read.

Commands that modify their own candidate inputs cannot yield reusable evidence.
Generated artifacts must be current before the checkpoint. An integrity sentinel
must itself bypass the application's cache; the wrapper disables only its own
reuse. A stability second pass executes the actual command again.

## Roll back

Set `tool.template.verification.enabled = false`. This disables admission,
path selection and evidence reuse; full checks retain the application adapter and
run every declared expensive tier uncached. Evidence files are retained. Revert
the activation/configuration commit to restore the previous application policy;
never delete historical evidence to make a check pass. A tool downgrade uses the
reviewed update commit's revert and `uv sync --locked --offline` from the restored
lockfile; Copier does not support arbitrary backwards updates.

## Schema content proof

Schema qualification generates fresh JSON and grammar inputs on every run. The
existing Draft202012 schema validation and Lark compilation can reuse successful
proof only when exact input bytes, worker source, Python and dependency identities
match. The template owns these receipts under `.agent-ready/verification/content`.
The shard's bound outcomes identify each check as `executed` or `reused`, including
its receipt and hash. Missing or corrupt proof runs the actual check; a failure
cannot use an older result. Ordinary `pytest --schema` runs execute both checks.

This reuse leaves both independent serial artifact builds and all other assertions
in place. Byte comparison still covers compressed products; metadata excludes only
`generated_at`. Cold/changed inputs remain slower. Clearing the ignored content
store forces actual validation again; inspect an occupied lock before recovering
an interrupted run. Local proof is not an import or cross-machine trust protocol.
