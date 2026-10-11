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
