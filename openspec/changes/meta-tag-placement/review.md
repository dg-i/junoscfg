## Specification challenges

Raised by the independent Test/Challenge role (`test-challenge.md`, 2026-10-10,
fresh context-isolated agent, worktree at 0c9e24d). Interim actions are the
Builder's safe, reversible steps under the frozen rule (a tag marks the node its
statement starts) and the one-IR rule; the owner decides each.

### S1 — Where an entry starts when its list keyword opens a block

- **Artifact**: requirement "A tag on a curly statement marks the node the statement starts"; `set_input._merge_tokens`, list path.
- **Counterexample**: executed: `source-prefix-list { inactive: PL1; PL2; }` raised "a tag inside a key or value" (CLI exit 2; change A's head exits 0). Tagging every level of the device re-export one at a time raised on 122 of them.
- **User impact**: valid device-layout curly refused once one such entry is tagged.
- **Proposed correction**: the level that starts at an entry's key marks the entry.
- **Decision**: Pending owner decision. Interim action taken: every level start is recorded; a tag on an entry's own line marks the entry, and a tag on a list keyword alone on its line marks the whole list (`deactivate … source-prefix-list`, as `inactive: routing-instance {` is `deactivate … routing-instance` in `deactivate6.txt`). The probe now raises on 0 of 3,422 statements. Scenario "Entry inside its list's block" and `test_a_tag_on_a_bare_list_keyword_marks_the_list` added; the challenger's four shapes pass.

### S2 — Round trip of a tagged leaf-list

- **Artifact**: requirement "Structured output puts a tag at the head of its node's line".
- **Counterexample**: executed: two-value `members`, static `next-hop`, `vlan members` with a tag → `members [ … ];` without it (pre-existing on master; reachable from change A's XML IR).
- **User impact**: curly output re-activates a deactivated leaf-list on load, silently.
- **Proposed correction**: the writer keeps the tag (`inactive: members [ … ];`, `deactivate6.txt`).
- **Decision**: Pending owner decision. Interim action taken: `DictWalker` emits the leaf-list's tag after its bracket line; requirement text and test ids extended.

### S3 — A tag on a `family` block widened to every family inside

- **Artifact**: "the child that follows it in the same statement" and "reported from any input".
- **Counterexample**: executed: `inactive: family { inet {…} inet6; }` tagged both families, no diagnostic.
- **User impact**: more deactivated than written, silently; other inputs report it.
- **Proposed correction**: pass the tag only within one level.
- **Decision**: Pending owner decision. Interim action taken: as proposed; a lone `family` level keeps the tag and field validation reports it; structured input added to the "every input" test.

### S4 — Widening onto a node the statement does not start

- **Artifact**: `_tags_from` in the `apply-macro` and `apply-groups` paths; the leaf rule.
- **Counterexample**: executed: `apply-macro M1 { k1 v1; inactive: k2 v2; }` tagged `M1`; `members 64496:1; inactive: members 64496:2;` tagged both values.
- **User impact**: active configuration deactivated silently; XML refuses the leaf-list shape.
- **Proposed correction**: keep whole and report, or refuse as XML does.
- **Decision**: Pending owner decision. Interim action taken: a tagged `apply-macro` data line is kept whole and reported (UNPLACED), as in change A; uneven tags across one leaf's values in curly input raise `ValueError`, as XML input does. No device artefact for `apply-macro` data tags yet (`deactivate system apply-macro M1 k2`).

### Low findings

- JSON `"@family"` beside `family` was reported UNPLACED but dropped from set output; set output now repeats it (`test_set_output_repeats_a_sibling_family_tag_from_json`).
- `test_a_tagged_child_is_not_joined` asserted the `then {` layout; it now asserts the IR, keeping the "no tag mid-line" check.
- A rebase onto change A's fixes left one call to the renamed `_get_inactive_attrs` in `display/to_yaml.py`; corrected before any run.
