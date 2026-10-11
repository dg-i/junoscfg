## 1. Verification

- [x] 1.1 Acceptance tests (fail on the merge base `50b0a10` by design, pins named in `evidence-freeze.md`): `tests/unit/display/test_value_format.py::TestAValueIsSpelledByItsLeaf`; catalogue rows in `tests/support/shapes.py` (`a-one-term-policy-expression`, `a-quoted-policy-name-that-reads-as-an-expression`, `a-quoted-plain-policy-name` (pin), `a-value-holding-an-escaped-quote`, `an-expression-in-a-description`, and the lexing rows `an-escaped-quote-in-a-one-line-block`, `an-escaped-quote-beside-comments`, `an-escaped-quote-in-a-template`, `an-escaped-quote-in-prose`, `address-forms-inside-words-beside-an-escaped-quote`) through `tests/contract/test_format_matrix.py`; `tests/unit/display/test_set_converter.py::TestMalformedTextIsRefused::test_it_raises[a-statement-across-lines-holding-an-escaped-quote]` (pin); `tests/unit/validate/test_grammar_generator.py::TestAnyLeafValueMayBeQuoted`; `tests/corpus/test_shipped_artifacts.py::TestTheShippedGrammarKeepsRejecting` rows; the strict xfail on `tests/unit/anonymize/test_integration.py::TestKeyedEntriesSurvive::test_the_mapping_restores_the_set_output` removed.
- [x] 1.2 Independent Test/Challenge on these tests (high risk floor): `test-challenge.md`; findings F1-F10 and SC1-SC3 ruled by the orchestrator, all accepted and applied (chain rows, nodeless escaping, audit rendering, SC2/SC3 interim pins, P11/P13 strict xfails).

## 2. Change

- [x] 2.1 `display/value_format.py`: `format_value(value, node=None)` writes a `policy-algebra` token the reader keeps as written as it is, quotes any other value where it must be and always escapes `"`; `policy_expression()` goes.
- [x] 2.2 `convert/output/dict_walker.py`: every call passes the leaf's schema node.
- [x] 2.3 `convert/input/set_input.py`: a quoted `policy-algebra` value whose text starts with `(` keeps its quotes.
- [x] 2.4 `validate/grammar_generator.py`: `QUOTED` takes `\"` and keeps a trailing backslash (SC2); schema tier regenerates `validate/data/` (ef06855; second run byte-identical except `junos-schema-meta.json.gz`); `tools/device_grammar_corpus.py` (false rejections 66 -> 65) and `tools/device_differences.py` (928 -> 716 lines, four classes gone) rebuild their records.
- [x] 2.5 Changelog fragments (bugfix, removal), docs (`design-decisions.md` Value Quoting, `guide/audit.md`), `display/CONTRACT.md` invariant; before/after comparison over every capture: plain 36 of 96 conversions differ, anonymized 432 of 1,152 (the same 36 under each of 12 rule sets), every changed line a policy-algebra token (DEV-4/5/6) or an escaped quote (DEV-7), no diagnostic, field-validation or exception difference.

- [x] 2.6 Historical full checkpoint (invalidated for the current candidate by rebase and runtime/test repair): `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` at `4fafc72`: every check passed; application tests 8,351 passed, 37 skipped, 20 xfailed.

- [x] 2.7 Repair independent review F1 without changing the spec: one complete lexical expression, shared statement-boundary helper, fail-before-emission when quoting cannot preserve IR, JSON/YAML/XML negatives and quoted-name delimiter positives. Focused tests: 155 passed, 2 strict P11 xfailed.
- [x] 2.8 Historical first repair integration checkpoint (invalidated by F2 runtime/tests) at base `40173ba8ec6c0664ea3590b5a3b14786fcf22629`: affected tests, fast, full and refreshed device comparisons; old full checkpoint is historical.

- [x] 2.9 Same-Reviewer F2 correction: reuse shared lexical primitive without canonical raw-record restrictions; preserve raw helper, F1 negatives and scoped interims; compact/nested five-reader catalogue rows and meaningful quoted-space row; settled focused tests 332 passed, 2 strict xfailed.
- [x] 2.10 Historical e38 F2 checkpoint, superseded by F3: fresh device comparison and fast/full passed; full 8,641 passed/37 skipped/20 xfailed.
- [x] 2.11 F3 omitted-negative correction: public quote-aware input bracket provider; 24 singleton/chain negatives and 12 quoted-bracket positives; settled focused 368 passed/2 strict xfailed.
- [x] 2.12 F3 settled committed candidate at a4f822/base40173: refreshed device comparison, fast and new full green (8,677 passed/37 skipped/20 strict xfailed); same independent Reviewer APPROVE. Lifecycle tasks 3.1–3.3 remain with orchestrator/Finalizer.

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review: same independent Reviewer APPROVE exact a4f822/base40173, verbatim report in `review.md`; candidate fast/full green as recorded above.
- [x] 3.2 Capture and review `metrics.md` and `metrics.json` for immutable base `40173ba8ec6c0664ea3590b5a3b14786fcf22629` and code head `a4f822b4e131c75d667022218dd868003df985aa`; unsupported usage remains UNMEASURED.
- [x] 3.3 Finalizer completes bounded pre-merge spec application, evidence, and archive-readiness housekeeping without product edits. Actual post-merge live-folder archive is reserved to the orchestrator, per the explicit phase-7 handoff scope.

## Repair checkpoint and handoff

Immutable integration base `40173ba8ec6c0664ea3590b5a3b14786fcf22629`; runtime/test code head `cf6aa270b506c90ce527c3cfa45dca1d91c07a77`. Focused: 155 passed, 2 strict P11 xfailed. Affected/device: 7,993 passed, 1 skipped, 20 strict xfailed. Fast check: every check passed. New full command `UV_OFFLINE=1 npm_config_offline=true PYTHONDONTWRITEBYTECODE=1 uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full`: exit 0, every check passed; 8,443 passed, 37 skipped, 20 strict xfailed, coverage floor passed. Logs are in private scratch `roles/repair-{affected,fast-committed,full}.out`. Tree clean after full. No expensive schema-tier rerun: repair and integration diff changed no relevant generation input.

Resume at same independent Reviewer reconfirmation (F1/conditional SC4 on unchanged governing requirements), then the owner disposition and bounded Finalizer; tasks 3.1–3.3 stay open. This evidence-only commit changes no runtime/test/generation input and does not invalidate the full checkpoint. Owner interview has no received answer for F1; do not infer approval. Orchestrator performed the rebase; Builder performed no branch switch, rebase, push, merge, archive or version bump.


## Final repair handoff (supersedes historical checkpoint above)

Final committed F3 checkpoint at code head `a4f822b4e131c75d667022218dd868003df985aa`, immutable integration base `40173ba8ec6c0664ea3590b5a3b14786fcf22629`: focused 368 passed/2 strict P11 xfailed; all commit hooks passed; fast and full both exit 0 with every check passed. Full application result 8,677 passed/37 skipped/20 strict xfailed; coverage floor passed. Commands used `UV_OFFLINE=1 npm_config_offline=true PYTHONDONTWRITEBYTECODE=1 uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set fast` and the same command with `--set full`. Private logs: `roles/repair-f3-{focused,fast,full}.out`. Fresh device-head comparison covers 1,152 runs, all exactly equal F2 head; against unchanged 40173 baseline 36/96 plain and 432/1,152 total differ, output only through DEV-4/5/6/7 (bare expression, retained expression-shaped quoted name, no doubled enclosing quotes, escaped inner quote); no diagnostic/field-validation/exception differences. Baseline reuse is bound to unchanged SHA, manifest/captures, recipe, dependencies and configuration. No generation input changed; historical expensive-schema evidence retained and no retired JVD tier repeated.

Same independent Reviewer APPROVE exact a4f822/base40173; no blocking owner question for this correction. Owner explicitly selected reject-before-output. No runtime/test/generation changes after the approved code head; this evidence-only record preserves checkpoint validity. Finish lifecycle records and bounded main-spec application under the Finalizer; Builder does not tick 3.1–3.3, archive, bump, merge, rebase, switch branches, push or contact external systems.

## Bounded phase-7 pre-merge checkpoint

Main-spec application commit `c3ce39a`: supported OpenSpec 1.13.0 archive in a disposable tracked-tree copy produced four conversion/value-quoting requirements and one validation/set-command-validation requirement. Only those two main specs returned to this live branch. Exact-body assertions confirmed the reviewed delta was copied without meaning changes and the existing validation requirements were preserved; both strict change validation and all 21 main specs passed. The live change folder remains present.

Metrics capture/review binds the full immutable base/code-head above: own-file diff 25 files, +932/-331 and 2 binary files; declared runtime dependencies 6/6 and locked packages 63/63. Native session/workflow/human timing evidence was not supplied, so its fields stay UNMEASURED. Context-expansion and measured behavioral-evidence rows survive. Owner F1 refusal and executed P11/P13 facts are already recorded in the freeze and review; SC1–SC3 keep their existing scoped interims. No blanket approval or requirement/oracle change is introduced.

Next action: orchestrator's bounded main-spec inspection and integration, then merge-time version/tag and supported post-merge `archive --yes --skip-specs`. The approved a4f822 runtime/test/generation inputs and their final full checkpoint are unchanged. No full, expensive schema or retired JVD tier is repeated for these records.

Same independent Reviewer APPROVE bounded main-spec application at immutable `c3ce39a42ec0d8ec5d5d3171f041af589ebd16a9`; report `private_test_data/makeover-work/value-quoting-by-type/roles/codex-main-spec-review.md` (main checkout scratch), exact two paths/+129 lines and unchanged requirement bodies/test references/scoped interims. Product approval stays bound to a4f822. Fields and caps passed; initial lane refused uncommitted governed records as designed, then committed evidence `dec3db23dbf71fd693ede0f51eee95b8289ccae8` passed lane, strict change validation and status 8/8 artifacts complete.
