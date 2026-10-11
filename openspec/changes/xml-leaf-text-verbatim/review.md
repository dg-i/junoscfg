# Review: xml-leaf-text-verbatim (ledger #9: DEV-17)

## Review requirement

No fresh isolated Reviewer and no independent Test/Challenge role ran: the standing owner preference is
`economy` (`[tool.template.assurance]`, record `docs/how-to/run-a-batch-of-changes.md#assurance`, key
`default`), and the change sits below the high-risk floor: one yellow zone (`kernel`,
`src/junoscfg/display/to_yaml.py`), no named surface file edited, no security or trust-boundary work,
no migration, no declared break, one domain. `economy` omits both roles below the floor
(`agent-ready-change` phase 6). This record is not a review; the Builder's own checks are listed below
as Builder evidence only.

## Builder evidence (not independent)

- Acceptance tests `tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText` (3): fail on the merge
  base `13719d9`, pass at `5f93b36`.
- Before/after comparison over every rendering in `tests/data/device/manifest.json`, each anonymize rule
  alone and all rules on: 96 of 1,152 conversions differ, all from the two `junoscfg-oracle.xml`
  captures, every changed line the `allow-commands` value gaining the device's trailing space; no
  diagnostic, field-validation message or exception changes.
- Full check at `5f93b36`: every step passes except the application tests: 7,561 passed, 37 skipped,
  18 xfailed, 2 failed. The two failures are
  `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet::test_only_the_recorded_lines_differ`
  for `synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.xml` and `synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.xml`,
  each reporting exactly the two `xml-value-whitespace-lost` lines "recorded but gone (shrink the record)".

## Open before merge

- Task 2.3: remove the class `xml-value-whitespace-lost` from `tools/device_differences.py` and regenerate
  `tests/data/device/known-differences.json` with `uv run --locked python tools/device_differences.py`.
  Both are held by change 8 (`value-quoting-by-type`, lane S) and the record is a serialized path, so
  the orchestrator sequences this step after change 8 merges (kickoff; preflight C2). Then the full
  check runs once more on the rebased branch.

## Specification challenges

None.

## Resumed implementation evidence (2026-10-11)

The original task-2.3 deferral above is historical. Change 8 merged; the orchestrator lifted C2 and rebased this branch onto `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b` (v0.21.0), resumed HEAD `5e765a969c76a1a2d60ab19e1dfd18056fc444c0`. Task 2.3 removed the classifier and regenerated the record from captured source outputs: 716 to 712 lines, exactly four removals, no additions. Focused tests pass (4,654 passed / 5 xfailed). The old full check at `5f93b36` is superseded; a new full checkpoint and exact-base comparison are still required at the orchestrator's integration boundary. Existing economy/risk rationale remains unchanged; these are Builder checks, not an independent review.
