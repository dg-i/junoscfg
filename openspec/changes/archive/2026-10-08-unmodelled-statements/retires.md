## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired.

## Symbols

None removed. The nokeyword catch-all's early return and the one-token
fallback leave `_merge_tokens`; neither was a symbol.

## Dependencies

None added or removed.

## Requirements

None; `skip_specs: true`.

## Tests and fixtures

`test_unknown_keys_ignored` in `tests/test_field_validator.py` pinned the
silence and is replaced by `TestAnUnmodelledStatementIsReported`. Nothing
else is retired; `test_unknown_token_still_flattens` still holds, since the
unknown-token path is what the fix routes to.

## Docs

`docs/guide/validation.md` gains the check. Pre-existing and recorded, not
fixed: the leaf path joins a trailing switch spelling into the value, so
`set interfaces ge-0/0/0 mtu 9000 disable` reads as `mtu: "9000 disable"`;
and the meta commands still apply to the nearest placed ancestor, so
`deactivate system nonsense alpha` deactivates `system` and drops its tail.
