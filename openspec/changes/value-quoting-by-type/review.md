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
