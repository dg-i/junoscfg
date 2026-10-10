# Test/Challenge report

## Challenger

Independent Test/Challenge role (fresh `general-purpose` agent, `claude-opus-5-5`), 2026-10-10.
Inputs: this change folder, `git diff 7a60907..0c9e24d`, `ARCHITECTURE.md` §1, `AGENTS.md`,
`src/junoscfg/{display,convert}/CONTRACT.md`, the cited tests, the device captures
`private_test_data/deactivate{,2,3,4,5,6}.txt` and the device re-export
`private_test_data/anon/anonymized_bordergw_rexport.*` (read in memory; no value copied).
No product code, spec or approved test was edited. Adversarial tests:
`tests/test_meta_tags_challenge.py` (new, untracked; 14 pass, 13 strict-xfail). Run against
change A's head the same file shows 13 failures/XPASS: the passing guards discriminate B's fix,
and the block-list tests prove a B regression.

## Verdict on the acceptance tests

| Test id | Verdict | Reason |
|---|---|---|
| `test_characterization.py::…::test_a_one_line_tagged_route_reaches_one_ir` | keep | Four doors, exact IR; fails on A |
| `…::test_an_inactive_family_inet_reaches_one_ir` | keep | Four doors plus a JSON→curly→JSON round trip |
| `…::test_a_protected_one_line_route_reaches_one_ir` | keep | Four doors; device JSON spelling normalised as designed |
| `test_meta_tags.py::TestACurlyTagMarksTheStatementStart::test_every_tag_on_a_one_line_entry` | keep | 8 cases, asserts tag placement and absence |
| `…::test_a_transparent_list_entry` | keep | |
| `…::test_an_entry_keyed_by_two_fields` | keep | |
| `…::test_set_input_still_marks_the_last_node` | keep | |
| — (missing) | **missing** | No test reads a tag on an entry **inside its list's block** (`source-prefix-list { inactive: PL1; }`), the device's layout for lists of bare entries. B raises `ValueError` there; A reads it (adversarial test 1) |
| `TestStructuredOutputPutsATagFirst::test_an_inactive_family_inet` | keep | Asserts a line shape, but the shape is the meaning-bearing one (§1 exception) |
| `…::test_a_tagged_child_is_not_joined` | tighten | `"then {" in lines` asserts layout; the meaning is "`accept` keeps its tag and `then` none after reading back", already covered by the round-trip SHAPE. Replace the layout asserts by an IR assert |
| `…::test_round_trips_keep_the_ir` | tighten | Discriminating for its 8 shapes, but SHAPES omits a tagged leaf-list (the shape change A creates from XML), which fails (adversarial test 2); and it only reads back junoscfg's own curly, never the device's block layout |
| `TestATagOnFamilyIsReported::test_every_input_reports_it` | tighten | Covers set/XML/JSON/YAML; structured input (`inactive: family { … }`) is not covered and gives no diagnostic (adversarial test 3). Asserts by substring, not `expected == UNPLACED` |
| `…::test_set_output_repeats_it` | tighten | Only set input; JSON's sibling form `"@family"` is reported but dropped from set output (adversarial test 4) |
| `…::test_structured_output_drops_it_with_a_note` | keep | |
| `test_artifact_builder.py::TestHomogeneousFlag::test_the_tree_carries_it` | keep | |

## Adversarial tests

Run: `uv run --locked pytest -q -rxX tests/test_meta_tags_challenge.py` in this worktree. Probes: session scratchpad `probe/p3.py`–`p11.py`.

1. **Tag on an entry inside its list block (regression)** — e.g.
   `firewall { family inet { filter FILTER-V4 { term T1 { from { source-prefix-list { inactive: PL1; PL2; } } } } } }`;
   also `from source-address { inactive: 198.51.100.0/24; }`, `system name-server { inactive: 192.168.0.1; }`, `snmp community public clients { inactive: 10.0.0.0/8; }`, `snmp filter-interfaces interfaces { inactive: xe-0/0/0; }`.
   Expected: the IR of `deactivate … source-prefix-list PL1` (entry `@`), which change A gives.
   Observed: `ValueError: Invalid structured input: a tag inside a key or value …`; CLI `convert -i structured -e set` exits 2 (A exits 0 with the right `deactivate` line).
   Cause: in `_merge_tokens` the list path marks the entry with `here` (the tag at the list keyword's token) only; a level that starts at the first key token keeps its tag in `tags`, and `statements_to_dict` raises.
   Blast radius: tagging each level of the device re-export `.conf` one at a time, 122 level taggings of 3,422 statements raise, in 70 shapes (firewall `source-/destination-prefix-list`, `source-/destination-address`, `prefix-list`; snmp `clients`, `filter-interfaces interfaces`, `routing-instance-access access-list`; `system name-server`, `archive-sites`; event-options `attributes-match`, `destinations`; and per-value leaf-list lines such as `change-configuration commands`, where refusal is defensible). The re-export as captured has no tag in such a block, which is why the Builder's oracle stayed green.
   Command: `… -k entry_inside_its_list_block` (4 strict-xfail on B; XPASS on A). **Product defect, High.**
2. **Tagged leaf-list through structured output** — `set … community C1 members 64496:1/2` + `deactivate … members` (also `protect`, static `next-hop` ×2, `ethernet-switching vlan members`, and change A's XML leaf-list).
   Expected (device, `deactivate6.txt` line 20): `inactive: members [ 64496:1 64496:2 ];`.
   Observed: `members [ 64496:1 64496:2 ];` — tag dropped, no diagnostic; set→curly→set loses it. Pre-existing writer gap (the `[ … ]` key does not match the `@members` path in `ConfigStore`), in scope of requirement "Structured output puts a tag at the head of its node's line".
   Command: `… -k survives_structured_output` (5 strict-xfail). Reading the device form `inactive: members [ … ];` works (`test_the_device_curly_of_an_inactive_leaf_list_reads` passes). **Product defect, High** (silent activation on load).
3. **`inactive: family { inet {…} inet6; }` (block form)** — Observed: the tag is copied to every family inside, no diagnostic (A kept it on `family`, unreported). The spec says the reader passes it to "the child that follows it in the same statement" and that a tag on `family` is reported from every input; here the child is in another statement and nothing is reported. Not device output. Command: `… -k family_block` (strict-xfail). **Test idea / spec challenge, Medium.**
4. **JSON `"@family"` beside `family`** — field validation reports it, set output drops it (spec: repeats it). Command: `… -k sibling_family` (strict-xfail). **Product defect, Low** (not the device's JSON form).
5. **Tag on one `apply-macro` data line** — `apply-macro M1 { k1 v1; inactive: k2 v2; }`. Observed: the whole macro `M1` is tagged (`_tags_from(tags, i)` gathers later tags); A kept the line whole and reported it. No device artefact. Command: `… -k apply_macro` (strict-xfail). **Test idea, Medium** (silent widening).
6. **Per-value tag in curly** — `members 64496:1; inactive: members 64496:2;` deactivates both values silently, where XML refuses the same shape (change A) and the CLI rejects the per-value tag (`deactivate5.txt`). Command: `… -k per_value` (strict-xfail). **Spec challenge, Low–Medium.**
7. **Guards that pass on B and fail on A** — stacked `protect: inactive:` / `inactive: protect:` on one route; device shape `protect: family inet { inactive: address …; }` (`deactivate6.txt` lines 457–496) equal from XML, set and curly; XML leaf with `protect` and `inactive`; round trips for route + next-hop both tagged, route-filter entry + action, `family inet dhcp` with tagged child, two families (one protected, one inactive), `then` + `accept` both tagged, `groups` entry, firewall `from` container; a quoted description `"inactive: route …"` stays a value.
8. Probes not turned into tests:
   - `inactive: services { }` (empty block) and `inactive: xe-0/0/0 { }` give `{}`; untested on A, not device output.
   - `route 0.0.0.0/0 inactive: next-hop 10.0.0.1;` (tag mid-line) is kept whole as an unknown statement; not device output.
   - Leaf-list with even `inactive` but uneven `protect` in XML: refused with a message that says "marks some of its values inactive" (Low: message names the wrong tag).
   - `tunnel encapsulation`: the refusal and merged print apply to it as well (`passes_tag_to_child` is generic), while the freeze says the refusal covers `family` only until `deactivate7.in` returns; `gre` under it is already UNPLACED on A (pre-existing).
   - `deactivate system apply-macro M1` in set input is kept whole (pre-existing `_apply_meta`), so set and curly give different IRs for an inactive macro (follow-up "`_apply_meta`'s schema walk").
   - `validate=False` drops the `family` UNPLACED diagnostic (by design of the flag; noted only).
   - Device re-export, all four formats: equal tag sets (2) from set, XML, JSON and curly input.

## Specification challenges

### S1 — Where an entry starts when its list keyword opens a block

- **Artifact**: requirement "A tag on a curly statement marks the node the statement starts"; `set_input._merge_tokens` list path; `statements_to_dict` `ValueError`.
- **Counterexample**: `source-prefix-list { inactive: PL1; }` — the statement `PL1;` starts the entry `PL1`; the reader raises "a tag inside a key or value".
- **User impact**: valid device curly that worked on master/A is refused (CLI exit 2) as soon as one such entry is deactivated or protected.
- **Proposed correction**: state that a level starting at an entry's first key token marks that entry; add the four shapes of adversarial test 1 as acceptance tests; keep the `ValueError` only for a level boundary strictly inside a multi-token key or a value. The new `ValueError` should also be checked against every level of the device re-export (the probe in this report does that in seconds).
- **Decision**: Pending owner decision

### S2 — Round trip of a tagged leaf-list

- **Artifact**: requirement "Structured output puts a tag at the head of its node's line", scenario "Round trips" ("each tagged shape of this capability"); change A's leaf-list requirement is in the same capability.
- **Counterexample**: `deactivate policy-options community C1 members` with two values → `members [ … ];` without `inactive:`.
- **User impact**: curly output loads the deactivated list as active; no diagnostic.
- **Proposed correction**: add a tagged multi-value leaf-list to SHAPES and fix the writer (the device writes `inactive: members [ … ];`).
- **Decision**: Pending owner decision

### S3 — "Every input" reports a tag on `family`, but curly block form widens it

- **Artifact**: requirements "A tag on a curly statement…" ("the child that follows it in the same statement") and "A tag on an unkeyed homogeneous container is reported" ("any input").
- **Counterexample**: `inactive: family { inet { … } inet6; }` → both families inactive, no diagnostic.
- **User impact**: a hand-written or foreign-tool curly config deactivates more than one family silently; set/XML/JSON/YAML of the same shape report UNPLACED.
- **Proposed correction**: pass the tag only within one level (`inactive: family inet {`); a tag on a level that is `family` alone is reported UNPLACED like the other inputs.
- **Decision**: Pending owner decision

### S4 — Widening a tag onto a node the statement does not start

- **Artifact**: `_tags_from` ("every tag left at or after token *i*, taken") used by `apply-macro` and `apply-groups`, and the leaf rule "a leaf or leaf-list, never its value".
- **Counterexample**: `apply-macro M1 { k1 v1; inactive: k2 v2; }` tags `M1`; `members 64496:1; inactive: members 64496:2;` tags both values. XML refuses the leaf-list case (change A).
- **User impact**: active configuration silently deactivated; XML and curly disagree on the same shape.
- **Proposed correction**: keep such a statement whole and report it (the `entry-keys` "kept whole" rule), or refuse it as XML does; ask for a device artefact for apply-macro data (`deactivate system apply-macro M1 k2`).
- **Decision**: Pending owner decision

## Not checked

- The full suite, `agent-ready check`, `--regen-schema` and the `--schema` tier over every dump (owner answer 3; the Builder runs them per head).
- Set validation (Lark grammar) after the `h` flag: taken from the delta log (masked grammar identical), not re-derived.
- `SetConverter.to_set()` callers on the consumer surface beyond `structured_to_dict`.
- Anonymize and audit pipelines with tagged input.
