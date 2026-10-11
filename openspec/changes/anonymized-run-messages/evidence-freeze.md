<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner brief and intake answers of 2026-10-11 (`instruction-integrity.md`): IDs NEW-R1, NEW-R3, NEW-R4, NEW-R9, the `anonymize:` warning's wording carried from change 5 ("each an address"), and NEW-R10 found here (C10). Assurance `balanced`; fast-forward into local `master`, archive, tag, never push.
- C3 one change. C4 NEW-R9's address half is FIXED_ALREADY by change 5 (pinned), the rest follows one rule. C5 the two raw-set-input requirements gain an anonymized-run clause. C7 `anonymize()` copies on entry; `apply_revert` and `walk` keep their documented in-place contract; the salt write-back stays. C8 withholding is decided once per run by `AnonymizeConfig.any_enabled`. C9 declared break on `consumer` and `cli`, minor 0.20.0. C11 debug prints originals by design, documented. C12 crashes, option echoes, the dump-map file, revert output and audit are outside the outcome.

## Requirements

- `specs/anonymization/placed-values/spec.md`: ADDED "No message of an anonymized run quotes the configuration" and "anonymize() leaves its input alone". The existing "Content the walk cannot place ..." keeps its `UNPLACED` sentence, now one case of the added rule.
- `specs/conversion/raw-set-input/spec.md`: MODIFIED "Raw set conversion rejects unquoted square brackets". Contradicted, quoted: "SHALL report the complete original offending line as `Unsupported bracket syntax in set input on line N:\n<line>`" (C5); the anonymized-run clause and scenario are added, the rest repeated unchanged.
- `specs/validation/raw-set-input/spec.md`: MODIFIED "CLI validation distinguishes invalid input from conversion failure". Contradicted, quoted: "SHALL print the same line-specific diagnostic" (C5).
- Unchanged and binding: `conversion/diagnostics` ("the caller owns diagnostic rendering"; the CLI renders the library's text, now withheld at its source), `conversion/structured-input` (an anonymized run withholds a read note's path), `conversion/writers` (a writer leaves its IR unchanged).

## Evidence

Observed on `b8e6fc1` (v0.19.0), synthetic values, scripts and outputs in
`private_test_data/makeover-work/anonymized-run-messages/` (`*-base.out`):

- Message doors and what each printed in an anonymized run (`repro.py`, `v_doors.py`, `notes.py`, `r9.py`, `as_warn.py`):

| Door | Base output (anonymized run) | Quotes the configuration |
|---|---|---|
| CLI `-v` (with `-e` and validate-only), set: grammar error | `Invalid syntax: set system bogus-statement 203.0.114.9 (line 1)` | yes (NEW-R1) |
| CLI `-v`, set: bracket, `Line does not start with` | the whole line | yes (NEW-R1/R4) |
| CLI `-v`, structured: grammar error, a conversion failure | `Invalid syntax: set system bogus 203.0.114.9`; `Failed to convert structured config: ... statement 'host-name 203.0.114.9' has no ';'` | yes |
| CLI `-v`, JSON/YAML: schema error | `'bogus 203.0.114.9' does not match any of the regexes ... at configuration.system` (an unknown key) | yes |
| CLI `-v`, YAML parse error | PyYAML's snippet of the source line | yes |
| CLI `-v`, JSON parse error | `Expecting ',' delimiter: line 1 column 25` | no |
| CLI `-v`, XML; any `-v` without artifacts | `SchemaLoadError`: names the artifact directory | no |
| CLI `-v` warnings (structured read notes) | path withheld since change 1 | no |
| Library and CLI: set reader's bracket refusal (`ValueError`) | `Unsupported bracket syntax in set input on line 1:\nset system name-server [ 203.0.114.9 ]` | yes (NEW-R4) |
| Library and CLI: structured reader's refusal | `Invalid structured input on line 2: statement 'host-name 203.0.114.9' has no ';'\nhost-name 203.0.114.9` | yes (NEW-R10) |
| Library and CLI: YAML parse error | PyYAML snippet holding `203.0.114.9` | yes (NEW-R10) |
| Library and CLI: XML parse error | `Opening and ending tag mismatch: system line 1 and sys` (element names of the input) | yes, words (NEW-R10) |
| Field validation (diagnostics, `--strict`, `FieldValidationError`) | `Invalid value '203.102.152.234': must be one of [v2]` (the pseudonym; an address on an enum-only leaf has been replaced since change 5); `Invalid value 'bogus'` for a word no rule replaces | pseudonym or word left as written (NEW-R9, C4) |
| Field validation `UNPLACED` | withheld since change 5 | no |
| Structured writer note | `note: 1 tag(s) dropped ... (deactivate protocols bgp group G neighbor 203.211.226.131 family)` | entry names and pseudonym (NEW-R10) |
| `anonymize:` warnings | schema path, count, shapes; "each an address in it is replaced" | no (wording only) |
| AS-number rule (`warnings.warn`, on stderr) | `Sequential AS replacement 65016→64512 exceeds RFC 5398 ...` | pairs an original with its replacement (NEW-R10) |
| `ipanon` pass-through collision (`PassThroughCollisionError`) | `Anonymized IP <x> (from <original>) collides with --pass-through prefix` | yes, not reached in 15,000 probes (`ptc.py`) (NEW-R10) |
| Walker debug diagnostics, `ipanon` warnings | only at `log_level="debug"` | yes, by design (C11) |
| `junoscfg audit` | no `--anonymize-*` option | no anonymized run |

- NEW-R3 (`repro.py`): after `anonymize({"configuration": ir}, cfg)` the caller's `ir` holds the pseudonym. Callers: `convert/__init__.py` reads `anon_result.ir`; README and `docs/getting-started.md` read `result.ir`; nothing in `src/` relies on the rewrite.
- Contracts: `apply_revert` "Returns: The same *ir* dict (mutated in place)"; `walk` "ir: The full IR dict (mutated in-place)"; `anonymize/CONTRACT.md` "Not for": the generated salt is written back.

## Non-goals

As `proposal.md`: tracebacks of crashes, echoed options, the dump-map file, revert output, audit (C12); the messages of a run that does not anonymize.

## Acceptance criteria

- Every test id the delta names exists and `agent-ready reconcile` passes. The new tests fail on the merge base `b8e6fc1` and pass after the change, except the named pins: `test_an_address_on_an_enum_only_leaf_is_replaced` (C4, FIXED_ALREADY), the rows of the door law whose base message already quotes nothing (JSON parse error, `SchemaLoadError`, `UNPLACED`, the `anonymize:` warnings), the whole of `TestARunThatDoesNotAnonymizeKeepsItsMessages`, `TestOnlyTheDebugLevelPrintsOriginals`, `TestTheAuditHasNoAnonymizedRun`, `test_revert_still_rewrites_in_place` and `test_the_callers_ir_is_unchanged[no-rule]` (no rule, nothing rewritten). Measured on `b8e6fc1`: the door law fails 25 of 32 anonymized doors (the 7 passing quote nothing on the base: `field-validation-unplaced`, `unplaced-strict`, `read-json`, `read-note`, `cli-validate-only-schema-load`, `cli-validate-warning`, `cli-anonymize-warning`; `read-xml`, `cli-read-xml` fail on element names); the unit tests fail 11 of 16.
- The door law drives each door of the table with a configuration word a reader can find (an address, its pseudonym, an entry name, a word no rule replaces) and asserts none appears in an anonymized run, and that the same run without anonymization prints the word; it asserts per door that it scanned a non-empty message, so an empty scan never passes.
- Existing messages of runs that do not anonymize are unchanged: every existing test of a message text passes unmodified.
- `tests/contract/test_every_rule.py` in full, `tests/unit/anonymize/`, `tests/unit/convert/`, `tests/unit/cli/` green; the corpus anonymization law green in the full check.
- High risk floor: independent Test/Challenge (STOP-T) and a fresh Reviewer (STOP-R).

## Performance expectations

`anonymize()` copies its input once (`copy.deepcopy`). Timed per the developer guide on the largest configuration under `private_test_data/` and a synthetic list of tens of thousands of entries, base and head, recorded in the delta log; a record, never a gate. The pipeline passes its own freshly read IR, so the copy is the only added cost.

## Outstanding decisions

None, because C1–C12 are resolved by precedence, evidence and repository rules.

## Execution and checkpoint

- Assurance preference: balanced
- Risk floor: high (red zone `anonymize`, trust boundary, cross-domain, declared break on `consumer` and `cli`)
- Roles required: Builder; independent Test/Challenge; fresh Reviewer at least as capable as the Builder; Finalizer duties run by the Builder under the owner's brief
- Resume point: phase 4 (acceptance tests). Phase 3 does not apply to type `bug`

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze established after the proposal commit `652a554` and the delta. Approved under the owner's unattended-run instruction of 2026-10-11.
- 2026-10-11, phase 4: acceptance tests committed at `46ebcc1`, failing on `b8e6fc1` as measured above. Checkpoint: STOP-T, independent Test/Challenge next; then phase 5 (implementation). Approved under the owner's unattended-run instruction of 2026-10-11.
