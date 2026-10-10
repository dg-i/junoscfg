# Test/Challenge report

## Challenger

Independent Test/Challenge role (fresh `general-purpose` agent, `claude-opus-5-5`), 2026-10-10.
Inputs: this change folder, `git diff 6635b11..7a60907`, `ARCHITECTURE.md` §1, `AGENTS.md`,
`src/junoscfg/display/CONTRACT.md`, the cited tests, and the device captures
`private_test_data/deactivate{,2,3,4,5,6}.txt` (read, values not copied). No product code,
spec or approved test was edited. Adversarial tests: `tests/test_meta_tags_challenge.py`
(new, untracked; 8 pass, 3 strict-xfail).

## Verdict on the acceptance tests

| Test id | Verdict | Reason |
|---|---|---|
| `test_characterization.py::TestXmlAndStructuredInputAgreeOnTheIr::test_an_inactive_leaf_reaches_one_ir` | keep, tighten | Compares the unit across XML, JSON, set and structured: fails on regression. The JSON fixture writes `"vlan-id": "751"`, but the device JSON the spec cites writes a number (`deactivate6.txt`, D2 in the evidence freeze), so the "device JSON" door is not exercised; with the number, JSON input keeps `751` (int) and the IRs differ. Set output agrees (guard added: `test_device_json_with_a_number_value_writes_the_same_set_lines_as_xml`). Either use the device's number and state the known follow-up, or drop "device's JSON" from the scenario |
| `…::test_an_inactive_unit_and_leaf_reach_one_ir` | keep | Same, with the unit tag; discriminating |
| `test_to_yaml.py::TestInactiveLeaf::test_an_inactive_presence_flag_matches_set_input` | keep, missing sibling | Correct for a presence flag. Missing: an empty *container* with the tag (`<lldp inactive="inactive"/>`), which the same code path now reads as a presence flag — see the first adversarial test |
| `test_to_yaml.py::TestInactiveLeaf::test_an_inactive_leaf_list_takes_one_marker` | keep, tighten | Asserts only `xml_to_dict`. Does not reach any writer; structured output of this IR silently loses the tag (adversarial test 3). Add a set-output assertion (added as a guard) and a structured round trip |
| `test_to_yaml.py::TestInactiveLeaf::test_a_partly_inactive_leaf_list_is_refused` | keep | Discriminating. Doors `convert_config_result` and CLI (exit 2) added as guards; both pass |
| `test_cli.py::TestInactiveXmlLeaf::test_set_output_deactivates_the_leaf` | keep | Exact set lines = meaning here |

## Adversarial tests

Commands are run inside the worktree; probes live in the session scratchpad (`probe/p1.py`, `p2.py`).

1. **Empty inactive container** — `<protocols><lldp inactive="inactive"/></protocols>` (also `<system><services inactive="inactive"/></system>`).
   Expected (one-IR rule; set and structured input; master's XML input): `"lldp": {"@": {"inactive": true}}`.
   Observed: `"lldp": [null], "@lldp": {"inactive": true}`; master gave `{"@": …}`, so this change moved XML away from set input. Set output is still `set protocols lldp` / `deactivate protocols lldp` (meaning kept there); JSON/YAML output and XML→structured→XML differ.
   Command: `uv run --locked pytest -q tests/test_meta_tags_challenge.py -k empty_inactive_container` (2 strict-xfail; 1 guard passes). **Product defect** (A regression of IR agreement).
2. **Partly tagged leaf-list at every door** — `convert_config_result` raises `ValueError` naming `members`; CLI prints `Error: Invalid XML: <members> …` and exits 2. Passes. Command: `uv run --locked pytest -q tests/test_meta_tags_challenge.py -k partly`.
3. **Whole inactive leaf-list → structured output** — `LEAF_LIST_XML` (both values tagged, `deactivate6.txt` lines 29–36 shape).
   Expected (device curly, `deactivate6.txt` line 20): `inactive: members [ … ];`.
   Observed: `members [ 64496:1 64496:2 ];`, no tag, no diagnostic; read back the tag is gone. Pre-existing writer gap (set input reaches it too), now reachable from XML.
   Command: `… -k survives_structured_output` (strict-xfail). **Product defect**, owned by the curly writer (change B).
4. **Whole inactive leaf-list → set output** — three lines, one `deactivate … members`. Passes.
5. **One-value inactive leaf-list** — XML, set and device-shaped JSON give one IR (`["64496:1"]` + `@members`). Passes.
6. **Namespaced `junos:inactive`** and **`<undocumented>` wrapper** on a leaf — both mark the leaf. Pass.
7. **Device JSON number** — `"vlan-id": 751` + `@vlan-id` writes the same set lines as XML. Passes (IR differs: int vs string, known follow-up in change B's delta log).
8. Probes not turned into tests (scratchpad `probe/p1.py`, run in this worktree):
   - `inactive="yes"` is ignored silently (not device output; no action).
   - Whitespace-only text with `inactive` reads as a presence flag `[null]` (not device output).
   - Two `<no-redirects>` siblings, one tagged, raise the leaf-list `ValueError` (not device output; acceptable).
   - `inactive` on a `<name>` key element writes `deactivate … name` (not device output; was worse on master).
   - A comment node inside a leaf element (`<host-name>router1<!-- c --></host-name>`) raises `ValueError: Invalid input tag of type <cython function>`, an lxml internals message. Not device output and not checked against master; low.
   - `protect="protect"` is still dropped on this head (expected: change B adds it). A leaf-list where values carry `inactive` evenly but `protect` unevenly passes here and is refused on B with a message that says "inactive" (see B's report).

## Specification challenges

### S1 — "Presence flag" is decided without the schema

- **Artifact**: `specs/conversion/meta-tags/spec.md`, requirement "An inactive leaf from XML reaches the IR set and structured input give" (scenario "Inactive presence flag"); `_xml_children_to_dict` treats every childless element as a leaf.
- **Counterexample**: `<protocols><lldp inactive="inactive"/></protocols>` → `[null]` + `@lldp`; `set protocols lldp` + `deactivate protocols lldp` → `{"lldp": {"@": {"inactive": true}}}`; master XML gave the latter.
- **User impact**: JSON/YAML output from XML differs from the same configuration read as set/curly; XML→structured→XML changes the IR. Set and curly output keep the meaning.
- **Proposed correction**: add a scenario for an empty tagged container (expected IR = set input's), and decide leaf vs container from the structure tree (`p`/`l` vs `c`), falling back to today's rule outside the tree. Alternatively ask for a device artefact: `set protocols lldp`, `deactivate protocols lldp`, `show protocols | display json`.
- **Decision**: Pending owner decision

### S2 — The JSON scenario cites the device JSON but uses a string value

- **Artifact**: scenario "Single inactive leaf" ("from the device's JSON (`"vlan-id": "751"` …)") and its test fixture.
- **Counterexample**: `deactivate6.txt` writes `"vlan-id" : 751` (number). With the number, JSON input gives `"vlan-id": 751` and the four IRs are not equal.
- **User impact**: none on set/curly output; the spec claims an equality the device's JSON does not reach.
- **Proposed correction**: write the fixture as the device does and assert set-output equality for the JSON door, or note the number/string follow-up in the scenario.
- **Decision**: Pending owner decision

### S3 — The whole-leaf-list requirement stops at the IR

- **Artifact**: requirement "An inactive leaf-list is inactive as a whole".
- **Counterexample**: the IR it builds is written by structured output as `members [ … ];` without the tag.
- **User impact**: XML → structured output silently activates a deactivated community/next-hop list on load.
- **Proposed correction**: add "and every writer keeps it" with a structured round-trip test; implementation belongs to the curly writer (change B or a follow-up).
- **Decision**: Pending owner decision

## Not checked

- The full suite and `agent-ready check` (owner answer 3: run once per head by the Builder).
- The device re-export through XML input beyond tag counts (2 tags, equal to set and JSON input).
- Python versions other than the worktree venv's.
