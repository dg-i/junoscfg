## Why

The set and curly writers decide quoting by the look of a value, not by its leaf. A one-term
policy expression `import ( P-A )` is written `"( P-A )"`, a policy name (DEV-4); a quoted name
`"( P-A && P-B )"` is read as an expression (DEV-5); the device's own XML and JSON value
`"( P-A )"` is written `""( P-A )""` (DEV-6); and `description "uplink to sw1 \"core\""` is written
with bare inner quotes and does not load (DEV-7 = NEW-C6 = ANON-P4). The set grammar rejects that
escaped quote outright (DEV-V1, escape half). 212 recorded device lines are wrong today.

## What Changes

- `junoscfg.display.format_value` takes the leaf's schema node: a `policy-algebra` value that is
  already one device token, an expression `( … )` or a quoted name `"…"`, is written as it is;
  every other value is quoted where it must be, its `"` escaped as `\"`. `\` is written as it is,
  as the device writes `\n` (C3). The look-based `policy_expression()` heuristic goes.
- **BREAKING** (`consumer`, `cli`): set and curly input keep a quoted `policy-algebra` token's
  quotes where the bare text would read as an expression (`"( P-A )"`), as the device's XML and
  JSON hold it; JSON and YAML output change for such input only.
- The set grammar's `QUOTED` terminal takes `\"` inside a quoted value, the curly lexer's rule;
  `validate/data/` is regenerated. `known-differences.json` loses four classes (212 lines).
- ANON-P4's strict xfail goes: revert was right, the writer was not.

## Capabilities

### New Capabilities

- `conversion/value-quoting`: how a writer spells a value and how a reader reads a quoted one,
  by the leaf's type.

### Modified Capabilities

- `validation/set-command-validation`: an escaped quote inside a quoted value validates (added
  requirement).

## Non-goals

- The backslash half of DEV-7 (probe P11), quoted plain policy names (probe P12), DEV-V7
  `$junos-…` quoting (intentional), DEV-V1 meta verbs (change 14), XML whitespace (change 9).

## Impact

`display/value_format.py` (kernel), `convert/output/dict_walker.py`, `convert/input/set_input.py`
(conversion), `validate/grammar_generator.py` and `validate/data/` (schema), the device record,
tests. Search for the formatter: `format_value|needs_quoting|policy_expression` over `src/`,
`tools/`, `tests/` finds `dict_walker.py`, `structured_output.py`, `set_output.py`,
`audit/render.py`. Reproduce: `private_test_data/makeover-work/value-quoting-by-type/repro.py`.
