## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime (Claude Code, Opus 5.5, offline) | Tools, filesystem | Highest | yes | Isolated worktree `/private/tmp/junoscfg-device-validation`; no network, no device calls, no push |
| Organisation policy (DG-i) | All output | Highest | yes | Never repeat a credential: the owner's log `private_test_data/error-messages.txt` and the captures hold synthetic secrets, quoted nowhere; synthetic values only in tests |
| Owner request 2026-10-16, relayed first-hand by the coordinator | This change | Owner (relayed) | yes | Fix the validators' errors on the committed device captures (device output is the oracle); add tests that catch such errors on captures; full-checkpoint budget may rise by at most 25 %, none preferred |
| Owner-approved design, relayed in the same brief | This change | Owner (relayed) | yes | Per-format XSD fixes (or an equivalent simpler rule); JSON/XML/YAML validation follows Juniper's names plus device-proven additions; regenerate artifacts through the supported path; update the fix counts; device-capture validation law plus focused unit tests, written first |
| Coordinator scope rulings 2026-10-16 (investigation report RC1–RC6, MSG1, MSG2) | This change | Coordinator, within the owner's direction | yes | Root causes and rulings listed in the proposal; rulings marked (P) are pending owner decisions with interim defaults |
| Coordinator coordination instructions | Shared inventory, files owned by parallel sessions | Coordinator | yes | Readiness parked until re-admitted; do not edit device captures, manifest, README or `tools/import_device_captures.py`; `known-differences.json` and `grammar-corpus.json` belong to the parallel session (see C2) |
| AGENTS.md, ARCHITECTURE.md §1, §8 | Repository | Repository | yes | Evidence hierarchy (device > corrected schema model > artifacts); one IR; generated artifacts never hand-edited; fix at the owning layer; equivalent, not identical; docs checklist item 6 (fix counts) |
| `src/junoscfg/validate/CONTRACT.md`, `tests/CONTRACT.md` | Modules, tests | Repository | yes | Corrections live in `xsd_fixes.py`; runtime validators import no `xsd_*` module; tests at the owning layer, package doors, strict xfail only |
| `docs/decisions/2026-10-15-configuration-input-is-trusted.md`, `tests/contract/test_every_message.py` | Messages | Decisions | yes | Messages name a path and a reason; no hardening against hostile input |
| agent-ready-change skill and phases | Workflow | Skill | yes | Standard lane, type bug; tests first; one full checkpoint; fresh Reviewer dispatched by the coordinator |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Brief: "keep conversion output byte-identical"; measured at base: set input written as JSON spells `802.3ad` and `to` where the device's JSON spells `ieee-802.3ad` and `end-range`, and JSON input never resolves the renames (one configuration, two IRs). Coordinator ruling RC2a relaxes the brief | automatically resolved by precedence | Builder: set and structured output byte-identical over every capture and the corpus; legacy `yaml` identical unless the IR unification changes it (reported); JSON, yaml-new output may change only toward the device's spelling, each change counted | JSON and yaml-new output change for renamed statements |
| C2 | Coordinator: `known-differences.json` and `grammar-corpus.json` belong to the parallel session; repository rule: a fix shrinks its record, and the device law fails on a recorded line that is gone | runtime/operator correction | Builder regenerates both records only through their tools (`tools/device_differences.py`, `tools/device_grammar_corpus.py`) after merging master, and reports the edit to the coordinator | Merge order with qfx-null-probes |
| C3 | Brief names `XsdFix.targets`; the code's field is `applies_to`, identical on all 42 fixes and read by nothing | automatically resolved by precedence | Builder: the owner allowed "an equivalent, simpler rule if the code shows one" | Recorded in the proposal |
| C4 | Risk floor: a named surface's output changes (validation results, JSON output) — high risk requires independent Test/Challenge and a fresh Reviewer; the brief says the coordinator dispatches the Reviewer | automatically resolved by precedence | Builder dispatches an independent Test/Challenge read of the acceptance tests in phase 4; the coordinator dispatches the Reviewer | Phase 4 and 6 |
| C5 | Rulings marked (P): placement of undocumented-statement fixes; the general keyed-singleton rule; "no validation message reprints a subtree" as a rule | owner decision required | Interim defaults taken as ruled, each recorded in `review.md` as a pending owner decision | None blocking |
| C6 | `-v` on XML needs `junos-validated.xsd`, which is not shipped | automatically resolved by precedence | Out of scope (documented limitation); the law covers XML through field validation | Recorded |

## Assurance

- Standing preference: economy (`pyproject.toml` `[tool.template.assurance]`, record
  docs/how-to/run-a-batch-of-changes.md#assurance; keys `default` and `declared-break`).
- Required roles: Builder; independent Test/Challenge; fresh isolated Reviewer at least as
  capable as the Builder (dispatched by the coordinator); Finalizer (later, by instruction).
- Mandatory risk floor: high. Named surfaces (`consumer`: `validate_config`,
  `convert_config` diagnostics and JSON output; `cli`: `-v`, field-validation messages,
  `-e json`) change results.

## Execution checkpoint

Base `2d4904b` (master, v0.28.21). Worktree `/private/tmp/junoscfg-device-validation`,
branch `change/device-validation`. Standard lane, type bug, zone schema. Schema dumps copied
physically into `private_test_data/schemas/`. Regeneration: `uv run pytest tests/ -q
--regen-schema`. Full check: `uv run --locked --group dev --with griffe --with tach --with
towncrier --with vulture agent-ready check --set full` once readiness re-admits the branch.
Integration: not by the Builder (hand-off after phase 5).

## Owner decision batch

None blocking; the (P) rulings carry interim defaults (C5).

## Delta log

- Initial preflight: consistent after C1 to C6. Resume: phase 1 proposal.
- Coordinator request: readiness parked (commit `bad05a9`) until re-admitted.
- Phase 1: proposal written within the owner's approved direction and the coordinator's
  rulings (the request fixes the scope; no routine reconfirmation). Resume: phase 2.
