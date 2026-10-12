## Independent Test/Challenge
ADEQUATE accepted by root: original STOP-T historical; renewed current-base report at f530b00/base06c889aa records 84 cases, 77 failures, 7 passes, exit 1 and zero errors/skips. Root bound applicability to admitted38c4930/basebbc125eb by operator-only byte identity. Private reports/rulings preserved unchanged. Whole-input ordering remains a fresh-review inspection obligation.

## Specification challenges

### Existing validation diagnostic assertion correction
- Artifact: tests/unit/validate/test_set_validator.py::TestSetValidator::test_no_set_prefix_error asserted obsolete substring `does not start with`.
- Counterexample: repaired source returns exactly the frozen validation/raw-set-input message `Unsupported command in set input on line 1`; the old wording assertion failed in executed focused evidence while invalid result and line were preserved.
- User impact: conversion and validation now share a value-free lexical diagnostic under the declared public break.
- Proposed correction: retain source and invalid-result assertion; assert the exact approved message and error.line == 1.
- Decision: Accepted by root under explicit owner test-correction authorization; bounded ownership extension for this assertion only. No requirement change or acceptance weakening. Original failing output preserved privately.

## Fresh review
Required after implementation; not started. Reviewer must inspect whole-file preflight before normalization, schema loading or any IR construction and global bracket precedence.

### Existing plain validation message catalogue correction
- Artifact: tests/contract/test_every_message.py DOORS[cli-validate-only-line] expected original `bogus-acme` text in the plain validation message.
- Counterexample: normal NOSKIP commit affected-tests rejected that one row; 9484 other tests passed and20 xfailed. Focused old-row execution also fails because the approved value-free reason replaces input quotation; both original input and invalid result remain unchanged.
- User impact: plain and anonymized validation now share lexical classification while withholding unsupported input values.
- Proposed correction: keep the row, source, non-None kept fragment, privacy scans and paired exit comparison; set only kept to exact approved `Unsupported command in set input on line 1`.
- Decision: Accepted by root under owner test-correction authorization; narrow row ownership granted. No requirement, marker, class or other assertion changed. Fresh Reviewer must inspect both bounded old-test corrections.
