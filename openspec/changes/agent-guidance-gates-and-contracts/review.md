## Specification challenges

<!-- Raised by the independent Test/Challenge role in phase 4 (full text and executed evidence in test-challenge.md). Pending owner resolution is not approval. Each Decision records the interim safe, reversible action the Builder took, fixed by existing approved artefacts; the owner records accept, reject or clarify. -->

### S1. The new metadata clause claimed more than the product does

- Artifact: `main-spec-edit.md` as frozen at eb369dd, the clause "WHEN a `deactivate`, `activate`, `protect` or `delete` line names such a path, or a path the configuration does not hold, THEN … SHALL attach the attribute to no shorter valid path … SHALL report it `UNPLACED` once"; `docs-plan.md` row "metadata command stays whole and loud through every door".
- Counterexample (executed by the challenger, read-only): `deactivate apply-groups G1 G2` gives IR `{"@apply-groups": {"inactive": true}}`, output `deactivate apply-groups`, 0 unplaced: the attribute lands on the shorter path and both names are dropped silently. A meta line on a second nokeyword value (`deactivate access securid-server SAMPLE-SERVER-2` after `set … SAMPLE-SERVER configuration-file sample-1`) is not reproduced. `deactivate system ntp` with no such statement is placed (a `set system ntp` line appears), 0 unplaced. The five `TestAMetaCommandIsNeverPartiallyApplied` tests cover only a partial key, a surplus token and an unmodelled path.
- User impact: the main spec would assert behaviour the product lacks, and "traceability only, behaviour unchanged" would be false.
- Proposed correction: narrow the clause to what the tests pin, using the sibling delta's wording (S3). Record the three executed cases as an open product defect for a separate `bug`-lane change, settled with a device artefact first (named path only).
- Decision: Pending owner decision. Interim action: `main-spec-edit.md` now carries the sibling's owner-approved wording verbatim plus the five test ids; the three cases are listed under "Open defects" below and in the final report.

### S2. "Reports nothing" for a whole list was unpinned

- Artifact: the same frozen clause, "an attribute on a whole list, or on a positional value the reader placed, is written back and reports nothing".
- Counterexample (proposed probe; today's behaviour executed): `test_a_meta_attribute_on_a_whole_list_is_written` asserts only that the set and meta lines are in the output; it has no `_unplaced` assertion, so a regression that reported a whole list would pass.
- User impact: an untested promise in a SHALL-adjacent sentence.
- Proposed correction: say only that a meta attribute on a whole list survives set output at the list path, which is the sibling's sentence.
- Decision: Pending owner decision. Interim action: resolved by adopting the sibling wording (S1).

### S3. The sibling live delta already carries the same requirement with different wording

- Artifact: `main-spec-edit.md` and `evidence-freeze.md` ("No other requirement changes").
- Counterexample (executed): `openspec/changes/identifier-key-fields/specs/conversion/entry-keys/spec.md` (commit 211a165, after that change's main-spec application a920fab) carries "A statement the reader cannot complete is kept whole" under `## ADDED Requirements` with the sentence "The same applies to `deactivate`, `activate`, `protect` and `delete`: a partial or surplus keyed-list key and an unknown path SHALL apply no attribute to the nearest valid parent or entry. A meta attribute addressed to an entire list SHALL survive set output at that list path." and two scenarios, and without the five test ids. The sibling archives with `--skip-specs`, so that text would never reach the main spec.
- User impact: two live texts for one requirement; whichever change finishes second overwrites or loses the other's wording.
- Proposed correction: one agreed wording, the sibling's, plus the five ids; log the overlap in both change records; the finalizer's phase-7 check compares the applied main spec against both.
- Decision: Pending owner decision. Interim action: adopted. The sibling's own folder is not edited by this change; the overlap is logged here, in `evidence-freeze.md` and in the final report for the owner to carry into the sibling's record if wanted.

### S4. A cited test id did not exist

- Artifact: `docs-plan.md` row "Anonymization is the red zone …", `evidence-freeze.md` Evidence line 1 ("60 nodes"), `tasks.md` baseline.
- Counterexample (executed): `tests/test_anonymize/test_integration.py::TestPipelineIntegration::test_revert_map_restores_originals` → `ERROR: not found`, exit 4. The test lives in `TestPipelineDumpMapIntegration`. The 60 nodes were the 24 `main-spec-edit.md` ids only.
- User impact: a deliverable copying the row would cite a dead id; a frozen claim was false.
- Proposed correction: fix the class name; re-baseline as "every cited id collects, exit 0, ids listed".
- Decision: Pending owner decision. Interim action: both corrected in `docs-plan.md` and `evidence-freeze.md`; task 1.2 now expects exit 0 and no `not found` line rather than a count.

### S5. The timing guard cited for entry lookup times the set validator

- Artifact: `docs-plan.md` row "A bounded timing guard exists …" and proposal measure (1), "entry lookup or a schema-wide walk: bounded timing against a frozen baseline".
- Counterexample (executed read): `test_compact_siblings_keep_practical_parse_time` times `bundled_set_validator.validate(source)` against the Lark grammar; it never touches entry-key lookup or the reader's schema walk. The large-case baseline is a private file's timing recorded in a live change folder, which moves on archive.
- User impact: a slow entry-lookup change passes the named guard; the guide would point at a path that rots.
- Proposed correction: state that no committed timing guard covers entry lookup; describe the measure-and-explain procedure against the base commit on the same machine without naming any private file, as a record, never a gate over correctness (ARCHITECTURE.md section 1 ranks latency last).
- Decision: Pending owner decision. Interim action: the guide's row is written in that form; the docs-plan row is corrected.

### S6. The display and validate invariants were not fully backed by their cited tests

- Artifact: `docs-plan.md` rows for the display and validate contracts.
- Counterexample (executed read): `test_statement_children_drop_the_key_fields` asserts `statement_children`'s output and its presence in `__all__`; `test_reader_and_writer_share_the_grammar_rule` asserts reader and writer agree on a monkeypatched tree; `key_is_positional` is named by no test. `test_entry_properties_are_the_key_fields` expects a property set that includes non-key children; `test_bundled_grammar_matches_its_structure_tree` asserts reproducibility, not key-driven generation.
- User impact: a contract would say "enforced by" for a guarantee the test does not enforce.
- Proposed correction: display cites `TestEntryKeysComeFromTheTree::test_the_helper_answers_the_key_tuple`, `::test_statement_children_drop_the_key_fields` and `::test_no_module_keeps_its_own_key` for "the kernel answers an entry's keys and statement children, and no module keeps a key spelling of its own"; validate narrows to "any `maxOccurs` other than 1 is a list", citing `TestCardinality::test_a_numeric_max_occurs_is_list` alone.
- Decision: Pending owner decision. Interim action: both invariants narrowed to those wordings and tests.

### S7. The solo-review rule would have applied to this docs change and named no corpus

- Artifact: proposal measure (2), task 2.2.
- Counterexample (proposed probe): this change edits contracts under `validate/`, `convert/` and `anonymize/`, three of the rule's six areas, and plans no corpus review.
- User impact: a rule its own change cannot satisfy is read as optional.
- Proposed correction: trigger on behaviour-bearing paths (`src/**` code and generated data, not `CONTRACT.md` or docs); name the corpus (`--jvd`), the baseline comparison already in the guide, the device captures, and the report's required contents; say "fresh agent", never a second human.
- Decision: Pending owner decision. Interim action: the rule is written in that form.

## Open defects found by the challenge (not this change's to fix)

1. `deactivate apply-groups G1 G2` attaches `inactive` to the shorter path `apply-groups` and drops both names without a diagnostic (executed, read-only).
2. A meta line addressed to a second nokeyword value is not reproduced in set output (executed, read-only).
3. `deactivate system ntp` with no such statement is placed and a `set system ntp` line is synthesised, with no diagnostic (executed, read-only). Whether the device accepts, warns or rejects needs a device artefact for `system ntp` before the rule is decided.
