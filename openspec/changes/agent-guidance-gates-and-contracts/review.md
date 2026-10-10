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

## Phase-6 review (fresh session, 2026-10-10)

Reviewed commit 19d05de (the eight deliverables) against eb369dd, in a detached worktree
of 19d05de (`git worktree add --detach /Users/manon-dev/src/junoscfg-wt-review 19d05de`,
`agent-ready skills --regenerate` first, removed afterwards). No Builder report was read.
Reading order: `evidence-freeze.md`, `docs-plan.md`, `proposal.md`, `main-spec-edit.md`
against the main spec and the sibling delta, the four contracts and their cited tests,
`test-challenge.md` and S1 to S7, `tasks.md`, the diff and the built site. Synthetic values
only; the private configuration the sibling's task 4.4 names is not repeated here.

Instruction integrity first: the owner's limits in `instruction-integrity.md` hold on the
diff. `git diff --name-only eb369dd..19d05de` outside the change folder lists exactly the
eight deliverables, all Markdown; `git diff --name-only 01efe85..19d05de -- .agents/` is
empty; `ARCHITECTURE.md` and `pyproject.toml` are untouched; the guide's stderr and "safe
fallback" sentences (C7) are not in the diff; no deliverable names the untracked review
(C3); no timing figure is added (0 hits on the added lines). Every field of the owner's
measure (4) form is present in rule 5. Measure (3)'s "positional-versus-keyword form"
(display) and "declared keys drive the generated artifacts" (validate) are absent from the
contracts by the S6 interim narrowing, which stays pending.

### Verified

- 1.1 `uv run --locked --group docs mkdocs build --strict`: exit 0, 0 `WARNING`, 4 INFO
  lines, none naming an edited page; `id="when-to-use-each-tier"` and
  `id="pre-review-evidence-by-the-paths-a-change-touches"` present once each; solo-review
  links `../../architecture/developer-guide/#when-to-use-each-tier`; tables 15/0/1, broken
  list or table markers (`<p>(- |\|)`) 0/0/0.
- 1.2 46 distinct `tests/…::…` ids across the eight deliverables: `uv run pytest
  --collect-only -q <ids>` exit 0, 154 collected, 0 `not found`; the 24 `main-spec-edit.md`
  ids: 60 collected; `TestAMetaCommandIsNeverPartiallyApplied`: 19 nodes;
  `pytest --help --color=no | grep -oE -- '--(schema|jvd|regen-schema)\b' | sort -u | wc -l`
  = 3. Every tier-table command dry-run with `--collect-only` (never `--regen-schema`,
  `--schema` or `--jvd`): row 3's parity command 101 nodes, `tests/test_anonymize` 369,
  `tests/test_device_truth.py` 23, `tests/test_jvd_corpus.py` 8, `tests/test_schema_data.py`
  12, the row-1 and row-2 "while editing" files 158 and 322, row 3's 57.
- 1.3 Every backticked repository path on the added lines is tracked
  (`git ls-files --error-unmatch`); the two `private_test_data/` mentions sit beside
  "gitignored"; every bare `test_*.py` and `src/junoscfg/...` name in the tier table and the
  solo-review trigger list exists; `entry_keys` is defined in `display/constants.py:138`.
- 1.4 Deny-list over the added lines: 0 hits. Canonical spellings kept (`UNPLACED`, "kept
  whole", "key choice", "nokeyword"). Drift found outside the deny-list: see Low 2.
- 1.5 Placement as recorded; policy-word hits in the guide are the two `ARCHITECTURE.md`
  pointers (row 5 and the closing paragraph), no restatement.
- 1.6 `agent-ready caps` exit 0; contracts 30/26/30/30 lines (27/24/30/28 at eb369dd);
  `awk 'length>84 && $0 !~ /`tests\//'` prints nothing; `git diff --check eb369dd..19d05de`
  silent; `pre-commit run markdownlint --files <eight files>` Passed.
- 1.7 `agent-ready lane --base master` in the worktree: exit 1, "documentation-only
  changes may not alter non-documentation files: .agents/skills/agent-ready-garden/SKILL.md,
  …/jobs/5-instructions.md" (the owner's 01efe85), as recorded.
- 1.8 `diff` of the sibling's requirement block against `main-spec-edit.md` from line 5:
  one changed line, `Tests:`, the old line an exact prefix; the five appended ids are the
  five `TestAMetaCommandIsNeverPartiallyApplied` ids. The requirement body (non-Tests) is
  the main spec's text plus the sibling's two sentences. `211a165` is not an ancestor of
  `a920fab` (so the sibling's wording never reached the main spec), as S3 says.
- 1.9 (not required of me, run anyway) `agent-ready check --set full --base master` in the
  worktree: exit 1, `failing: fields, lane`, both the recorded external causes; every other
  check passed.
- 1.11 Old tier section split into 9 blocks, whitespace-normalised: 0 missing from the new
  section.
- 1.12 Per contract, lost backticked tokens 0/0/0/0; `## Invariants` bullets 2→3, 2→3,
  3→4, 3→4; `## Precedent` 3→3, 2→2, 3→3, 2→2; every heading and `Interface:` line kept.
- 1.13 Assertions behind each new invariant, quoted from the test bodies. display:
  `assert entry_keys({"L": True, "k": ["list-type", "list-name"]}) == ("list-type",
  "list-name")`; `assert list(statement_children(keyed)) == ["accept"]`;
  `test_no_module_keeps_its_own_key` walks every `src/junoscfg/**/*.py` AST for
  `{"fe", "values-only", "community-name"}`, `^_v\d+$` and three retired names, with
  `assert len(files) > 60`. validate: `assert root.children["class"].is_list is True`
  (maxOccurs 16), `["source-port"].is_list is True` (32), `["host-name"].is_list is
  False` (1). convert: `assert any(e.expected == UNPLACED for e in result.errors)` and
  `pytest.raises(FieldValidationError)` on strict (set door); `assert messages == ["…
  without its key field 'list-type' could not be placed … kept as written, not validated"]`
  per JSON, YAML, XML door; `assert "@" not in from_`, `assert "@" not in
  from_["as-path-neighbors"][0]`, `assert from_[suffix]["@"] == self._ATTRS[command]`,
  `assert len(_unplaced(...)) == 1`, `assert meta_line in dict_to_set(ir).splitlines()`.
  anonymize: `assert entry["list-type"] == "as-list-group"` with
  `sensitive_words=["as-list"]` and seven rules on; `assert anonymized["exact"] == [None]
  and anonymized["accept"] == [None]`, `assert term["then"]["community"][0]["add"] ==
  [None]`, and `[v for v, _, p in rule.seen if p[-1] in ("exact", "accept")] == []` with
  all eight rule flags on.
- 1.14 On the 27 added lines of the schema-question page: 0 IPv4 addresses, 0 AS numbers,
  0 prompts, 0 pathless captures, set/json/xml views named, `private_test_data` beside
  "gitignored", 0 timing figures, "Four rules" gone.
- 1.15 8 needles (private capture names and the `.conf` names in the sibling's tasks):
  0 hits on the added `docs` and `src` lines.
- 1.16 The eight probes A to H re-run through `convert_config_result` (set to set) at
  19d05de: A 0 unplaced, `deactivate apply-groups`; B same; C 1 unplaced; D 1 unplaced,
  meta line not reproduced; E 0 unplaced, `set system ntp` synthesised; F reproduced, 0;
  G reproduced, 1; H reproduced, 1. Identical to the challenger's run; A, D, E stay open
  defects. None contradicts the narrowed clause: A is no keyed-list key, E is no unknown
  path.
- 1.17 Freeze Requirements, delta log and S3 name the shared wording.
- 1.18 dry-run in the worktree only, restored by `git checkout --`: the block applied
  over the main spec's requirement, `diff` against `main-spec-edit.md` from line 5 empty;
  `agent-ready reconcile` exit 0; one new id misspelt, `reconcile` exit 1 naming
  "tests/test_set_input.py has no
  TestAMetaCommandIsNeverPartiallyApplied::test_a_meta_attribute_on_a_whole_list_is_written".
  The Finalizer's phase-7 plan works as written.
- 1.19 Nine hits; "same salt", "with the mapping", "Measure and explain … never a gate
  over correctness", and the `AGENTS.md` Verification pointer, as recorded.
- 1.20 and 1.21 as recorded; `.openspec.yaml` declares `conversion` and `anonymization`,
  matching `[tool.template.domains.*]` paths.
- C4 probed: a `specs/conversion/entry-keys/spec.md` delta beside `skip_specs: true` makes
  `npx --yes @fission-ai/openspec@1.13.0 validate … --strict` report "[ERROR] file:
  skip_specs is set in .openspec.yaml but spec files exist under specs/"; without it the
  change is valid. Delta deleted again; worktree clean.

### Findings, by severity

1. **Medium. The reviewed `Tests:` line cites a test that asserts the opposite of the
   requirement's THEN.** `main-spec-edit.md` line 11 lists
   `tests/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_meta_on_an_existing_positional_value_is_kept_whole`,
   whose assertions are `ir["protocols"]["isis"]["enable-disable"] == "SAMPLE-UNKNOWN"`,
   `ir["protocols"]["isis"]["@SAMPLE-UNKNOWN"] == {"inactive": True}`,
   `_unplaced(source + "\n") == []` and an exact round trip: a placed value, an attribute
   attached, nothing reported. The requirement says "field validation SHALL report it
   `UNPLACED`" and no sentence of the clause describes this case (the sentence that did,
   "one on a positional value the reader placed is written back and reports nothing", was
   dropped with the S2 interim action). A reader tracing "reported `UNPLACED`" to that id
   finds the reverse; `reconcile` cannot see it (it only checks the id exists; proved in
   1.18). Correction, one of: (a) drop that id from the `Tests:` line, or (b) add the
   sentence "A meta attribute on a positional value the reader placed is written back and
   reports nothing." before `Tests:`, which the test asserts. Recommendation: (b), one
   sentence, because the test exists and should be traceable. Recorded as S8.
2. **Medium. The path-to-evidence table and the solo-review trigger miss the grammar's
   runtime path, so the reader's task fails for it.** Guide diff line +760 (row 2) names
   `set_input.py`, "the grammar rules in `grammar_generator.py`" and `field_validator.py`;
   `src/junoscfg/validate/set_validator.py`, which loads the Lark grammar (`from lark
   import Lark`, line 20) and changed in d1628eb and 5da8aee, is in no row, nor is the
   generated `src/junoscfg/validate/data/junos-set.lark.gz`, nor `src/junoscfg/input/`
   (the lexical boundary both the convert and validate contracts cite; row 3's
   `convert/input/` is a different package). The proposal promises "the complete
   path-to-risk mapping" and the intro says "the paths a change touches select what runs
   beside it", so an agent editing `set_validator.py` reads "nothing beside the full
   checkpoint", though the old bullet "After a grammar … change — Run `--jvd`" meant it.
   The two pages also draw the areas differently: solo-review's "validation
   (`validate/*_validator.py`, …)" includes `set_validator.py` while row 2 does not;
   solo-review's "the grammar" has no path; solo-review's `validate/xsd_*.py` includes
   `xsd_extractor.py`, which row 1 omits. Correction: add `src/junoscfg/validate/
   set_validator.py`, `src/junoscfg/validate/data/junos-set.lark.gz` and
   `src/junoscfg/input/` to row 2; give "the grammar" its path in solo-review; close the
   table with "any other path: the full checkpoint alone, and say so in the record".
3. **Low. The display invariant is broader than its guard.** `display/CONTRACT.md`
   lines 19–21: "no module keeps a key spelling of its own — enforced by
   `test_no_module_keeps_its_own_key`". The test bans the retired spellings `fe`,
   `values-only`, `community-name`, `_v<n>` and three retired names; a new module
   hard-coding `"list-type"` passes it. Narrow to "no module reads a retired key spelling
   (`fe`, `values-only`, `community-name`, `_v<n>`)" or say "guarded by". Within the cap
   (display is at 30; the wording is no longer). S6 is pending on the same bullet.
4. **Low. Terminology drift.** (a) "metadata verb" (solo-review +48, the changelog
   fragment, the proposal) against "meta command" in the specs, the sibling scenario
   titles and `TestAMetaCommandIsNeverPartiallyApplied` (6 occurrences; "metadata verb"
   occurs nowhere else in `docs/`, `openspec/specs/` or `tests/`). (b) "immutable
   baseline" (guide row 2, solo-review +42) against "frozen master baseline" in the same
   guide section (line 744). (c) "sanitised" (rule 5 heading) against "sanitized"
   elsewhere under `docs/` (1:1 today). Use "meta command", "frozen master baseline", and
   one spelling.
5. **Low. Duplicated mechanics.** `uv run pytest --jvd tests/test_jvd_corpus.py -q` and
   `uv run pytest tests/test_device_truth.py -q` now live in the guide (item 1, rows 1
   and 3) and in solo-review (+40, +44). S7 asked solo-review to name the corpus and the
   command, so this is owner-directed; the docs-plan's placement check says "mechanics
   only in the developer guide". Recommendation: solo-review names the corpus, the
   baseline and the capture pairs and keeps its link to the guide's section; the literal
   commands stay in the guide only.
6. **Low. Row 1 reads as one schema run per dump.** Guide +759: "`uv run pytest --schema
   tests/test_schema_data.py -q` for each dump under gitignored
   `private_test_data/schemas/`". `tests/conftest.py` `schema_dump` is
   `params=[p.name for p in schema_data.available()]`, so one run covers every dump (the
   tier table above already says "Runs against each NETCONF dump"). Say "once; it
   parametrises over every dump".
7. **Low (trust boundary). The form's "device's response quoted" does not say to mask the
   prompt.** Settle page +86–88. A quoted CLI response carries `user@hostname#`, which
   identifies device and operator; the "Family and release" bullet forbids exactly that,
   and the sibling's own record notes "prompts masked" each time. Add "prompt masked" to
   the "Forms tried" bullet.
8. **Low. A figure nobody can rerun.** `proposal.md` line 25, "recorded in the v0.7.8
   format": no "0.7.8" exists in the repository (`docs/how-to/capture-change-metrics.md`
   names `schema_version: 1`; `[tool.template] reorganise-to = 0.7`). Not a deliverable;
   the Finalizer binds the file against `schema_version: 1`, and the proposal line should
   drop the version.

### Already provided

- `agent-ready reconcile` already enforces every cited id on the main spec after
  application (proved by the negative probe in 1.18); no new gate is needed for the
  `Tests:` line, only the one-sentence choice in finding 1.
- The three grammar guards row 2 points at are the existing code block at guide line 683
  (`test_set_corpus.py … test_rejections_are_exactly_the_recorded_ones`,
  `test_cli_validate.py … test_validate_set_with_multiple_siblings`,
  `test_grammar_generator.py … test_bundled_grammar_matches_its_structure_tree`), and the
  reproducibility check in row 1 is the sibling's task 5.4 procedure; both are referenced,
  not restated.
- The unbounded case of the validate invariant ("however the dump bounds it") is pinned
  by `tests/test_xsd_parser.py::TestCardinality::test_unbounded_is_list`, not cited;
  validate is at 26 lines, so there is room to add it.
- The second timed assertion in the suite, `tests/test_integration.py:158`, is a
  line-count ratio (`0.5 < ratio < 2.0`), not a time bound, so row 5's "the only
  committed bound … times the grammar" holds.

### Review prompts

1. **Trust-boundary input.** Device captures (operator data) entering the committed change
   record through rule 5's form. The boundary invariant is `AGENTS.md` "Never use real
   operator data" plus gitignored `private_test_data/`. The form holds it (raw stays
   private, synthetic ranges, named path, family and release only) except the quoted
   response's prompt (finding 7). The deliverables themselves carry no operator
   identifier (1.15, 0 hits on 8 needles) and no address or AS number (1.14).
2. **Incompatible-but-valid input.** A change touching `validate/set_validator.py`,
   `validate/data/junos-set.lark.gz`, `src/junoscfg/input/`, `audit/` beyond `walker.py`,
   `edityaml/` or `tests/data/captures/` is valid under the guide's promise "by the paths
   a change touches" and meets no row (finding 2). For the spec clause: probes A, D and E
   (1.16) stay outside the narrowed wording (no keyed-list key, no unknown path), so the
   clause the Finalizer applies is not contradicted; they remain the three open defects.
3. **Shared blind spot.** The QA plan, the Builder's evidence and the lane, caps,
   markdownlint and MkDocs gates all pass on "the id collects"; collection proves
   existence, not that the test asserts the sentence. Independent evidence is the
   assertion body, which 1.13 quotes for the contracts and which I extended to the
   `Tests:` line of `main-spec-edit.md`; that is where findings 1 and 3 surface.
   Corrected criterion: for every id a deliverable cites, quote the assertion that
   enforces the sentence it sits under (recorded in S8).
4. **Second answer.** The diff adds no override, fallback, parameter or environment read
   (prose and one table). Two homes for one answer exist: the corpus and device-truth
   commands (guide item 1 and rows 1, 3; solo-review list items 1) and two names for one
   baseline ("frozen master", "immutable"), findings 4b and 5. Row 2's "items 1 and 2
   above" is a pointer, not a second answer.
5. **Stated figures and non-goals.** Rerun: 24 ids → 60 nodes; 46 ids → 154 nodes;
   contract lengths 27/24/30/28 → 30/26/30/30, cap 30; old tier section at eb369dd lines
   726–750; graph 7,245 nodes, 13,203 edges (`graphify-out/graph.json`); "three High
   findings after the full check was green" (sibling `review.md` findings 1–3 High, line
   236 "Full check at fc22c57: exit 0"); "five probe rounds relayed through chat" (sibling
   `metrics.md` and `review.md` name rounds 2 to 5 and "relayed"; round 1 implied, not
   named); merge base 2a3e025. "Cannot" claims: OpenSpec refuses the delta beside
   `skip_specs` (probed, ERROR text above); the lane cannot pass with 01efe85 in range
   (exit 1 naming its two files); `fields` fails on the sibling (full check). Unproven:
   "v0.7.8 format" (finding 8).

### Could not check

- The `--schema`, `--jvd` and `--regen-schema` tiers themselves (forbidden): every
  command was dry-run with `--collect-only` only.
- Device behaviour for probes A, D and E (`deactivate apply-groups G1 G2`, a meta line on
  a second nokeyword value, `deactivate system ntp` with no statement): needs a device
  artefact at the named paths before the `bug`-lane change the record proposes.
- Whether `openspec archive` of the sibling's `ADDED` requirement over the existing one
  fails or overwrites (would mutate the repository; carried from the challenge).
- 1.9 and 1.7 on the head that results from the owner's decision on 01efe85 and 306233b;
  1.10 (no telemetry file yet); 1.18 on the real phase-7 commit (dry-run passed here).
- markdownlint on `main-spec-edit.md` (the hook excludes `openspec/changes/`).
- The 94 hidden lines of the owner's task: checked against the reconstruction in
  `instruction-integrity.md` only.

### Specification challenges

**S8.**
- Artifact: `main-spec-edit.md`, the `Tests:` line's 23rd id,
  `tests/test_set_input.py::TestAMetaCommandIsNeverPartiallyApplied::test_meta_on_an_existing_positional_value_is_kept_whole`,
  under the requirement "… field validation SHALL report it `UNPLACED`".
- Counterexample (executed read, and 1.18 executed): the test asserts
  `ir["protocols"]["isis"]["enable-disable"] == "SAMPLE-UNKNOWN"`,
  `ir["protocols"]["isis"]["@SAMPLE-UNKNOWN"] == {"inactive": True}`,
  `_unplaced(source + "\n") == []` and an exact round trip; no sentence of the clause
  describes a placed positional value, and `reconcile` passes on the applied block because
  it checks only that the id exists.
- User impact: the applied main spec cites, as evidence for "SHALL report it `UNPLACED`",
  a test whose assertion is "reports nothing"; traceability, the one thing this edit is
  for, points the wrong way for that case.
- Proposed correction: add before `Tests:` the sentence "A meta attribute on a positional
  value the reader placed is written back and reports nothing." (what the test asserts),
  or drop the id from the line. Recommendation: the sentence.
- Decision: Pending owner decision.

### Verdict

Not merge-ready as it stands; merge-ready once two bounded corrections land and are
re-read: finding 1 (the owner's one-sentence choice on `main-spec-edit.md`, applied by the
Finalizer in phase 7) and finding 2 (the missing paths in the guide's row 2 and the
solo-review trigger). Findings 3 to 8 are at the owner's discretion with S6 and S7. The
`lane` and `fields` failures are the two pending owner decisions already in
`checkpoint.md`, not this change's defects. S1 to S7 stand as recorded with their interim
actions; the main-spec wording the Finalizer applies is otherwise the sibling's
owner-approved text, verbatim, and the phase-7 application plus `reconcile` was dry-run
successfully.

## Fix pass (2026-10-10, Builder, on the phase-6 review and the post-implementation challenge)

Every correction is a documentation edit on the same branch; nothing outside the eight
deliverables and this folder changed. QA re-run after the edits: 47 cited ids collect (155
nodes, exit 0), deny-list 0 hits, 8 tier blocks survive, contracts 30/26/30/30 lines with no
line over 84 bytes outside test ids and 0 tokens lost, form checks clean, 0 operator-name
leaks, caps exit 0, markdownlint Passed, strict MkDocs 0 warnings with the new anchor present.

- Finding 1 (Medium) and S8: the sentence "A meta attribute on a positional value the reader
  placed is written back and reports nothing." is added to `main-spec-edit.md` before
  `Tests:`, option (b), which `test_meta_on_an_existing_positional_value_is_kept_whole`
  asserts (`_unplaced(source + "\n") == []`, attribute attached, exact round trip). The diff
  against the sibling block is now that sentence plus the five ids. S8 Decision: Pending
  owner decision; interim action (b) applied.
- Finding 2 (Medium): guide row 2 names `src/junoscfg/input.py` (the lexical boundary; it is
  a module, not a package), the shipped grammar `validate/data/junos-set.lark.gz` and its
  runtime `validate/set_validator.py`; row 1 names `xsd_extractor.py`; the intro closes with
  "a path under `src/junoscfg/` in no row takes its focused tests and the full checkpoint
  alone, and the change record says so". `solo-review.md` draws six disjoint areas with the
  same paths (schema pipeline, generated artifacts, conversion with `input.py`, the grammar's
  runtime, validation including `validate/validator.py`, anonymization), which also answers
  the challenge's claim 13.
- Finding 3 (Low) and S6: display narrowed to "no module reads a retired key spelling
  (`fe`, `values-only`, `community-name`, `_v<n>`)", which is what
  `test_no_module_keeps_its_own_key` bans; still 30 lines. Validate also cites
  `TestCardinality::test_unbounded_is_list` for "however the dump bounds it".
- Finding 4 (Low): "meta command" replaces "metadata verb" in `solo-review.md`, the changelog
  fragment and the proposal; "frozen master baseline" replaces "immutable baseline" in the
  guide and `solo-review.md`; "sanitized" throughout (the one committed precedent,
  `docs/decisions/2026-10-09-reject-raw-set-brackets.md`).
- Finding 5 (Low): `solo-review.md` names the corpus tier, the baseline and the capture pairs
  and links the guide's new table for the commands; the literal commands live in the guide
  only.
- Finding 6 (Low): row 1 reads "`--schema … -q` once, which parametrises over every dump".
- Finding 7 (Low): rule 5's "Forms tried" bullet adds "and its prompt masked".
- Finding 8 (Low): the proposal cites the format by `schema_version: 1` and the how-to, not a
  template version.
- Challenge, failed claim 1: the guide's intro now says the full checkpoint "runs neither
  the schema nor the corpus tier (device truth runs in the default tier wherever capture
  pairs exist)".
- Challenge, partial claims: the anonymize invariant says "passes the rules unchanged" (the
  two walker tests enable the rules they need, not all nine); the convert contract's
  rewording of its "Not for" paragraph dropped the pointer "section 1" to stay inside 84
  columns, recorded in tasks 1.12; `docs-plan.md` cites sibling items 4.12 and 5.4 for
  reproducibility.
- Not changed: S1's "The same applies to…" sentence stays the sibling's wording; the three
  product defects stay open for a `bug`-lane change with a device artefact first; the
  sibling's live ADDED block is not edited by this change (S3).

## Phase-6 re-review (fresh session, 2026-10-10)

Re-reviewed the fix pass only, commit 68b4f5a against b20ca29, in a detached worktree of
68b4f5a (`git worktree add --detach /Users/manon-dev/src/junoscfg-wt-review2 68b4f5a`,
skills mirror regenerated, removed afterwards). `git diff --stat b20ca29..68b4f5a` outside
the change folder: the eight deliverables only (the `mkdocs.yml` and
`docs/reviews/2026-10-10-instruction-audit.md` in the wider `eb369dd..68b4f5a` range are the
owner's 306233b, not the fix pass); `.agents/` unchanged since 01efe85.

### Verified

- Finding 1 / S8: `main-spec-edit.md` line 8 now ends "A meta attribute on a positional
  value the reader placed is written back and reports nothing." The diff against the
  sibling's requirement block is exactly that sentence plus the five ids on `Tests:`.
  The sentence matches `test_meta_on_an_existing_positional_value_is_kept_whole`:
  `ir["protocols"]["isis"]["@SAMPLE-UNKNOWN"] == {"inactive": True}`, exact round trip,
  `_unplaced(source + "\n") == []`, where `_unplaced` (test_set_input.py:1078) collects
  the `field-validate` "could not be placed" messages.
- Finding 2: guide row 1 names `xsd_extractor.py`; row 2 names `src/junoscfg/input.py`,
  `src/junoscfg/validate/data/junos-set.lark.gz` and `src/junoscfg/validate/set_validator.py`;
  the intro closes with the "path in no row" rule. Every newly named path exists
  (`test -e` on nine paths, all present; `src/junoscfg/input.py` is a module beside
  `input.CONTRACT.md`). `solo-review.md` lists six areas whose path sets are pairwise
  disjoint (schema pipeline, `validate/data/`, `convert/` except `field_validator.py` plus
  `input.py`, `validate/set_validator.py`, the four runtime validators plus
  `convert/field_validator.py`, `anonymize/`), and item 1 links the guide's table instead
  of repeating commands; the link target
  `../../architecture/developer-guide/#pre-review-evidence-by-the-paths-a-change-touches`
  resolves to an `id` present once in the built page.
- Finding 3 / S6: display reads "no module reads a retired key spelling (`fe`,
  `values-only`, `community-name`, `_v<n>`)", the set `test_no_module_keeps_its_own_key`
  bans; 30 lines. Validate adds `TestCardinality::test_unbounded_is_list`
  (`assert ifaces.is_list is True`, `maxOccurs="unbounded"`); 26 lines.
- Finding 4: `grep -rni 'metadata verb|metadata-verb|immutable baseline|sanitis'` over
  `docs`, `src`, `changelog.d`, `main-spec-edit.md` and the proposal: one residual hit,
  `proposal.md` line 35 ("metadata-verb clause", Capabilities section); "sanitized" has
  its committed precedent in `docs/decisions/2026-10-09-reject-raw-set-brackets.md`.
- Finding 5: the literal `--jvd` and device-truth commands are in the guide only.
- Finding 6: row 1 reads "`--schema … -q` once, which parametrises over every dump".
- Finding 7: "with the device's response quoted and its prompt masked".
- Finding 8: the proposal names `schema_version: 1` and the metrics how-to.
- Challenge claim 1: "device truth runs in the default tier wherever capture pairs exist"
  holds: `pytest --collect-only -q tests/test_device_truth.py -m 'not schema and not jvd'`
  collects 23 nodes and `tests/data/captures/` holds 31 files.
- Anonymize "passes the rules unchanged": the two walker tests enable seven and eight
  rule flags, so the narrower wording is the backed one.
- `docs-plan.md` now cites sibling items 4.12 and 5.4 for reproducibility; 4.12 is
  "Artifacts regenerated twice with `--regen-schema` … each committed separately", 5.4
  "Regenerate affected artifacts twice and prove reproducibility". Correct.
- Mechanical QA at 68b4f5a: `mkdocs build --strict` exit 0, 0 WARNING, no INFO anchor
  line naming an edited page, tables 15/0/1, broken markers 0/0/0; 47 distinct cited ids
  collect (155 nodes, exit 0, 0 `not found`); `agent-ready caps` exit 0, contracts
  30/26/30/30, no line over 84 outside test ids; `git diff --check eb369dd..68b4f5a`
  silent; markdownlint Passed on the eight files; deny-list 0 hits; 9 old tier blocks
  survive; 0 backticked tokens lost per contract; `agent-ready check --set fast --base
  master` exit 1, `failing: fields, lane`, both the recorded external causes.

### Findings

1. **Low. One residual "metadata-verb" in the proposal.** `proposal.md` line 35,
   Capabilities: "gains the metadata-verb clause and test ids". Finding 4 is otherwise
   closed; this is the one spelling the fix pass missed. Not a deliverable; fix when the
   proposal is next touched.
2. **Low (wording). "as the developer guide's rows draw them" overstates.**
   `solo-review.md` line 36: the six areas are disjoint, but the guide's rows are not
   (`grammar_generator.py` sits in rows 1 and 2, `convert/input/` in rows 2 and 3,
   `config_store.py` in rows 3 and 5). The areas use the rows' path names, not their
   grouping. Say "with the paths the developer guide's rows name".
3. **Info. "reports nothing" is read against `UNPLACED`.** The added sentence's test
   asserts only that no "could not be placed" message is emitted; other diagnostics are
   not asserted. In the requirement's context ("field validation SHALL report it
   `UNPLACED`") the sentence reads correctly; "is not reported `UNPLACED`" would be the
   exact form. No action required.

### Could not check

- Unchanged from the first review: the `--schema`, `--jvd` and `--regen-schema` tiers
  themselves; device behaviour of probes A, D and E; `openspec archive` of the sibling's
  `ADDED` block; 1.7 and 1.9 on the head after the owner decides on 01efe85 and 306233b
  (the lane message now also names `mkdocs.yml`); 1.10 and 1.18 on the real phase-7 commit.
- The challenger's post-implementation sampling (20 claims) was read for its headings
  and the fix pass's account of it, not re-executed claim by claim; the two failed and
  four partial claims it names are the ones the fix pass lists, and each correction above
  is verified against its source.

### Specification challenges

None new. S8's interim action (option b) is applied; S1 to S8 remain "Pending owner
decision" with their interim actions.

### Verdict

Merge-ready on this change's own terms: both Medium findings are corrected and verified
at 68b4f5a, the Low findings are closed except the one residual word in the proposal
(finding 1 above, non-blocking), and the main-spec text the Finalizer applies is the
sibling's owner-approved wording plus one test-backed sentence and the five ids. What
still stands between this branch and merge is outside the change: the owner's decisions on
01efe85 and 306233b (lane) and the sibling's `assurance` (fields), and the owner's
accept/reject on S1 to S8 and the three open product defects.

## Residue after the re-review (2026-10-10, Builder)

- Re-review finding 1 (Low): `proposal.md` now says "meta-command clause".
- Re-review finding 2 (Low): `solo-review.md` says "The six areas, disjoint, with the paths
  the developer guide's rows name", since the guide's rows overlap and the areas do not.
- Re-review finding 3 (Info): the S8 sentence keeps "reports nothing", which is correct in
  the requirement's `UNPLACED` context; no change.
