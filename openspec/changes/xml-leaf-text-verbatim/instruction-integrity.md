<!-- Complete before proposal work. Precedence decides what is effective, not whether it is correct. -->

## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Immutable platform constraints (harness, organisation policy DG-i) | every action; no credentials, personal or operator data in output | 1 | yes | tests use the `AGENTS.md` test-data values; nothing from `private_test_data/` enters a tracked file |
| Runtime (Claude Code, model `claude-opus-5-5`, unattended Builder subagent of the nightly orchestrator, lane C of wave 2) | tool access; roles | 2 | partial: the Builder cannot be its own Test/Challenge or Reviewer | the orchestrator runs those roles as fresh agents if a stop point requires them |
| Invoked skill `agent-ready-change` (`SKILL.md`, phase files) | lanes, phases, roles, gates | 3 | yes | one task, so `batches.md` is not loaded; type `bug`, standard lane |
| Repository `AGENTS.md`, `ARCHITECTURE.md`, `tests/CONTRACT.md`, `src/junoscfg/display/CONTRACT.md`, `docs/how-to/run-a-batch-of-changes.md`, `pyproject.toml` `[tool.template.*]` | house rules, test placement, serialized paths, device-evidence checks, stage `beta` | 4 | yes | fix at the owning layer: `junoscfg.display.xml_to_dict` is "the one XML walker" (display contract, Precedent); the unit test lives in `tests/unit/display/test_to_yaml.py`; `tests/data/device/known-differences.json` is a serialized path |
| Owner instructions: `private_test_data/makeover-work/builder-brief.md` (intake answers of 2026-10-11), `builder-kickoff.md`, the ledger row 9, the orchestrator's task message | ID DEV-17; lane C; stop points; no version bump | 5 | yes | branch `change/xml-leaf-text-verbatim` in `../junoscfg-wt/xml-leaf-text-verbatim`; a known-differences regeneration is reported at STOP-R for the orchestrator to sequence; overlap with change 8 (`value-quoting-by-type`) stops the work |
| Approved specifications: `openspec/specs/conversion/entry-keys/spec.md` (an empty XML element of a value leaf reads as `""`, DEV-16) | XML leaf values | 6 | yes | consistent: this change extends the same reading to text with surrounding spaces |
| Acceptance and device-law tests: `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet`, `tests/unit/display/test_to_yaml.py` | the oracle | 7 | yes | the device-law record carries the four lines of class `xml-value-whitespace-lost`; the fix makes them "recorded but gone", so the record shrinks through `tools/device_differences.py` |
| Device evidence: `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.{xml,set}.gz` (vMX, 23.2R2-S7.5) and `tests/data/device/synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.{xml,set}.gz` (QFX5120, 25.2R2-S1.5) | XML leaf text | evidence, above the schema model | yes | the device writes `<allow-commands>^show </allow-commands>` in XML and `allow-commands "^show "` in display set: the space is part of the value |
| Observed behaviour on `13719d9` (`private_test_data/makeover-work/xml-leaf-text-verbatim/repro.py`, synthetic values) | XML to set and JSON | 8 | yes | `<allow-commands>^show </allow-commands>` reads as `"^show"`; `<passive>\n</passive>` reads as the flag `[null]` and must keep doing so |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Skill phase approvals by the owner versus an unattended run | automatically resolved by precedence | Builder: each approval reads "approved under the owner's unattended-run instruction of 2026-10-11" | phases progress without a relay |
| C2 | The device-evidence rule (a fix that removes a recorded difference commits the record with the fix) versus the kickoff (lane C; `known-differences.json` is serialized and change 8, lane S, holds it and `tools/device_differences.py`) | automatically resolved by precedence (the owner's kickoff names the sequencing) | Builder: commit the code and tests; leave the record and the class in `tools/device_differences.py` untouched; report at STOP-R; the orchestrator sequences the regeneration after change 8 | until then `TestJunoscfgWritesTheDevicesSet` fails for the two XML captures with "recorded but gone" lines, which is the expected shrink, not a regression |
| C3 | Inventory lead "strip only where the node is not a leaf" versus a node outside the tree, which may be a value or a flag | not a source conflict; design choice recorded | Builder: one rule. An element's text is its value as written; text that is only whitespace counts as a value only on a leaf the tree says takes one, so pretty-printed flags (`<passive>\n</passive>`) and containers stay as they are everywhere | no special case per node kind for non-blank text |

## Assurance

<!-- Also set the exact value as `assurance` in .openspec.yaml. -->
- Standing preference: economy
- Standing record: `[tool.template.assurance]` record `docs/how-to/run-a-batch-of-changes.md#assurance`; matched key `default` (no zone entry; no declared break; no trust boundary)
- Mandatory risk floor: not high. One yellow zone (`kernel`, `src/junoscfg/display/to_yaml.py`), no domain table entry for `display/` beyond the conversion it feeds, no security or trust-boundary work, no migration, no named-surface change (`src/junoscfg/__init__.py` and `cli.py` are not edited; no name or signature changes; the production consumer's calls are unchanged and XML values now read as the device wrote them). Under `economy`: no Test/Challenge and no Reviewer role; the regression test fails on the merge base (`agent-ready lane`), one full check before the report, `fields`, `caps`, OpenSpec strict validation.

## Owner decision batch

None asked: the run is unattended. Intake answers 1–8 and the kickoff settle assurance, integration and sequencing; C2 and C3 are settled by repository rules and the kickoff.

## Delta log

<!-- Append later instructions or evidence and their consistency result. -->

- Initial preflight: consistent; C1–C3 resolved. Approved under the owner's unattended-run instruction of 2026-10-11.

- 2026-10-11 resumed phase 5: orchestrator task explicitly lifts C2 after change 8 merged. The branch was rebased by the orchestrator onto integrated master `3ba9300a8a3d7d1bef713a8f202103ebc34e2c9b` (v0.21.0), resume HEAD `5e765a969c76a1a2d60ab19e1dfd18056fc444c0`. Task 2.3 now owns both serialized paths; no concurrent owner edits them. Consistency: same approved DEV-17 scope, no new acceptance promise or assurance waiver; original C2 deferral is historical. Full and expensive/schema checks are explicitly deferred to the orchestrator integration boundary; focused and fast checks run now.
