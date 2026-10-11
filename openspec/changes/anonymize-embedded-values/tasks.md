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

- [ ] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [ ] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [ ] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits.

## Supplemental resumption checkpoint — 2026-10-11

- [x] Record explicit owner decisions and freeze delta consistency; preserve T1–T12 and historical S1–S7 entries. No v2 mapping machinery approved.
- [x] Add supplemental public-door regressions across every reader and watch them fail before code.
- [x] Implement flat-map IP ambiguity rejection before returning anonymized output; ambiguous legacy reverse maps reject before mutation.
- [x] Extend the existing name/pattern comparison kernel for literal apply-path selectors and excluded selectors; leave filters authoritative on both sides and report by schema path only.
- [ ] Resolve safe ambiguity refusal at the conversion boundary: it currently suppresses the value-free reason into generic RuntimeError. No blanket propagation of arbitrary source exceptions is authorized.
- [ ] Complete S5 conversion/CLI rejection coverage, including no output/map creation and clear value-free diagnostics.
- [ ] Finish deferred #8 integration expectations, public docstrings/contracts, declared docs and truthful migration declaration.
- [ ] Focused package/contract tests, fields/caps/reconcile/codemap checks, fast check and normal-hook commit; clean checkpoint.
- [ ] Full check and final device comparison, held until orchestrator explicitly releases #9 integrated baseline. Original #7 full never passed.

Command run twice: `uv run --offline --locked --group dev pytest -q tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_ambiguous_spellings_are_rejected_before_output tests/unit/anonymize/test_walker.py::TestValuesInsideFreeText::test_an_unambiguous_spelling_restores_exactly tests/unit/anonymize/test_walker.py::TestAnApplyPathNamesConfiguration::test_filtered_selector_meaning_is_reported tests/unit/anonymize/test_revert.py::TestRevertUndoesEachReplacementOnce::test_an_ambiguous_ip_map_is_rejected_before_mutation --tb=short`. Red on `04d95fb`: exit 1, 86 failed/36 passed (XML-output test setup corrected; XML remains input-only). Post-fix: exit 1, 10 failed/112 passed. The ten remaining conversion rows receive generic RuntimeError instead of the required explicit ambiguity refusal. Stopped after the same test command failed twice, no third attempt. Current edits are uncommitted; no green full/fast checkpoint or fresh-review verdict claimed.

### Latest stop: message catalogue replacement did not apply

Changed-hypothesis ambiguity repair passed all 122 supplemental rows; five-reader old-map rejection, integration expectation/doc changes are implemented. Focused package/contract run twice yielded 7608 passed, 14 xfailed, 2 failed. Intended `wildcard name(s)` label replacement was a no-op; actual catalogue fragment is `wildcard`. Mandatory repeated unchanged-failure stop. Exact remaining repair: `_APPLY_PATH_WILDCARD_SHOWN` fragment becomes `selector`, retain path/reason/privacy checks, rerun exact affected message nodes and supplemental/integration nodes, then fast and normal-hook commit. Caps and lint green; declarations/reconcile/codemap commands completed, full still held. All product/doc/test edits remain uncommitted. No third run or false clean checkpoint claim.

### Completed corrections; checkpoint pending commit/fast

- [x] Safe fixed-message ambiguity subtype at existing IpRule door; conversion rebuilds only that refusal, withholding arbitrary exception details. Supplemental rerun: 122 passed.
- [x] Five-reader legacy-map rejection through conversion/CLI, measured integration expectations, contracts/docstrings/declared docs/migration completed; no v2 representation.
- [x] Actual message-catalogue fragment corrected after verifying git diff. Exact two affected message-door nodes: 2 passed, exit 0. Previous focused run's 7608 passing cases and 14 existing xfails remain evidence; do not claim one fully green focused command.
- [x] Fields, caps, reconcile and codemap check exit 0. Delta compacted to 51 lines without wording changes; no cap raised.
- [x] Normal-hook commit plus fast check and clean checkpoint (immutable fast-checked HEAD recorded below).
- [ ] Root rebase onto integrated #9 baseline, then explicitly released full/device comparison; high-risk fresh Reviewer, metrics and Finalizer remain open.

### Final local handoff checkpoint

- [x] S5/S7 corrections and #8 expectation updates complete; fixed-message ambiguity refusal, flat map rejection before output/mutation, literal/wildcard selector risk in both filter directions, value-free warnings, excluded selector unchanged.
- [x] Normal-hook implementation commit `348108a67421e952a692d7306659eb7e0fff4a8f` passes affected tests and all hooks. Supplemental 122 cases passed; newly added five-reader legacy-map rows and integration expectations passed in the focused selection. Exact two message-catalogue corrections pass. Prior failures/no-op/record-write provenance is preserved without claiming a completely green focused command.
- [x] Fast check passes exit 0 on `1d144fcdf073b12f69d05ff74ff6a249a2105d3e`; fields/caps/reconcile/codemap green. This final commit changes evidence only and preserves the checkpoint.
- [ ] Next incomplete phase-5 work: orchestrator rebase onto integrated #9 baseline `0438299772819f24c871d4cb2b8768f9233f9318`, then explicitly released full checkpoint and device comparison. Original #7 full never passed.
- [ ] Fresh high-risk isolated Reviewer, immutable metrics and bounded Finalizer remain incomplete; no Builder self-approval.

All candidate writes transfer to the orchestrator after this evidence-only handoff. No further local mutations before its explicit resumption.

### Post-rebase verification checkpoint

- Integration base `0438299772819f24c871d4cb2b8768f9233f9318`; resumed candidate `074736b115c45da31c2a0d92ecf35c88054ef32a`. Earlier SHAs remain historical, and #9 runtime invalidates earlier combined-input verification.
- [x] Exact supplemental S5/S7/legacy refusal plus relevant XML/quoting/integration/message selection: 195 passed, exit 0; no product/test edit needed.
- [ ] Fast on new immutable record HEAD; normal-hook clean handoff.
- [ ] Full/device comparison awaits independent final Test/Challenge verdict and orchestrator release. No prior full pass claimed; fresh Reviewer/metrics/Finalizer still open.
