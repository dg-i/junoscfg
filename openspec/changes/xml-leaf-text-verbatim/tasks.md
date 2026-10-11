## 1. Verification

- [x] 1.1 Acceptance tests in `tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText`: `test_spaces_around_a_value_are_kept` (a single leaf, a leaf list, an entry key), `test_whitespace_alone_is_a_value_only_where_the_tree_takes_one` (a value leaf takes `" "`; a pretty-printed flag, container and element outside the tree read as their empty spelling), `test_every_door_writes_the_devices_line` (`xml_to_dict`, `xml_to_yaml`, `convert_config` to JSON, YAML, set and structured, `junoscfg convert -i xml -e set`). All three fail on the merge base `13719d9`.
- [x] 1.2 Independent Test/Challenge: not run; `economy` below the high-risk floor omits it (evidence freeze, Execution and checkpoint).

## 2. Change

- [x] 2.1 `src/junoscfg/display/to_yaml.py` `_xml_leaf`: the text is the value as written; whitespace-only text is a value only on a tree value leaf.
- [x] 2.2 Changelog fragment `changelog.d/+xml-leaf-text-verbatim.bugfix.md`; no version bump (the orchestrator bumps at merge).
- [x] 2.3 Sequenced by the orchestrator after change 8: remove class `xml-value-whitespace-lost` from `tools/device_differences.py` and regenerate `tests/data/device/known-differences.json` (serialized path).

## 3. Review and evidence

Pre-review checkpoint: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` at 5f93b36: every step passed except the application tests, 7,561 passed / 37 skipped / 18 xfailed / 2 failed; the two failures are the device law for the two XML captures, the four `xml-value-whitespace-lost` lines "recorded but gone", closed by task 2.3.

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it: not required, `economy` below the high-risk floor (`review.md`).
- [x] 3.2 Capture `metrics.md` and `metrics.json` for immutable base `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b` and code/full-check head `53c31f841576447857f6ff6332f8b3bd8a773e7e` (product settlement `7ef8fa5fb8dd72f7813ec6f08e16488b51c7c187`).
- [x] 3.3 Finalizer completes bounded pre-merge spec application, metrics evidence, and archive preparation without product edits. The orchestrator owns merge and the subsequent live-folder archive, version and tag.

## Resumed phase-5 checkpoint (2026-10-11)

Integration base: `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b` (v0.21.0); resumed records HEAD: `5e765a969c76a1a2d60ab19e1dfd18056fc444c0`. The orchestrator rebased the branch and lifted C2 after change 8 merged. The historical full result above at `5f93b36` is superseded and does not establish a current full checkpoint.

Task 2.3: `UV_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 uv run --locked python tools/device_differences.py` succeeded. Actual regeneration shrank 716 recorded lines to 712, removing four `xml-value-whitespace-lost` lines (missing and extra for each vMX/QFX5120 XML oracle capture), with no added lines or other class changes. The classifier was removed at its source; the JSON was not hand-edited.

Focused check: `UV_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 uv run --locked pytest -q tests/unit/display/test_to_yaml.py tests/unit/convert/test_field_validator.py tests/corpus/test_device_renderings.py tests/corpus/test_device_anonymization.py tests/contract/test_format_matrix.py 'tests/contract/test_round_trip_validates.py::TestTheExampleRendersValid'` — exit 0, 4,654 passed / 5 xfailed. This includes the whitespace acceptance cases and the typed-empty XML regression cases.

Fast attempt before the product commit: `UV_OFFLINE=1 npm_config_offline=true OPENSPEC_TELEMETRY=0 PYTHONDONTWRITEBYTECODE=1 uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set fast` — exit 1 at `snapshot`, because governed changes must first be committed. Resolution: normal-hook product commit, then rerun on that immutable head.

Remaining: fast checkpoint after commit; exact-base 96/plain and 1,152/rule comparison using the existing private provider; one final full checkpoint after the orchestrator integration sequence. Full and expensive/schema checks were not run in this resume, as explicitly instructed. Metrics recapture, main-spec application and archive remain open (tasks 3.2/3.3); no new assurance waiver or self-review is recorded.

Scheduling supersession: the orchestrator releases exact-base comparison and one full checkpoint now, before integrating change 9. Fast check at product settlement HEAD `7ef8fa5fb8dd72f7813ec6f08e16488b51c7c187` exited 0 (every check passed) with the command above after the normal-hook commit. Full/comparison deferral above is historical; both now run against the stated integration base and settled code. Schema tier is not triggered. Tasks 3.2/3.3 remain open.

## Current phase-5 completion evidence

Exact-base comparison: existing private `private_test_data/makeover-work/xml-leaf-text-verbatim/compare.py` (SHA-256 `d8fcd67eb70ca23edb2bb40fe1cdfe4656afa1961fd3edb6686f2784fc9b0710`), base `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b`, head `53c31f841576447857f6ff6332f8b3bd8a773e7e` (product settlement `7ef8fa5fb8dd72f7813ec6f08e16488b51c7c187`). Both provider `record --anonymize` commands exited 0 and recorded 1,152 conversions. Of the 96 plain conversions, 8 differ; of all 1,152 conversions, 96 differ. Every changed input is `synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.xml` (vMX 23.2R2-S7.5) or `synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.xml` (QFX5120 25.2R2-S1.5), every output difference restores the DEV-17 `allow-commands` trailing space. No diagnostic, field-validation message or exception change; zero exceptions on either side. The provider `diff` exited 0; raw outputs remain private in `integration-base.json`, `integration-head.json`, `integration-diff.txt`, and aggregate provenance in `integration-summary.json`.

Comparison probe history: the initial stricter text-only restoration check exited 1 for 24 YAML outputs, because YAML must quote the restored whitespace value. Format classification showed all 24 were YAML; an evidence-backed parsed-YAML restoration probe exited 0 and confirmed only the specified leaf-value change. No acceptance oracle or product code changed, and no unexplained differences remain.

New immutable full checkpoint: `UV_OFFLINE=1 npm_config_offline=true OPENSPEC_TELEMETRY=0 PYTHONDONTWRITEBYTECODE=1 uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` at `53c31f841576447857f6ff6332f8b3bd8a773e7e` — exit 0, every check passed; application tests 8,680 passed / 37 skipped / 20 xfailed. Private log: `private_test_data/makeover-work/xml-leaf-text-verbatim/integration-full-check.log`. This replaces the historical failed checkpoint at `5f93b36`. Evidence-only record edits following this check preserve its validity (phase 5); no runtime, test, generated-artifact or configuration edits followed it. No schema-tier inputs changed; schema regeneration was not run.

Current resume point: bounded finalization. All test/implementation tasks are complete; tasks 3.2 and 3.3 remain open for metrics recapture against the current immutable base/code head, reviewed main-spec application, and archive housekeeping. Original economy/risk omission remains unchanged; no independent review is claimed.

Environment evidence: initial offline OpenSpec `status` and `instructions apply` calls exited 1 with npm `ENOTCACHED` and blocked cache-log access under the filesystem sandbox. One evidence-backed offline cache escalation made both commands succeed (exit 0), without network access. Fields and caps exited 0 before the final evidence commit; normal hooks remain enabled.

## Bounded phase-7 pre-merge completion

The reviewed delta was applied through offline OpenSpec 1.13.0 `archive xml-leaf-text-verbatim --yes` in disposable clone `/private/tmp/xml-leaf-phase7-spec-apply`; only `openspec/specs/conversion/xml-input/spec.md` was brought back. The disposable command reported the two then-open housekeeping tasks; it did not archive the live folder. A byte comparison against the reviewed delta after only the main title, Requirements heading and Purpose spacing transformations confirms the purpose, requirement and all four scenarios are unchanged. The generated Purpose already contains the reviewed purpose, with no placeholder. Main-spec commit: `b45ce0631c9d8b2408fe4f0576ad9eb95c561b28` (one new spec, 46 added lines). Strict change validation and all-spec validation passed (22 specs).

Metrics capture exited 0 for base `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b` and immutable code/full-check head `53c31f841576447857f6ff6332f8b3bd8a773e7e`. Its five-file product scope records 91 added and 28 removed lines; the later main-spec addition and evidence records are outside that measurement. Native usage, cost, human effort and workflow telemetry are UNMEASURED; no bound evidence was supplied. The full result remains scoped to `53c31f841576447857f6ff6332f8b3bd8a773e7e`, not the later finalizer commits; subsequent changes are reviewed main-spec application and records only. No product/test/acceptance promise or review verdict changed.

Next incomplete lifecycle operation: orchestrator review of bounded main-spec evidence, merge, then supported `archive --yes --skip-specs`, version/tag and cleanup. All pre-merge tasks are complete; the live folder remains. Fields, caps, lane and post-commit fast checks are required for this bounded finalization; no full/expensive/schema rerun is authorized for these record/spec edits.
