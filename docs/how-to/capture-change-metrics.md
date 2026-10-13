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

Use `--workflow-telemetry PATH` for provider-neutral workflow observations.
The file is bound to the same immutable change and SHA pair:

```json
{
  "schema_version": 1,
  "change": "my-change",
  "base_sha": "full-base-commit-id",
  "head_sha": "full-code-commit-id",
  "entries": [
    {
      "phase": "implement",
      "role": "builder",
      "provider": "provider-name",
      "model": "model-name",
      "usage": {
        "input_tokens": 100,
        "output_tokens": 20,
        "cache_reads": 1,
        "cache_writes": 1,
        "cache_read_input_tokens": 80,
        "cache_write_input_tokens": 10
      },
      "commands": [
        {
          "kind": "test",
          "name": "pytest tests/test_feature.py",
          "duration_ms": 1200,
          "outcome": "passed"
        }
      ],
      "retries": 0,
      "regenerations": 1,
      "stalls": [],
      "owner_interventions": [
        {"duration_ms": 60, "reason": "resolved an acceptance criterion"}
      ]
    }
  ]
}
```

Roles are `builder`, `test-challenge`, `reviewer`, or `finalizer`; command kinds
are `command` or `test`; outcomes are `passed`, `failed`, `error`, or
`cancelled`. Usage may be null. Each usage counter may be a nonnegative integer
or null when the provider does not expose it. Durations are finite nonnegative
milliseconds, and reasons, phases, providers, models, and command names are
nonempty. The importer retains entries, hashes the exact file, and derives
additive summaries. An empty entry list is unmeasured. Unknown fields, invalid
roles or outcomes, negative counters, and identity mismatches are rejected.

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
