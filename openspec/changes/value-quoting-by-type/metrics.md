
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
| Acceptance tests on base product code (phase 4) | 277 failed, 3,744 passed over the named files and nodes; every new test or row fails except the named pins (`a-quoted-plain-policy-name` 33 nodes, `test_a_backslash_is_written_as_it_is`, `test_a_junos_variable_stays_quoted`, `test_bare_inner_quotes_are_not_one_value`, `bare-inner-quotes-end-the-value`, `a-statement-across-lines-holding-an-escaped-quote`) |
| Context expansion: `src/junoscfg/display/value_format.py` | Builder: below the code-map cut; the one value formatter |
| Context expansion: `src/junoscfg/convert/output/dict_walker.py` | Builder: the writers' call sites of `format_value` |
| Context expansion: `src/junoscfg/validate/grammar_generator.py` | Builder: the `QUOTED` terminal (serialized path) |
| Context expansion: `src/junoscfg/display/set_converter.py`, `src/junoscfg/audit/algebra.py` | Builder: the curly lexer's and the audit's quoting rules |
| Context expansion: `tests/support/shapes.py`, `tests/contract/test_format_matrix.py` | Builder: the owning catalogue for the rows |
| Context expansion: `tools/device_differences.py`, `tools/device_grammar_corpus.py` | Builder: the record and the grammar corpus to rebuild |

Machine evidence and per-field provenance: [metrics.json](metrics.json).
