## Findings

A fresh session reviewed this change. Every falsifiable number held, several
exactly: 49 of 61 lines rejected before and 61 of 61 after, 4,379 rules with
670 `__list`, 10,958 element names in 24.4R0 and zero doubled underscores in
any of the four schemas. All three defects are real in the code it replaced.
Nine findings; six acted on.

1. **The change's namesake fix has no test that bites.** The reviewer rewrote
   `_rule_name_for` to `return base` and the suite stayed green:
   `TestNamedListKeysSurviveRuleMerging` passes either way, because dropping
   `has_non_list` alone restores the entry-name slot. Verified here. The suffix
   is load-bearing — without it the rebuilt grammar drops from 61 of 61 to 51
   — and its real effect is on the container side, which nothing exercises.
   **Partly fixed**: `TestBundledGrammarIsReproducible`, added by the successor
   change, now catches any change to it byte-for-byte. A behaviour test for
   `set snmp user name X` is carried forward, not written here.
2. **The decision rested on the wrong measurement.** Impact compared grammar
   *load*, 25s against 43s. What mattered was parse: this emission costs
   ~228 ms a line against ~4 ms, and the alternative rejected here on load time
   had to be adopted two commits later. **Fixed** in Impact.
3. **"61 of 61" is partly undeserved.** `set interfaces ge-0/0/1 unit 0
   vlan-id 100` parsed only because the repetition let a bare `VALUE` swallow
   both tokens — the over-acceptance this record pins as a non-goal. **Fixed**:
   stated in What Changes.
4. **The `vlan-id` non-goal was misattributed.** It blamed `xsd_fixes.py` and
   declared the fix out of reach without a 24.4R0 dump. `_fix_freeform_nk_keys`
   was already in that file saying these nodes are "treated as normal keywords
   in conversion"; the generator was reading the wrong flag. `acd0633` fixed it
   in the generator with no schema change. **Fixed**: the non-goal is gone.
   Writing it felt like diligence, which is why nothing challenged it.
5. **The corpus was unreproducible.** Two reviewers independently failed to
   land on 113 commands, getting 187 and 77 under their own extraction rules,
   so 23→99 could not be audited. **Fixed** by the successor change, which
   commits `tests/data/set_corpus.txt` with its derivation; the figures here
   are now marked indicative.
6. **The biggest rejection class was never named.** Keying the splice on
   `nokeyword` rather than `transparent:` is right for 134 of 135 transparent
   flags; the one exception is `groups`/`group`, so every `set groups <name>
   ...` is rejected. `examples/router1.set` has no such line, which is why the
   headline hid it. **Fixed**: named in Non-goals and in the corpus test.
7. **Test count contradiction**, seven against five. Six net. **Fixed.**
8. **"534 such nodes" conflates two populations**: 534 nokeyword non-leaf
   nodes, of which 330 have children and reach the new branch. The other 204
   were a second defect, fixed in the successor change. **Not reworded** — the
   test docstring states the figure precisely — but it is why the 204 existed.

## Accepted as-is

- "~11,000 names in each dump" is loose (10,840 / 10,105 / 10,455). The
  substantive claim, zero doubled underscores, is exact in all four.
- tasks.md 3.1 cites a rebuild that needed `read_structure_tree`, added two
  commits later, so it was unauditable when written. The numbers do reproduce
  now.

## Specification challenges

No challenge. `skip_specs: true`.

## Verdict

Accepted after correction. The defect analysis and every measurement held;
what failed was what the record left out — an untested headline fix, a decision
made on the wrong metric, and the largest cost of its own design choice
unnamed. Owner acceptance: the owner asked for the open changes to be archived
in this session; they have not reviewed these findings individually.
