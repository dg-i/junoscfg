## Why

An anonymized run still prints the configuration it was asked to hide. `junoscfg convert -v
--anonymize-ips` prints `Invalid syntax: set system bogus-statement 203.0.114.9` (NEW-R1); the set
reader's bracket refusal, the structured reader's, PyYAML's and the XML reader's quote the source
(NEW-R4, NEW-R10); field-validation messages and the structured writer's tag note quote values and
entry names (NEW-R9, NEW-R10); the AS-number warnings pair an original with its replacement. And
`anonymize()` rewrites the IR its caller passed, which no document says (NEW-R3).

## What Changes

- **BREAKING** (`consumer`, `cli`): in an anonymized run no message quotes a word of the
  configuration, original or replaced. Field validation keeps the path, the reason and what was
  expected, and withholds the value; a refusal to read the input says it could not be read, with
  the line where the parser gives one, and is raised as `ValueError` (YAML: `yaml.YAMLError`); the
  CLI's `-v` prints each error's line, never its text or document path; the structured writer's
  tag note gives its count. A run that does not anonymize, revert included, keeps every message.
- The withholding of `UNPLACED` texts moves from the pipeline into the field validator, which
  owns its messages (`FieldValidator(withhold_values=True)`); `_withhold_unplaced` goes.
- `anonymize()` copies its input once on entry and never changes it; `apply_revert` and `walk`
  keep their documented in-place contract (C7); the generated salt is still written back.
- The AS-number warnings name no original AS; `ipanon`'s pass-through collision error is raised
  without the address. `log_level="debug"` prints originals by design, now documented.
- The `anonymize:` warning reads "each address or password hash ... in it is replaced".
- No override, fallback or environment read is added; `withhold_values` is a keyword the
  pipeline passes, read nowhere else.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `anonymization/placed-values`: no message of an anonymized run quotes the configuration; `anonymize()` leaves its input alone.
- `conversion/raw-set-input`: the bracket refusal withholds its line in an anonymized run.
- `validation/raw-set-input`: CLI `-v` withholds its errors' texts in an anonymized run.

## Non-goals

- Tracebacks of crashes, echoed options, the dump-map file and revert output (C12); `junoscfg
  audit` has no anonymized run. Messages of a run that does not anonymize.

## Impact

`convert/__init__.py`, `convert/field_validator.py`, `convert/output/{__init__,structured_output}.py`,
`anonymize/{__init__,rules/as_number,rules/ip}.py`, `cli.py`, contracts, docs, version.
Reproduce: `private_test_data/makeover-work/anonymized-run-messages/`.
