<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

`instruction-integrity.md`: C1 (unattended approvals), C2 (the known-differences record and the class in
`tools/device_differences.py` are not edited here; the orchestrator sequences their regeneration after
change 8), C3 (one rule: text verbatim; whitespace-only text is a value only on a tree value leaf).
House rules: fix at the owning layer, `junoscfg.display.xml_to_dict` (display contract, Precedent);
the test at `tests/unit/display/test_to_yaml.py`; tracked files hold synthetic values only.

## Requirements

- `specs/conversion/xml-input/spec.md`, Requirement "An XML leaf's text is its value as written" (new capability).
- Consistent with `openspec/specs/conversion/entry-keys/spec.md` (an empty XML element of a value leaf reads as `""`, DEV-16): unchanged.

## Evidence

- Device: `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.xml.gz` holds
  `<allow-commands>^show </allow-commands>`; the matching `.set.gz` holds
  `set system login class OPS allow-commands "^show "` (vMX, 23.2R2-S7.5); the QFX5120 25.2R2-S1.5
  pair under `tests/data/device/synthetic/qfx5120-25.2R2-S1.5/` holds the same.
- Record: `tests/data/device/known-differences.json` class `xml-value-whitespace-lost`, four lines
  (one missing and one extra per XML capture).
- Base behaviour on `13719d9`: XML input gives `allow-commands "^show"` in set output and `"^show"` in
  JSON; `<passive>\n</passive>` gives the flag `[null]` (synthetic repro, scratch).
- Owning code: `src/junoscfg/display/to_yaml.py` `_xml_leaf` strips every leaf's text; the only XML text
  read in `src/junoscfg` outside the XSD parser. Every XML door (`convert.input.xml_input`, `xml_to_yaml`)
  goes through `xml_to_dict`.
- Tree: 203,156 value leaves (`l`), 120,576 presence flags (`p`), 70 nodes both value leaf and container.

## Non-goals

- DEV-16 (empty element of a value leaf), fixed in change 3.
- Quoting of values holding spaces in set output (change 8).
- Editing `known-differences.json` or `tools/device_differences.py` in this branch (serialized; C2).

## Acceptance criteria

- `tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText::test_spaces_around_a_value_are_kept`
- `tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText::test_whitespace_alone_is_a_value_only_where_the_tree_takes_one`
- `tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText::test_every_door_writes_the_devices_line`
- Each fails on the merge base where it asserts the fix (`agent-ready lane`).
- Device law: `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet` reports exactly the
  four `xml-value-whitespace-lost` lines as "recorded but gone" and nothing else, until the sequenced
  regeneration removes them.
- Before/after comparison over every capture in `tests/data/device/manifest.json`: only XML-input outputs
  change, each change explained by a leaf value's surrounding spaces.
- No independent Test/Challenge required (economy, risk normal).

## Performance expectations

None, because the walker does the same work: it drops one `strip()` per leaf.

## Outstanding decisions

None, because all material decisions are resolved.

## Execution and checkpoint

- Assurance preference: economy
- Risk floor: normal: one yellow zone (`kernel`), no named surface edited, no security or trust boundary, no migration
- Roles required: Builder; Finalizer at phase 7 (orchestrator); no Test/Challenge, no fresh Reviewer
- Resume point: phase 4 (tests); last valid evidence this freeze

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established: preflight `51b459c`, intent `04527e1`, this commit.
- Implementation (phase 5): before/after comparison over every rendering in `tests/data/device/manifest.json`, each rule alone and all rules on (`compare-template.py`, base `13719d9`): 96 of 1,152 conversions differ, all from the two `junoscfg-oracle.xml` captures (vMX 23.2R2-S7.5, QFX5120 25.2R2-S1.5) into the four outputs under the twelve rule settings; every changed line is `allow-commands` gaining the device's trailing space (DEV-17); no diagnostic, field-validation message or exception changes. Device-evidence checks: 3,662 passed, 5 xfailed, 2 failed, the two XML captures of `TestJunoscfgWritesTheDevicesSet`, each with exactly the two recorded `xml-value-whitespace-lost` lines reported "recorded but gone": the expected shrink, sequenced with the record (C2). Conclusion unchanged; no work invalidated.

- 2026-10-11 orchestrator resume instruction: C2 deferral lifted after change 8 merged; task 2.3 may remove the classifier and regenerate the device record. Current immutable integration base is `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b` (v0.21.0), resumed HEAD `5e765a969c76a1a2d60ab19e1dfd18056fc444c0`. Consistency: implementation completes the frozen scope, preserving meaningful whitespace and typed-empty XML handling. The original base `13719d9`, code head `5f93b36`, full failure and comparison remain historical evidence, superseded as current checkpoints by this integration base. Rerun required: regenerated device law, focused tests, fast checks; exact-base comparison and full check remain pending until the orchestrator integration sequence permits them. No full/schema tier runs in this resume.

- Task 2.3 executed: classifier removed; source-output regeneration observed 716 to 712 recorded lines, four XML whitespace-class removals and zero additions. Focused XML/device/typed-empty checks: exit 0, 4,654 passed / 5 xfailed. Fast snapshot correctly rejected uncommitted governed edits; commit then rerun required. New full and exact-base comparison remain pending; historical comparison is not current-base evidence.

- Orchestrator scheduling update: change 9 now integrates before parked change 7. Authorized exact-base comparison against `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b` and one new full check after committed focused/fast evidence. Consistency: execution sequencing only, no runtime scope or assurance change; earlier full/comparison deferral is superseded. No schema-tier inputs changed, so no schema regeneration is required. Product settlement head `7ef8fa5fb8dd72f7813ec6f08e16488b51c7c187`; fast check there exited 0, every check passed.

- Current comparison and full supersede the historical evidence: Exact-base comparison: existing private `private_test_data/makeover-work/xml-leaf-text-verbatim/compare.py` (SHA-256 `d8fcd67eb70ca23edb2bb40fe1cdfe4656afa1961fd3edb6686f2784fc9b0710`), base `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b`, head `53c31f841576447857f6ff6332f8b3bd8a773e7e` (product settlement `7ef8fa5fb8dd72f7813ec6f08e16488b51c7c187`). Both provider `record --anonymize` commands exited 0 and recorded 1,152 conversions. Of the 96 plain conversions, 8 differ; of all 1,152 conversions, 96 differ. Every changed input is `synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.xml` (vMX 23.2R2-S7.5) or `synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.xml` (QFX5120 25.2R2-S1.5), every output difference restores the DEV-17 `allow-commands` trailing space. No diagnostic, field-validation message or exception change; zero exceptions on either side. The provider `diff` exited 0; raw outputs remain private in `integration-base.json`, `integration-head.json`, `integration-diff.txt`, and aggregate provenance in `integration-summary.json`.

Comparison probe history: the initial stricter text-only restoration check exited 1 for 24 YAML outputs, because YAML must quote the restored whitespace value. Format classification showed all 24 were YAML; an evidence-backed parsed-YAML restoration probe exited 0 and confirmed only the specified leaf-value change. No acceptance oracle or product code changed, and no unexplained differences remain.

- New immutable full checkpoint: `UV_OFFLINE=1 npm_config_offline=true OPENSPEC_TELEMETRY=0 PYTHONDONTWRITEBYTECODE=1 uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` at `53c31f841576447857f6ff6332f8b3bd8a773e7e` — exit 0, every check passed; application tests 8,680 passed / 37 skipped / 20 xfailed. Private log: `private_test_data/makeover-work/xml-leaf-text-verbatim/integration-full-check.log`. This replaces the historical failed checkpoint at `5f93b36`. Evidence-only record edits following this check preserve its validity (phase 5); no runtime, test, generated-artifact or configuration edits followed it. No schema-tier inputs changed; schema regeneration was not run.

- Current resume point: bounded finalization; phase-5 implementation complete, metrics/main-spec/archive lifecycle tasks remain open.

- Bounded phase 7: applied the already-reviewed main-spec body without meaning changes (main-spec commit `b45ce0631c9d8b2408fe4f0576ad9eb95c561b28`), recaptured metrics on exact base `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b` / immutable code/full head `53c31f841576447857f6ff6332f8b3bd8a773e7e`. No new instruction/evidence conflict or assurance decision. Previous full evidence retains its immutable scope; later spec/record commits require bounded gates only. Resume at orchestrator pre-merge main-spec review; merge/archive/version/tag/cleanup remain orchestrator-owned.
