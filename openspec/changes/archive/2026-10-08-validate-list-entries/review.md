# Review

Fresh agent session, read-only, against `ff1d4f3` (v0.11.0), with all
mutation and regeneration work in a detached worktree. The session that wrote
the record also wrote the code; the review was told to treat the record as
self-serving and check it by running things.

## Confirmed exact

Every mechanical claim tested reproduces. The plan's six probes reject and its
three shapes and three fragments validate against the shipped artifact.
`tests/test_device_truth.py` 4 passed, 0 skipped — and the device's own
`| display json` captures validate with **0 errors** against the new schema,
the oracle that needs no schema. The mutation table reproduced exactly with
hashes verified changed under each mutation (7 / 2 / 3 / 2) from a baseline
regeneration byte-identical to the committed artifacts. 8,782 `required`
arrays; `string` gone from all 52,218 container types; `^@` on all 83,824
containers; 1,576 / 72 / 2; `openspec validate --strict` valid; minor bump
correct for a declared api+cli break under beta. An independent jvd sample
(150 of 1,535): 19 invalid before → 35 after, every new rejection a statement
the field validator already reports. Nothing the other seven live changes
assert is broken.

## Findings

1. **Medium — the transparent-items branch over-accepted on 186 of 187
   containers.** It fired on every node with a `transparent:` flag, but only
   `groups` drops its wrapper in JSON; `interfaces`, `vlans`,
   `routing-instances` and the UFD `group` keep it, so
   `{"configuration": {"interfaces": [{...}]}}` validated — a shape no device
   and no converter emits. Over-accept, not over-reject. **Fixed before
   archive**: the branch is conditioned on `node.name == "groups"`, with a
   generator test (`interfaces` keeps the scalar array form) and a shipped-
   artifact probe (`interfaces` as a list rejects). Artifacts regenerated.
2. **Medium — the break's error message is unusable on real documents, and
   the migration text overstated it.** jsonschema reports a list matching
   neither `anyOf` branch as one error naming the list's path and dumping the
   list — 7,355 characters for one `mtuu` in entry 37 of 60, never naming
   `mtuu`. The migration said "the error names the path". **Migration text
   corrected** in `.openspec.yaml` to say what it names and how to descend;
   the formatting fix belongs in `json_yaml_validator._validate_data` and is
   recorded as a follow-up in `retires.md`, not folded in here.
3. **Low — "mandatory stays a field-validator warning" is API-only.** The CLI
   prints warnings only beside an error, so `-v`/`--strict` show nothing for a
   missing mandatory field. Unchanged from before (`required` was inert);
   **recorded** in `retires.md` rather than claimed otherwise.
4. **Low — the "nested `groups` escape" was misdescribed.** Junos has no
   groups inside groups; the branch serves three unrelated statements named
   `groups`. **`retires.md` corrected** to describe what it actually covers.
5. **Low — 43,331 was stale.** It is the v0.7.0 / 24.4R0 artifact's count; the
   25.2R2 artifact had 52,219 before and 83,825 after. Measurement rule 2 of
   the plan — re-take every count — was not followed for this one. **Fixed**
   in the source comment, the test docstring and `retires.md`; the commit
   message of `ff1d4f3` keeps the stale figure and this note corrects it.
6. **Low — unrecorded cost: artifacts grew ~50%** (652 → 984 KB gz; load
   0.17 → 0.32 s), because `properties["group"]` is inlined into `groups`'
   `items.anyOf`. **Recorded** in `retires.md` with the `$ref` follow-up; the
   fix for finding 1 trims the 186 other inlines but not this one.
7. **Low — what the array form still admits.** Nested arrays and strings in a
   list position; presence flags take any object or array; leaves anything;
   depth-12 cutoff. All pre-existing and structural by design; **recorded** so
   "`additionalProperties: false` now binds" is read with its limits.
8. **Info — the one valid Junos rendering that now fails `-v`** is
   verbose-format device JSON (`"system": [{...}]`), which junoscfg's reader
   never supported and the owner's captures do not use. Owner-approved via the
   plan's probe 5.
9. **Info — record hygiene.** Checklist said "seven shapes", proposal "four";
   "twelve new tests" is eleven new and one rewritten. **Corrected**.

## Resolution

The change does what it says and the review could not break it in the
direction that sank the first attempt: no over-rejection beyond the
owner-approved shapes, and the device's own JSON validates. Where the record
fell short it was by omission — the breadth of the transparent branch, the
real target of the groups escape, the artifact growth, the unusable error —
and by one count carried over from a different artifact. Findings 1, 2, 4, 5
and 9 are fixed in the change before archive; 3, 6 and 7 are recorded; 8 is
owner-approved.

## Owner acceptance

The owner accepted the eight live reviews in one pass on 2026-10-08, before
this one existed, on the condition that it be added once it landed. The two
Medium findings were fixed in the change before archive and the owner was
shown them with the archive request. This is a single acceptance of the set
on its summary, not a per-finding sign-off.
