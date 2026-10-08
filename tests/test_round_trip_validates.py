"""junoscfg accepts what junoscfg produces.

No test did this before. Conversion had its tests, validation had its tests,
and nothing ran the two in sequence -- so the JSON and YAML schemas rejected
the converter's own output for every configuration carrying a named list, a
presence flag, a bare container statement or an `apply-groups`, which is very
nearly all of them. `examples/router1.set` failed eight ways; three real device
configurations failed 51, 17 and 38 ways.

The shapes below are each a separate cause, kept as separate tests so a
regression names the one that came back.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from junoscfg import Format, convert_config

if TYPE_CHECKING:
    from pathlib import Path

# One line per cause, with the rendering that used to be rejected.
SHAPES: list[tuple[str, str, str]] = [
    ("named list key", "set interfaces ge-0/0/0 mtu 9192", '"name"'),
    ("statement switch, off", "set interfaces ge-0/0/0 disable", '"disable"'),
    ("statement switch, on", "set interfaces ge-0/0/0 enable", '"enable"'),
    ("presence flag", "set protocols ospf area 0.0.0.0 interface lo0.0 passive", "null"),
    ("bare container", "set system services netconf ssh", "null"),
    ("universal statement", "set system apply-groups GLOBAL", "apply-groups"),
    (
        "flat-entry key",
        "set policy-options policy-statement P term T from route-filter 10.0.0.0/8 orlonger",
        '"address"',
    ),
    (
        "overridden entry key",
        "set policy-options policy-statement P term T then community add COMM-A",
        "community",
    ),
]


class TestTheConverterOutputValidates:
    """Every rendering junoscfg writes is one junoscfg accepts."""

    @pytest.mark.parametrize(("label", "command", "marker"), SHAPES, ids=[s[0] for s in SHAPES])
    @pytest.mark.parametrize("fmt", [Format.JSON, Format.YAML], ids=["json", "yaml"])
    def test_shape_round_trips(
        self, label: str, command: str, marker: str, fmt: Format, bundled_validator: Any
    ) -> None:
        rendered = convert_config(command + "\n", from_format=Format.SET, to_format=fmt)
        errors = (
            bundled_validator.validate_json(rendered)
            if fmt is Format.JSON
            else bundled_validator.validate_yaml(rendered)
        ).errors
        assert not errors, f"{label}: {rendered[:200]} -> {errors[:2]}"

    @pytest.mark.parametrize("fmt", [Format.JSON, Format.YAML], ids=["json", "yaml"])
    def test_the_example_configuration_round_trips(
        self, fmt: Format, bundled_validator: Any, project_root: Path
    ) -> None:
        """`examples/router1.set` failed eight ways, every one its own output."""
        text = (project_root / "examples" / "router1.set").read_text(encoding="utf-8")
        rendered = convert_config(text, from_format=Format.SET, to_format=fmt)
        errors = (
            bundled_validator.validate_json(rendered)
            if fmt is Format.JSON
            else bundled_validator.validate_yaml(rendered)
        ).errors
        assert not errors, errors[:3]

    def test_a_named_list_entry_carries_its_key(self, bundled_validator: Any) -> None:
        """The cause behind most of the eight: 20,363 of 24.4R0's 20,367 named
        lists had no `name` property, so every interface, policy and BGP group
        junoscfg emitted was an unexpected property."""
        rendered = convert_config(
            "set interfaces ge-0/0/0 mtu 9192\n", from_format=Format.SET, to_format=Format.JSON
        )
        entry = json.loads(rendered)["configuration"]["interfaces"]["interface"][0]
        assert entry["name"] == "ge-0/0/0"
        assert not bundled_validator.validate_json(rendered).errors
