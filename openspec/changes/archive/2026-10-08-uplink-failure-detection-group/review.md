# Review

Fresh agent session, read-only, against commit `1f8e504` before it was
amended and tagged `v0.10.0`. The reviewer regenerated the artifacts from the
same dump, diffed the structure tree against the previous commit, walked the
shipped tree for the flag, and ran eight synthetic lines under both sets.

## Confirmed exact

Within the owner's limit: an 18-line function and a 7-line registration, no
line in the reader, the writers or the positional-key code, the name-keyed
table untouched. Regenerated, not hand-edited: four of five files
byte-identical to an independent rebuild, the metadata differing only in
`generated_at`; against the previous commit the structure tree differs in
exactly four additions of the flag and nothing else. Scope exact: the four
`uplink-failure-detection` nodes with a `group` carry it, the four satellite
ones without do not, no other `group` anywhere gained it, BGP round-trips.
The XSD declares `group` as a container and `ufd-group-name` unbounded and
nokeyword, byte for byte the `interfaces`/`interface` idiom; `groups` is the
one wrapper the XSD declares unbounded, which is why it alone unwraps. The
device-style unwrapped JSON converts to the same set line. Full suite 1,544.

## Findings

1. **Both fix-group tables summed to 41**: D read 13 in the developer guide
   and G read 5 in schema internals, each a pre-existing row short that this
   change touched without fixing. **Applied**: 14 and 6, as the registry has.
2. **The one place the wrapper rule is written down omitted the new
   wrapper**, `json_output._native_groups`. **Applied**.
3. **`deactivate ... group G` used to lose its `G`** and now round-trips;
   untested. **Applied**: one test.
4. **The shipped JSON Schema cannot tell the two shapes apart**: an array
   under `group` passes whatever it holds, the array escape change
   `validate-list-entries` proposes to close. **Accepted**, recorded.
5. **A group literally named `ufd-group-name`** is read as the hidden
   keyword, as `set groups group foo` is for every transparent container.
   **Accepted**: the same pre-existing class, outside the limit.
6. **The 23.2R2 half of the docstring claim runs only under `--schema`.**
   Measured during implementation on the 23.2R2 dump: the fix does not fire
   there, so 38 of 42 follows from the 38 of 41 already recorded. **Accepted**.
7. **The JSON shape rested on XSD idiom, not a capture.** The owner supplied
   one the same day, in structured, JSON and XML. **Settled**: the device
   renders `group` → `ufd-group-name` → entries with `name`, links as lists
   of names, which is junoscfg's output to the path; the pair is in
   `private_test_data/captures/` and the device-truth tier passes on it.
   The XML form converts to the same six set lines as the structured form.
   One rendering difference, recorded and not this change's: the device
   writes a name-only list entry as a block, `link-to-monitor { X }`, where
   junoscfg's structured writer puts `link-to-monitor X;` on one line.

## Already provided

Nothing the toolbox or the standard library covers was rewritten.

## Specification challenges

None.

## Verdict

Sound, minimal and correctly scoped; ship with 1, 2 and 3 applied, which the
amended commit does.

## Owner acceptance

Accepted by the owner on 2026-10-08, in one pass over the eight live reviews,
on the summary that each review's findings were resolved or recorded as
accepted-as-is. The owner did not sign off per finding.

The capture asked for in finding 7 was supplied by the owner and settled it.
