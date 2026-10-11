## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `50b0a10` by design, pins named in `evidence-freeze.md`): `tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText` (the synthetic adversarial catalogue `_FREE_TEXT`) and `::TestAnApplyPathNamesConfiguration`, `test_revert.py::TestRevertUndoesEachReplacementOnce`, `test_sensitive_word_rule.py::TestEachSpellingHasItsPseudonym`, `test_as_number_rule.py::TestAWildcardUnderAsNumbersInStrings`, `test_identity_rule.py::TestAUrlUserIsAnIdentity`, `test_password_rule.py::TestAUrlPasswordIsASecret`, `test_ip_rule.py::TestIpAnonymizeIntegration::test_an_address_inside_free_text_is_replaced` (replaces `test_ips_in_strings_disabled_by_default`, which asserted ANON-P5).
- [x] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`; T1-T12 ruled by the orchestrator, all accepted; S3-S7 recorded; the rulings' tests committed.

## 2. Change

- [x] 2.1 `anonymize/rules`: `Rule.spans` and `Rule.rewrite` (where a rule recognises a value by its shape, and its replacement); the IP rule's addresses, the identity rule's URL user, the password rule's hash words and URL password, the sensitive-word rule's words keyed by spelling, the AS rule's numbers outside addresses under `as_numbers_in_strings` and its wildcard report (NEW-R14).
- [x] 2.2 `anonymize/walker.py`: one chain for a value no whole-value rule takes, placed or not, that never offers a rule's text to another; a whole-value shape only where its rule takes the value; `apply-path` read against the tree.
- [x] 2.3 `anonymize/__init__.py`: the strings passes go; `anonymize/revert.py`: one pass, longest first, numbers between non-digits and outside addresses, addresses last.
- [x] 2.4 After #8 merged and the orchestrator rebased: sensitive-case harmless control, exact-case docstring, and mapping pin updated from measured case/annotation behavior; focused integration assertions pass.
- [x] 2.5 Contract (`anonymize/CONTRACT.md`), config docstring, CLI help of the in-strings options and the generated reference, CLI guide, developer guide, changelog fragment; before/after comparison with `--anonymize`; timing record.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.

## Supplemental resumption checkpoint — 2026-10-11

- [x] Record explicit owner decisions and freeze delta consistency; preserve T1–T12 and historical S1–S7 entries. No v2 mapping machinery approved.
- [x] Add supplemental public-door regressions across every reader and watch them fail before code.
- [x] Implement flat-map IP ambiguity rejection before returning anonymized output; ambiguous legacy reverse maps reject before mutation.
- [x] Extend the existing name/pattern comparison kernel for literal apply-path selectors and excluded selectors; leave filters authoritative on both sides and report by schema path only.
- [x] Resolve safe ambiguity refusal at the conversion boundary: it currently suppresses the value-free reason into generic RuntimeError. No blanket propagation of arbitrary source exceptions is authorized.
- [x] Complete S5 conversion/CLI rejection coverage, including no output/map creation and clear value-free diagnostics.
- [x] Finish deferred #8 integration expectations, public docstrings/contracts, declared docs and truthful migration declaration.
- [x] Focused package/contract tests, fields/caps/reconcile/codemap checks, fast check and normal-hook commit; clean checkpoint.
- [x] Full check and final device comparison, held until orchestrator explicitly releases #9 integrated baseline. Original #7 full never passed.

Command run twice: `uv run --offline --locked --group dev pytest -q tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_ambiguous_spellings_are_rejected_before_output tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_an_unambiguous_spelling_restores_exactly tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration::test_filtered_selector_meaning_is_reported tests/unit/anonymize/test_revert.py::TestRevertUndoesEachReplacementOnce::test_an_ambiguous_ip_map_is_rejected_before_mutation --tb=short`. Red on `04d95fb`: exit 1, 86 failed/36 passed (XML-output test setup corrected; XML remains input-only). Post-fix: exit 1, 10 failed/112 passed. The ten remaining conversion rows receive generic RuntimeError instead of the required explicit ambiguity refusal. Stopped after the same test command failed twice, no third attempt. Current edits are uncommitted; no green full/fast checkpoint or fresh-review verdict claimed.

### Latest stop: message catalogue replacement did not apply

Changed-hypothesis ambiguity repair passed all 122 supplemental rows; five-reader old-map rejection, integration expectation/doc changes are implemented. Focused package/contract run twice yielded 7608 passed, 14 xfailed, 2 failed. Intended `wildcard name(s)` label replacement was a no-op; actual catalogue fragment is `wildcard`. Mandatory repeated unchanged-failure stop. Exact remaining repair: `_APPLY_PATH_WILDCARD_SHOWN` fragment becomes `selector`, retain path/reason/privacy checks, rerun exact affected message nodes and supplemental/integration nodes, then fast and normal-hook commit. Caps and lint green; declarations/reconcile/codemap commands completed, full still held. All product/doc/test edits remain uncommitted. No third run or false clean checkpoint claim.

### Completed corrections; checkpoint pending commit/fast

- [x] Safe fixed-message ambiguity subtype at existing IpRule door; conversion rebuilds only that refusal, withholding arbitrary exception details. Supplemental rerun: 122 passed.
- [x] Five-reader legacy-map rejection through conversion/CLI, measured integration expectations, contracts/docstrings/declared docs/migration completed; no v2 representation.
- [x] Actual message-catalogue fragment corrected after verifying git diff. Exact two affected message-door nodes: 2 passed, exit 0. Previous focused run's 7608 passing cases and 14 existing xfails remain evidence; do not claim one fully green focused command.
- [x] Fields, caps, reconcile and codemap check exit 0. Delta compacted to 51 lines without wording changes; no cap raised.
- [x] Normal-hook commit plus fast check and clean checkpoint (immutable fast-checked HEAD recorded below).
- [x] Root rebase onto integrated #9 baseline, then explicitly released full/device comparison; high-risk fresh Reviewer, metrics and Finalizer remain open.

### Final local handoff checkpoint

- [x] S5/S7 corrections and #8 expectation updates complete; fixed-message ambiguity refusal, flat map rejection before output/mutation, literal/wildcard selector risk in both filter directions, value-free warnings, excluded selector unchanged.
- [x] Normal-hook implementation commit `348108a67421e952a692d7306659eb7e0fff4a8f` passes affected tests and all hooks. Supplemental 122 cases passed; newly added five-reader legacy-map rows and integration expectations passed in the focused selection. Exact two message-catalogue corrections pass. Prior failures/no-op/record-write provenance is preserved without claiming a completely green focused command.
- [x] Fast check passes exit 0 on `1d144fcdf073b12f69d05ff74ff6a249a2105d3e`; fields/caps/reconcile/codemap green. This final commit changes evidence only and preserves the checkpoint.
- [x] Next incomplete phase-5 work: orchestrator rebase onto integrated #9 baseline `0438299772819f24c871d4cb2b8768f9233f9318`, then explicitly released full checkpoint and device comparison. Original #7 full never passed.
- [x] Fresh high-risk isolated Reviewer, immutable metrics and bounded Finalizer remain incomplete; no Builder self-approval.

All candidate writes transfer to the orchestrator after this evidence-only handoff. No further local mutations before its explicit resumption.

### Post-rebase verification checkpoint

- Integration base `0438299772819f24c871d4cb2b8768f9233f9318`; resumed candidate `074736b115c45da31c2a0d92ecf35c88054ef32a`. Earlier SHAs remain historical, and #9 runtime invalidates earlier combined-input verification.
- [x] Exact supplemental S5/S7/legacy refusal plus relevant XML/quoting/integration/message selection: 195 passed, exit 0; no product/test edit needed.
- [x] Fast on new immutable record HEAD; normal-hook clean handoff.
- [x] Full/device comparison awaits independent final Test/Challenge verdict and orchestrator release. No prior full pass claimed; fresh Reviewer/metrics/Finalizer still open.

### Final Test/Challenge IPv6 correction checkpoint

- [x] Pre-correction fast passed on `e6f24b85a41d78fe9cc86a6b66f112e7b694e19a`; preserved as earlier-runtime evidence.
- [x] Independent executed counterexamples recorded under existing S5 invariant: compressed/expanded and differently cased IPv6 spellings could succeed forward with a duplicate replacement, then fail reverse.
- [x] Test first: both alias pairs/both orders/five readers/public doors, red 20 failed/10 passed. Minimal fix removes the IPv4-only condition from the existing merged-map collision guard; no representation or exception change.
- [x] Exact focused command below: 235 passed, exit 0; ruff and caps exit 0. Single-spelling controls still restore exactly.
- [x] Normal-hook source commit `574b55ef9895f88a9f417e9480eb017b6055d133` passed all hooks including affected tests; clean tree. Fast passed every gate, exit 0, on that same immutable HEAD. Subsequent handoff record is evidence-only.
- [x] Corrected independent Test/Challenge verdict, explicitly released full/device comparison, fresh Reviewer, metrics and Finalizer remain open.

Command: `uv run --offline --locked --group dev pytest -q tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_ambiguous_spellings_are_rejected_before_output tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_an_ambiguous_legacy_map_is_rejected_before_output tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_an_unambiguous_spelling_restores_exactly tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_an_annotation_is_free_text tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration::test_filtered_selector_meaning_is_reported tests/unit/anonymize/test_revert.py::TestRevertUndoesEachReplacementOnce::test_an_ambiguous_ip_map_is_rejected_before_mutation tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_name_keyed_output_is_unchanged tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_the_mapping_restores_the_set_output tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_word_in_two_cases_reverts_to_each tests/unit/anonymize/test_integration.py::TestAWildcardNameIsAPattern::test_a_wildcard_that_selects_the_same_names_is_not_reported tests/unit/convert/test_convert_roundtrip.py::TestAPolicyChainIsWrittenAsTheDevicesTokens tests/unit/display/test_to_yaml.py::TestALeafKeepsItsText tests/unit/display/test_to_yaml.py::TestXmlToYamlReadsBackToTheSameIr tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration tests/contract/test_every_message.py::TestTheLibraryRaisesAFailureByItsClassOnly --tb=short`.

All candidate writes transfer to the orchestrator after this evidence-only handoff. No further local mutations before explicit resumption.

### Released final phase-5 validation

- [x] Independent corrected Test/Challenge APPROVE exact source `574b55ef9895f88a9f417e9480eb017b6055d133`; report/evidence preserved, no Builder self-approval.
- [x] Immutable integration base `0438299772819f24c871d4cb2b8768f9233f9318` and live source/fast checkpoint recorded; only lifecycle records differ in handoff `d1200731428360ebe22fdd4e3cb2b603e29e6fd4`.
- [x] One full standard offline check on clean record commit; complete raw private log, tool exit/counts/coverage retained.
- [x] Candidate-only device comparison after full green against frozen integration-base.json; classify every output/diagnostic/validation/exception difference without normalization.
- [x] Current bounded performance measurement if frozen inputs exist; otherwise precise UNMEASURED reason, historical figures scoped to their earlier source.
- [x] Fresh Reviewer, immutable metrics and bounded Finalizer remain root-owned incomplete lifecycle.

### Fresh review corrections — R2 and R1

- [x] Original-candidate full/device and frozen bounded timing completed on `2fa6c604`; historical evidence retained, not attributed to future corrected runtime.
- [x] Public-door red regression for original URL credential ownership, hash delimiter and same URL/login pseudonym; wildcard generated-prefix protection plus untouched surrounding text. Original red and helper setup failure provenance retained.
- [x] Bounded owning-chain correction using existing rewrite/shift helpers; unchanged wildcard return shape and no new consumer obligation. Targeted 31 passed; focused 1,120 passed/one existing xfail, exit 0.
- [x] Focused/fast/normal clean source checkpoint, independent exact-head correction verification, then required released full/device rerun.
- [x] Fresh corrected Reviewer verdict, lifecycle metrics and Finalizer remain open.

Focused R1/R2 command: `uv run --offline --locked --group dev pytest -q tests/unit/anonymize/test_walker.py tests/unit/anonymize/test_ip_rule.py tests/unit/anonymize/test_as_number_rule.py tests/unit/anonymize/test_identity_rule.py tests/unit/anonymize/test_password_rule.py tests/unit/anonymize/test_sensitive_word_rule.py tests/unit/anonymize/test_revert.py tests/unit/anonymize/test_integration.py tests/contract/test_every_rule.py tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration tests/contract/test_every_message.py::TestTheLibraryRaisesAFailureByItsClassOnly --tb=short`. Raw private evidence: review-correction-focused.out. Source hooks/fast and independent exact-head verification remain pending; no corrected full checkpoint claimed.

### Kept-prefix R1 continuation checkpoint

- [x] Source b162444 normal hooks/fast and independent R1/R2 Test/Challenge APPROVE recorded; root full passed 9,016/37 skipped/20 strict xfails, exit 0. Original 2fa evidence and red/setup/caps provenance remain.
- [x] Sequential b162 device comparison and candidate-only benchmark completed, exit 0; immutable baseline result reused unchanged. Separate private artifacts and exact head/option/input hashes retained. Coverage exported from the existing full data without rerunning tests.
- [x] New independent preserved-prefix counterevidence recorded under existing invariant; baseline red 33 failed/31 passed. Expanded existing nodes cover both default documentation prefixes, explicit preserve, mixed surrounding names and all five readers/public doors; no criterion changes.
- [x] Minimal owned IP-prefix/address metadata correction; targeted 64 passed, exit 0. Surrounding original text still reaches later rules; no mapping/interface change.
- [x] Focused checks, normal hooks and fast on new immutable source; independent exact-head challenge, then explicitly released full and sequential new candidate device/timing. Prior b162 results are historical-for-this-runtime-correction.
- [x] Corrected fresh Reviewer closure, lifecycle metrics and Finalizer remain root-owned open.

Kept-prefix focused command: `UV_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 uv run --offline --locked --group dev pytest -q tests/unit/anonymize/test_walker.py tests/unit/anonymize/test_ip_rule.py tests/unit/anonymize/test_as_number_rule.py tests/unit/anonymize/test_identity_rule.py tests/unit/anonymize/test_password_rule.py tests/unit/anonymize/test_sensitive_word_rule.py tests/unit/anonymize/test_revert.py tests/unit/anonymize/test_integration.py tests/contract/test_every_rule.py tests/contract/test_every_message.py::TestAnAnonymizedRunQuotesNothingOfTheConfiguration tests/contract/test_every_message.py::TestTheLibraryRaisesAFailureByItsClassOnly --tb=short`: 1,168 passed/one existing xfail, exit 0.

### Final phase-5 evidence handoff

This latest checkpoint supersedes earlier execution/resume states; all historical stops and results above remain provenance.

- [x] Final runtime source `48f8a858153696809ff1cd6496a84feed9a4b557`: focused 1,168 passed/one existing xfail, targeted 64 passed, normal source hooks and fast passed; clean immutable source.
- [x] Independent exact-head Test/Challenge APPROVE (kept-prefix/correction/report.md): 252 focused passes; all kept/generated selectors, URL/alias and ambiguity/error probes satisfy their original invariants.
- [x] Root-owned required final full on clean source: 9,064 passed/37 skipped/20 strict xfails, every gate/exit 0. Full log/provenance/coverage retained; actual durations 119.32 seconds application and 171.53 seconds whole command. Coverage 92.92812349252291%, exported from retained data without test rerun.
- [x] Sequential final device record/diff/classification: 1,440 conversions/96 plain unchanged/132 approved output changes; zero diagnostics/field-validation/exceptions, byte-identical to prior candidates. Separate exact raw evidence retained.
- [x] Sequential final candidate-only benchmark: all three inputs measured with unchanged frozen script/options/inputs/IR/lock and retained baseline timing; no duplicate baseline run. Exact samples/hashes/medians recorded in freeze/metrics and private benchmark-final-48f8a858/.
- [x] Evidence-only normal record hooks/fast passed on immutable `51a969264bd79dff377a809e92f432b94cb8c0af`; subsequent handoff also changes evidence only. No source/test/spec changes invalidate the final full.
- [x] Root-owned fresh corrected Reviewer closure, lifecycle metrics and bounded Finalizer remain open; Builder does not approve them.

Final fast command: `UV_OFFLINE=1 npm_config_offline=true PYTHONDONTWRITEBYTECODE=1 uv run --offline --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set fast`, exit 0/every gate passed on 51a9692. Independently challenged/full-tested source remains 48f8a858. All candidate writes transfer to root after this evidence-only normal-hook handoff; no further Builder mutations.

### Authoritative phase-7 lifecycle checkpoint

All preceding stop/resume prose and exact-head results remain historical provenance; completed boxes now reflect final closure, not success at those earlier checkpoints.

- [x] Fresh isolated Reviewer APPROVE on exact runtime `48f8a858153696809ff1cd6496a84feed9a4b557`, private `roles/codex-fresh-review/kept-correction/report.md`; original 2fa6c604 and b162444 NEEDS CORRECTION verdicts remain unchanged. Own 372 focused tests and 13 extra controls pass; independent challenge, full, device and timing hashes audited.
- [x] Supported disposable OpenSpec archive applied exactly the frozen three capability deltas; copied only main-spec results to the live branch, commit `dea7fc7a353f4086317b3bddfd60210192f34fd6`. Strict change validation and all 23 main specs pass. Live change remains. Independent main-spec review is pending at this checkpoint.
- [x] Supported immutable metrics capture uses integration base `0438299772819f24c871d4cb2b8768f9233f9318` and reviewed runtime `48f8a858153696809ff1cd6496a84feed9a4b557`; 28 own substantive files, +2,508/-519, zero binary files, 6 direct dependencies and 63 root-lock packages unchanged. Later +99/-27 main-spec application and lifecycle records are outside this source-head capture. Runtime usage and Strategy A workflow efficiency stay UNMEASURED.
- [x] Complete independent main-spec review, bounded final checks and root-owned archive/version/integration housekeeping. Finalizer does not archive, bump, merge or tag.

### Final bounded prearchive delivery

Independent main-spec APPROVE exact `67c37324e5db8e1a8155ec3ab813641419e2b391`, private `roles/codex-fresh-review/main-spec/correction/review.md`; original dea7fc7 NEEDS CORRECTION finding retained. Only the new capability Purpose sentence was corrected to the already-approved flat-map rejection policy; requirement/scenario bytes remain unchanged. All historical boxes now reflect final closure, with original execution prose retained. Task 3.3 marks this bounded prearchive delivery: root remains executor of archive, version, integration and tag; none executed by Finalizer. Next incomplete lifecycle action is root-owned archive/version/integration after final bounded fast/checkpoint.
