<!-- Complete at the end of phase 2. Later instructions or evidence require a delta consistency check before affected work continues. -->

## Resolved instructions

- Owner prompt `private_test_data/deactivate-fix-prompt.md`, change A: defect 2 at the owning layer (`display/to_yaml.py`), single and repeated leaves and leaf-lists; no per-value marker format (C1, resolved by `deactivate5.txt`).
- Standard lane, type `bug`, zone `kernel` (C2); A and B are separate changes, B stacked on A (C3, owner answer 3); no archive without the owner's go-ahead (C4).
- Owner answer 3: focused tests and the fast check set during A and B; one full check per change head, the independent Test/Challenge work and the fresh Reviewer for A and B together at the end, one `review.md` per change.

## Requirements

- `specs/conversion/meta-tags/spec.md`: "An inactive leaf from XML reaches the IR set and structured input give"; "An inactive leaf-list is inactive as a whole". No existing requirement is contradicted: no main spec names meta tags (`grep -rl inactive openspec/specs` is empty).

## Evidence

- `private_test_data/deactivate2.txt`: `<vlan-id inactive="inactive">751</vlan-id>`, set `deactivate … unit 751 vlan-id`; nested inactive unit + leaf.
- `private_test_data/deactivate5.txt`: the CLI rejects `deactivate policy-options community C1 members 64496:2` (`syntax error, expecting ';'`).
- Probe (scratchpad, test-data values): XML gives `{"vlan-id": {"@": …, "vlan-id": ["751"]}}` and `set … vlan-id vlan-id 751`; set input gives `"vlan-id": "751"` + `"@vlan-id"`; XML leaf-list with one tagged value nests `{"@": …, "members": ["64496:2"]}` inside the list.
- Owning code: `_xml_single_element` and `_xml_multi_elements` in `src/junoscfg/display/to_yaml.py`, called by `_xml_children_to_dict`.

## Non-goals

As `proposal.md`: tag placement on one-line curly statements, the curly writer, print flags and `homogeneous` containers (change B); set input's acceptance of `deactivate … members <value>` (raised in B's preflight); a per-value marker format.

## Acceptance criteria

- The five test ids in the delta fail before the fix and pass after it; existing XML, set and structured tests stay green.
- Independent Test/Challenge evidence on the tests and a fresh Reviewer verdict (`balanced`, yellow zone), run together with change B's at the end (owner answer 3).

## Performance expectations

None, because the change replaces one dict shape with another on the same walk.

## Outstanding decisions

- D1: how the device writes a whole inactive leaf-list in XML and JSON (`deactivate policy-options community C1 members`): one tag on every `<members>` element, or one only? The second requirement's "every value tagged" reading rests on it.
- D2: the device JSON for an inactive leaf with a value (`deactivate2.txt` has XML and set only); the IR's sibling `@vlan-id` follows Junos JSON's attribute convention, not a capture.

## Execution and checkpoint

- Assurance preference: balanced
- Risk floor: normal (yellow zone, one package, no surface break)
- Roles required: Builder; independent Test/Challenge; fresh Reviewer; Finalizer
- Resume point: phase 2 closes when D1 and D2 are answered; then phase 4

## Delta log

<!-- Append source, change, consistency result, invalidated work, and rerun required. -->

- Freeze drafted on `change/xml-inactive-leaf` after 69c1684, with D1 and D2 outstanding.
