| Field | Value |
|---|---|
| tokens per phase, prefix and work | UNMEASURED |
| distinct files read per phase, by artefact type | UNMEASURED |
| agent-review findings by severity, and how many survived human review | UNMEASURED |
| human artefacts read and human minutes per phase | UNMEASURED |
| wall-clock from intent to merge | UNMEASURED |
| lines added and removed | {"added": 2508, "binary_files": 0, "files": 28, "removed": 519} |
| dependency count | UNMEASURED |
| residue-arm firings, and additions a fixer made beyond the proposal | UNMEASURED |
| requirement-to-test reconcile result | UNMEASURED |
| pre-commit wall-clock, total and per hook | UNMEASURED |
| direct declared runtime dependencies | {"base": 6, "delta": 0, "head": 6} |
| total root-lock packages | {"base": 63, "delta": 0, "head": 63} |
| runtime tokens | UNMEASURED |
| runtime files read | UNMEASURED |
| runtime retries | UNMEASURED |
| runtime phase span | UNMEASURED |
| workflow telemetry by phase and model | UNMEASURED |
| Acceptance tests on base product code (phase 4) | 36 failed, 17 passed (named pins), `50b0a10` |
| Acceptance tests on base product code (after Test/Challenge) | the new nodes: 89 failed, 49 passed (named pins), `50b0a10` |
| Before/after comparison (how-to; 12 renderings x 4 outputs x 15 runs: plain, each rule alone, `ips_in_strings`, `as_numbers_in_strings`, all, all with both in-strings options) | 132 of 1,440 conversions differ, all explained: 96 rename the sensitive word `CM-CUSTOMER` (pseudonym per spelling, NEW-R13/S2) in the sensitive-words, all and all+in-strings runs; 64 renumber the sequential AS replacements under `as_numbers_in_strings` (numbers inside text are now met in walk order, so 64500/64501/64502 go to other originals; each original keeps one replacement); 4 `ips` runs and the JSON/YAML outputs of the all runs replace `3ffe:b00::/32` in the device JSON's annotation (S3); no diagnostic, field-validation message or exception differs. Revert exact on every capture under all 14 rule sets, base and head (`revert_check.py`) |
| Historical timing, `anonymize()` with six rules, largest held configuration (296,365 lines); timed source SHA/recipe not retained, not current evidence | base 2.592 s, head 3.076 s (+0.48 s: the chain runs on every placed string value); device example 8.6 ms and 10.3 ms; a record, not a gate |
| Context expansion: `src/junoscfg/anonymize/` (every module, ≈3,000 lines) | Builder, phase 0: the change's owning package, read in source; the rules' shapes, the walker's chain, revert |
| Context expansion: `tests/unit/anonymize/test_integration.py` (wildcard and unplaced catalogues, the mapping pin) | Builder, phase 0: which existing tests the delta changes |
| Context expansion: `src/junoscfg/convert/__init__.py` (`_unplaced_warnings`, `_pattern_warnings`) | Builder, phase 2: whether the warnings name the new shapes |
| Context expansion: `tests/contract/test_every_rule.py` | Builder, phase 2: the mapping law the sensitive-word rule must keep (whole values) |
| Context expansion: `tests/unit/cli/test_cli.py` (the ips-in-strings row of `ANONYMIZE_OPTIONS`) | Builder, phase 5: its source no longer told the option apart |
| Context expansion: `.agent-ready/vulture-whitelist.py` | Builder, phase 5: `Rule.lexical` is public API the walker no longer calls |
| Context expansion: `tests/contract/test_every_message.py` (apply-path shown-message catalogue) | Supplemental S7 warning wording now names selectors; preserve required reason/count/path and every privacy assertion |
| Context expansion: `tests/support/devices.py` and `tests/conftest.py` (example source) | Measure rebased integration mapping and annotation-only additions before re-pinning |
| Context expansion: `tests/support/shapes.py` (format catalogue documentation) | XML is input-only; correct supplemental test construction without adding XML output |
| Current original-candidate full at `2fa6c604` | exit 0; 8,984 passed, 37 skipped, 20 xfailed; 92.90204042162267% coverage; complete private log/coverage/provenance retained |
| Current original-candidate device comparison, base `0438299`, head `2fa6c604` | 132 of 1,440 outputs differ; overlapping 96 S2, 64 NEW-R17, 8 S3; 96 plain unchanged; zero diagnostic/field-validation/exception differences; exact private results/classification hashes retained |
| Current original-candidate timing, base `0438299`, head `2fa6c604` | identical all+in_strings options/inputs/script/lock; warmup+3 median, public parsing excluded: largest 8,192,579 bytes/63,211 entries 3.142488583 to 3.837202583 s; device 25,308 bytes/222 entries 0.010175750 to 0.011876625 s; synthetic 20k list 1,075,635 bytes/20,001 named entries including parent 5.147812500 to 5.570328834 s. Chain scans free text and annotations; no profiling attribution, latency is not a gate. R1/R2 corrections invalidate these as future-head measurements. |
| Historical-for-kept-prefix correction full at `b162444` | Root full exit 0, every gate passed; 9,016 passed/37 skipped/20 strict xfails; 32 additional full-suite tests versus 2fa, distinct from the targeted 31-row result. Read-only coverage export 92.93085157681551%. Application report 120.65 seconds; whole-command lifetime unavailable/null in provenance; not Strategy A reuse. |
| Historical-for-kept-prefix correction device comparison, base `0438299`, head `b162444` | 1,440 conversions/96 plain unchanged; 132 approved output deltas (96 S2, 64 NEW-R17, 8 S3 overlap), zero diagnostics/field-validation/exceptions. New separate raw results/diff/classification/provenance; candidate result byte-identical to retained 2fa result. |
| Historical-for-kept-prefix correction timing, base `0438299`, head `b162444` | Candidate-only run reuses unchanged retained baseline and exact frozen script/options/inputs/IR/lock/platform; warmup+3 median, parsing excluded. Largest 8,192,579 bytes/63,211 entries: 3.1424885829910636 to 4.213402875000611 seconds; example 25,308 bytes/222 entries: 0.010175750008784235 to 0.01281295801163651; synthetic20k 1,075,635 bytes/20,001 named entries: 5.14781250001397 to 5.431824625004083. Private benchmark-correction-b162444/ retains samples/hashes; no baseline rerun, profiling attribution or future-head claim. |
| Final corrected source and independent challenge | Source `48f8a858153696809ff1cd6496a84feed9a4b557`, base `0438299772819f24c871d4cb2b8768f9233f9318`; normal hooks/fast passed; independent APPROVE with 252 focused passes and all kept/generated/URL/alias/ambiguity probes passing. Fresh corrected Reviewer lifecycle remains root-owned pending. |
| Final corrected full | Root run exit 0/every gate passed; 9,064 passed/37 skipped/20 strict xfails; 48 more tests than b162 and 80 more than 2fa. Coverage read-only export 92.92812349252291%. Application report 119.32 seconds, actual whole command 171.53 seconds from /usr/bin/time. Complete full-kept-prefix-48f8a858 log/provenance/input hashes retained, no old-process Strategy A evidence import. |
| Final device comparison | 1,440 conversions, 96 plain unchanged, 132 exact output changes classified by approved IDs (96 S2, 64 NEW-R17, 8 S3 overlap); zero diagnostics/field-validation/exceptions. Final result byte-identical to both prior candidate results; separate raw results/diff/classification/provenance retained, no normalization. |
| Final same-recipe timing, largest private structured input | 8,192,579 bytes/296,365 lines/63,211 named entries; retained base median 3.1424885829910636 seconds, final median 4.179101249988889. Largest chosen by actual bytes; operator paths/contents stay private. |
| Final same-recipe timing, committed device example | 25,308 bytes/1,028 lines/222 named entries; retained base median 0.010175750008784235 seconds, final median 0.012632458005100489. |
| Final same-recipe timing, synthetic20k list | 1,075,635 bytes/20,000 lines/20,001 named entries including parent; retained base median 5.14781250001397 seconds, final median 5.483503625000594. |
| Final timing provenance | Candidate-only on clean 48f8a858 after full/device; unchanged frozen script/options/inputs/IR/lock/python/platform, manifest only updates candidate SHA; public parsing before timer, one warmup plus three public anonymize samples including caller copy. Private benchmark-final-48f8a858/ retains all actual samples/hashes. Baseline not rerun; prior candidate figures remain historical. No profiling attribution or efficiency claim. |

Machine evidence and per-field provenance: [metrics.json](metrics.json).

| Phase-7 metrics capture scope | Supported immutable base `0438299772819f24c871d4cb2b8768f9233f9318` to reviewed source `48f8a858153696809ff1cd6496a84feed9a4b557`: 28 own substantive files, +2,508/-519, zero binary files; excludes later main-spec +99/-27 and lifecycle record edits. Six declared runtime dependencies and 63 root-lock packages unchanged. |
| Final fresh isolated review | APPROVE exact48, private kept-correction/report.md; 372 focused plus 13 extra tests, independent probes and final device/timing/full provenance audit. Historical 2fa/b162 NEEDS CORRECTION retained. |
| Strategy A workflow efficiency | UNMEASURED; recorded core anonymizer latency is a different quantity. |
