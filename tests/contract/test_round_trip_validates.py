"""junoscfg accepts what junoscfg produces.

No test did this before. Conversion had its tests, validation had its tests,
and nothing ran the two in sequence -- so the JSON and YAML schemas rejected
the converter's own output for every configuration carrying a named list, a
presence flag, a bare container statement or an `apply-groups`, which is very
nearly all of them. `examples/router1.set`, the synthetic example of the time,
failed eight ways; three real device configurations failed 51, 17 and 38 ways.

Each cause is a separate row of the shape catalogue, so a regression names
the one that came back. The example is now the device's own
(`examples/junoscfg-oracle.*`), held here by `TestTheExampleRendersValid`.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from junoscfg import Format, convert_config
from tests.support.devices import example
from tests.support.shapes import BY_NAME, SHAPES, Shape

VALID = [shape for shape in SHAPES if shape.valid]
INVALID = [shape for shape in SHAPES if not shape.valid]


def _rendering(shape: Shape, fmt: Format) -> str:
    reader = next(iter(shape.sources))
    return convert_config(shape.sources[reader], from_format=reader, to_format=fmt)


def _errors(validator: Any, rendered: str, fmt: Format) -> list[Any]:
    """The bundled schema's errors: yaml-new is judged as the JSON it spells."""
    validate = {
        Format.JSON: validator.validate_json,
        Format.YAML: validator.validate_yaml,
        Format.YAML_NEW: validator.validate_yaml_as_json,
    }[fmt]
    return list(validate(rendered).errors)


#: Each rendering a schema judges: JSON, YAML and yaml-new.
_SCHEMA_FORMATS = [Format.JSON, Format.YAML, Format.YAML_NEW]
_SCHEMA_IDS = [fmt.value for fmt in _SCHEMA_FORMATS]


class TestTheConverterOutputValidates:
    """Every rendering junoscfg writes of valid input is one junoscfg accepts.

    Over the whole shape catalogue (`tests/support/shapes.py`): the rows
    `a-named-list-key` to `an-overridden-entry-key` are the causes listed
    above, one row each.
    """

    @pytest.mark.parametrize("shape", VALID, ids=[shape.name for shape in VALID])
    @pytest.mark.parametrize("fmt", _SCHEMA_FORMATS, ids=_SCHEMA_IDS)
    def test_the_rendering_validates(
        self, shape: Shape, fmt: Format, bundled_validator: Any
    ) -> None:
        errors = _errors(bundled_validator, _rendering(shape, fmt), fmt)
        assert not errors, f"{shape.name}: {_rendering(shape, fmt)[:200]} -> {errors[:2]}"

    @pytest.mark.parametrize("shape", INVALID, ids=[shape.name for shape in INVALID])
    @pytest.mark.parametrize("fmt", _SCHEMA_FORMATS, ids=_SCHEMA_IDS)
    def test_a_row_that_is_not_valid_junos_is_rejected(
        self, shape: Shape, fmt: Format, bundled_validator: Any
    ) -> None:
        """The converter keeps such input as written; the schema must still say no."""
        assert _errors(bundled_validator, _rendering(shape, fmt), fmt), shape.name

    def test_a_named_list_entry_carries_its_key(self, bundled_validator: Any) -> None:
        """The cause behind most of the eight: 20,363 of 24.4R0's 20,367 named
        lists had no `name` property, so every interface, policy and BGP group
        junoscfg emitted was an unexpected property."""
        rendered = convert_config(
            BY_NAME["a-named-list-key"].sources[Format.SET],
            from_format=Format.SET,
            to_format=Format.JSON,
        )
        entry = json.loads(rendered)["configuration"]["interfaces"]["interface"][0]
        assert entry["name"] == "ge-0/0/0"
        assert not bundled_validator.validate_json(rendered).errors


class TestTheExampleRendersValid:
    """The example a vMX printed, read and written by junoscfg, is one junoscfg accepts.

    `examples/junoscfg-oracle.*` (`tests/data/device/README.md`): the device
    loaded every statement, so each schema error is junoscfg's. Until change
    device-validation five of its statements had no node in the schema model
    (`UNPLACED_IN_THE_EXAMPLE`) and its JSON names `end-range` and
    `ieee-802.3ad` were the model's `to` and `802.3ad`; both renderings were
    strict xfails.
    """

    @pytest.mark.parametrize("fmt", _SCHEMA_FORMATS, ids=_SCHEMA_IDS)
    @pytest.mark.parametrize("suffix", ["xml", "json"])
    def test_the_example_renders_valid(
        self, suffix: str, fmt: Format, bundled_validator: Any
    ) -> None:
        source = example().rendering(suffix)
        reader = Format.XML if suffix == "xml" else Format.JSON
        rendered = convert_config(source, from_format=reader, to_format=fmt)
        assert not _errors(bundled_validator, rendered, fmt)


class TestTheSchemaStillRejects:
    """Accepting junoscfg's own output must not mean accepting anything.

    `properties` and `additionalProperties` are object-only keywords, so the
    moment a container's type union admitted `array` with no `items`, every
    `additionalProperties: false` node -- 52,219 in the 25.2R2 artifact --
    stopped binding anything behind an array wrapper: `{"configuration":
    "garbage"}` validated, and so did a misspelled leaf three lists deep.
    Every case here passed when the round trip was first made to work, which
    is why the round-trip tests above could not tell a correct schema from one
    that accepts everything.
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
            (
                "a set-transparent container given as its child's list",
                {"configuration": {"interfaces": [{"name": "ge-0/0/0", "mtu": 1500}]}},
            ),
            (
                # The keyword is an alias only where the node records an element
                # name; elsewhere a renamed element's names are as unknown as any
                # other (change device-validation, review B1).
                "an element name where nothing was renamed",
                {"configuration": {"system": {"end-range": "x", "ieee-802.3ad": {}}}},
            ),
            (
                "an unknown statement under an undocumented one",
                {
                    "configuration": {
                        "system": {
                            "ddos-protection": {
                                "protocols": {"autoconf": {"aggregate": {"bogus": "1"}}}
                            }
                        }
                    }
                },
            ),
            (
                "an unknown statement beside grpc clear-text's port",
                {
                    "configuration": {
                        "system": {
                            "services": {
                                "extension-service": {
                                    "request-response": {
                                        "grpc": {"clear-text": {"port": "32767", "bogus": "1"}}
                                    }
                                }
                            }
                        }
                    }
                },
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


class TestTheKeywordOfARenameIsAnAlias:
    """junoscfg 0.28.23 and earlier wrote a renamed statement's CLI keyword in JSON
    (`"802.3ad"`, `"to"`), which the JSON reader reads. The JSON schema takes it
    beside the device's element name for good: the QFX5120 25.2R2-S1.5 loads the
    keyword JSON as it loads the element names (probe D3; owner ruling
    2026-10-17, change device-probe-fixes; first change device-validation,
    review B1)."""

    @pytest.mark.parametrize("spelling", ["ieee-802.3ad", "802.3ad"])
    def test_both_spellings_validate(self, spelling: str, bundled_validator: Any) -> None:
        doc = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {"name": "ge-0/0/0", "ether-options": {spelling: {"bundle": "ae0"}}}
                    ],
                    "interface-range": [
                        {"name": "IR-A", "member-range": [{"name": "ge-0/0/2", "to": "ge-0/0/5"}]}
                    ],
                }
            }
        }
        assert not bundled_validator.validate_json(json.dumps(doc)).errors
        assert not bundled_validator.validate_yaml_as_json(json.dumps(doc)).errors


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
