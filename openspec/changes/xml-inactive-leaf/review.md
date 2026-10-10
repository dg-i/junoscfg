## Specification challenges

Raised by the independent Test/Challenge role (`test-challenge.md`, 2026-10-10,
fresh context-isolated agent, worktree at 7a60907). Interim actions are the
Builder's safe, reversible steps under existing architecture (`ARCHITECTURE.md`
one-IR rule); the owner decides each.

### S1 — "Presence flag" was decided without the schema

- **Artifact**: requirement "An inactive leaf from XML reaches the IR set and structured input give"; `display/to_yaml.py::_xml_children_to_dict`.
- **Counterexample**: executed: `<protocols><lldp inactive="inactive"/></protocols>` gave `[null]` + `@lldp`; set and structured input and master's XML input give `{"lldp": {"@": {"inactive": true}}}`.
- **User impact**: JSON/YAML output from XML differed from the same configuration read as set; set and curly output kept the meaning.
- **Proposed correction**: decide leaf versus empty container from the structure tree (`l`/`p`); add a scenario.
- **Decision**: Pending owner decision. Interim action taken (one-IR rule): `_holds_a_value` asks the tree; an untagged empty element stays `[null]` as on master; scenario "Empty tagged container" and `tests/test_xml_inactive_leaf_challenge.py::test_an_empty_inactive_container_matches_set_input` added; the challenger's strict xfail is promoted.

### S2 — The JSON scenario cited the device JSON but used a string

- **Artifact**: scenario "Single inactive leaf".
- **Counterexample**: `deactivate6.txt` writes `"vlan-id" : 751`; JSON input keeps the number, so the four IRs differ by type, while set output agrees (`test_device_json_with_a_number_value_writes_the_same_set_lines_as_xml`).
- **User impact**: none on set or curly output; the scenario claimed more than the device's JSON reaches.
- **Proposed correction**: say so in the scenario; JSON input's numbers are follow-up 6 in `private_test_data/meta-tag-follow-ups.md`.
- **Decision**: Pending owner decision. Interim action taken: scenario wording only.

### S3 — The whole-leaf-list requirement stopped at the IR

- **Artifact**: requirement "An inactive leaf-list is inactive as a whole".
- **Counterexample**: executed: structured output writes `members [ … ];` without the tag, from XML (this change's IR) as from set input (pre-existing writer gap).
- **User impact**: XML or set → structured output silently re-activates a deactivated leaf-list on load.
- **Proposed correction**: the curly writer keeps the tag; that writer is change B's scope.
- **Decision**: Pending owner decision. Interim action: fixed in change B (`meta-tag-placement`); here the challenger's test stays a strict xfail naming B.

### Low findings without a spec change

- The refusal message for uneven tags said "inactive" for uneven `protect`; it now says "tags".
- A comment node inside a leaf element raises an lxml `ValueError`; no device writes it; carried forward as not checked against master.
