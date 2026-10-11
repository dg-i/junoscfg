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
