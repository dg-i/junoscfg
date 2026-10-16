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


@pytest.mark.parametrize("command", ["deactivate", "activate", "protect", "delete"])
@pytest.mark.parametrize(
    "path", ["policy-options policy-statement", "policy-options policy-statement P1 term"]
)
def test_a_list_keyword_without_its_entry_cannot_be_tagged(command: str, path: str) -> None:
    """A verb names a statement the device can tag, and a list's keyword
    without its entry's name is none: the QFX5120 25.2R2-S1.5 refuses `protect
    policy-options policy-statement` ("syntax error, expecting <identifier>",
    probe D5). The set reader tagged the whole list and wrote the line back,
    so junoscfg's set output failed its own `-v` (Test/Challenge S7, change
    device-probe-fixes). The reader and the validator share one walk
    (`junoscfg.display.meta_target`)."""
    source = f"set policy-options policy-statement P1 term T1 then accept\n{command} {path}"
    with pytest.raises(ValueError, match="a list without its entry's name"):
        to_dict(source, "set")
