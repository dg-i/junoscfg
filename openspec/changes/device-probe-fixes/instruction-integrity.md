## Effective instruction stack

| Source | Scope | Priority | Available | Effect on this change |
|---|---|---|---|---|
| Platform and runtime (Claude Code, Opus 5.5, offline) | Tools, filesystem | Highest | yes | Worktree `/Users/manon-dev/src/junoscfg-wt/device-probe-fixes`, branch `change/device-probe-fixes`; no network, no device calls, no push |
| Organisation policy (DG-i) | All output | Highest | yes | No credential, hostname or user name leaves `private_test_data/`; the probe output names the device and the user, so it is quoted nowhere; synthetic values only in tests |
| Coordinator brief carrying the owner rulings of 2026-10-17 (first-hand, approved) | This change | Owner (relayed) | yes | One standard-lane change: record the QFX5120 probe of 2026-10-16 and fix VERB-PREFIX-001 with the validator half of A2, ANCESTOR-TAGS-001, RELATIVE-TAGS-001 (ruling 2), LEAF-LIST-VALUE-TAGS-001, UNDOCUMENTED-001; close HOLD-TIME-001, RENAME-EVIDENCE-001 (five renames) and JSON-KEYWORD-ALIAS-001 (ruling 1). Stop after the acceptance tests and before review; no push |
| AGENTS.md, ARCHITECTURE.md section 8 | Repository | Repository | yes | Device output outranks the schema model; equivalent, not identical; fix at the owning layer; measure the blast radius; one IR; generated artifacts are regenerated, never edited; beta stage, patch for a non-break |
| agent-ready-change skill (SKILL.md, phases 0, 1, 2, 4 read so far) | Workflow | Skill | yes | Standard lane, type bug; tests first and seen failing; one full checkpoint on a committed snapshot; high-risk floor |
| `docs/how-to/run-a-batch-of-changes.md`, `docs/how-to/settle-a-schema-question.md` | Process | Repository | yes | Own worktree; private entries linked, the three XSD dumps hard-linked as physical files; device-evidence checks and the before/after comparison; serialized paths (`xsd_fixes.py`, `validate/data/`, `known-differences.json`); the schema tier when generated products change; evidence frozen once, sanitized |
| `src/junoscfg/validate/CONTRACT.md`, `convert/CONTRACT.md`, `display/CONTRACT.md`, `input.CONTRACT.md`, `tests/CONTRACT.md` | Modules, tests | Repository | yes | Corrections in `xsd_fixes.py`; `display` and `input` are the kernel; validate may not import convert; tests at the owning layer through package doors; strict xfail only |
| Approved specs `conversion/path-filtering`, `validation/set-command-validation`, `schema-pipeline/conversion-hints`, `validation/device-captures` | Requirements | Specs | yes | Requirements this change modifies; ruling 2 reverses part of path-filtering |
| `docs/BACKLOG.md` entries named in the brief | Backlog | Repository | yes | Each touched entry gets the evidence, its status and a link to this change |

## Conflicts

| ID | Sources and contradiction | Classification | Resolution owner and safe action | Effect |
|---|---|---|---|---|
| C1 | Owner ruling 2 versus the approved `conversion/path-filtering` requirements ("a tag on the selected statement itself is a bare command in set output") | automatically resolved by precedence | Owner ruling wins; carried as a MODIFIED delta that cites the device evidence (SC1: the device refuses a bare `deactivate` and `protect`) and the ruling | The relative scenario "set r1, deactivate, protect" changes |
| C2 | Owner ruling 1 versus the approved `schema-pipeline/conversion-hints` text, the changelog fragment `+device-validation.bugfix.md`, BACKLOG and tests that call the keyword alias "deprecated" | automatically resolved by precedence | Owner ruling wins; the records and the test name are corrected; behaviour does not change | Records only |
| C3 | Existing tests pin behaviour the rulings change: `tests/unit/validate/test_set_validator.py::TestSetValidator::test_deactivate_line` and `TestEveryVerbIsValidated::test_a_verb_line_is_validated_as_its_path` take a verb line ending in a leaf's value; `tests/unit/convert/test_convert_api.py::TestPathFiltering::test_a_relative_leaf_selection_writes_its_tags_as_a_container_does` pins the bare verbs | specification/test disagreement | Resolved by rulings 2 and 3a: the brief allows a verb line to stop at a container, at a leaf before its value, or after a list entry's full key, nothing else; the tests change with the delta | Three tests change their expectation |
| C4 | Ruling 3a names "one value of a leaf-list"; a scalar leaf's value after a verb is not named. The brief's list of allowed stops excludes it, and the set reader already refuses it ("Metadata commands cannot target scalar-leaf values") | automatically resolved by precedence | Builder applies the brief's list as written: a leaf's value, single or one of a list, is no statement | Recorded in the proposal; a challenge may reopen it |
| C5 | The rule covers every non-`set` verb; the device evidence covers `deactivate` and `protect` only (a `delete` of one leaf-list value is unproven) | automatically resolved by precedence | Builder applies one rule to every verb, as the set reader already does; recorded as an observation in the proposal's non-goals | None blocking |
| C6 | Ruling 3b keeps the ancestors' tags in the IR the pipeline hands to every writer; a relative selection then holds tags above its path, which ruling 2 covers only for "the selected statement itself" | automatically resolved by precedence | Ruling 2's purpose governs ("no format drops a tag silently"): a tag at or above the path that relative output cannot write is dropped with the same note | Recorded in the proposal and the delta |
| C7 | The set validator judges a verb line from the generated grammar alone, but the grammar cannot tell a list's name from a leaf's value: measured at base, `deactivate interfaces ge-0/0/1 unit 200`, `protect interfaces lo0` and `deactivate vlans V999` (device lines) parse with their last value in a non-list rule | automatically resolved by precedence | Fix at the owning layer: the set reader's decision of what a verb line names moves to `display`, read only, and the reader and the validator share it (AGENTS.md: prefer an existing helper; one rule) | The validator reads the structure tree beside its grammar |
| C8 | `docs/how-to/run-a-batch-of-changes.md` links every private entry into the worktree; the coordinator requires the XSD dumps as physical files | automatically resolved by precedence | `private_test_data/schemas/` is a directory of hard links; every other entry is a symbolic link | None |
| C9 | `docs/VERIFICATION.md`: the cadence invitation is pending | automatically resolved by precedence | Unattended job: the invitation is deferred to the job's end (coordinator) | None for this change |

## Assurance

- Standing preference: economy (`pyproject.toml` `[tool.template.assurance]`, record
  docs/how-to/run-a-batch-of-changes.md#assurance; keys `default` and `declared-break`).
- Required roles: Builder; independent Test/Challenge; a fresh isolated Reviewer at least as
  capable as the Builder. The coordinator dispatches both.
- Application policy: device-evidence checks and the before/after comparison
  (`docs/how-to/run-a-batch-of-changes.md`); the schema tier when the shipped artifacts change.
- Mandatory risk floor: high. The change is cross-domain (validation, conversion, schema
  pipeline, kernel) and changes results on both named surfaces (`consumer`:
  `validate_config`, `convert_config(_result)` with `path=`; `cli`: `-v`, `--path`,
  `--relative`).

## Execution checkpoint

Base `ec62908` (master, v0.28.25). Worktree `/Users/manon-dev/src/junoscfg-wt/device-probe-fixes`,
branch `change/device-probe-fixes`. Regeneration: `uv run --locked pytest tests/ -q --regen-schema`;
records: `tools/device_differences.py`, `tools/device_grammar_corpus.py`. Full check:
`uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full`.
Integration by the Builder after the review: merge, archive, patch bump, tag, remove the worktree.

## Owner decision batch

None, because the brief fixes the scope and every open choice above is settled by precedence or
the rulings. C4 and C5 are recorded for the Test/Challenge and Reviewer roles.

## Delta log

- Initial preflight: consistent after C1 to C9. Resume: phase 1 proposal.
- Delta 1 (coordinator, 2026-10-17): the Test/Challenge report and owner rulings: fix F1 (the
  literal keywords) and F2 (one-line `hold-time`) here; dispositions M1, S1 to S8, N1 to N9.
  Consistent; phase-4 additions written. S7 (the reader writes back a device-refused verb line)
  meets the approved entry-keys requirement that a whole-list tag survives set output:
  resolved by the S7 ruling for lists the device refuses, with device evidence
  (`deactivate6.txt`) that a homogeneous list is tagged whole (review S-6, pending owner
  decision, interim implemented).
- Delta 2 (coordinator, 2026-10-17, owner instruction, supersedes the F2 ruling): set input is
  what a device exports; ARCHITECTURE.md rule, decision record, the unsupported list; `delete`
  and `activate` stay; F2 fixed only if cheap. Measured: not cheap (12,416 containers, +27 %
  grammar, +2.2 s compile); `-v` names the form unsupported, conversion reads it. The widening
  written under delta 1 was reverted before commit; its tests were replaced. No other work
  invalidated.
