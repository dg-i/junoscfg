# Verification evidence

Acceptance verification and fresh integrated review are complete. Metrics capture
and the final evidence commit remain pending; the reviewer capability limitation
in review.md remains explicit.

## Environment and execution

Measured on macOS arm64 with Python 3.14.7, jsonschema 4.26.0 and Lark 1.3.1;
template implementation 43433b0. Base: 6d5d41937b82db0e7e5b46c505edb08e72bdefc4.
Native qualification ran `.venv/bin/python -B -m tools.schema_verification qualify
schema-<release>` through `/usr/bin/time -l`; the timing harness measured the whole
subprocess with `time.perf_counter()`. Times include native guards, process startup,
receipts, fresh assertions and two standalone generation passes. Warm means the
pure-check proof store was populated; whole-run completion was executed anew.

The final canonical command was `uv run --locked --group dev --with griffe --with
tach --with towncrier --with vulture agent-ready check --set full` against the
recorded base. Final application head: e8ff3cfcf7d92fc1aab6862305add4f36bb06e90.

## Executed checks

- Independent upstream content-proof tests: 36 passed; existing verification
  tests: 13 passed. Upstream suite: 722 passed; two sandbox-blocked Copier tests
  then passed with permitted cache access, using the same source implementation.
- Optional-framework compatibility correction: four valid/invalid JSON Schema
  and Lark regression cases passed without the development framework.
- Final full checkpoint: 10,448 passed, 37 skipped, 20 xfailed in 221.88 seconds
  for pytest; all repository checks and native tiers passed, total 597.57 seconds.
  Log: `/private/tmp/schema-native-final-full.log`; native receipt provenance is
  retained in events.jsonl at the final application head.
- All three available device releases completed native assertion and two-pass
  generation qualification with exit zero. Existing skips retained their meaning.

## Measured qualification

| Workload | Elapsed seconds | Evidence / conditions |
|---|---:|---|
| Historical cold full checkpoint | 794.74 | Head 60670f058b271776230886379e4803ac6bc2f8a7; 10,444 passed, 37 skipped, 20 xfailed; `/private/tmp/schema-native-full.log` |
| Cold schema portions within that checkpoint | 318.009 | Assertion and generation portions; excludes surrounding full-check work |
| Warm shipped 25.2, run 1 | 112.638111417 | `/private/tmp/schema-native-first-results.json`, first row only; exit 0 |
| Warm shipped 25.2, run 2 | 111.743011875 | `/private/tmp/schema-native-warm-2/results.json`; exit 0 |
| Warm shipped 25.2, run 3 | 112.506422750 | `/private/tmp/schema-native-warm-3/results.json`; exit 0 |
| Three warm runs, arithmetic mean | 112.296 | All three complete native runs meet the owner-approved 180-second target |
| Explicit 21.4 qualification | 287.039505959 | `/private/tmp/schema-native-release-21.4/results.json`; exit 0; distinct release content |
| Explicit 23.2 qualification | 307.921749459 | `/private/tmp/schema-native-release-23.2/results.json`; exit 0; distinct release content |

The second row in schema-native-first-results.json is an exit-1 refusal taking
0.662419709 seconds, not a successful qualification or a warm performance sample.
It is gate cost and excluded from the three-run mean. Peak native warm RSS was
4,515,643,392 / 4,516,347,904 / 4,515,676,160 bytes respectively. This total-process
measurement does not independently isolate the accepted approximately 201 MiB
serialization-memory tradeoff from research.

## Assessment and limits

Feedback time: three warm native observations meet the agreed target; the final
full checkpoint meets the 900-second budget. Cold and warm workload timings are
kept separate; these observations do not establish a long-term regression trend.
Behavioural assurance: original checker semantics, exact protected artifact
comparisons, fresh generation and all-release obligations remain intact.
Reliability: independent failure, corruption, dependency and bytecode probes cover
proof reuse; the ordinary-test dependency regression was caught and corrected.
Longitudinal flake rates remain UNMEASURED. Corpus ownership and structure are
unchanged; no independent corpus reorganization was selected. Local-store trust
and no cross-machine reuse remain the declared boundary. Stronger-reviewer
availability and capability equivalence remain the assurance limitation in review.md.
