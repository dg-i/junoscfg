## Reader and task

- Reader: an agent or contributor about to change junoscfg's schema pipeline, readers,
  writers, validators or anonymizer, or to settle a device question; and the reviewer of
  such a change.
- Task: select the pre-review evidence from the paths the change touches; read the module's
  settled invariant and its test before editing; freeze device evidence once, sanitized;
  trace the metadata no-partial-application rule from its requirement to its tests.

## Authoritative sources

| Claim | Source |
|---|---|
| The `--schema`, `--jvd` and `--regen-schema` tiers, their data needs and the regen exit code 7 | `tests/conftest.py` `pytest_addoption`; `tests/test_schema_data.py` docstring; the existing tier table |
| The JVD gate is the only place the field-warning budget runs | `tests/test_jvd_corpus.py::TestFieldWarningBudget::test_warnings_stay_within_budget`; existing guide text |
| A regenerated artifact set is reproducible when a second regeneration leaves `git diff --stat -- src/junoscfg/validate/data` empty | `openspec/changes/identifier-key-fields/tasks.md` items 4.12 and 5.4 |
| Public-door semantic parity and round trip are pinned by named tests | `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_every_writer_reads_back_the_device_ir`, `tests/test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr`, `tests/test_convert_consistency.py::TestJsonRoundTripConsistency::test_roundtrip_preserves_content`, `tests/test_device_truth.py::test_every_door_gives_the_device_ir` |
| Anonymization is the red zone; syntax values pass unchanged; mapping is deterministic and revertible | `[tool.template.zones.anonymize]`; `tests/test_anonymize/test_walker.py::TestKeyFieldsAreLeaves`; `tests/test_anonymize/test_ip_rule.py::TestIpRuleTransform::test_deterministic_with_same_salt`; `tests/test_anonymize/test_integration.py::TestPipelineDumpMapIntegration::test_revert_map_restores_originals` |
| No committed timing guard covers entry lookup or a schema-wide walk; the only committed bound times the set validator's grammar; a large-case measure-and-explain record exists | `tests/test_set_validator.py::TestTheShippedGrammarAcceptsMultipleSiblings::test_compact_siblings_keep_practical_parse_time` (grammar only); `openspec/changes/identifier-key-fields/tasks.md` 4.4 and 5.6 (the procedure; the private file is never named in a deliverable) |
| Latency ranks last for the product, not for the workflow | `ARCHITECTURE.md` section 1; `.agents/skills/agent-ready-change/batches.md` ("do not run one full checkpoint per checklist item") |
| Fresh review found High findings after a green full gate | `openspec/changes/identifier-key-fields/review.md`, "Phase-6 review" and challenges A to C; `docs/how-to/solo-review.md` |
| The kernel answers an entry's key fields and a statement's children, and no module keeps a key spelling of its own | `src/junoscfg/display/__init__.py` `__all__` (`entry_keys`, `statement_children`); `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_the_helper_answers_the_key_tuple`, `::test_statement_children_drop_the_key_fields`, `::test_no_module_keeps_its_own_key` |
| Any `maxOccurs` other than 1 is a list | `tests/test_xsd_parser.py::TestCardinality::test_a_numeric_max_occurs_is_list` |
| An incomplete set statement, a keyed entry without its key from JSON, YAML or XML, and a meta command on a partial or surplus key or an unmodelled path are kept whole and reported `UNPLACED` | `tests/test_field_validator.py::TestAnIncompleteStatementIsUnplaced::test_each_door_reports_it`; `tests/test_field_validator.py::TestAnEntryWithoutItsKeyIsUnplaced::test_each_structured_door_reports_it`; `tests/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_a_partial_or_surplus_key_is_kept_whole` |
| A schema enum value or keyword of a key choice is syntax and is never anonymized | `tests/test_anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_an_enum_key_passes_unchanged`, `::test_a_key_choice_keyword_passes_unchanged`; `tests/test_anonymize/test_integration.py::TestKeyedEntriesSurvive::test_a_value_from_its_leafs_enum_passes_every_rule` |
| The device-evidence form's fields and privacy rules | `ARCHITECTURE.md` evidence hierarchy; `docs/how-to/settle-a-schema-question.md` rules 1 and 2; `AGENTS.md` test-data conventions; `openspec/schemas/agent-ready/templates/evidence-freeze.md` |
| The telemetry file format and its binding | `docs/how-to/capture-change-metrics.md`, `--workflow-telemetry` |

## Affected documents

- `docs/architecture/developer-guide.md`: `AGENTS.md` sends grammar changes to its focused
  list and `ARCHITECTURE.md` stays policy-only, so tier mechanics belong here.
- `docs/how-to/solo-review.md`: the repository's review policy home.
- `src/junoscfg/display/CONTRACT.md`, `validate/CONTRACT.md`, `convert/CONTRACT.md`,
  `anonymize/CONTRACT.md`: module truth, read before an edit (`AGENTS.md`).
- `docs/how-to/settle-a-schema-question.md`: how device evidence is asked for.
- `openspec/changes/agent-guidance-gates-and-contracts/main-spec-edit.md`: the reviewed
  edit the finalizer applies to `openspec/specs/conversion/entry-keys/spec.md` in phase 7
  (OpenSpec refuses a `specs/` delta beside `skip_specs`, which the docs lane sets).
- `openspec/changes/agent-guidance-gates-and-contracts/workflow-telemetry.json`: this
  change's observed telemetry, bound in phase 7.

## Documentation QA

- Links and anchors: `uv run --locked --group docs mkdocs build --strict`; expect a clean
  build with no warning, and every relative link in the edited pages resolving.
- Commands and examples: `uv run pytest --collect-only -q` over every test id the edited
  documents cite; expect every id collected. `uv run pytest --help` lists `--schema`, `--jvd`
  and `--regen-schema`; expect all three.
- Referenced paths: `test -f` for every repository path the edited documents name;
  `uv run --locked --group dev agent-ready reconcile`; expect every path present and exit 0
  with the delta live.
- Terminology: compare "evidence hierarchy", "kept whole", "UNPLACED", "entry keys", "key
  choice", "nokeyword", "red zone" in the edited text with `ARCHITECTURE.md`, the main specs
  and the contracts; expect the same words, no new synonym.
- Diátaxis placement: inspect the diff; expect mechanics only in the developer guide and no
  second testing policy, how-to steps only under `docs/how-to/`, invariants only in contracts,
  and `ARCHITECTURE.md` untouched.
- Rendered output: `uv run --locked --group dev agent-ready caps` (contracts at or under 30
  lines); markdownlint through the pre-commit hook on the changed files; `git diff --check`;
  inspect the built HTML of the three edited pages for intact tables and lists.
