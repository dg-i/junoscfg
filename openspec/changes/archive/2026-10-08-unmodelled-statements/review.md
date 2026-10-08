# Review

Fresh agent session, read-only, against commit `e1aafe5` before it was
amended and tagged `v0.9.0`. The reviewer ran a differential of the reader
against the previous commit over 1,398,624 unique jvd set lines and the three
devices, and probed the validator's exemptions on both.

## Confirmed exact

The reader change is narrow: 69 jvd lines change IR, every one strictly better
(`vlan-range 100-200`, `srgb-label-range 16000 23999` kept whole where a
value vanished); 0 of 7,002 device lines change. Seven device statements are
reported, all `uplink-failure-detection group` and `chassis dump-on-panic`;
0 false positives on the devices and on eleven legitimate IR shapes. The
pipeline prints the statement, raises under strict, exits 0 / 1 / silent as
declared. No new stderr site in `src/`. Full suite and the jvd tier green.

## Findings

1. **Anonymization leaked what it used to drop.** A kept statement lives in
   a key, and the anonymizer never rewrites a key the schema does not name,
   so `set protocols bgp neighbor 10.11.12.13 description X` left verbatim
   where the reader had dropped its tail. 1,502 of 33,074 unplaced keys in
   500 jvd files carry an address; 0 of the 7 device keys do. **Applied**:
   the pipeline refuses anonymization on an unplaced statement whatever
   `validate` and `strict` say, declared on `api` and `cli`, tested.
2. **`validate_ir` on the `{"configuration": ...}` wrapper errored** where it
   had validated nothing in silence. **Applied**: the wrapper is stripped.
3. **The `_` exemption was wider than its rule**: `set system _bogus alpha`
   escaped. **Applied**: only `_v<n>` is a reader's.
4. **The meta commands still drop**: `deactivate system nonsense alpha`
   deactivates `system` and loses its tail, unchanged by this commit but
   contradicting "the reader never drops". **Accepted**: the proposal and
   `removes:` now say a `set` line; recorded as a known defect.
5. **The message could not name the list entry.** **Applied**: it names it,
   `under interfaces ge-0/0/0`, as Junos would.
6. **The only valid lines the guard moves had no test**, and "is not in the
   schema" misattributed a reader limit (`flow-server 1.2.3.4 port 2055`).
   **Applied**: one test on `srgb-label-range 16000 23999`; the wording is
   "could not be placed in the schema".
7. **The guide listed three exemptions of five and filed the error under
   warnings.** **Applied**. The volume through the library's stderr door
   grows by ~69k lines on jvd; the architecture already names that door a
   defect, and this change opens no new one. **Accepted**, recorded.

## Already provided

`find_configuration` in `convert.ir` strips the wrapper; the validator does
the one-key case inline rather than import across the package.

## Specification challenges

None.

## Verdict

Correct and measurably narrow; ship once finding 1 is closed, which the
amended commit does. 1, 2, 3, 5, 6, 7 applied; 4 and the stderr volume
recorded.

## Owner acceptance

Accepted by the owner on 2026-10-08, in one pass over the eight live reviews,
on the summary that each review's findings were resolved or recorded as
accepted-as-is. The owner did not sign off per finding.

Decisions: anonymization keeps the hard fail on a statement the schema
cannot place, with no opt-out — a statement that cannot be placed is one
whose scrubbing cannot be promised; the meta-command drop (4) stays a
recorded known defect, outside this plan's scope.
