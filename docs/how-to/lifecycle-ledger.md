# Lifecycle events and comparable cohorts

Human intent, acceptance criteria, findings and decisions remain authoritative.
The event ledger generates observations; it does not approve requirements or
infer usage from text length. Missing observations remain `UNMEASURED`.

## Capture events

`agent-ready lifecycle append --change <slug> --input <event.json>` appends one
validated event to the live change's `events.jsonl`. The input contains `base`
and `head` as immutable full SHAs, `actor`, timezone-qualified `at`, `kind`,
`source` with relative `path` and `sha256`, and `payload`. Keep source artifacts
immutable and available for revalidation. The writer adds schema, change,
sequence, predecessor and event digest. Reordering, duplicates, corrupt events
or changed source artifacts refuse reporting. Concurrent append fails safely.

Supported kinds: `intent`, `archive`, `verification`, `progress`, `role`,
`observation`, `finding`, `ruling`, `carry`, `renew`, and `close`.

- Verification payload: `tier` (`full`, `expensive`, `focused`), `checkpoint`,
  `evidence`, `duration_ms`, integer `exit_status`, and boolean `reused`.
  The verification wrapper generates full and expensive command events.
- Progress payload: integer `completed` and `total` counts from the task source.
- Role payload: `role`, `verdict`, and `referent` identifying reviewed evidence.
- Observation payload: `metric`, `value`, or null plus `reason` when unavailable.
- Finding payload: `id`, `severity`, `requirement`, `counterexample`, `path`,
  `disposition`, and `invalidated-evidence` ID array. Keep rejected findings.
- Ruling payload: `finding`, `decision`, `authority`, `scope`, boolean
  `requirement-change`, and `role`. One ruling per finding. The orchestrator
  records ordinary rulings once; Builders consume that record. A requirement
  change requires role `owner`, a distinct actor, and the owner's authority
  reference. Actor labels index provenance; they are not authentication.
- Carry payload: `id`, `owning-change`, `risk`, `dependencies` array,
  `discovery-date`, `target-checkpoint`, and timezone-qualified `expires-at`.
- Renewal payload: existing `id`, `authority`, `reason`, `target-checkpoint`,
  and a future `expires-at`; renew before expiry, never retroactively.
- Closure payload: existing `id`, `authority`, and `closure` evidence.

Scope interim actions exactly to the owner's recorded ruling. Do not generalize
an interim exception into a new requirement. New evidence creates a new finding;
it does not silently overwrite the existing ruling.

## Generate records

`agent-ready lifecycle report --change <slug> --base-sha <SHA> --head-sha <SHA>`
writes `lifecycle.json`. The existing `agent-ready metrics` command imports the
same generated summary into `metrics.json` and its Markdown view. Each summary
names its ledger hash and immutable SHA pair. Checks, durations, checkpoint IDs,
progress, role verdicts and archive status come from all validated events for the change, including failed attempts before rebases.
The requested base and head must resolve to immutable commits; checkpoint validity
is evaluated separately by verification identity.
Intent-to-archive spans observed intent and archive events, not Git timestamps.
Usage and active minutes require explicit observed sources or existing runtime
telemetry; absent values are never estimated. Archive the ledger with the change.

## Compare cohorts

`agent-ready lifecycle cohort --input <cohort.json>` prints a descriptive report.
The input has a `records` array. Each member names `pair`, `arm` (`baseline` or
`strategy-a`), `kind` (`high-risk-bug` or `bounded-fix`), `application`,
`environment`, `task`, `policy`, `record-kind` (`observed` or `synthetic`), and a
relative completed lifecycle `summary` path with its `sha256`. Keep its sibling
`events.jsonl` and original source artifacts available: comparison regenerates
the summary and rejects repeated completed-change identities.

Match task, application, environment, kind and record kind across both arms.
At least five completed high-risk-bug pairs and five bounded-fix pairs make the
comparison eligible. Report unmatched members and each missing measurement.
Medians require complete observations for that metric in both arms; a missing
value yields `UNMEASURED`, not zero or a favorable complete-case estimate.

Metrics: intent-to-archive minutes, active agent minutes, output/cache tokens,
full/expensive runs, review findings, post-review code churn and escaped
regressions. Synthetic fixtures prove the mechanism, not workflow improvement.
The existing comparative protocol's ten-pair directional and twenty-pair policy
floors still apply. Provenance truth, independence and follow-up completeness need
independent review. This command never declares measured improvement.
