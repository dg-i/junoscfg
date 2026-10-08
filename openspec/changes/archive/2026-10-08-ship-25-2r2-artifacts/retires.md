## Terms

<!-- agent-ready:retires:begin -->
<!-- agent-ready:retires:end -->

No vocabulary is retired. "Bridge" and "stripper" survive only in the record
of what was removed.

## Symbols

- `junoscfg.validate.set_validator._strip_apply_groups`: the grammar models
  the four statements it cut off.
- `junoscfg.validate.set_validator._inside_quotes`: guarded that cut.

## Dependencies

None added or removed.

## Requirements

None; `skip_specs: true`.

## Tests and fixtures

Retired, as they said they would be on this day:
`TestTheApplyGroupsStripperIsStillLoadBearing` (2),
`TestTheApplyFixReachesARealGrammar` (3), `TestStripApplyGroups` (3),
`TestApplyGroupsStrippingStopsAtQuotes` (2) and `test_apply_groups_stripped`,
all of which tested the stripper. Two classes against the shipped artifacts
replace them. The five bundled artifacts are replaced, not retired.

## Docs

The 24.4R0 references in `docs/guide/validation.md`, `docs/guide/cli.md`,
`docs/architecture/schema-internals.md`, `ARCHITECTURE.md` and
`docs/how-to/settle-a-schema-question.md` now describe 25.2R2 and the bridge
in the past tense. A stale clause in the `anonymize/rules/group.py`
docstring, "the bundled artifacts predate the fix", is left for a change in
that zone; its conclusion still holds, since the walker does not read the flag.
