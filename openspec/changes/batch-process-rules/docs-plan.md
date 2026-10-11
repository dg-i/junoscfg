## Reader and task

- Reader: the orchestrator and the Builders and Reviewers of a batch of junoscfg changes, human
  or agent, who already know `agent-ready-change` and `batches.md`.
- Task: run several changes at once (worktrees, serialized paths, merge-time versions) and
  verify each change touching the schema, grammar, readers, writers or anonymizer against the
  committed device evidence instead of the JVD clone.

## Authoritative sources

| Claim | Source |
|---|---|
| Batch roles, STOP-T/STOP-R, max Builders, serialized paths, expensive tiers, merge steps | `.agents/skills/agent-ready-change/batches.md` (upstream v0.9.0); `pyproject.toml` `[tool.template.batch]` |
| Rules 1–8 and the JVD removal | owner task 2026-10-11 (preflight, owner row) |
| Assurance keys and the high-risk floor | `.agents/skills/agent-ready-change/SKILL.md` "Sessions", `phases/0-preflight.md` step 6, `pyproject.toml` `[tool.template.assurance]` |
| Check 2 device law and the record tool | `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet`, `tools/device_differences.py` docstring |
| Check 3 universal statements over every capture; the format matrix over shapes | `tests/corpus/test_device_renderings.py::TestEveryDoorReadsTheDevicesUniversalStatements`, `tests/contract/test_format_matrix.py` |
| Check 4 over the vMX example | `tests/support/devices.py` `UNPLACED_IN_THE_EXAMPLE`, `example()`; `tests/contract/test_round_trip_validates.py::TestTheExampleRendersValid`; `tests/unit/convert/test_field_validator.py::TestTheExampleConfigurationValidates` |
| Check 5 over every capture, all rules on, addresses only | `tests/corpus/test_device_anonymization.py::TestEveryCaptureAnonymizes` (`_every_rule`, `_is_address`) |
| Checks 1 and 6 have no committed test | survey of `tests/` and `tools/` in phase 0 (preflight C10); `tools/affected_tests.py` reads git only to select tests |
| Run times | measured here: the six check files 17.6 s (3,664 passed, 5 xfailed); the output loop 51 s over 24 renderings × 4 formats |
| `--schema`, `--regen-schema`, `--jvd`, `--device-grammar` | `tests/conftest.py` options and markers; regeneration "about three minutes" per dump (conftest comment) |
| `SchemaLoadError` exit 3 | `src/junoscfg/validate/__init__.py` (`SchemaLoadError`), `src/junoscfg/cli.py` (`sys.exit(3)`) |
| Value-free re-raise in an anonymized run | archived change `2026-10-11-anonymized-run-messages`, `tests/contract/test_every_message.py` |
| `SKIP=affected-tests` | `.pre-commit-config.yaml` hook id `affected-tests` |
| Version rules | `AGENTS.md` Version Management, `pyproject.toml` `[tool.template.stage] break-bumps` |
| JVD cost 45–90 minutes per run | owner task 2026-10-11 (the conftest comment's "about three minutes" predates the warning budget and the 1,535-file corpus) |

## Affected documents

- `docs/how-to/run-a-batch-of-changes.md` (new): a how-to, task-shaped, beside `solo-review.md` and `settle-a-schema-question.md`.
- `AGENTS.md`: Verification and "Where things are" point at the how-to; the file stays within its 100-line cap.
- `docs/architecture/developer-guide.md` Testing Architecture: the jvd tier row, the nightly row and the pre-review evidence table stop naming the JVD tier as per-change evidence; the table points at the oracle checks.
- `docs/how-to/solo-review.md`: the Reviewer's report item 1 names the oracle checks instead of the JVD tier.
- `docs/how-to/work-with-agents.md`: unchanged; its nightly CI row stays true.
- `docs/decisions/2026-10-11-<slug>.md` (new, scaffolded) and the generated `docs/decisions/index.md`.

## Documentation QA

- Links and anchors: `uv run --locked --group docs mkdocs build --strict` reports no broken link or anchor except the expected "not in nav" notice for the new page (nav lands in `batch-process-config`); every relative link in the changed files resolves (inspection).
- Commands and examples: every command in the how-to runs at the checked head in this worktree, with its observed result recorded in `tasks.md`; `--schema` and `--regen-schema` need a dump under `private_test_data/schemas/` and are run once if one is present, otherwise recorded as not run.
- Referenced paths: every `src/`, `tests/`, `tools/`, `examples/` path and test node named in the changed files exists (`ls` / `pytest --collect-only`).
- Terminology: "oracle checks", "(a)/(b)", "serialized paths", "expensive tier", "Builder/Reviewer/Orchestrator" match `batches.md` and the device decision record; no "JVD tier" remains as per-change evidence (`grep -n -i jvd` on the changed files).
- Diátaxis placement: the new page is a how-to (steps and commands); rationale goes to the decision record; reference facts stay in the developer guide.
- Rendered output: the strict MkDocs build renders the page; markdownlint passes on changed files; `AGENTS.md` ≤ 100 lines (`agent-ready caps`).
