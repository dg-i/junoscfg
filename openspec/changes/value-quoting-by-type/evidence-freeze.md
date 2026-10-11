<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner brief, kickoff and intake answers of 2026-10-11 (`instruction-integrity.md`): ledger row 8, IDs DEV-4, DEV-5, DEV-6, DEV-7, ANON-P4, NEW-C6, DEV-V1 (escape half); this Builder is the S-lane Builder (C6); no bump, archive, merge or push.
- C3 escape `"` only, `\` as written (device evidence); P11 for the rest. C4 a reader keeps a quoted `policy-algebra` token's quotes only where its text starts with `(`; P12 for the rest. C5 ANON-P4 needs no anonymizer edit; only the strict xfail marker in `tests/unit/anonymize/test_integration.py` goes, after re-checking Builder #7's `files.txt`. C7 `QUOTED` takes the curly lexer's rule. C8 declared break on `consumer` and `cli`. C9 meta verbs stay with change 14. C10 DEV-V7 unchanged.

## Requirements

- `specs/conversion/value-quoting/spec.md` (new capability): ADDED "A policy-algebra value is written as the device's token", "A reader keeps the quotes of a policy name that reads as an expression", "A quote inside a value is escaped", "The leaf's type, not the value's look, decides".
- `specs/validation/set-command-validation/spec.md`: ADDED "A quoted value takes an escaped quote".
- Unchanged and binding: `conversion/writers` "A writer leaves the IR it is given unchanged"; `conversion/raw-set-input` "Quoted content and ignored comments remain accepted" (quoted brackets); `validation/set-command-validation` "A keyed entry takes exactly its key values".

## Evidence

Observed on `50b0a10` (`private_test_data/makeover-work/value-quoting-by-type/repro.py`, `repro-base.out`; synthetic values):

| Input | Base set output | Device or expected |
|---|---|---|
| set `import ( P-A )` | `import "( P-A )"` (a policy name) | `import ( P-A )` (DEV-4) |
| set `import "( P-A && P-B )"` | `import ( P-A && P-B )`; JSON `["( P-A && P-B )"]` | the line as read; JSON `["\"( P-A && P-B )\""]` (DEV-5) |
| JSON `["\"( P-A )\""]` (device JSON/XML) | `import ""( P-A )""`, does not load | `import "( P-A )"` (DEV-6) |
| JSON `["( P-A )"]` | `import "( P-A )"` | `import ( P-A )` (DEV-4) |
| set `description "uplink to sw1 \"core\""` | `description "uplink to sw1 "core""`, does not load; `validate_set` rejects the input | the line as read; valid (DEV-7, NEW-C6, DEV-V1) |
| set `import "PS-1"`, `import PS-1`, `import "PS 1"` | `PS-1`, `PS-1`, `"PS 1"` | unchanged (P12 open) |
| set `message "a\nb"` | `message "a\nb"` | unchanged (device writes `\n` as is) |

- Device renderings (vMX 23.2R2-S7.5 and QFX5120 25.2R2-S1.5): `junoscfg-oracle.set.gz` lines 313-315 `import ( P-A && P-B )`, `export ( P-A || P-B )`, `import ( P-A )`; line 75 `description "uplink to sw1 \"core\""`; line 47 `message "Authorized use only.\nAll access is logged."`; XML `<description>uplink to sw1 "core"</description>`, `<message>…only.\nAll…</message>`. vMX `synthetic-probes.{set,conf}.gz` `import "( P-A && P-B )"`, `.xml.gz` `<import>"( P-A &amp;&amp; P-B )"</import>`, `.json.gz` `"import" : ["\"( P-A && P-B )\""]`.
- Record (`tests/data/device/known-differences.json`): `policy-expression-quoted` 176 lines (JVD `services-leaf1_qfx5130-48c` 160, vMX 8, QFX 8), `escaped-quote-lost` 16, `policy-name-unquoted` 14, `policy-expression-double-quoted` 6: 212 lines.
- Grammar corpus (`tests/data/device/grammar-corpus.json`): 66 recorded false rejections, one of them the escaped-quote line.
- Owning code: `display/value_format.py` `format_value` (the heuristic `policy_expression()`; no escape), its callers in `convert/output/dict_walker.py` (leaf, leaf-list, flat dict, structured bracket list), `structured_output.py` (apply-groups), `set_output.py`, `audit/render.py`; `convert/input/set_input.py` `_parse_value` strips quotes type-blind; `validate/grammar_generator.py` `QUOTED: /"[^"]*"/`. The curly lexer already reads `"(?:[^"\\]|\\.)*"` (`display/set_converter.py` `_TOKEN`), the set tokenizer skips `\x` pairs inside quotes.
- The schema tree carries `tr: policy-algebra` on 7,730 nodes (bundled tree).
- Device questions: P11 (backslash forms) and P12 (quoted plain policy names) in `private_test_data/makeover-probes.md`; no `.out` yet.
- Lexing rows (how-to, "Device captures are machine-formatted"): synthetic catalogue rows in `tests/support/shapes.py` cover the escaped quote in a one-line curly block, a statement spanning lines, comments holding `;`, `{`, `}` and quotes, a template `${SITE}`, prose, and address-form words (`10.255.0.1:100`, `target:<ip>:<n>`, `host:<ip>`, `lo_<ip>`); they stand in for corpus coverage of hand-written text.

## Non-goals

As `proposal.md`: DEV-7's backslash half (P11), quoted plain policy names (P12), DEV-V7, DEV-V1 meta verbs (change 14), XML whitespace (change 9).

## Acceptance criteria

- Every test id the deltas name exists and `agent-ready reconcile` passes. Each new test fails on `50b0a10` and passes after the change, except named pins: `test_a_backslash_is_written_as_it_is`, `test_a_junos_variable_stays_quoted`, `test_a_plain_name_is_quoted_only_where_it_must_be`, the `a-quoted-plain-policy-name` catalogue row, and `test_bare_inner_quotes_are_not_one_value` (base behaviour kept).
- The strict xfail on `test_the_mapping_restores_the_set_output` is removed because it passes.
- `tools/device_differences.py` rebuilds `known-differences.json` without the four classes (212 lines fewer) and nothing else changes; `tools/device_grammar_corpus.py` drops the escaped-quote line from the false rejections and nothing else.
- Schema tier: two regenerations byte-identical except `junos-schema-meta.json.gz`; `pytest --schema tests/corpus/test_schema_data.py` green.
- Before/after comparison over every capture in `manifest.json` (four inputs, four outputs): every difference names the ID it closes.
- Device-evidence checks 2-5 green; `tests/unit/display/`, `tests/unit/convert/`, `tests/unit/validate/`, `tests/unit/audit/`, `tests/unit/anonymize/`, `tests/contract/` green.
- High risk floor: independent Test/Challenge (STOP-T) and a fresh Reviewer (STOP-R).

## Performance expectations

None, because quoting stays one string scan per value and the grammar terminal one regular expression; the full check's timings are the record.

## Outstanding decisions

None blocking: P11 and P12 are device questions with safe interim actions (C3, C4, C7), recorded as non-goals.

## Execution and checkpoint

- Assurance preference: economy
- Risk floor: high (declared break on `consumer` and `cli`; cross-domain: conversion, validation, schema-pipeline, display kernel)
- Roles required: Builder; independent Test/Challenge (STOP-T after phase 4); fresh Reviewer at least as capable as the Builder (STOP-R after phase 5); Finalizer
- Resume point: phase 5 complete at approved immutable a4f822/base40173; refreshed device comparison and fast/new full green. Same independent Reviewer APPROVE; ready for bounded finalization, lifecycle tasks still assigned to orchestrator/Finalizer. Owner explicitly approved F1 reject-before-output, preserving complete expressions and quoted names. Earlier code checkpoints remain historical at their cited heads (high risk floor).

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established: preflight `e03b220`, intent `6bb03f5`, this commit (deltas, code map, freeze). Approved under the owner's unattended-run instruction of 2026-10-11.
- Phase 4: acceptance tests committed at `e6efdb2` (277 nodes fail on `50b0a10`, pins named above). The curly lexing row "statement across lines" became a refusal pin in `tests/unit/display/test_set_converter.py`: the reader refuses a statement across lines whatever it quotes (change 1, probe P7); consistent with the freeze, no criterion changes. Approved under the owner's unattended-run instruction of 2026-10-11.
- 2026-10-11, independent Test/Challenge rulings: all accepted (`test-challenge.md`, F1-F10, SC1-SC3, relayed by the orchestrator), as below.
  - F1: policy chains through every reader and writer (rows `a-policy-chain-holding-a-quoted-name`, `a-policy-chain-of-names`; `TestAPolicyChainIsWrittenAsTheDevicesTokens`); SC1 (curly splits an expression inside `[ ]`) is not this change's layer: pending owner, interim recorded in `review.md`, strict xfail, probe P13, ledgered under change 13.
  - F2, F10: escaping never depends on a node: tests over entry names, apply-macro values and the audit's rendering; the audit output change is in the `cli` declared break.
  - SC2 replaces C7's interim: no new rejection without device evidence; a quoted value ending in a lone backslash stays accepted (`QUOTED` takes an optional trailing backslash), pinned, and junoscfg's own set output validates; P11 strict xfail on the backslash round trip.
  - SC3 changes C4's writer side: a policy-algebra value is written as it is only when the reader keeps it so (an expression starting with `(`, or a quoted token whose text starts with `(`); any other value is escaped, so every value written reads back.
  - F5 over-acceptance negatives, F6 pins and signature-only failures recorded in `metrics.md`, F7 `$junos-` pin with a node, F8 the XML door on the description rows, F9 the empty value and a P11 strict xfail.
  - Criteria affected: the acceptance list above (pins now as in `metrics.md`); the grammar criterion: no line the base grammar accepted is rejected except by the escape rule's design (`"a\\" b"`, still rejected as on the base). Work invalidated: none (no product code yet). Reruns: phase-4 base counts (404 failed). Approved under the owner's unattended-run instruction of 2026-10-11.

- 2026-10-11, new owner instruction (orchestrator repair brief): exclusive makeover ownership transferred to Codex with Claude sessions idle; no session control, network, push, external systems, merge, archive or version bump. Test relaxation is authorized only by concrete evidence/challenge, not convenience. Rebase performed by the orchestrator onto `40173ba8ec6c0664ea3590b5a3b14786fcf22629`, yielding `f04ec2f1f693a6ce5642b844d7f4f0295073c1b3`. Historical full/schema/device evidence retains its original base/head identity.
- Independent review F1 (original immutable report copied to `review.md`) demonstrates schema-valid JSON/YAML `( A ) ; export P-B` becoming two statements. Delta consistency: the existing one-device-token and preservation obligations already forbid this output, and architecture's structural-error door supplies fail-before-emission when quoting cannot preserve the approved reader IR. No specification or acceptance oracle is relaxed. SC4 retains its original conditional decision wording; SC1–SC3 interim actions remain unchanged. Safe repair: use the shared lexical boundary helper and require one complete parenthesized expression; reject before writing malformed expression-shaped values. Runtime/test changes invalidate the old full checkpoint and require focused, fast and new full checks and same-Reviewer reconfirmation. Schema generation inputs are unchanged by this repair; retain expensive-tier evidence without repeating it. Refresh device comparisons against the current integration base.

- Repair evidence on integration base `40173ba`: focused 155 passed/2 strict xfailed; affected/device 7,993 passed/1 skipped/20 strict xfailed. Fresh device comparison 36/96 plain and 432/1,152 all rule runs differ, output only, each explained by DEV-4/5/6/7; all repair outputs/results equal original Reviewer head records. Fast snapshot refusal diagnosed as required commit ordering; commit code before retry. Owner F1 disposition is being interviewed by the orchestrator; no answer or generic merge permission is inferred.

- New final-candidate checkpoint at `cf6aa270b506c90ce527c3cfa45dca1d91c07a77`: fast and full exit 0, every check passed; full application tests 8,443 passed/37 skipped/20 strict xfailed with coverage floor passed. The first commit hook attempt lacked hatchling in the scratch uv cache; one evidence-backed cache correction used the populated default cache offline, and all commit hooks passed. No generated record was invalidated by the F1 repair, no expensive tier or retired JVD tier was repeated. Same-Reviewer reconfirmation and owner F1 disposition still required.

- Same independent Reviewer reconfirmation F2 (`roles/codex-rereview.md`, preserved in tracked review) establishes exact five-reader and baseline round-trip support for `("P 1" && P-B)` and `(("P 1") && P-B)`. The canonical `reads_as_one_statement` precondition imposes a stronger invariant than the unchanged expression requirement. Delta consistency: accepted implementation/test correction, no spec change or new owner approval; replace only that formatter precondition using suitable existing lexical primitives, preserve the raw/unplaced helper unchanged, all F1 negatives and SC1–SC3 interims. New runtime/tests invalidate the cf6aa270 fast/full checkpoint; exact editing feedback, settled focused/fast and one new committed full checkpoint required. Refresh device comparisons; generation inputs remain unchanged, so no expensive schema-tier rerun. SC4 can be classified as omitted-negative implementation coverage under the existing structural-error invariant, as the same Reviewer assessed; original conditional wording and owner's unanswered picker remain intact.

- F2 settled implementation: same-package shared `_TOKEN` lexical primitive replaces the canonical raw-record helper precondition; raw helper behavior unchanged. Parentheses/quotes/line boundaries retained. Five-reader exact compact/nested rows and quoted meaningful-space row pass, 332 focused passed/2 strict xfailed; lexical compact-semicolon limitation explicitly carried forward with integration-base failure evidence, spaced positive kept. No spec or interface change; `agent-ready interfaces` exit 0.

- Orchestrator instruction: accurately document resulting fail-before-emission behavior under the existing preservation/error invariant in consumer/CLI break declarations, migration and existing quoting docs/changelog; no requirement rewrite or owner approval. Copied independent reports contain synthetic examples, no private operator data. This documentation correction accompanies the pending reviewed code candidate.

- F2 fresh device-head comparison completed over all 1,152 rule runs, reusing unchanged integration-base inputs/result: output-only 36/96 plain and 432/1,152 total differ via DEV-4/5/6/7; every F2 head result equals prior repaired-head result. No generated record invalidated; generator inputs unchanged. Ready to commit settled runtime/test/doc correction before fast/full.

- Owner interview (2026-10-11, relayed by orchestrator): F1 reject-before-output explicitly approved, preserving complete expressions and quoted names. No requirement rewrite or agent-manufactured approval. Device probe source is being curated by the orchestrator; its P11–P13/P16 assessment requests no schema/runtime expansion for this repair and retains SC1 strict xfail/reader compatibility. Record narrow capture references when supplied; never infer outcomes from echoed input.

- 2026-10-11, same independent Reviewer F3 (`roles/codex-rereview-final.md`): standalone and word-attached unquoted closing brackets pass the curly lexical guard but create unreadable SET/structured output. Existing preservation/one-token/error obligation and explicit owner refusal decision authorize a bounded omitted-negative correction using the public input bracket provider; no requirement rewrite or changed SC1–SC3 interim. Runtime/test changes invalidate e38 fast/full; run focused, fast and one new committed full checkpoint, refresh device-head comparison. No generation input changed; expensive schema evidence retained. The e38 full completed before a stop signal reached it, exit 0 with 8,641 passed/37 skipped/20 xfailed; it is superseded by the independently demonstrated F3, not final-candidate evidence.

- 2026-10-11 factual device delta: narrow executed P11/P12/P13 extracts in private `makeover-work/codex-resumption/device-evidence/`, bound by `provenance.json` to vMX 23.2R2-S7.5, `device-probe.out` SHA256 `48e591da0c6dbde33d18ce21e92a83844ae876abf229564d2aace2f0a159747d` (49,908 bytes/1,465 lines). Early paste echo is excluded. P11 retains the two supplied internal backslash spellings in XML/decoded JSON (source starts 917/921/940 and 956/960/979); its supplied trailing-backslash command rejects expecting data at 912–914, so absence in subsequent output is not a successful empty value. P12 (1022/1027/1054) canonicalizes quoted plain P12-A and retains literal enclosing quotes for the name with a space; arbitrary IR quote stripping is not authorized. P13 (1089/1095/1100/1126) writes expression plus P-C as structured bracket chain and two JSON/XML values; no commit-success claim is made. Existing SC1 strict xfail is a demonstrated owning-reader defect, SC2 base acceptance/round-trip compatibility and SC3 writer interim remain unchanged. P16's accepted definition/rejected BGP reference does not establish the synthetic audit tokenizer case as device-valid; audit defect and XSD-model limitation remain separate carry-forward items. No raw operator prompt/configuration is copied. Historical unknown/no-output statements above retain their original evidence date; these executed narrow facts supersede current unknown explanations without changing requirements or xfail outcomes.
- F3 implementation uses the public quote-aware input provider; focused 368 passed/2 strict xfailed. Current-facing P11/P13 explanations updated factually only. Reconfirm with the same Reviewer after the new committed checkpoint; no lifecycle task completed here.

- Final committed F3 checkpoint at code head `a4f822b4e131c75d667022218dd868003df985aa`, immutable integration base `40173ba8ec6c0664ea3590b5a3b14786fcf22629`: focused 368 passed/2 strict P11 xfailed; all commit hooks passed; fast and full both exit 0 with every check passed. Full application result 8,677 passed/37 skipped/20 strict xfailed; coverage floor passed. Commands used `UV_OFFLINE=1 npm_config_offline=true PYTHONDONTWRITEBYTECODE=1 uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set fast` and the same command with `--set full`. Private logs: `roles/repair-f3-{focused,fast,full}.out`. Fresh device-head comparison covers 1,152 runs, all exactly equal F2 head; against unchanged 40173 baseline 36/96 plain and 432/1,152 total differ, output only through DEV-4/5/6/7 (bare expression, retained expression-shaped quoted name, no doubled enclosing quotes, escaped inner quote); no diagnostic/field-validation/exception differences. Baseline reuse is bound to unchanged SHA, manifest/captures, recipe, dependencies and configuration. No generation input changed; historical expensive-schema evidence retained and no retired JVD tier repeated.
- Same independent Reviewer `roles/codex-rereview-approved.md` APPROVE exact a4f822/base40173, independent isolated 5,061 passed/6 strict xfailed and separate refusal/preservation probes. Full finished green afterward; ready for bounded finalization. This evidence-only amendment does not invalidate the checkpoint or require another correction review. Lifecycle records/main-spec application remain with orchestrator/Finalizer.
