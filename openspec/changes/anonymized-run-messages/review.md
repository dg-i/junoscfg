## Findings

Pending: a fresh, isolated Reviewer (high risk floor) at STOP-R.

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

## Already provided

- `AnonymizeConfig.any_enabled` decides once per run whether it anonymizes (changes 1 and 5).
- The read notes (change 1), the `anonymize:` warnings and the `UNPLACED` texts (change 5) already
  named no word of the configuration; the field validator now owns the `UNPLACED` withholding.
- `copy.deepcopy` once on entry, as the JSON writer copies (change json-writer-pure).

## Specification challenges

None.

## Verdict

Pending the fresh Reviewer.
