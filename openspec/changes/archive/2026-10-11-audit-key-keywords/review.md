# Review: audit-key-keywords (ledger #21, OPEN-12)

Reviewer: fresh isolated agent (lightweight fresh-agent review, conflict C2), 2026-10-11.
Base 87ac8f7, head b08b543 (code cacbf73), branch `change/audit-key-keywords`.
Read in order: instruction-integrity (freeze), proposal (no delta, `skip_specs: true`),
`openspec/specs/audit/keyed-references/spec.md`, `audit/model.py` `Occurrence` contract,
Builder evidence (`blast.py`, `compare.py`, `check_device.py`, `repro.py`), tests, diff.
Probes and outputs: `private_test_data/makeover-work/audit-key-keywords/roles/`
(`probe.py` + `probe-{base,head}.txt`, `doors.py` + `doors-head.txt`, `aliases.py`,
`find.py`, `base.json`, `head.json`, `cmp.txt`).

## Verdict

**CHANGES REQUIRED** (record-level only; no code change is required inside the fix-lane caps).
The code change is correct for what it changes: every changed entry path now equals a device
line. The record overclaims what it fixes and does not name the failure mode that OPEN-12's own
reproduction still shows.

## Verified independently

| Claim | Result |
|---|---|
| Regression test fails on the base for the right reason | Yes. Head's `test_walker.py` on a detached base worktree: 1 failed, 36 passed; `AssertionError`, the base path reads `virtual-link 10.0.0.1 ...`. The route-filter half also fails on the base on its own (`probe-base.txt`: path ends `upto`). Worktree removed afterwards |
| Passes at head | `tests/unit/audit`: 219 passed |
| The `nk` edit doesn't weaken `test_a_single_key_other_than_name` | Correct. The shipped tree marks positional keys `nk: True` (`route_address`, `mac_addr`, static-route `name`; `find.py`). The asserted kind and path are unchanged, and the edited test also passes at base, so the edit hides nothing |
| Before/after over 24 renderings | Rerun with the Builder's `compare.py`: **occurrences differ in 16 of 24 renderings, render output differs in 0 of 24**. My `base.json`/`head.json` are byte-identical to the Builder's |
| 194 changed paths: 84 equal device lines, 110 after dropping `rf_list`, 0 other | Confirmed by exact line equality (`set`/`deactivate`): head 194/194 exact (84 + 110), 0 other; base 0/194 exact (all 194 are only token-prefixes of a device line) |
| Doors | set, JSON and structured give identical occurrence paths for 8 statements (`doors-head.txt`). XML output isn't supported as a converter target, so XML is covered only through the device `.xml` captures in `compare.py` (6 renderings) |
| Negative cases | `route-filter ... exact` writes `exact` with no value token (bool excluded). A positional key stays bare (`route-filter 10.0.0.0/8`, `track route 10.1.0.0/16`). Quoted name `"pl a"` is quoted by `render`. `apply-groups` and inactive entries carry the same entry path. Every style of the `delete`/`deactivate`/`show configuration` command lines is unchanged |
| Fix-lane caps | 2 files, 30 lines (walker +12/-8, test +9/-1): exactly at the cap. `agent-ready lane --base 87ac8f7` reports nothing. Proposal is 9 lines |
| Device citation | `tests/contract/test_every_door.py` rows `virtual-link-keys-in-order` (accepted) and `virtual-link-keys-without-keywords` (rejected), vMX 23.2R2-S7.5: these exist and say what the record says. The route-filter spelling is the 84 device lines in `tests/data/device/jvd/vmx-23.2R2-S7.5` |

## Findings (ranked)

### F1 (medium): OPEN-12's own reproduction still yields paths no device accepts, and the record doesn't name it

`Occurrence.path` is documented as "Full hierarchy path in CLI tokens ... (suitable for emitting
Junos commands)" (`src/junoscfg/audit/model.py:30`). For an entry with several value key fields,
`_walk_entries` emits each key field as a leaf at `entry_cli_path + (f,) + value`
(`walker.py` multi-field branch, which the diff leaves unchanged). Now that `entry_cli_path`
holds `f value` for a keyworded field, the field is written twice. For a positional field, the
path carries the internal IR name. Executed (`probe-head.txt`):

- `set protocols ospf area 0.0.0.1 virtual-link neighbor-id 10.0.0.1 transit-area 0.0.0.2` gives
  `... virtual-link neighbor-id 10.0.0.1 transit-area 0.0.0.2 transit-area 0.0.0.2`.
- `... vrrp-group 1 track route 10.1.0.0/16 routing-instance ri1` gives
  `... routing-instance ri1 routing-instance ri1` and `... routing-instance ri1 route_address 10.1.0.0/16`.
- The doubled path reaches rendered output, as the verbose `# unresolved:` line
  (`aliases.py`, prefix-list `0.0.0.2`).

These are exactly the occurrences in the OPEN-12 reproduction: the virtual-link entry has no
entry-key occurrence, only these two leaves. The regression test passes because it compares only
a prefix (`o.path[: len(words)]`). The proposal's "both entry paths equal the writer's line" is
therefore true only as a prefix for virtual-link. The base was not better
(`virtual-link 10.0.0.1 0.0.0.2 neighbor-id 10.0.0.1`), so this is not a regression. But OPEN-12
is only partly closed, and the proposal's "Remaining failure mode" omits it.

### F2 (low): the changelog and the proposal's "Why" overclaim the script fix

The changelog says "so delete, deactivate and show scripts built from these paths load". Script
command lines are built from `Finding.path`, which is a definition's path. No registry type
(`audit/data/unused-types.yaml`) is defined beneath a keyworded-key or key-choice entry. Two runs
agree: 0 of 24 renderings change any rendered style, and no probe changed a command line. The
only user-visible effects are the `collect_occurrences` paths (public, `__all__`) and the verbose
`# unresolved:` comment lines.

### F3 (low, record): `check_device.py` doesn't discriminate between base and head

Its substring/prefix test passes the base's removed paths at the same rate as head's new ones
(60/194 each). The record's "84 equal a set or deactivate line" is nevertheless true under exact
equality (recomputed above). The record should name the exact-equality method, or the script
should test `line == "set " + path`.

### F4 (info, prompt 4, second answer)

The writer's `_entry_key` (`convert/output/dict_walker.py:553`) and the audit's `_key_tokens`
answer the same question. The audit lacks three things the writer has:

- a list-valued key field (the writer takes `value[0]`; the audit drops the token, as base did);
- `resolve_key_alias` on choice alternatives (only `then community`'s `=`/`+`/`-` choice is
  affected, and set, JSON and structured already give `+` in the IR, so it is not reachable here);
- `None` for a missing key field.

The proposal names the duplicated loop and `KEY_ALIASES`. The follow-up "move `_entry_key` into
`display`" is the right provider.

## Specification challenges

| Artifact | Counterexample | User impact | Proposed correction | Decision |
|---|---|---|---|---|
| `proposal.md` "Remaining failure mode"; regression test `test_the_key_as_the_set_writer_writes_it` | `collect_occurrences` on the OPEN-12 virtual-link statement returns `... transit-area 0.0.0.2 transit-area 0.0.0.2`; `track route ... routing-instance ri1` returns `... ri1 route_address 10.1.0.0/16`; the test's prefix comparison passes both | API consumers of `Occurrence.path` and verbose `# unresolved:` lines still get paths the device would not accept, contrary to the `model.py` docstring | Record-only within caps: name this failure mode (key-field leaves of multi-key entries append `field value` after an entry path that already holds it, or the IR name of a positional field) in the proposal, and carry it forward as a follow-up (emit those leaves at `entry_cli_path`; assert full-path equality). Alternatively, fix it if the caps allow a third file | Pending owner decision. Interim action: merged with the failure mode named in the proposal as NEW-R19 and carried to follow-up 21b `audit-entry-key-from-kernel` (owner intake 2026-10-11: merge with recorded interim action) |
| `changelog.d/+audit-key-keywords.bugfix.md`, proposal "Why" | 0 of 24 renderings and every probe: no `delete`/`deactivate`/`show` command line changes | A reader expects changed script output that never occurs | Reword: the occurrence paths from `collect_occurrences`, and the verbose `# unresolved:` lines, now write an entry's key as the set writer does | Pending owner decision. Interim action: merged with the changelog and the proposal's "Why" reworded to claim only the occurrence paths and the verbose lines (owner intake 2026-10-11: merge with recorded interim action) |

## Five prompts

1. **Trust boundary:** the change adds no new boundary. Key values are copied verbatim into path
   tokens, and `render._format_path` still quotes them and escapes newlines.
2. **Incompatible-but-valid input:** multi-key entries with a keyworded or positional key field
   that is also walked as a leaf (F1).
3. **Shared blind spot:** the test's prefix comparison and the record's "entry paths" agree on a
   criterion that a doubled-token path satisfies (F1). The independent evidence is the exact
   device-line comparison, which holds for entry-key paths only.
4. **Second answer:** see F4. It is named in the proposal and deferred because of the live
   S-lane Builder, which is justified by C3.
5. **Figures:** 32 keyworded key fields and 19 valued choice alternatives (`blast.py`, rerun);
   16/24 and 0/24; 194 = 84 + 110 + 0. All rerun and confirmed. I found no "cannot" non-goal.

## Could not check

- The device verdict on any `show`/`delete` path that ends with a repeated key
  (`... transit-area 0.0.0.2 transit-area 0.0.0.2`). No capture or probe holds one. Carry forward.
- Whether any input door produces a list-valued key field (the writer takes `[0]`; the audit
  drops it). Carry forward with the `_entry_key`-into-`display` follow-up.
- XML as a converter target is unsupported, so the XML door was checked only through the 6
  device `.xml` captures.

## Resolution (orchestrator rulings, applied by the Builder)

- F1, accepted as a recorded remaining failure mode, not fixed here (the fix-lane caps are used up: 2 files, 30 lines). `proposal.md` names it: an entry with several value key fields still emits each key field as a leaf after the entry path, so the path repeats it (`transit-area 0.0.0.2 transit-area 0.0.0.2`) or names a positional field by its IR name (`route_address 10.1.0.0/16`); not a regression. Ledgered as NEW-R19 and carried to follow-up 21b `audit-entry-key-from-kernel` (with the `_entry_key` move into `display`, after #8 merges). OPEN-12 is FIXED_PARTIAL: keyword-written keys and choice values are fixed.
- F2, accepted: `changelog.d/+audit-key-keywords.bugfix.md` and the proposal's "Why" now claim only what changed, the entry paths of `collect_occurrences` and the verbose `# unresolved:` lines, and say the command lines are unchanged.
- F3, accepted, record-only: `check_device.py` does not discriminate base from head (its prefix test passes 60/194 of each). The evidence is exact line equality with a device `set` or `deactivate` line: head 194/194 (84 directly, 110 once the pre-existing `rf_list` token is dropped), base 0/194. `instruction-integrity.md` records this method.
- F4, informational: the list-valued key field gap is now named in the proposal beside `KEY_ALIASES`; both go to follow-up 21b.
- None of these edits touches code or tests, so no re-review was needed and the full check at cacbf73 still stands.
