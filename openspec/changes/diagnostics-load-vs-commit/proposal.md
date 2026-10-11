## Why

A conversion reports a field-validation warning only when an unrelated error exists: `set access
profile PROF-1 radius-server 192.168.50.10 timeout 10` alone converts with no diagnostic, and the
same line beside `set chassis dump-on-panic` adds `Missing mandatory field 'secret'` (NEW-B7 =
NEW-C2). That message also hides the boundary: the vMX and the QFX5120 loaded the line without
`secret`; the schema marks it mandatory, which Junos checks at commit (DEV-V3, OPEN-16).

## What Changes

- `convert_config_result`, `pipeline_result` and `junoscfg convert` carry every field-validation
  warning as a diagnostic whether or not the validation found errors; with `strict` the errors
  still raise `FieldValidationError` and a configuration with warnings only converts, its warnings
  reported.
- The mandatory-field warning names the boundary: `Missing mandatory field 'secret': required at
  commit; the configuration loads without it`. It stays a warning and `strict` never raises on it.
- Removes the coupling of warnings to errors in `convert/__init__.py::_convert`.
- No override, fallback, parameter or environment read is added.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `conversion/diagnostics`: requirement "The caller owns diagnostic rendering" gains the rule that
  field-validation warnings are carried whether or not errors were found; a new requirement states
  that a missing mandatory statement is a commit-time warning which `strict` does not escalate.

## Non-goals

- A commit-check option or strict level that escalates mandatory warnings (a feature, C4).
- Field validation inside `validate_set`, `validate_config` or `junoscfg convert -v`: schema and
  field validation keep their separate doors (C5).
- Mandatory checks inside `groups` (whether Junos checks a group's statements as written or after
  inheritance is a device question; recorded in the evidence freeze).
- The JSON reader's `end-range` alias that leaves `member-range` without `to` (NEW-B8, row 13).

## Impact

`src/junoscfg/convert/__init__.py`, `src/junoscfg/convert/field_validator.py`, their unit tests,
`src/junoscfg/convert/CONTRACT.md`, `docs/guide/validation.md` (`docs/guide/cli.md` already says
warnings are printed, and is change #7's path), a changelog fragment, the `conversion/diagnostics` delta. More diagnostics, no output change: measured with
`private_test_data/makeover-work/diagnostics-load-vs-commit/compare.py` over
`tests/data/device/manifest.json` (96 conversions) and `probe_mandatory.py` (mandatory warnings per
rendering).
