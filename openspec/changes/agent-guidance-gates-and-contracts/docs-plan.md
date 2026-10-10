## Reader and task

- Reader: an agent or contributor about to change junoscfg's schema pipeline, readers,
  writers, validators or anonymizer, or to settle a device question; and the reviewer of
  such a change.
- Task: select the pre-review evidence from the paths the change touches; read the module's
  settled invariant and its test before editing; freeze device evidence once, sanitised;
  trace the metadata no-partial-application rule from its requirement to its tests.

## Authoritative sources

| Claim | Source |
|---|---|
| The `--schema`, `--jvd` and `--regen-schema` tiers, their data needs and the regen exit code 7 | `tests/conftest.py` `pytest_addoption`; `tests/test_schema_data.py` docstring; the existing tier table |
| The JVD gate is the only place the field-warning budget runs | `tests/test_jvd_corpus.py::TestFieldWarningBudget::test_warnings_stay_within_budget`; existing guide text |
| A regenerated artifact set is reproducible when a second regeneration leaves `git diff --stat -- src/junoscfg/validate/data` empty | `openspec/changes/identifier-key-fields/tasks.md` items 4.15 and 5.4 |
| Public-door semantic parity and round trip are pinned by named tests | `tests/test_characterization.py::TestKeyedEntriesAgreeAcrossReaders::test_every_writer_reads_back_the_device_ir`, `tests/test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr`, `tests/test_convert_consistency.py::TestJsonRoundTripConsistency::test_roundtrip_preserves_content`, `tests/test_device_truth.py::test_every_door_gives_the_device_ir` |
| Anonymization is the red zone; syntax values pass unchanged; mapping is deterministic and revertible | `[tool.template.zones.anonymize]`; `tests/test_anonymize/test_walker.py::TestKeyFieldsAreLeaves`; `tests/test_anonymize/test_ip_rule.py::TestIpRuleTransform::test_deterministic_with_same_salt`; `tests/test_anonymize/test_integration.py::TestPipelineIntegration::test_revert_map_restores_originals` |
| A bounded timing guard exists and a large-case baseline was recorded | `tests/test_set_validator.py::TestTheShippedGrammarAcceptsMultipleSiblings::test_compact_siblings_keep_practical_parse_time`; `openspec/changes/identifier-key-fields/tasks.md` 4.4 and 5.6 |
| Latency ranks last for the product, not for the workflow | `ARCHITECTURE.md` section 1; `.agents/skills/agent-ready-change/batches.md` ("do not run one full checkpoint per checklist item") |
| Fresh review found High findings after a green full gate | `openspec/changes/identifier-key-fields/review.md`, "Phase-6 review" and challenges A to C; `docs/how-to/solo-review.md` |
| One kernel answer owns entry keys, statement children and key form | `src/junoscfg/display/__init__.py` `__all__` (`entry_keys`, `statement_children`, `key_is_positional`); `tests/test_characterization.py::TestEntryKeysComeFromTheTree::test_statement_children_drop_the_key_fields`; `tests/test_set_input.py::TestAFreeformNokeywordKeyKeepsItsKeyword::test_reader_and_writer_share_the_grammar_rule` |
| Any `maxOccurs` other than 1 is a list; declared keys drive the generated artifacts | `tests/test_xsd_parser.py::TestCardinality::test_a_numeric_max_occurs_is_list`; `tests/test_schema_generator.py::TestEntryKeysAreTheTreesFields::test_entry_properties_are_the_key_fields`; `tests/test_grammar_generator.py::TestBundledGrammarIsReproducible::test_bundled_grammar_matches_its_structure_tree` |
| An incomplete statement or metadata command stays whole and loud through every door | `tests/test_field_validator.py::TestAnIncompleteStatementIsUnplaced::test_each_door_reports_it`; `tests/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied` (five tests) |
| A schema enum value or key-choice keyword is syntax and is never anonymized | `tests/test_anonymize/test_walker.py::TestKeyFieldsAreLeaves::test_an_enum_key_passes_unchanged`, `::test_a_key_choice_keyword_passes_unchanged`; `tests/test_anonymize/test_integration.py::TestKeyedEntriesSurvive::test_a_value_from_its_leafs_enum_passes_every_rule` |
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
