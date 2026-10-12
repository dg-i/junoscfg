from __future__ import annotations

import pytest

from junoscfg.convert import to_dict


@pytest.mark.parametrize("command", ["deactivate", "activate", "protect", "delete"])
@pytest.mark.parametrize(
    ("path", "first", "second", "tail"),
    [
        ("system apply-groups", "G1", "G2", "G1"),
        ("policy-options community C1 members", "64496:1", "64496:2", "64496:2"),
        ("system host-name", "router1", "router1", "router2 extra"),
    ],
)
def test_a_scalar_value_target_cannot_tag_the_whole_leaf(
    command: str, path: str, first: str, second: str, tail: str
) -> None:
    """Held P9/deactivate5 rejection; other verbs/scalars are IR limitations."""
    source = f"set {path} {first}\nset {path} {second}\n{command} {path} {tail}"
    with pytest.raises(ValueError, match="scalar.leaf"):
        to_dict(source, "set")
