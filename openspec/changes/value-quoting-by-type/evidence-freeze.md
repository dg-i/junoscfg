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
- Resume point: STOP-R same-Reviewer reconfirmation of F1/conditional SC4 on code head `cf6aa270b506c90ce527c3cfa45dca1d91c07a77`, base `40173ba8ec6c0664ea3590b5a3b14786fcf22629`; focused, affected/device, fast and new full checks green. Owner F1 disposition remains pending. Original `4fafc72` checkpoint remains historical (high risk floor).

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
