## Findings

A fresh, isolated Reviewer read the freeze, the deltas, the touched contracts, the
Test/Challenge record and its rulings, the tests and the diff `b8e6fc1..8860818`; probes with
synthetic values in `private_test_data/makeover-work/anonymized-run-messages/roles/` (`rv_*.py`,
outputs beside them; full report `roles/review.md`). Verdict at `8860818`: **CHANGES REQUIRED**.
Rulings relayed by the orchestrator on 2026-10-11, all accepted; dispositions:

1. R1, MEDIUM-HIGH (trust boundary): the library still raised a word of the configuration in an
   anonymized run. A YAML date (`x-acme: 2026-10-11`) converted to JSON raised the writer's
   `TypeError` noting "when serializing dict item 'x-acme'"; `from None` keeps notes, and only
   the reader's refusals were withheld (`rv_probe_date.py`). Fixed in the library, the CLI's
   rule: in an anonymized run `pipeline_result` raises any failure but `FieldValidationError`
   and a withheld refusal as `RuntimeError("the conversion failed (<class>); details withheld:
   the run anonymizes")` (wording unified by R7), raised outside the handler so it has no cause, context or
   notes; the CLI prints that message as it stands. Rows `unexpected-failure`,
   `cli-unexpected-failure`; `TestTheLibraryRaisesAFailureByItsClassOnly`. The pass-through
   collision now reaches a library caller as such a `RuntimeError` (declared in the migration).
2. R2, MEDIUM: a withheld refusal lost its line for the set and structured readers. Fixed at
   the readers: `junoscfg.input.InputError(ValueError)` carries `lineno`; the set reader's
   bracket refusal, the structured lexer's refusals, its tag-inside refusal (the lexer now
   records where each statement starts, `SetConverter.statement_lines()`, so that refusal names
   its line in every run) and the XML reader raise it; JSON and YAML give theirs. Every read
   row requires `(line N)`.
3. R3, MEDIUM: the law matched `shown` against the whole chain, whose frame lines say `line 113`
   (counterexample W6, `rv_w4w6.py`). Fixed: `shown` is matched against what the door said
   (`traceback.format_exception_only`, the diagnostics, stderr and warnings); the whole chain
   is still scanned for leaks. W6 now fails 13 read rows.
4. R4, LOW-MEDIUM: migration note and changelog name every lost subclass and attribute
   (`JSONDecodeError`, `MarkedYAMLError`, `__cause__`) and the `RuntimeError`; the `Raises:`
   sections of `convert_config_result`, `convert_config` and `pipeline_result` say so.
5. R5, LOW: the debug level is documented in the `AnonymizeConfig` docstring and in
   `anonymize()`'s `diagnostic_sink` argument, which mkdocstrings renders.
6. R6, NIT: the collision message names `preserve_prefixes` and the flag.

Carried forward to change 13 (pre-existing in plain runs, ledgered by the orchestrator): NEW-R11,
YAML scalars that are no JSON value (a date, `!!binary`) and non-string keys are not refused by
the YAML reader, so JSON output raises and set output drops a statement field validation calls
kept; NEW-R12, `{"configuration": [...]}` converts in a plain run and crashes `anonymize()`.

Independent Test/Challenge (`test-challenge.md`, at `bd17a78`), rulings relayed by the
orchestrator on 2026-10-11, all accepted and applied before implementation closed:

1. F1, HIGH, missing doors (`-v -i xml` with a user XSD, the CLI pass-through collision, the
   structured reader's tag-inside and open-quote refusals, the AS-number warnings on the command
   line): added to `tests/contract/test_every_message.py` and closed.
2. F2, HIGH, the crash exclusion (C12) reversed: in an anonymized run `junoscfg convert`
   (validation and conversion) prints `Error: the conversion failed (<class>); details withheld:
   the run anonymizes` for every exception its handlers leave, exit 1, no traceback
   (`cli.py::_failure_withheld`); a run that does not anonymize keeps its traceback. Library
   refusals are raised afresh `from None` (`convert/__init__.py::_withheld_refusal`,
   `IpRule._anonymize`). `TestAFailureNoHandlerExpectsNamesOnlyItsClass`.
3. F3, HIGH, the law scans the whole formatted chain, stdout of a failed or validate-only run and
   Python warnings, and asserts each door's meaning (`Door.shown`).
4. F4, MEDIUM, every non-schema word of every row carries `acme`; the law refuses it in any case
   and refuses any dotted quad.
5. F5, LOW, settled: messages carry neither originals nor replacements of the run. The AS-number
   warnings name no AS; `test_explicit_map_collision_warns`, which asserted the replacement
   `64497` in the warning, now asserts neither number (the law wins); the unit test
   `test_no_warning_pairs_an_original_with_its_replacement` checks both originals and
   replacements. JSON and YAML refusals are fresh exceptions, so `JSONDecodeError.doc` and the
   YAML mark's buffer are not carried.

Re-review (same Reviewer, at `5b8e22e`): R1–R6 confirmed closed (`rv_recheck_attrs.py`: every
anonymized error a one-element chain, no attribute quoting the configuration; door, reader and fuzz
probes 0 leaks; W6 caught on all 12 line-bearing doors; door law on base product code 38 failed,
46 passed; `tach check` OK; the `InputError` door coherent: `__all__`, tach `expose`,
`input.CONTRACT.md`, a `ValueError` subclass). One new finding, ruled and fixed:

- R7, LOW: two endings for the failure message: the library's `RuntimeError` ended "the
  conversion anonymizes", which the CLI passes through, its own text "the run anonymizes".
  Fixed: one wording, "the conversion failed (<class>); details withheld: the run anonymizes",
  in the library and the CLI; the collision rows, `cli-unexpected-failure`,
  `TestAFailureNoHandlerExpectsNamesOnlyItsClass` and
  `TestTheLibraryRaisesAFailureByItsClassOnly` assert the full string.

Optional, recorded for the owner (not a finding): an anonymized refusal to read could be raised as
`InputError(message, line)` so consumers get the line as data; kept a plain `ValueError` with the
line in its text, as the requirement reads.

## Already provided

- `AnonymizeConfig.any_enabled` decides once per run whether it anonymizes (changes 1 and 5).
- The read notes (change 1), the `anonymize:` warnings and the `UNPLACED` texts (change 5) already
  named no word of the configuration; the field validator now owns the `UNPLACED` withholding.
- `copy.deepcopy` once on entry, as the JSON writer copies (change json-writer-pure).

## Specification challenges

### S1: "raises" covered every failure, the library withheld only its reader's refusals

- Artifact: `specs/anonymization/placed-values/spec.md`, "No message of an anonymized run quotes the configuration": "no message it returns, raises or prints SHALL quote a word of the configuration".
- Counterexample: executed by the Reviewer (`roles/rv_probe_date.py`): `configuration: {system: {x-acme: 2026-10-11}}` as YAML to JSON with `AnonymizeConfig(ips=True)` raised `TypeError` whose `__notes__` read "when serializing dict item 'x-acme'".
- User impact: a library consumer who logs the exception publishes a word the run was to hide.
- Proposed correction: (a) the pipeline raises an unexpected failure of an anonymized run as `RuntimeError("the conversion failed (<class>) ...")` with no cause, context or notes, as the CLI prints it; or (b) narrow the promise to the refusals and named errors.
- Decision: Resolved by correction (a), ruling of 2026-10-11 relayed by the orchestrator (owner intake 2026-10-11); applied in `convert/__init__.py`, rows `unexpected-failure`, `cli-unexpected-failure`, `TestTheLibraryRaisesAFailureByItsClassOnly`.

### S2: "with the line where the parser gives one"

- Artifact: the same requirement, as first frozen.
- Counterexample: executed by the Reviewer: the bracket refusal and the structured `;` refusal lost `line N` in an anonymized run while `-v` printed it.
- User impact: the user cannot find the faulty line without re-running unanonymized.
- Proposed correction: keep the requirement; every reader names the line of its refusal (R2).
- Decision: Resolved by the proposed correction, ruling of 2026-10-11 relayed by the orchestrator; the requirement now reads "naming its line (`(line N)`)".

## Verdict

CHANGES REQUIRED at `8860818` (R1–R6), then **APPROVE at `5b8e22e`** from the same fresh Reviewer
(full text `private_test_data/makeover-work/anonymized-run-messages/roles/review.md`), with R7 (low)
fixed before finalization. No correctness challenge remains open; S1 and S2 are resolved by the
ruled corrections. Carried forward: NEW-R11, NEW-R12 (change 13).
