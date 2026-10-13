# Execution path and measurement record

## Existing evidence retained

Base master is 6498ec9, v0.28.14. Archived schema-qualification-scope has independent
approval, 10612 passing ordinary tests, 92.97% coverage, schema tier successes and
an 83.88s no-schema checkpoint. Its final combined check was 170.50s with only a
mirror-integrity failure, repaired by supported regeneration and a passing skills
gate. That is component evidence, not a relabelled successful full exit. No prior
native receipt is copied to this physical root. Repeating its evidence-reuse
schema demonstration is unnecessary for ordinary selector changes.

## Actual obligations

- Focused: explicit pytest nodes/files chosen by the developer, or affected_tests
  output. No coverage claim follows unless the command actually enabled coverage.
- Ordinary commit: pre-commit invokes Ruff, deptry, test doors when selected,
  affected-tests on staged paths, caps and Markdown lint when selected. The
  affected hook invokes serial pytest with its selected paths. Shared fixtures,
  project config, lock, package root and shipped data select the complete suite.
- Canonical full under strategy-a: pre-commit retains all integrity hooks while
  the declared affected hook is omitted by the supported shared full runner.
  tools.verification_tests executes the entire default suite on ten workers,
  validates complete/disjoint collection and phase outcomes, and enforces combined
  coverage. Selected real-schema tiers are additional obligations, not ordinary
  --schema tests silently lost from that suite.

Changed tests/runtime/configuration require their affected checks. The full suite
with coverage is distinct from a focused or no-coverage hook run. Separate commits
of the same coherent tooling work can repeatedly select the same broad suite even
when their apparent progress is bookkeeping. OpenSpec metrics/review records do
not themselves select tests; a version/lock change does, intentionally, because
release consistency and environment are executable inputs. Unknown configuration
stays conservative rather than using a content-blind exemption.

## Shared reuse boundary

The existing upstream verification.execute API records the actual command and
validates successful native evidence. Arbitrary prior logs cannot be promoted.
Identity includes command/selection, coverage flags, physical root, base, source
bytes, runtime/environment and policy. Identical staged bytes followed by a commit
can reuse only if all those inputs still match. Changed hook Git environment or
uv driver may conservatively invalidate; no local environment normalization or
receipt copy is introduced. A serial focused run never satisfies the parallel
full coverage command. Historical successful findings inform planning but do not
replace root-bound proof.

## Measurements

Raw local logs: /private/tmp/selection-baseline-setup.log and
/private/tmp/selection-baseline-hook.log. Baseline is a disposable detached worktree
at 6498ec9 with only the CLI-reference generator docstring changed. The comparison
will use the same wording edit and ordinary hooks after selection changes. Neither
measurement changes product assertions. Concurrent upstream checks are a recorded
noise source; these observations do not establish a long-term trend.

Baseline environment setup: 0.47s (uv sync --locked --group dev, 32 installed
packages, Python 3.14.7). Preflight commit including normal hooks: 1.14s.
Failed setup attempts: Git worktree creation and uv cache access were denied by
sandbox, then succeeded with scoped escalation; initial pinned OpenSpec invocation
failed DNS and succeeded with escalation. Initial proposal-only strict validation
correctly failed for absent deltas; the frozen specification then passed. These
attempts remain part of elapsed work, not successful verification.

Whole job and before/after hook totals: pending completion. Token use and complete
interactive setup overhead remain UNMEASURED where no native observation exists.
Targets remain 400s cold, 200s warm and 95s no-schema happy-flow workloads with
dependencies installed. Commit, setup and failed-attempt costs are reported beside
those checkpoints, not silently charged out of end-to-end work.

Baseline ordinary commit finished: **173.37s** wall (116.19 user, 54.84 system),
plus 0.47s setup. All normal hooks passed. Initial selection regressions observed
19 failures/40 passes in 0.86s; selector implementation passed 63 in 3.62s. Shared
adapter integration first found one stale expected selection because its new test
became a genuine consumer (66 passed/1 failed, 3.62s); updating the expected consumer
set produced 67 passed in 3.60s, 3.82s wall. No assertion was removed.
