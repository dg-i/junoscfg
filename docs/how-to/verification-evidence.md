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
- `runtime-command`: optional Python invocation prefix, for example
  `[".venv/bin/python"]`, paired with `runtime-packages`: canonical names of the
  installed distribution closure used by the tier. The runtime is probed before
  every receipt lookup and after successful execution; stale preparation is not proof.
- `selection-command`: optional application classifier argument list. It receives
  `--base <resolved-commit>` and must exit zero with exactly `{"selected": true}` or
  `{"selected": false}` on stdout. It replaces path matching while admission is
  enabled and runs on every invocation before reuse. Errors or ambiguous output
  select conservatively. The application owns complete input/runtime classification;
  a freshly prepared context alone cannot establish successful qualification.
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

## Bounded scheduling

`tool.template.verification.gate-workers` defaults to 1 and permits 1–16 workers.
Only consecutive native read-only tach, OpenSpec and stage gates overlap. Index
construction, hooks and other gates remain barriers. `overlap-tiers` defaults to
false; opting in requires `full-suite = true`, the application's declaration that
its configured `tool.template.test-command` (or default pytest command) executes
its complete required suite and coverage checks. All preceding gates finish before
that suite and the serial expensive-tier sequence overlap in two workers.

An optional `affected-test-hook` names one duplicate affected-test hook. It requires
`full-suite = true` and is suppressed only in a full invocation whose plan includes
the complete application suite. Fast and docs-lane plans keep the hook. Full checks
refuse inherited `SKIP`, so unrelated gates cannot silently disappear. Worker and
gate failures propagate, every selected tier is attempted, and the shared capacity
lock and native checkpoint/lifecycle receipts remain in force. Install/sync runtimes
before overlap and use existing Python environments in concurrent adapters.

Qualify adapter completeness, fixture isolation and selection boundaries using
[parallel verification](parallel-verification.md). `full-suite` is an application
assertion, not native inspection of worker reports or a proof of test completeness.

## Evidence identity and recovery

Evidence lives under `.agent-ready/verification/`. Each command records full
input identity, completion, exit status, timestamps, duration, provenance, output
path and hash, and result hashes. Failed or incomplete evidence cannot be reused.
Unknown, corrupt, missing, legacy or mismatched evidence is a miss. No automatic
legacy import exists. Preserve historical records under their historical rules.

Identity includes tracked source/test/configuration bytes, explicit ignored
inputs, manifests, lockfiles when tracked, comparison base, command/options,
selected declaration, check-package content and version, Python/platform identity,
executable bytes, stdlib/native library and installed dependency bytes, startup
hooks, import-path order, external version files and a digest of the process environment.
A declared tier runtime additionally binds its executing interpreter/dependency
closure and startup/import context. Application source bytes remain in the tracked
manifest; ignored import shadows and anomalous or sourceless bytecode are bound too.
Normal cached code is ignored only after proving it equals compilation of the bound
source at the cache's optimization level. Changing semantic cached code invalidates proof.
The active uv temporary overlay prefix is canonicalized only in identity path fields,
`PATH`/`VIRTUAL_ENV`, and an exact launcher interpreter shebang. Overlay program
literals, other environment values, executable and startup bytes remain meaningful.
Candidate and declared input symlinks, submodules and missing declared files fail closed.
Runtime import symlink targets and their code participate in identity; traversal
detects directory cycles and refuses inaccessible targets. Do not include secret
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

## Exact-content proof

The existing `agent_ready_checks.verification_content.execute_content` API is for
isolated, side-effect-free checks of captured input bytes. Its worker may read only
that input and import stdlib plus declared distributions; the caller owns that
contract, and the API is not a sandbox. Keep other checks on whole-command evidence.

Content receipts under `.agent-ready/verification/content` bind exact input and
worker bytes, operation, Python and dependency identity. Retain the complete
returned reference (`id`, `executed` or `reused` status, receipt path and hash) in
the adapter's completion report. Call `verify_reference(root, reference)` from the
same module for each reference before publishing completion; a failed recheck
must fail the adapter. Declare that report in the enclosing tier's `evidence-files`
so whole-command evidence binds it. Whole-command validation does not recursively
validate nested content references. Missing, corrupt or mismatched proof executes
the check; failure cannot borrow an older success. This local proof is not a
cross-machine trust protocol.

Reuse does not replace fresh input generation, independent stability passes,
other assertions or whole-run identity. Keep integrity sentinels uncached. To
measure cold content checks, invalidate the enclosing whole-command receipt too
and confirm actual execution; clearing only content proof cannot force a cached
whole command to run. Inspect occupied locks before recovering interrupted work.
Application-specific worker contracts and artifact authority belong in companion
pages, following the refresh skill's ownership rule.

## Roll back

Set `tool.template.verification.enabled = false`. This disables admission,
path selection and evidence reuse; full checks retain the application adapter and
run every declared expensive tier uncached. Evidence files are retained. Revert
the activation/configuration commit to restore the previous application policy;
never delete historical evidence to make a check pass. A tool downgrade uses the
reviewed update commit's revert and `uv sync --locked --offline` from the restored
lockfile; Copier does not support arbitrary backwards updates.
