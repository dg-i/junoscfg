# Review

Fresh agent session, read-only, on 2026-10-08 against HEAD `a9841c5`, of the
change that shipped as v0.7.0 in `d7dfdcc`. Taken late: this was the one
older change with no review on record. The reviewer ran the examples through
both round trips, probed the generated JSON schema against the pre-change
artifact, and re-measured the switch-spelling and enum claims on the shipped
25.2R2 tree.

## Confirmed exact

Both example round trips byte-identical. The four named causes fixed: a named
list writes and validates its `name`, a presence flag and a bare container
write `[null]` and validate, `apply-groups` validates at depth under a list
entry. The either-order fix holds. 4,226 switch nodes on the shipped tree,
all `enable-disable`, no widening. The enum tightening over-rejects nothing
found; the unquotable-type grammar rejects only nonsense. The cli break is
accurate: `--strict` exits 1 on a value a device rejects, and without it the
warning goes to stderr.

## Findings

1. **The JSON and YAML half bought self-acceptance by switching shape
   checking off behind every list.** Every container's type union admits
   `array` and `string`, so a list's `items` constraint is dead and
   `additionalProperties: false` binds nothing behind an array:
   `{"configuration": "hello"}`, a list entry with a bogus property, a list
   of strings, all `Validation: OK`, all rejected by the pre-change
   artifact. A regression, not a pre-existing hole, and the trust-boundary
   gate for JSON junoscfg did not write. **Carried as the open defect** that
   `validate-list-entries`, Step 6 of the plan, closes; the plan's six probes
   are these.
2. **The break was declared on `cli` only.** `convert_config(strict=True)`
   raises where it did not, and `validate_json` accepts what it rejected.
   **Applied**: `api` declared, late, with its migration.
3. **The kernel list recreated the duplication it removed**:
   `UNIVERSAL_STATEMENTS` and `_APPLY_STATEMENTS` hold the same four names
   in two packages with no test pinning them equal. **Recorded** for a small
   later change.
4. **Every schema assertion in the new tests asks only whether the schema
   accepts**, so widening the type union passed 1,562 tests. **Recorded**;
   Step 6's tests are negative by design.
5. **The migration text's `maximum-entries` example does not reproduce**;
   `mtu` carries no type in the shipped tree. **Applied**: the text names
   `idle-timeout`, which does.
6. **`name`, flat-entry keys and switch spellings are added as `{}`
   properties**, deliberate and harmless alone, compounding finding 1.
   **Recorded**.

## Already provided

Nothing the toolbox or the standard library covers was rewritten.

## Specification challenges

None.

## Verdict

The set-grammar, field-validation and set-reader halves are sound; the JSON
and YAML half is carried as an open defect with its closing change named.
Archive once the owner accepts that, not before.

## Owner acceptance

Pending.
