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


class TestTheSchemaStillRejects:
    """Accepting junoscfg's own output must not mean accepting anything.

    `properties` and `additionalProperties` are object-only keywords, so the
    moment a container's type union admitted `array` with no `items`, all
    43,331 `additionalProperties: false` nodes stopped binding anything behind
    an array wrapper -- `{"configuration": "garbage"}` validated, and so did a
    misspelled leaf three lists deep. Every case here passed when the round
    trip was first made to work, which is why the round-trip tests above could
    not tell a correct schema from one that accepts everything.
    """

    @pytest.mark.parametrize(
        ("label", "doc"),
        [
            ("configuration as a bare string", {"configuration": "garbage"}),
            (
                "an unknown statement behind an array wrapper",
                {"configuration": {"system": ["garbage", {"no-such-stmt": 1}]}},
            ),
            (
                "an unknown child inside a list entry",
                {
                    "configuration": {
                        "interfaces": {"interface": [{"name": "ge-0/0/0", "no-such-child": "y"}]}
                    }
                },
            ),
            (
                "a misspelled leaf inside a list entry",
                {"configuration": {"interfaces": {"interface": [{"name": "ge-0/0/0", "mtuu": 9}]}}},
            ),
            (
                "a whole subtree wrapped in an array",
                {"configuration": {"system": [{"host-name": "r1"}]}},
            ),
            (
                "an unknown statement inside a transparent container",
                {"configuration": {"groups": [{"name": "g", "no-such-stmt": 1}]}},
            ),
        ],
    )
    def test_the_bundled_schema_rejects(self, label: str, doc: Any, bundled_validator: Any) -> None:
        assert bundled_validator.validate_json(json.dumps(doc)).errors, f"{label} was accepted"

    def test_a_transparent_container_still_takes_its_child(self, bundled_validator: Any) -> None:
        """`groups` holds `group` entries directly and is ~90% of a real
        configuration. Constraining the array form must not cost that."""
        doc = {"configuration": {"groups": [{"name": "g", "system": {"host-name": "r1"}}]}}
        assert not bundled_validator.validate_json(json.dumps(doc)).errors

    def test_device_attributes_are_accepted(self, bundled_validator: Any) -> None:
        """`| display json` puts `@` on an element and junoscfg round-trips it;
        `field_validator` skips the prefix, so the schema has to name it."""
        doc = {"configuration": {"@": {"junos:commit-seconds": "1"}, "system": {"host-name": "r1"}}}
        assert not bundled_validator.validate_json(json.dumps(doc)).errors


class TestFragmentsWithoutMandatoryFieldsStayValid:
    """The three lines that broke the first attempt at closing the escape.

    Each is valid Junos and each omits a field the XSD marks mandatory (`class`
    on a login user, `events` and `then` on an event policy). The schema's
    `required` arrays were inert behind the escape and went live with it
    closed, rejecting all three. They stay valid: mandatory is a field-validator
    warning, not a structural requirement on a fragment.
    """

    @pytest.mark.parametrize(
        "command",
        [
            "set system login user admin uid 2000",
            'set system login user admin authentication encrypted-password "$9$ExAmPlEhAsH.KEY"',
            "set event-options policy test-policy",
        ],
    )
    def test_the_fragment_validates(self, command: str, bundled_validator: Any) -> None:
        rendered = convert_config(command + "\n", from_format=Format.SET, to_format=Format.JSON)
        assert not bundled_validator.validate_json(rendered).errors, rendered[:200]
