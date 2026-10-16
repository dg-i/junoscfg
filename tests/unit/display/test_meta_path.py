"""What a verb line names: `meta_target`, the one walk the set reader and the set
validator share.

A `deactivate`, `protect`, `activate` or `delete` line names a statement by its
path, and the reader places the tag where the walk ends. The device can tag a
container, a list entry after its whole key, and a leaf, leaf-list or flag
before its value; it refuses a list's keyword without its entry's name and a
leaf's value (QFX5120 25.2R2-S1.5, probe D5 and A2,
`tests/data/device/probes/qfx5120-25.2R2-S1.5/2026-10-16.json`). The rows run on
the shipped tree; the lines are the probe's own and the device captures' verb
lines (change device-probe-fixes).
"""

from __future__ import annotations

from typing import Any

import pytest

from junoscfg.display import meta_target
from junoscfg.input import set_tokens

ROUTE = "routing-options static route 198.51.100.0/24"
VIRTUAL_LINK = "protocols ospf area 0.0.0.0 virtual-link neighbor-id 10.255.255.1"

#: (statement path after the verb, what it names)
ROWS = [
    ("routing-options static", "container"),
    (ROUTE, "entry"),
    (f"{ROUTE} description", "leaf"),
    (f"{ROUTE} community", "leaf"),
    (f"{ROUTE} discard", "leaf"),
    ("interfaces ge-0/0/1 unit 200", "entry"),
    ("interfaces ge-0/0/1 unit 300 family inet6", "container"),
    ("interfaces lo0", "entry"),
    ("vlans V999", "entry"),
    ("groups GR-ISIS-TPL protocols isis interface <ge-*> max-hello-size", "leaf"),
    (f"{VIRTUAL_LINK} transit-area 0.0.0.2", "entry"),
    (
        "policy-options policy-statement PS-BGP-MSE-EXPORT term LOOPBACK then community add C1",
        "entry",
    ),
    ("policy-options policy-statement", "list"),
    (f"{ROUTE} community 64496:2", "value"),
    ("system host-name r1", "value"),
    (f"{VIRTUAL_LINK} transit-area", "partial-key"),
    (VIRTUAL_LINK, "partial-key"),
    ("system no-such-statement", "unplaced"),
]


class TestAMetaPathNamesWhatTheReaderTags:
    @pytest.mark.parametrize(("path", "kind"), ROWS, ids=[f"{k}:{p}" for p, k in ROWS])
    def test_the_target(self, bundled_tree: dict[str, Any], path: str, kind: str) -> None:
        assert meta_target(set_tokens(path), bundled_tree).kind == kind

    def test_an_entry_step_carries_its_whole_key(self, bundled_tree: dict[str, Any]) -> None:
        """The walk records each step as the reader places it: a container's
        key, and a list's key with the entry's key fields."""
        target = meta_target(set_tokens(f"{VIRTUAL_LINK} transit-area 0.0.0.2"), bundled_tree)
        assert [(step.key, step.entry) for step in target.steps] == [
            ("protocols", None),
            ("ospf", None),
            ("area", {"name": "0.0.0.0"}),
            ("virtual-link", {"neighbor-id": "10.255.255.1", "transit-area": "0.0.0.2"}),
        ]

    def test_a_list_keyword_is_named_with_its_list_node(self, bundled_tree: dict[str, Any]) -> None:
        target = meta_target(set_tokens("policy-options policy-statement"), bundled_tree)
        assert target.key == "policy-statement"
        assert target.node is not None and target.node.get("L")
