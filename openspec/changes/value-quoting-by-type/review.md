## Findings

<!-- Filled by the fresh Reviewer at STOP-R. -->

## Already provided

<!-- Filled by the fresh Reviewer at STOP-R. -->

## Specification challenges

### SC1 An expression inside a curly policy chain

- Artifact: `specs/conversion/value-quoting/spec.md`, "A policy-algebra value is written as the device's token" (the structured chain `[ … ]`); `src/junoscfg/display/set_converter.py` bracket lists.
- Counterexample: executed (Test/Challenge F1, `test-challenge.md`). JSON `"import": ["( P-A )", "P-B"]` written to structured is `import [ "( P-A )" P-B ];` on the base, a policy name; written as the device's token it is `import [ ( P-A ) P-B ];`, which the curly lexer reads as `(`, `P-A`, `)`, `P-B`. Curly `import [ ( P-A && P-B ) P-C ];` already reads as six values on the base.
- User impact: a curly policy chain holding an expression does not read back as itself; set output is right (one line per value).
- Proposed correction: the curly lexer reads a parenthesised run inside a bracket list as one value, once the device says whether a chain may hold an expression and how it prints one (probe P13). The lexer's bracket lists are the readers' shared boundary, so the fix belongs to change 13 (`one-ir-at-reader-boundary`).
- Decision: Pending owner decision. Interim action: writers write each chain value as the device's token (the expression bare, its meaning kept); the curly read-back is the strict xfail `tests/unit/display/test_set_converter.py::TestStructuredBracketLists::test_an_expression_in_a_bracket_list_is_one_value`; probe P13; ledgered under change 13 (owner intake 2026-10-11: merge with recorded interim action).

### SC2 A quoted value ending in a lone backslash

- Artifact: `specs/validation/set-command-validation/spec.md`, "A quoted value takes an escaped quote" (as frozen at `a3b2472`: "A quoted value ending in a lone backslash is no longer one value"); `.openspec.yaml` declared break.
- Counterexample: executed (Test/Challenge F3). Under `QUOTED: /"(?:[^"\\]|\\.)*"/`, `set system host-name "abc\"` still validates (as `VALUE`) and `"a b\"` is rejected, while the set reader reads both (`abc\`, `a b\`) and junoscfg's set writer writes the value `a b\` as `"a b\"`, which validated on the base.
- User impact: junoscfg would reject its own set output; the declared break described the change wrongly.
- Proposed correction: no new rejection without device evidence; the grammar, the set reader and the writer agree; P11 decides how the device writes a trailing backslash.
- Decision: Pending owner decision. Interim action: base acceptance kept, round trip pinned, P11 (owner intake 2026-10-11: merge with recorded interim action). `QUOTED` takes an escaped character and an optional trailing backslash before the closing quote; pins `test_a_quoted_value_ending_in_a_backslash_parses`, `TestJunoscfgsOwnSetOutputValidates`, shipped-grammar rows `a-word-ending-in-a-backslash`, `a-quoted-value-ending-in-a-backslash`; the strict xfail `TestEveryValueReadsBackAsWritten::test_a_value_holding_a_backslash_reads_back` cites P11.

### SC3 A quoted plain policy name held in the IR

- Artifact: `specs/conversion/value-quoting/spec.md`, the writer requirement ("or a quoted name") against the reader requirement's `(`-only rule (C4).
- Counterexample: executed (Test/Challenge F4). IR `"import": ["\"P 1\""]` from JSON or XML written as is, `import "P 1"`, reads back as `["P 1"]`.
- User impact: JSON or YAML output after a set or curly hop differs from the input IR for a quoted plain policy name; the device configuration is probably the same (P12).
- Proposed correction: the writer round-trip law holds for every value the writer writes: a policy-algebra value is written as it is only when it is what the reader keeps as written (an expression, or a quoted token whose text starts with `(`); any other value is escaped as a value (`"\"P 1\""`).
- Decision: Pending owner decision. Interim action: escaped so it reads back as written, pinned by `TestAValueIsSpelledByItsLeaf::test_any_other_policy_algebra_value_is_escaped` and `TestEveryValueReadsBackAsWritten::test_a_policy_algebra_value_reads_back`; probe P12 is the evidence that would change it (owner intake 2026-10-11: merge with recorded interim action).

## Verdict

<!-- Filled by the fresh Reviewer at STOP-R. -->

## Independent review at original immutable head

The following report is preserved verbatim as historical evidence for `586841fe38b0b10aa402fafed6250c2001f73280`; it is not a verdict on the rebased repair candidate.

# Done

**CHANGES REQUIRED.** Fresh independent phase-6 review of `value-quoting-by-type`, immutable HEAD `586841fe38b0b10aa402fafed6250c2001f73280`, against merge-base with `master` `50b0a104f497ba2783ee81c7a72db4b85fc14e20`. The checkout was clean and remained on that HEAD. No Builder private reasoning was supplied or used; committed freeze, delta, contracts, challenge evidence, tests and diff were read in that order. Owner intake rulings were checked against `private_test_data/makeover-work/builder-brief.md`.

One new high-severity implementation finding blocks approval. The existing SC1–SC3 interim actions remain owner-authorized in their recorded scope. The normal quoting fixes, escaped-quote validation and device-accountability reductions are supported by independent execution.

# Evidence

## Ranked findings

### F1 — High: the expression bypass emits additional configuration statements

**Requirement:** delta `specs/conversion/value-quoting/spec.md`, “A policy-algebra value is written as the device's token,” limits the unquoted bypass to a value “that is one device token.” The same delta says every written value reads back as that value. `src/junoscfg/convert/CONTRACT.md` requires every supported pair to round-trip without content loss, and `display/CONTRACT.md` requires every value written to read back. `ARCHITECTURE.md` §1 ranks preserving configuration meaning first.

**Diff:** `src/junoscfg/display/value_format.py:44–45` returns true solely for `text.startswith("(")`; `:58–59` consequently writes the entire supplied string without quoting. `convert/output/dict_walker.py:409` now applies this bypass to the leaf node.

**Executed counterexample:** JSON `{"configuration":{"protocols":{"bgp":{"group":[{"name":"G","import":["( A ) ; export P-B"]}]}}}}` passes `validate_config(format=Format.JSON)` with no errors on both base and head. Conversion with `strict=True` also reports no field diagnostics. Base structured output contains `import "( A ) ; export P-B";` and reads back unchanged. Head contains `import ( A ) ; export P-B;` and reads back as `import: ["( A )"]` plus a new `export: ["P-B"]`. The preservation assertion exits 0 on base and 1 on head. YAML also passes schema validation and produces the same unsafe output; XML conversion with strict field validation does so without diagnostics. XML XSD validation is unavailable because this checkout has no cleaned XSD artifact.

This establishes a regression for an accepted JSON/YAML value and a violation at the value-to-command boundary. It does **not** claim that the payload is itself a valid Junos policy expression: the defect is treating a non-token as the token the bypass requires. A delimiter in caller-controlled data becomes configuration syntax. The semicolon example involves no backslashes, bracket chain or quoted plain-name ambiguity, so SC1–SC3 do not cover it.

**Recommendation:** make the shared bypass require one complete lexical expression, honoring delimiters inside quoted policy names but refusing statement boundaries outside them. If an accepted IR value cannot be represented with the required semantics, fail before emitting output rather than silently creating statements. Add the counterexample as a negative case through JSON, YAML and XML to structured, with set-output coverage too; retain positive cases such as `( "P;1" && P-B )`. Do not substitute the old look-based boolean-operator heuristic. Record the omitted boundary criterion through SC4 below if a specification decision is needed.

Minimal public-API reproduction, run in each tree:

```python
import json
from junoscfg import Format, convert_config, validate_config
ir = {"configuration": {"protocols": {"bgp": {"group": [
    {"name": "G", "import": ["( A ) ; export P-B"]}
]}}}}
source = json.dumps(ir)
assert validate_config(source, format=Format.JSON).valid
written = convert_config(source, from_format=Format.JSON,
                         to_format=Format.STRUCTURED, strict=True)
back = json.loads(convert_config(written, from_format=Format.STRUCTURED,
                                 to_format=Format.JSON, strict=True))
assert back == ir, "A single leaf value became two statements"
```

## Specification challenges

**Preserve SC1–SC3 verbatim in the tracked review.** Owner intake answer 3 explicitly permits their recorded interim actions: SC1 writes chain tokens with the curly reader gap kept as a strict xfail and owned by change 13/P13; SC2 preserves trailing-backslash acceptance pending P11; SC3 escapes quoted plain names held in the IR pending P12. No probe answer file exists. These narrowly recorded actions are not new findings and are not reversed by this review.

### SC4 — The one-token criterion lacks a statement-boundary negative

- **Artifact:** `specs/conversion/value-quoting/spec.md`, “A policy-algebra value is written as the device's token”; `display/CONTRACT.md` and `convert/CONTRACT.md` preservation invariants.
- **Counterexample:** executed F1 above; JSON/YAML schema-valid import value `( A ) ; export P-B` becomes two structured statements on head, while base preserves it. All committed acceptance tests pass because the policy-algebra examples lack an unquoted statement delimiter after an expression.
- **User impact:** caller-controlled value text adds an export policy and changes configuration meaning without a diagnostic, including under strict conversion.
- **Proposed correction:** explicitly require a bypassed value to occupy exactly one lexical expression/token. Add adversarial policy-algebra rows with semicolons/braces/comment or line boundaries outside quoted names, and positive quoted-name delimiter cases. Refuse before emission if preserving the value is impossible under the approved reader semantics. This supplements the existing preservation invariant rather than asserting new Junos compatibility.
- **Decision:** Pending owner decision if the correction needs a changed specification. No new interim merge action is established by this report. Existing scoped SC1–SC3 permission does not authorize this counterexample. Correct F1 before approval; do not merely record it as another mergeable limitation.

## Independent checks and figures

- Head focused run: **7,901 passed, 1 skipped, 20 strict xfailed** over display, conversion, validation, audit, anonymization and contract tests, plus device rendering, device anonymization, shipped-artifact and device grammar-corpus tests. This includes device-evidence checks 2–5, the format matrix, escaped quote/hand-written text cases and the formerly xfailed anonymization revert.
- Current acceptance files executed against base product code: **404 failed, 4,486 passed, 6 strict xfailed**. The failure count agrees with the phase-4 record; this review's selection also includes additional unchanged tests, hence different pass/xfail totals. Full output is `roles/review-base-tests.out`. Signature-only failures remain documented pins, not evidence of a behavioral defect.
- Independently recorded every rendering in `tests/data/device/manifest.json` using the public conversion-result API: **36 of 96 plain conversions differ; 432 of 1,152 runs with the rule combinations differ.** Only `output` differs. No diagnostics, field-validation message or exception difference occurred. The changed plain lines are the one-term expression, quoted expression-shaped policy names, removal of doubled quotes, and escaped description quote (DEV-4/5/6/7). The other rule runs follow the same changes. Raw comparison results are `roles/review-base.json` and `roles/review-head.json`.
- Independent record diff: **928 → 716** lines; exactly `policy-expression-quoted` **176**, `escaped-quote-lost` **16**, `policy-name-unquoted` **14**, and `policy-expression-double-quoted` **6** removed: **212** total. No added line or changed surviving classification. Other classes, including `junos-variable-quoted`, are unchanged.
- Grammar corpus: rejected rows **66 → 65**, losing exactly the device's escaped-description line; accepted rows **189 → 190**, adding `set groups GR-OMIT system apply-flags omit`. Independently parsed all accepted rows on base/head: **408 → 409** distinct parse rules, exactly their recorded counts. `device_lines: 8713` is unchanged record metadata; the exhaustive regeneration tier was not repeated during review.
- Independently traversed the bundled tree: **7,730 policy-algebra nodes, all 7,730 leaf-lists**. Decompressing the shipped grammar from base/head shows exactly one text-line change, `QUOTED`; the generated name-keyed grammar has the same terminal. No hand edit of other generated grammar content was detected.
- Device evidence reread from `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.set.gz` (vMX, 23.2R2-S7.5): message line 47, escaped-description line 75, one-term expression line 315. Equivalent QFX evidence is `synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.set.gz` (QFX5120, 25.2R2-S1.5), lines 47, 75 and 303. The quoted-name oracle is vMX `synthetic-probes.{xml,json}.gz`, as cited in the freeze.
- The saved full-check result at `4fafc72` says every check passed. `git diff --name-only 4fafc72..586841fe` contains only freeze, metrics and tasks records; no runtime change invalidates that checkpoint. Schema regeneration evidence was read, and the expensive schema tier was not repeated. Changelog fragments, declared consumer/CLI break and migration, version-at-merge policy, generated terminal and documentation agree for the intended cases.

## Five review prompts

1. **Trust-boundary input:** configuration values from JSON/YAML/XML are caller-controlled data crossing into emitted Junos commands. F1 demonstrates a statement-boundary violation independently of Junos acceptance of the malformed expression.
2. **Incompatible-but-valid input:** the F1 JSON and YAML pass current validators and strict field conversion, yet contradict the bypass's one-token assumption. Ordinary expression/quoted-name cases, nodeless values and all affected reader/writer pairs pass their matrix tests. Quoted set input containing the same semicolon remains one quoted name in all four writers, consistent with the approved interim semantics.
3. **Shared blind spot:** all acceptance tests pass while the unquoted `(` branch accepts the F1 payload. The independent preservation assertion and base/head contrast provide the missing evidence; SC4 adds the negative criterion without inventing device syntax.
4. **Second answer:** `display.format_value`, `is_policy_algebra` and `is_algebra_token` centralize the new reader/writer choice. Callers in dict_walker, structured apply-groups, set scalar output and audit rendering were checked; escaping applies even without a node. A separate pre-existing escaped-policy-name audit problem is carried forward below. The grammar's optional trailing backslash differs from the curly lexer deliberately under SC2, not as an unapproved fallback.
5. **Stated figures and non-goals:** the actionable record counts, comparison figures, node count and covering-rule count were rerun above. The phase-4 404-failure count was reproduced on current acceptance files. Backslashes P11, plain-name device spelling P12, curly expression chains P13, XML whitespace and validation meta verbs remain the declared non-goals. None claims an impossible capability that this review treats as proven. Full/schema checkpoint statistics are saved execution evidence, not a fresh rerun claim.

## Already provided and carry-forward

Existing providers are `junoscfg.display.format_value` for every writer's escaping, shared type/token predicates for the set reader, `DictWalker` for both command writers, and the device-format matrix/catalogue for family laws. No new formatter or per-output walker is needed to fix F1.

**Separate pre-existing audit defect:** `src/junoscfg/audit/algebra.py::_QUOTED` uses `"[^"]*"`, so an escaped quote inside a policy name is split into several names. With these synthetic set lines:

```text
set policy-options policy-statement "( P \"1\" )" then accept
set protocols bgp group G import "( P \"1\" )"
```

public `to_dict`, `collect_occurrences` and `find_unused(types=["policy-statement"])` classify the defined name `( P "1" )` as `unused` on both base and head and render a delete suggestion. Base splits the reference into `P` and `1`; head splits the preserved escaped token into three fragments. Thus this is not introduced by #8. Recommend ledgering a separate audit-name-tokenization follow-up; exact device spelling for these policy-name characters needs evidence before changing its semantic representation. No device-validity claim is made for this synthetic name. Do not suppress this observation merely because the formatter tests pass.

Carry forward the missing cleaned XSD if independent XML schema validation is required: conversion/field validation was executed, but `validate_config(format=XML)` raises `SchemaLoadError` before validating. Add this limitation to the tracked change's carry-forward evidence, not only this scratch report.

Suggested phase-6 context-expansion rows for the Builder to preserve in metrics: `display/value_format.py` (shared bypass), `convert/output/dict_walker.py` (all formatter call sites), `display/set_converter.py` (lexical statement boundary), `audit/algebra.py`, `audit/walker.py`, `audit/engine.py`, `audit/render.py` (checking the downstream meaning/rendering consumer), `tests/support/shapes.py` and `tests/contract/test_format_matrix.py` (coverage), `tools/device_differences.py`/`tools/device_grammar_corpus.py` (rerunning evidence figures), and the JVD-retirement decision below.

# Changed paths

Only review scratch under `/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/value-quoting-by-type/roles/`: this `codex-review.md`, independent `review-base.json`, `review-head.json`, `review-base-tests.out`, and review-only pytest temporary/cache directories. No tracked file, code, test, specification, Git state or other process was edited.

# Commands and exit status

All Python runs used `PYTHONDONTWRITEBYTECODE=1`, offline uv and `--locked --no-sync --group dev`; pytest used `-p no:cacheprovider` and scratch `--basetemp`. Successful runs also set scratch `UV_CACHE_DIR`.

- `git status --short`, `rev-parse HEAD`, `merge-base HEAD master`, diff/source reads and `git diff --check`: **0**, clean expected HEAD.
- Graph vocabulary inspection and `graphify query 'value quoting policy algebra walker reader grammar' --budget 1400` in main checkout: **0**. Main graph provided the map; its result was truncated, so current source supplied proof. No graph refresh/write was performed under review isolation.
- Head pytest: `tests/unit/{display,convert,validate,audit,anonymize}/ tests/contract/ tests/corpus/test_device_renderings.py tests/corpus/test_device_anonymization.py tests/corpus/test_shipped_artifacts.py tests/corpus/test_set_corpus.py`: **0**; 7,901 passed, 1 skipped, 20 xfailed.
- Base-code pytest selected current `test_value_format.py`, `test_set_converter.py`, `test_grammar_generator.py`, `test_convert_roundtrip.py`, `test_render.py`, anonymization revert node, shipped-grammar rejection/output classes and `test_format_matrix.py`, using `PYTHONPATH=<base>/src`: **1 expected**, 404 failures demonstrate the regressions against base.
- `compare.py record roles/review-base.json --anonymize` in existing base tree and `record roles/review-head.json --anonymize` in head: **0** each; 1,152 conversions each. Independent comparison/classification, record/tree counts and grammar text inspection: **0**. Independent Lark covering-rule union on base/head: **0**.
- F1 public-API preservation assertion: **0 on base, 1 on head**, with the expected assertion failure. Additional JSON/YAML/XML strict conversion and quoted-set control probes: **0** after separating unavailable XML XSD validation. Audit base/head probes: **0**, both expose the separate carry-forward defect.
- Combined `agent-ready fields`, `caps`, `reconcile` command: **0** overall; repository-standing informational diagnostics only. No record commit was made.
- Initial uv default-cache attempt: **2**, sandbox could not initialize `/Users/manon-dev/.cache/uv`; scratch cache resolved it without escalation. Exploratory import/signature probes initially exited **1**, corrected after reading the package door and signature. XML XSD validation probe exited **1**, `SchemaLoadError` for absent cleaned XSD; its conversion checks succeeded separately.

# Open questions for the owner

F1 must be corrected; SC4 records the decision needed only if the accepted-value promise must be clarified to permit a fail-before-emission outcome. No owner question was sent. Existing P11/P12/P13 decisions remain pending with their previously approved scoped interim actions. The separate audit-name device spelling remains a follow-up evidence question.

# Deviations

The orchestrator required a scratch report only, so this Reviewer did not edit tracked `review.md`, `metrics.md` or the lifecycle checkbox; the Builder must copy/preserve the report, challenges, carry-forward and context-expansion rows. No full check, schema regeneration, external call, network access or retired JVD tier was run. This follows decision `2026-10-11-retire-jvd-from-per-change-verification` and the explicit role boundaries. The graph was queried from main because this worktree has no graph checkout.

This verdict applies to the named immutable HEAD. The planned rebase onto newer `master` needs fresh required verification. Return runtime/test/generated-artifact corrections or any changed semantic review diff to this same isolated Reviewer; record-only copying needs no confirmation round. Repeat no declared expensive schema tier for a review-fix round.

## Builder repair of F1 on integration baseline

The original verdict and SC4 above remain unchanged. The F1 repair enforces the already-approved one-device-token and preservation boundary using `display.set_converter.reads_as_one_statement`, then checks one complete outer parenthesized run while skipping the existing quoted-token helper. Quoted-name delimiters remain data. An expression-shaped value that fails this boundary raises `ValueError` before output: quoting it would introduce a quoted-name IR under the frozen reader rule. No spec edit, new device-validity assertion or agent-approved requirement is made. Reconfirmation by the same independent Reviewer is required on the final candidate.

The omitted negative coverage is now present through JSON/YAML/XML and both command writers; JSON/YAML values are validated first. Schema-valid input is not sufficient permission to emit new statements. XML conversion and strict field validation are exercised; the independent review's missing-cleaned-XSD limitation remains, and no XML XSD validation claim is added. The separate escaped-policy-name audit tokenizer defect remains a carry-forward follow-up, outside this formatter repair. SC1–SC3 retain their original owner-authorized scope.

## Same independent Reviewer: first repair reconfirmation

The following immutable report applies to semantic head `cf6aa270b506c90ce527c3cfa45dca1d91c07a77` and the evidence-only head `f135310d0031a666b220607a0a4a0ad668ca218b`. It remains historical for the next correction.

# Done

**CHANGES REQUIRED** on semantic code HEAD `cf6aa270b506c90ce527c3cfa45dca1d91c07a77`, base/master `40173ba8ec6c0664ea3590b5a3b14786fcf22629`. This is the same independent Reviewer reconfirming the accepted correction and integration rebase. Original `roles/codex-review.md` is preserved.

During review the checkout advanced to `f135310d0031a666b220607a0a4a0ad668ca218b`; `git diff cf6aa270..f135310d --name-only` contains only the freeze, metrics and tasks. Runtime, tests, generated artifacts and executable configuration are identical to the requested semantic HEAD. Both observations below apply to that exact candidate.

Original high F1 is technically repaired: its malformed expression-shaped values now fail before output. New medium F2 blocks approval because the chosen helper rejects complete supported expressions that contain a quoted name touching an opening parenthesis. Owner disposition of F1 remains pending independently of this technical conclusion.

# Evidence

## Ranked findings

### F2 — Medium: the boundary guard rejects complete quoted-name expressions

**Requirement:** `specs/conversion/value-quoting/spec.md`, “A policy-algebra value is written as the device's token,” promises to write an expression starting with `(` as the same token when it occupies one token; its examples explicitly include quoted names inside expressions. `display/CONTRACT.md` and `convert/CONTRACT.md` require typed expression writing and preservation. No requirement limits these expressions to a space between every quoted span and each parenthesis. `ARCHITECTURE.md` §1 requires equivalent configuration, not a particular device layout.

**Diff:** `src/junoscfg/display/value_format.py:48–49` uses `reads_as_one_statement(text)` as a necessary precondition. This existing helper belongs to canonical kept-statement spelling: `display/set_converter.py:47–50` documents single-space words and no quote inside a word, and `:65–73` enforces those restrictions. It is stronger than the formatter's one-complete-expression boundary. The new call makes `is_algebra_token()` false for complete expressions such as `("P 1" && P-B)` and `(("P 1") && P-B)`, so `value_format.py:81–84` raises `ValueError` from both writers.

**Executed counterexamples:** both exact expressions pass the shipped set grammar on the integration candidate. Every input reader—set, structured, JSON, YAML and XML—reads them to the exact same expected IR with strict conversion. Candidate set and structured writers reject both from **all five input doors**. On original base `50b0a104`, both writers read back to the **exact original IR**, without a whitespace-normalization mismatch. A direct `git diff 50b0a104..40173ba8` over `value_format.py`, `set_converter.py` and `convert/input/set_input.py` is empty, so this established baseline behavior also applies to the new integration base. This is an actual newly introduced refusal, not an inference that a formerly lossy spelling deserves new compatibility.

This finding makes no new exact-device-format claim. The complete expressions are already inside the declared product promise; current reader and shipped-grammar execution and baseline round trips independently establish the counterexample.

Minimal reproduction on candidate:

```python
import json
from junoscfg import Format, convert_config, validate_set
value = '("P 1" && P-B)'
assert validate_set('set protocols bgp group G import ' + value).valid
ir = {"configuration": {"protocols": {"bgp": {"group": [
    {"name": "G", "import": [value]}
]}}}}
written = convert_config(json.dumps(ir), from_format=Format.JSON,
                         to_format=Format.STRUCTURED, strict=True)
back = json.loads(convert_config(written, from_format=Format.STRUCTURED,
                                 to_format=Format.JSON, strict=True))
assert back == ir
```

Candidate raises `ValueError: value is not one complete policy-algebra expression`; baseline succeeds and preserves the value. The nested counterexample substitutes `(("P 1") && P-B)`.

**Recommendation:** retain the complete-parenthesis and statement-delimiter checks, but use a boundary check whose requirements match expression tokenization rather than canonical kept-statement spelling. Do not loosen `reads_as_one_statement` globally, because its stronger invariants serve unplaced-record preservation. Add both compact quoted-name positives across the five readers and both writers; retain all F1 rejection cases and quoted-delimiter positives. This is an implementation/test correction under the existing requirement, not a new requirement decision.

Other probes showed refusal of double-spaced `( P-A  && P-B )` and `( P-A && "P 1")`. Their baseline round trips normalize whitespace, so they are **not** needed to establish F2 and are not treated as exact-IR preservation evidence. The two counterexamples above avoid that limitation.

## Original F1 and SC4 assessment

The original `( A ) ; export P-B` now raises the static structural `ValueError` before either command writer returns output. All 66 committed negatives across JSON/YAML/XML and set/structured writers pass, including delimiters inside the run, trailing statements, comment boundaries, bracket runs, unbalanced parentheses and open quotes. The 24 quoted-name delimiter positives pass. Independent controls `( "P;1" && P-B )` and the whole quoted name `"( A ) ; export P-B"` both round-trip unchanged in set and structured output.

For **malformed expression-shaped values that cannot satisfy the one-token criterion**, rejecting before output satisfies the existing lexical boundary and structural-error contract. The error contains no configuration value. `ARCHITECTURE.md` §8 already supplies the structural-error door; the public pipeline returns no result when this error propagates, and CLI conversion prints output only after the pipeline succeeds. The anonymized error wrapper remains covered by the message-contract tests.

Therefore original SC4's conditional wording does not require a specification change to correct F1: it can be classified as an omitted-negative-test implementation finding now fixed. This assessment does not accept or reject any owner-authored requirement decision and does not infer an answer to the pending **reject-before-output versus park #8** picker. F2 shows that the actual rejection must remain confined to values failing the lexical promise; rejecting a valid complete expression is a separate defect.

SC1–SC3 remain pending only within their existing owner-authorized scoped interim actions. Their source entries are preserved; no general merge permission is extended to F2. There is no additional specification challenge required for F2 because its required complete-expression behavior is already established.

## Verification and rebase impact

- Independent targeted run: **5,212 passed, 7 strict xfailed**, including `test_value_format.py`, `test_set_converter.py`, `test_convert_roundtrip.py`, the rebased audit walker and field validator tests, the full format matrix, message contracts, device rendering law and shipped-artifact tests. It includes all repair negatives and their added positive cases; none covers F2's compact quoted-name expressions.
- Rebase comparison `586841fe..f04ec2f` adds the reviewed integration changes to audit key-token writing, POSIX bracket escaping in field validation, documents, version/dependency records and archives. None changes the original #8 reader/formatter/lexer implementation. The relevant rebased runtime tests were included in the independent targeted run; no interaction failure was observed.
- Independently compared the Builder's new-base result records: **36 of 96 plain conversions** and **432 of 1,152 rule runs** differ, exclusively in output. Every field in repaired-head records equals the original independently recorded `roles/review-head.json`. This is verification of the stored refreshed comparison, not a claim to have rerun the whole comparison again.
- Saved fast/full checks on the committed candidate both end with `every check passed`; full application result is **8,443 passed, 37 skipped, 20 xfailed**. No full or expensive schema tier was repeated by this Reviewer. Their passing status does not cover F2.
- Checkout stayed clean. The original escaped-policy-name audit carry-forward remains separate; no unrelated #7 policy was evaluated or approved.

## Five review prompts, reconfirmed

1. **Trust-boundary input:** F1 caller values no longer become extra statements; refusal precedes returned output. F2 requires removing only the guard's unrelated canonical-text restriction while retaining that safety check.
2. **Incompatible-but-valid input:** the two compact quoted-name expressions above pass grammar/readers and baseline exact round trips yet are rejected by the correction. They are the new blocking counterexamples.
3. **Shared blind spot:** all correction positives place spaces around quoted names. Both implementation and tests consequently miss expressions whose quoted name touches a parenthesis. Add the exact positives; no oracle relaxation is needed.
4. **Second answer:** existing `reads_as_one_statement` provides safe canonical kept-record spelling, while `is_algebra_token` needs safe expression boundaries. Reusing the former imposes a capability restriction inappropriate to the latter. Preserve the helper's owning invariant and repair the expression boundary at its own scope.
5. **Figures and non-goals:** independent targeted counts and refreshed stored-comparison counts are stated above. Original device counts and expensive-tier evidence retain their original identities. P11/P12/P13 scoped interims, XML whitespace, meta verbs and the unrelated audit carry-forward are unchanged.

# Changed paths

Only this scratch report `roles/codex-rereview.md` and the review-only `roles/rereview-pytest-tmp` directory. Original report preserved. No tracked file, Git state, product implementation, acceptance test or specification was mutated by this Reviewer.

# Commands and exit status

- Git status/identity, semantic and rebase diffs, source/record reads and `git diff --check 40173ba8..cf6aa270`: **0**. Candidate changed only by the permitted evidence-only checkpoint during review.
- Offline `uv run --locked --no-sync --group dev pytest -q -p no:cacheprovider`, with scratch `UV_CACHE_DIR`, `--basetemp` and `PYTHONDONTWRITEBYTECODE=1`, on the nine targeted files listed above: **0**, 5,212 passed, 7 xfailed.
- Candidate F1 refusal/quoted-name controls: **0**; expected `ValueError` caught for original injection, both positives preserved IR.
- Independent candidate compact-expression probes: **0**, explicitly reporting all five readers preserve IR and all ten command conversions refuse it. Baseline probes: **0**, exact round trips and shipped grammar acceptance for both F2 cases. Additional whitespace cases were reported with their baseline normalization limitations.
- Independent comparison of `repair-base-40173ba.json`, `repair-head.json` and original `review-head.json`: **0**, asserted output-only changes and exact repaired-head equality.

# Open questions for the owner

The explicit owner disposition of reject-before-output versus parking #8 remains pending; no response or approval is inferred. Technical recommendation is to retain the structural refusal for malformed values and correct F2 before returning for review. No owner question was sent. Existing SC1–SC3 permissions remain as previously recorded, and unrelated #7 choices remain outside this review.

# Deviations

Scratch report only, as required; the Builder copies/preserves ranked evidence in tracked review records. No network, push, merge, full check, expensive schema rerun or other-session control. This re-review is complete for the exact named semantic candidate; F2 must return to the same isolated Reviewer after its focused/required verification.

## Builder correction of F2

`reads_as_one_statement` remains unchanged. Its canonical single-space/no-embedded-quote invariant belongs to kept raw/unplaced records, not policy-expression layout. The formatter instead reuses the same owning lexer's `_TOKEN` primitive, permitting its word/quoted/space tokens while refusing actual structural/comment boundaries and line breaks, then retains complete outer-parenthesis and quoted-span checking. This is intra-package `display` reuse: `tach.toml` declares `junoscfg.display` as one module, existing display files use sibling imports, and `agent-ready interfaces` passes. No private name or submodule is imported across a package door, and no interface is widened.

New catalogue rows cover both exact F2 compact/nested expressions through all five readers and every writer/second hop; another row preserves doubled spaces inside a quoted name. Formatter-only outer-whitespace pins require unchanged spelling without claiming an exact IR round trip the baseline never supplied. All F1 negatives remain, plus a compact open quote negative; spaced quoted-delimiter positives remain. Focused settled run: 332 passed, 2 strict P11 xfailed.

Carry-forward lexical limitation (synthetic, no device-invalidity claim): compact `("P;1" && P-B)` passes the shipped grammar, but the current structured lexer treats the semicolon inside a word-attached quote as structure. Public strict conversion on integration base `40173ba` emits structured text whose strict read-back raises `ValueError`; the corrected boundary refuses this unrepresentable spelling before output. The spaced `( "P;1" && P-B )` stays supported and preserves exact IR. Repairing the reader's embedded-quote delimiter handling is outside this scoped formatter correction; no generic requirement change or merge permission is manufactured.

## Owner disposition after F2 correction

2026-10-11, owner interview relayed by the orchestrator: explicitly approve F1 reject-before-output for unrepresentable values while preserving complete expressions and quoted names. This authorizes the concrete structural-error correction under the existing invariant; it does not approve a rewritten requirement or extend generic merge permission. Original SC4 conditional wording and the original immutable review reports remain historical. Same-Reviewer reconfirmation of the final F2 candidate remains required.
