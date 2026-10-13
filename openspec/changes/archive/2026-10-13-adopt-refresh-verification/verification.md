# Refresh verification evidence

Exact updater: ef33c70f8c04b9712eb9897761d52d0439dbb33f, reproduced from
95585fbf1cd59fe4b9cb15be870f6a5020be49a3 with matching local attestation.
Application adoption full checkpoint: fbce438a58c5ba42dcc45d48db94db33e446c791,
base ef33c70f8c04b9712eb9897761d52d0439dbb33f.

Command: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full --base ef33c70`.
Every gate passed. Application suite: 10440 passed, 37 skipped, 20 xfailed in
211.47 seconds; branch coverage 92.97%. All 12 selected real-schema assertions passed separately;
the schema wrapper also verified two actual public generation builds and stability.
The extra 24 default-suite skips correspond to the other schema parametrizations
made discoverable by the three physical dumps; they are not schema qualification.

Whole checkpoint elapsed: 1661.945 seconds, measured around the canonical command.
It was uncached for schema tiers: the earlier standalone qualification had the
same file inputs but a different environment fingerprint, so native reuse refused.
No identity or receipt was rewritten to force reuse. The earlier successful
qualification measured 827.563045 seconds for assertions and 434.378303 seconds
for double generation; final-check assertions measured 842.184589 seconds.
Historical comparable full-with-qualification observation: 1695.965102 seconds;
no controlled speedup or new regression is inferred from these single runs.

The owner approved a provisional 900-second whole-full budget after initially
choosing 275 seconds. The uncached run exceeds it; the record preserves that known
workload gap instead of changing the budget or waiving checks. Final budget edits
are documentation only and receive fast checks, not another runtime/schema rerun.

Earlier refusals remain evidence, not passes: the exact updater had a stale
fingerprint; its deliberate red checkpoint deferred the already-failed hook.
The owning generator repaired it in a separate reviewed commit (12 focused tests
passed). The first full attempt took 367.932 seconds and failed because runtime
identity was prepared in the temporary tooling environment; preparation in the
actual project environment repaired that setup error. Missing assertion exports
were a consequence of that refusal. Native events retain failed and successful
schema attempts. No test, policy, hook, cap or stage was weakened.

Final full log SHA-256: 4da24119aeeba0c28d330b9a7542f62ed671197755087742de08b57cb43e3c09.
Native schema receipts: `e42f8ddd1bad4b08a81ae1e7a18a56f1.json` (assertions)
and `65b52cb888794255bba2914966fa043a.json` (generation).
Native receipts/logs are retained under `.agent-ready/verification/` in the refresh
worktree and copied to the main checkout's refresh evidence directory at merge.

Native full receipt: `.agent-ready/verification/a91ded28d4324e2582712ba73be4be55.json`;
native duration 1659.230025 seconds, exit zero. Native log SHA-256:
`19371dfce2e00530392cf221827a54471990534a815de43f732f8be05140d7e3`.
The outer 1661.945-second measurement includes command startup/return overhead.

Final documentation follow-up: canonical `--set fast --base ef33c70` passed on db42944. No runtime changes followed the full checkpoint.
