
| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | UNMEASURED |
| dependency count | UNMEASURED |
| direct declared runtime dependencies | UNMEASURED |
| total root-lock packages | UNMEASURED |
| runtime tokens | UNMEASURED |
| runtime files read | UNMEASURED |
| runtime retries | UNMEASURED |
| runtime phase span | UNMEASURED |
| workflow telemetry by phase and model | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | UNMEASURED |
| requirement-to-test reconcile result | UNMEASURED |
| pre-commit wall-clock, total and per hook | UNMEASURED |
| Base SHA | 50b0a10 |
| Acceptance tests on base product code (phase 4, after the Test/Challenge rulings) | 404 failed, 3,852 passed, 3 xfailed (strict: SC1, P11 x2) over the named files and nodes. Every new test or row fails except the pins (base behaviour kept): row `a-quoted-plain-policy-name`, row `a-policy-chain-of-names`, `test_a_backslash_is_written_as_it_is`, `test_bare_inner_quotes_are_not_one_value`, `test_a_quoted_value_ending_in_a_backslash_parses`, `test_an_escaped_backslash_ends_before_the_quote`, shipped-grammar rows `bare-inner-quotes-end-the-value`, `an-escaped-backslash-ends-before-the-quote`, `a-word-ending-in-a-backslash`, `a-quoted-value-ending-in-a-backslash`, `TestJunoscfgsOwnSetOutputValidates` rows other than `an-escaped-quote` and `delimiters`, `a-statement-across-lines-holding-an-escaped-quote`, `test_a_policy_algebra_value_reads_back` for `( P-A )`, `( P-A && P-B )`, `( "P 1" && ! P-B )`, `P-1`, `P 1`. Signature-only base failures (fail on the new `node` argument alone; pins in substance, Test/Challenge F6): `test_a_plain_name_is_quoted_only_where_it_must_be` (3), `test_a_policy_algebra_token_is_written_as_it_is[two-terms, nested]`, `test_a_junos_variable_stays_quoted` (2) |
| Context expansion: `src/junoscfg/display/value_format.py` | Builder: below the code-map cut; the one value formatter |
| Context expansion: `src/junoscfg/convert/output/dict_walker.py` | Builder: the writers' call sites of `format_value` |
| Context expansion: `src/junoscfg/validate/grammar_generator.py` | Builder: the `QUOTED` terminal (serialized path) |
| Context expansion: `src/junoscfg/display/set_converter.py`, `src/junoscfg/audit/algebra.py` | Builder: the curly lexer's and the audit's quoting rules |
| Context expansion: `tests/support/shapes.py`, `tests/contract/test_format_matrix.py` | Builder: the owning catalogue for the rows |
| Context expansion: `tests/unit/audit/test_render.py`, `src/junoscfg/audit/render.py` | Test/Challenge F2, F10: the audit's rendering passes no node |
| Context expansion: `tools/device_differences.py`, `tools/device_grammar_corpus.py` | Builder: the record and the grammar corpus to rebuild |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
