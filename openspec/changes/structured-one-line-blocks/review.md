## Findings

### Independent Test/Challenge (phase 4, STOP-T)

Fresh context-isolated agent run by the orchestrator on `c9f760f` (merge base
`a19e978`); report copied to `test-challenge.md`. The orchestrator relayed the
rulings of 2026-10-11: accept F1 and F3–F11 with the proposed tests, F1 fixed in
the implementation; F2 recorded as evidence-blocked with probe P6; F6 reworded
and one changed verdict pinned. Disposition, all in the phase-5 commit:

1. F1 (high), sibling split accepted `hold-time up 2000 down;`: fixed. The walk
   records a leaf read without its value (`_Reading.incomplete`);
   `structured_set_lines()` returns those lines as `incomplete` and
   `validate_structured()` reports each as an error. Contract row
   `a-sibling-without-its-value` (invalid on every door, the deprecated one
   included) and the `structured_set_lines` case. The set grammar's own
   acceptance of `set … hold-time down` (merged rule: `hold-time` takes a value)
   is a set-validation defect, recorded in `ledger.md` for change 17.
2. F2 (high), empty block: see the challenge below; spec and tests now say
   "reported, not silently dropped" and assert only the warning.
3. F3 (medium-high), a tagged one-liner detected as YAML: fixed at the owning
   layer, `display/format_detection.py` (`_opens_a_block`). Detection cases and
   a CLI case without `-i` for convert and audit.
4. F4 (medium), audit door: `audit unused` added to `TestABlockOnOneLine` with a
   one-line prefix-list.
5. F5 (medium): `xfail_on` rows use `raises=AssertionError`, and `cases()`
   asserts every name in `xfail_on` is a door.
6. F6 (medium): see the challenge below; `test_the_new_lexer_changes_a_verdict`
   pins `system { bogus-statement 1; }` invalid on the deprecated door.
7. F7 (medium): absolute `statements()` for a tagged entry, a protected block
   holding a quoted value with `;`, `{`, `#` and `/* */`, and a tagged bracket
   list; comment cases with an open quote, the device's `## Warning: …` line,
   and a quote inside a block comment.
8. F8 (medium-low): `Row.warnings`, checked on every door that takes the row
   (the CLI's `-v` now prints `Warning:` lines, and the deprecated validator
   reports the lexer's notes too); `test_no_deprecation_reaches_their_caller`
   runs the recommended doors with `DeprecationWarning` as an error.
9. F9 (low): `test_every_defined_class_has_a_recorded_line`.
10. F10 (low): a `;` with no statement (`;;`, `};`, a lone `;`) reads as
    nothing (`TestAnEmptyStatementReadsAsNothing`); `audit unused` added to the
    refusal test (exit 2).
11. F11 (low): the freeze's list of base passes corrected;
    `test_the_walk_and_the_grammar_come_from_it` shows both the walk and the
    grammar come from the `artifacts_dir` given. `tests/support/artifacts.py`
    gains `write_minimal_tree` because curly validation now reads the structure
    tree; `test_validate_auto_detect_structured` writes it, its assertion
    unchanged. The minimal set itself stays tree-less, which
    `TestArtifactsOption` relies on.

### Builder measurement after Test/Challenge (JVD tier)

The `--jvd` tier failed on the first phase-5 head. Measured per file against
the merge base (evidence freeze, delta log), it led to two lexer rules and one
test-support change the Reviewer should check:

- A statement may not run onto a later line. Without it, 23 documentation
  files that the line reader refused (CLI prompt, `AN3:` labels, prose)
  converted silently, the prose read into the next path.
- A template's `${NAME}` is one word: 22 published template snippets converted
  before and still do.
- `tests/support/jvd_data.py` `NOT_CONFIGURATION`: the `Unknown statement: AN…`
  markers become `statement 'AN…` (the same 35 files fail on both sides), and
  `'}' closes no block` is added for the one corpus file with an extra `}`,
  which a device refuses and the line reader passed silently.

## Already provided

`display.artifacts_dir()` scopes the walk to the caller's artifacts; the
existing `diagnostic_sink` shape of `from_dict()` and `anonymize()` carries the
reader's warnings; `tools/device_differences.py` regenerates the device record.

## Phase-6 review (fresh Reviewer, 2026-10-11)


Fresh, isolated Reviewer (phase 6). Read in order: `evidence-freeze.md`, the two
deltas, `display/`, `convert/`, `validate/`, root and `input` contracts,
`test-challenge.md` with the dispositions in `review.md`, the new tests, then
`git diff a19e978..87d4d7d` (branch head 5ca644f adds only `tasks.md` and the freeze).
Nothing tracked was edited. Probes are in this folder (`rv_probe1.py` to
`rv_probe5.py`, `rv_jvd.py`) and use synthetic values only. Base and head ran
side by side from `git archive` trees in the session scratchpad, through `PYTHONPATH`.

#### Verdict

**CHANGES REQUIRED.** One trust-boundary defect (F1) and one break of the
§8 error door (F2) block approval. Everything else is low and can be fixed in
the same pass or carried forward. The lexer is sound. The JVD figures
reproduce exactly. The claimed IDs meet the Definition of done, apart from F1 and F2.

### Findings, ranked

#### F1 (high): an anonymized conversion prints original identifiers in the new reader warnings

- Violates the anonymization promise (mission Definition of done: "no eligible original value survives").
  It also violates the anonymize precedent (`anonymize/CONTRACT.md`): events that carry values
  leave only under `log_debug` (`anonymize/walker.py:203`).
- Diff: `src/junoscfg/convert/__init__.py:118-124` sends the lexer's notes to `diagnostics` *before*
  anonymization. `display/set_converter.py:320-327` puts the block's path, keys included, in each note.
- Counterexample (executed): run `junoscfg convert -i structured -e set --anonymize-ips --anonymize-groups --anonymize-salt s1` on
  `protocols { bgp { group G1 { neighbor 203.0.114.5 { } neighbor 203.0.114.6 { peer-as 64497; } } } } groups { GR-SECRET { system { /* OMITTED */ }; } }`.
  Stdout is anonymized (`group group_…`, `neighbor 203.23.95.177`). Stderr and
  `ConversionResult.diagnostics` carry `protocols bgp group G1 neighbor 203.0.114.5: an empty block…` and
  `groups GR-SECRET system: …`. On the base, an anonymized run emits no original value by default.
- Fix: collect the structured-input notes in a local list. When `anon_config.any_enabled`, rewrite each
  path through the anonymize mapping (`anon_result.mapping`) before appending, or drop the path and keep
  the count. Add a test: an anonymized `convert_config_result` of the input above has no diagnostic that
  contains `203.0.114.5`, `G1` or `GR-SECRET`.

#### F2 (medium): a missing structure tree is reported as an invalid configuration, not an artifact failure

- Violates `ARCHITECTURE.md` §8 ("a structural failure raises (`SchemaLoadError` …)"). The CLI keeps exit 3
  for "artifacts did not load" (`cli.py` `_run_validation`; `tests/contract/test_every_door.py` `_cli`).
- Diff: `src/junoscfg/__init__.py:289` `except ValueError` catches `load_schema_tree()`'s
  `ValueError("No junos-structure-tree.json in artifacts directory")` (`display/constants.py:410`) along with
  the lexer's. `tests/unit/convert/test_structured_input.py:313-320` pins that conflation.
- Counterexample (executed, `rv_probe2.py`): with a grammar-only `--artifacts` directory, `junoscfg -v -i structured`
  prints `Validation: FAILED (1 error(s))` and exits 1. A missing grammar on the same door exits 3.
- Fix: resolve the tree inside the scope before the `try` and raise `SchemaLoadError` when it is missing, or
  catch only the lexer's own error type. Change the test to expect `SchemaLoadError` (CLI exit 3). Add to
  the `consumer` `declared-break` that `validate_structured(..., artifacts_dir=X)` now needs X's structure tree.

#### F3 (medium-low): the new JVD marker hides every future brace-balance regression

- `tests/support/jvd_data.py:43` adds `"'}' closes no block"` as a global substring, and `is_configuration`
  (`:82-84`) matches it for all 1,535 files. The marker is meant for one file,
  `enterprise_wan/ewan_finance/configuration/conf/p2_ptx10001-36mr.conf`. I confirmed that file has an extra `}`
  on line 237, after `routing-options` closes on line 236. A lexer that loses a `{` (for example through the
  `${NAME}` word rule) would now be classed as "not configuration" anywhere in the corpus.
- Fix: key this exception by the relative path, for example `BROKEN_FILES = {path: "'}' closes no block"}`.

#### F4 (low): `#` inside a word is now a comment; the base kept it, and no device evidence decides

- `display/set_converter.py:33`: the continuation class of a word excludes `#`. On the base,
  `system { host-name router#1; }` converts to `set system host-name "router#1"`. On the head it raises
  `statement 'host-name router' has no ';'` (`rv_probe3.py`). The JVD corpus and the device captures hold no
  unquoted mid-word `#`.
- Fix: either let `#` start a comment only where a token starts (allow it in the continuation class), or
  record the refusal with a device probe (P7: `set snmp community abc#1`, then `show configuration snmp`).
  The owner decides.

#### F5 (low): auto-detection takes a YAML document with an explicit start as structured

- `display/format_detection.py:101` `_OPENER` matches `--- {configuration: {system: {host-name: router1}}}`,
  which is what `yaml.safe_dump(..., default_flow_style=True, explicit_start=True)` writes. Base: `yaml`.
  Head: `structured`, and it then fails.
- Fix: exclude the document markers, for example `(?!(?:-\s|---(?:\s|$)|\.\.\.(?:\s|$)))`, and add a
  `test_format_detection` case.

#### F6 (low): two contracts now say something false

- `src/junoscfg/CONTRACT.md:7` says the root is "not an implementation module". `validate_structured`
  (`__init__.py:259-307`) now composes the walk and set validation there, under ruling C4.
- `src/junoscfg/input.CONTRACT.md:18` says `normalize` is "the single entry point every input path calls".
  The curly lexer no longer calls it.
- Fix: record the C4 exception in the root contract. That, or move the composition into `convert` with a
  `convert -> validate` edge, which runs the same way as `ARCHITECTURE.md` §8's DAG. Narrow the `input`
  precedent to set input.

#### F7 (low): the record of the JVD measurement

- The figures reproduce exactly (`rv_jvd.py`, sha256 of the full output on both sides):
  1,535 files. 1,477 are identical, 22 changed, 35 fail on both sides, and 1 fails only on the head, the
  ewan_finance file above. Every head failure matches a marker.
- All 22 are lexer fixes: lost parents restored, `"$VAR"` and `${VAR}` paths kept, and the `OMITTED` line
  gone from `an3_acx7100-48l.conf`.
- Both `bgp-transport-class.conf` files (junos and evo) now show DEV-1 instead of hiding it:
  `set routing-options transport-class name "{'name': 'TC-128', 'color': '128'}" auto-create`, with four of
  the five classes lost and no diagnostic. DEV-1 belongs to change 11 and is already in the ledger. Say so
  in the delta log, so that "all fixes" is not read as "now correct".

#### F8 (low): `xfail_on` without `xfail` does nothing

- `tests/contract/test_every_door.py:168`: a row with `xfail_on` set and no `xfail` gets no mark.
- Fix: in `cases()`, add `assert row.xfail or not row.xfail_on`. Otherwise the mechanism is sound:
  `raises=AssertionError` holds, rows that already existed are unchanged, and `Row.warnings` is checked on
  every door that takes the row.

### The Builder's six questions

1. **JVD markers.** The `statement 'AN|MA|MSE|MEG` markers match the same 35 files the old
   `Unknown statement:` markers matched. The new marker is right for its file and too broad otherwise (F3).
2. **Lexer rules.** `${NAME}` as one word cannot swallow a real block: the inner class excludes whitespace,
   `{`, `;` and `"`. "A statement may not run onto a later line" refuses `host-name\n router1;`. The base
   refused that too, so nothing regressed. It does contradict the delta's Purpose ("the same whatever its
   layout"), and nothing shows a device's `load` refuses it (specification challenge below). Neither rule
   changes a device capture: on the vMX oracle, the head's curly errors are a strict subset of the base's (`rv_probe5.py`).
3. **JVD claim.** Rerun in full; see F7.
4. **`write_minimal_tree`.** It is harmless: `artifacts_dir` is a function-scoped `tmp_path`, so it cannot
   leak into `TestArtifactsOption`. Its `ssh: {"p": True}` differs from the shipped tree (a container) but
   matches the minimal grammar. It is evidence for the change in behaviour behind F2.
5. **`xfail_on` / `Row.warnings`.** Sound; see F8.
6. **Second answer?** No. `to_dict(..., diagnostic_sink=)` is the third reader of the `from_dict` and
   `anonymize` shape, and it reaches `ConversionResult` through `pipeline_result`, so §8 holds. The library
   never writes to a terminal. `structured_set_lines` is the input's tokens split by the conversion walk.
   The other route, `SetConverter.to_set()`, is the deprecated one, and C5 rejected the writer route on
   executed evidence. The only gap is that the diagnostic is emitted before anonymization (F1).

### The five prompts

1. **Trust boundary.** F1. The lexer is linear on hostile input: one `finditer` pass; an unclosed quote or
   comment fails once. `_OPENER` is linear up to a 64k-word line (timed).
2. **Valid input the implementation rejects.** A mid-word `#` (F4), a YAML document with an explicit start (F5),
   and a statement written across lines (the challenge below). On the base, `<ge-0/0/*>` was refused as
   `Unknown statement`. On the head it is refused as an unclosed comment. The device prints `<xe-0/0/1*>`
   unquoted, so `<ge-0/0/*>` is a probe candidate for the carry-forward list.
3. **Shared blind spot.** Every structured-input test runs without anonymization, so both sides pass while
   F1 holds. Independent evidence on validation: the vMX curly oracle accepts
   `port-mirroring … routing-instance { inactive: VRF-A { ip-address …; } }` through the walk split. The set
   door rejects the device's own line for it (grammar defect, change 12), so the curly verdict matches the device.
4. **Second answer.** See question 6.
5. **Figures.** Rerun and they hold: JVD 1,477/22/35/1; the device-law record loses exactly two lines and
   one class (the focused corpus test passes); 10 strict xfails in the focused set (5 OPEN-13, 2 new,
   3 OPEN-10); 549 focused tests pass. Not rerun: the full check, which the brief forbids, and the
   performance claim. Neither non-goal says "cannot".

### Definition of done, per claimed ID

| ID | Reproduction | Doors and formats | Negative cases | Device citation | Docs, changelog, version | Open |
|---|---|---|---|---|---|---|
| OPEN-1 | p1.py, and T/C confirms the tests fail on the base | convert, validate, CLI, audit, auto-detect | malformed, `;;` | not needed (lexical) | yes, 0.16.0 | F1, F2 |
| NEW-B6 | yes | lexer, every door | 8 comment cases | — | yes | — |
| DEV-18 | yes | warning on every door; class removed by the tool | — | vmx/qfx `junoscfg-oracle.conf.gz` | yes | F1 (note carries the path) |
| OPEN-10 | 3 strict xfails stay; deprecated | `to_set()`, deprecated doors | — | vmx `.set` | removal fragment | — |
| NEW-B5 | contract row | 5 structured doors | `a-sibling-without-its-value` | vmx/qfx curly and set | yes | F2 |
| EMPTY-BLOCK | EVIDENCE_BLOCKED on P6 (`private_test_data/makeover-probes.md`) | warning only | — | missing: P6 | — | owner |

#### Carry-forward (not checked by the Reviewer)

- The full check and the performance figure (forbidden by the brief).
- Validation over the JVD corpus at base and head. It started and was still running at the time of writing; it is not a claim of the change.
- Device probes: P6 (empty block), P7 (statement across lines), mid-word `#` (F4), `<ge-0/0/*>` unquoted in curly.

### Corrections after the fresh review

The orchestrator accepted F1–F8 on 2026-10-11:

- F1: the reader's notes are `Note(path, message)`; `to_dict`'s sink takes both; `pipeline_result` collects them and, when the conversion anonymizes, emits the message without the path (challenge R1). Test `TestAnAnonymizedConversionShowsNoInputPath`.
- F2: `validate_structured` loads the structure tree inside the artifacts scope first and raises `SchemaLoadError` without it (CLI exit 3); the test expects that; the `consumer` declared break names the new requirement.
- F3: `tests/support/jvd_data.py` `BROKEN_FILES` keys the unmatched-brace failure to its one file; the global marker is gone.
- F4: `#` starts a comment only where a token starts (`TestAHashInsideAWordIsPartOfIt`).
- F5: `_OPENER` excludes the YAML document markers; two detection cases.
- F6: `src/junoscfg/CONTRACT.md` records the `validate_structured` composition (C4); `input.CONTRACT.md` narrows `normalize` to raw set input.
- F7: the freeze's delta log names DEV-1 in both `bgp-transport-class.conf` files.
- F8: `cases()` asserts `row.xfail or not row.xfail_on`.

### Re-review (same Reviewer, 2026-10-11)

F2–F8 confirmed resolved. One item remained, F1b (medium): `junoscfg convert -v -i structured -e set
--anonymize-all --anonymize-salt s1` printed the reader's warnings with their original paths, because
`-v` validates the source before anonymization and the new `Warning:` loop printed `validate_structured`'s
notes whole. Corrected: the CLI builds the anonymization config first and passes whether the run
anonymizes to `_run_validation`, which then prints a warning without its path (validation warnings now
carry the path in `ValidationError.path`). `test_no_original_value_reaches_a_diagnostic` gains the `-v`
case.

Carry-forward, not this change's: under `-v` with anonymization a validation *error* prints original
values (`Invalid syntax: set system bogus-statement 203.0.114.9`), as on the merge base; ledgered as
NEW-R1 under change 5.

## Specification challenges

### F1: a sibling split must not create an acceptance

- Artifact: `specs/validation/structured-validation/spec.md`, "Curly text is validated as the conversion walk reads it" (as committed at `c9f760f`).
- Counterexample: executed (Test/Challenge `tc_probe3.py`, `tc_counter_c5.py`): curly `hold-time up 2000 down;` splits into `set … hold-time up 2000` and `set … hold-time down`, both accepted by the set grammar; on the merge base `validate_structured` rejected it. `down` takes an unsignedInt (schema); no capture holds a value-less `down`.
- User impact: a curly configuration missing a value would validate.
- Proposed correction: a statement the walk cannot complete is invalid in curly validation, whatever the set grammar says.
- Decision: Accepted (orchestrator ruling relayed 2026-10-11 under the owner's unattended-run instruction): fixed in the implementation; requirement text, scenario "A sibling without its value", contract row and `structured_set_lines` case added.

### F2: an empty block's meaning has no device evidence

- Artifact: `specs/conversion/structured-input/spec.md`, "What yields no statement is reported, never written" (as committed at `c9f760f`), and the `an-empty-block` parameters.
- Counterexample: executed on the base (`tc_probe1.py`): `protocols { lldp; }` gives `set protocols lldp`, `protocols { lldp { } }` gives nothing; if the device loads `lldp { }` as `lldp;`, "never written" pins a wrong configuration.
- User impact: possibly a presence statement lost, now with a warning instead of silently.
- Proposed correction: device probe; until then assert only the report.
- Decision: Pending owner decision. Interim action: the requirement is reworded "reported, not silently dropped" and the warning claims nothing about the device; tests assert the warning only; EVIDENCE_BLOCKED on probe P6 in `private_test_data/makeover-probes.md` (`protocols { lldp { } }`, `system { services { ssh { } } }`, then `display set`). `makeover-probes.out` does not exist at phase 5. (owner intake 2026-10-11: merge with recorded interim action)

### F6: the deprecated doors do not keep every verdict

- Artifact: `specs/validation/structured-validation/spec.md`, "The validate package's structured doors are deprecated", and `specs/conversion/structured-input/spec.md` on `to_set()` ("give the output it gave before").
- Counterexample: executed (contract rows): `JunosValidator.validate_structured` changes its verdict on `a-block-on-one-line`, `a-brace-too-many` and `the-omitted-placeholder`, because it reads with the new lexer.
- User impact: none harmful; the spec misstated what changes.
- Proposed correction: state which verdicts change and pin one.
- Decision: Accepted (orchestrator ruling relayed 2026-10-11 under the owner's unattended-run instruction): both requirements now name the schema-free route kept and the verdicts that change; `test_the_new_lexer_changes_a_verdict` pins one.

### R1: reader warnings leave an anonymized conversion unanonymized (fresh Reviewer)

- Artifact: `specs/conversion/structured-input/spec.md`, "What yields no statement is reported, not silently dropped".
- Counterexample: executed (Reviewer F1): `junoscfg convert -i structured -e set --anonymize-ips --anonymize-groups --anonymize-salt s1` on `protocols { bgp { group G1 { neighbor 203.0.114.5 { } neighbor 203.0.114.6 { peer-as 64497; } } } } groups { GR-SECRET { system { /* OMITTED */ }; } }` anonymizes stdout, but stderr and `ConversionResult.diagnostics` name `protocols bgp group G1 neighbor 203.0.114.5` and `groups GR-SECRET system`.
- User impact: an anonymized conversion meant for sharing carries the original addresses and group names in its diagnostics.
- Proposed correction: a warning's path is anonymized as the output is, with a test.
- Decision: Pending owner decision. Interim action: when the conversion anonymizes, a reader warning carries no path ("the block's path is withheld: the conversion anonymizes"); the block never reaches the IR, so no mapping exists to rewrite it with. Requirement text and `TestAnAnonymizedConversionShowsNoInputPath::test_no_original_value_reaches_a_diagnostic` added; without anonymization the path is kept. (owner intake 2026-10-11: merge with recorded interim action)

### R2: refusing a statement written across lines has no device evidence (fresh Reviewer)

- Artifact: `specs/conversion/structured-input/spec.md`, "Malformed structured text is refused" ("lets a statement run onto a later line"), against its Purpose ("means the same whatever its layout").
- Counterexample: `system {\n host-name\n router1;\n}` is refused, as on the merge base; whether a device's `load merge terminal` accepts it is unverified.
- User impact: hand-written curly a device loads may be refused.
- Proposed correction: device probe P7; until it answers, the spec says the rule is a corpus heuristic.
- Decision: Pending owner decision. Interim action: the refusal stays (it is the merge base's behaviour, and without it 23 JVD documentation files convert prose into configuration paths silently); the requirement now names the rule a corpus heuristic pending P7, appended to `private_test_data/makeover-probes.md`. (owner intake 2026-10-11: merge with recorded interim action)

## Verdict

Fresh Reviewer: CHANGES REQUIRED (F1, F2 blocking); re-review: CHANGES REQUIRED on F1b only. F1b corrected; awaiting the Reviewer's confirmation.
