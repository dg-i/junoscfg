"""The IR doors: `to_dict`, `from_dict` and `find_configuration`.

That a reader and a writer agree on the IR, for every pair, is
`tests/contract/test_format_matrix.py`; this file keeps what the dispatch
doors decide themselves: where the configuration is found, the envelope a
writer wraps it in, that no writer changes the IR it is given, the order of
the JSON writer's keys, and what is refused.
"""

from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING, Any

import pytest
import yaml

from junoscfg import Format, convert_config, validate_config
from junoscfg.convert import find_configuration, from_dict, to_dict
from tests.support.artifacts import using_tree
from tests.support.shapes import BY_NAME, SHAPES, WRITERS

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


# ── IR utilities ─────────────────────────────────────────────────────


class TestFindConfiguration:
    def test_standard_wrapper(self) -> None:
        data = {"configuration": {"system": {"host-name": "r1"}}}
        assert find_configuration(data) == {"system": {"host-name": "r1"}}

    def test_rpc_reply_wrapper(self) -> None:
        data = {"rpc-reply": {"configuration": {"system": {"host-name": "r1"}}}}
        assert find_configuration(data) == {"system": {"host-name": "r1"}}

    def test_bare_content(self) -> None:
        data = {"system": {"host-name": "r1"}, "interfaces": {}}
        assert find_configuration(data) == data

    def test_no_configuration(self) -> None:
        assert find_configuration({"foo": "bar"}) is None

    def test_non_dict(self) -> None:
        assert find_configuration([1, 2, 3]) is None


class TestTheJsonAndYamlEnvelope:
    """JSON and YAML output wrap the IR in `configuration`, unless told not to."""

    @pytest.mark.parametrize(
        ("fmt", "load"), [("json", json.loads), ("yaml", yaml.safe_load)], ids=["json", "yaml"]
    )
    def test_the_ir_is_wrapped_in_configuration(self, fmt: str, load: Callable[[str], Any]) -> None:
        config = {"system": {"host-name": "r1"}}
        assert load(from_dict(config, fmt)) == {"configuration": config}
        assert load(from_dict(config, fmt, wrap=False)) == config


# ── Every writer ─────────────────────────────────────────────────────

_SSH_FLAG = {"system": {"services": {"ssh": [None]}}}
_ADMIN = {"name": "admin", "class": ["super-user"]}
_ADMIN_JSON = {"name": "admin", "class": "super-user"}

#: name -> (an IR spelling a caller may build, its JSON `configuration`); None
#: where no device rendering decides the output, so only purity is asserted.
_HAND_BUILT: dict[str, tuple[Any, Any]] = {
    "a-presence-flag-as-true": ({"system": {"services": {"ssh": True}}}, _SSH_FLAG),
    "a-presence-flag-as-an-empty-mapping": ({"system": {"services": {"ssh": {}}}}, _SSH_FLAG),
    # The JSON and YAML readers give it; its device output is open (NEW-R2, change 13).
    "a-presence-flag-inside-a-list": ({"system": {"services": {"ssh": [True]}}}, None),
    "a-tagged-presence-flag": (
        {"system": {"services": {"ssh": True, "@ssh": {"inactive": True}}}},
        {"system": {"services": {"ssh": [None], "@ssh": {"inactive": True}}}},
    ),
    "a-leaf-as-a-one-element-list": (
        {"system": {"login": {"user": [_ADMIN]}}},
        {"system": {"login": {"user": [_ADMIN_JSON]}}},
    ),
    "a-group-in-its-wrapper": (
        {"groups": {"group": [{"name": "G1", "system": {"services": {"ssh": True}}}]}},
        {"groups": [{"name": "G1", **_SSH_FLAG}]},
    ),
    "a-one-element-list-in-a-wrapped-group": (
        {"groups": {"group": [{"name": "G1", "system": {"login": {"user": [_ADMIN]}}}]}},
        {"groups": [{"name": "G1", "system": {"login": {"user": [_ADMIN_JSON]}}}]},
    ),
    "a-group-list-as-json-reads-it": (
        {"groups": [{"name": "G1", "system": {"services": {"ssh": {}}}}]},
        {"groups": [{"name": "G1", **_SSH_FLAG}]},
    ),
    "a-flag-four-lists-deep": (
        {
            "interfaces": {
                "interface": [
                    {
                        "name": "ge-0/0/0",
                        "unit": [
                            {
                                "name": "0",
                                "family": {
                                    "inet": {
                                        "address": [{"name": "198.51.100.1/24", "primary": True}]
                                    }
                                },
                            }
                        ],
                    }
                ]
            }
        },
        {
            "interfaces": {
                "interface": [
                    {
                        "name": "ge-0/0/0",
                        "unit": [
                            {
                                "name": "0",
                                "family": {
                                    "inet": {
                                        "address": [{"name": "198.51.100.1/24", "primary": [None]}]
                                    }
                                },
                            }
                        ],
                    }
                ]
            }
        },
    ),
    # A leaf-list is never coerced: a fix that coerces it changes what is applied.
    "a-leaf-list-with-one-value": (
        {"apply-groups": ["G1"], "system": {"host-name": "router1"}},
        {"apply-groups": ["G1"], "system": {"host-name": "router1"}},
    ),
}

#: Every writer door; `wrap` reaches only the JSON and the two YAML writers.
_WRITER_DOORS = [
    pytest.param("set", {}, id="set"),
    pytest.param("structured", {}, id="structured"),
    pytest.param("json", {}, id="json"),
    pytest.param("json", {"wrap": False}, id="json-bare"),
    pytest.param("yaml", {}, id="yaml"),
    pytest.param("yaml", {"wrap": False}, id="yaml-bare"),
    pytest.param("yaml-new", {}, id="yaml-new"),
    pytest.param("yaml-new", {"wrap": False}, id="yaml-new-bare"),
]


class TestNoWriterChangesTheIrItIsGiven:
    """A writer reads the IR and never writes into it (spec conversion/writers).

    ARCH-C11: the JSON writer normalized presence flags and one-element leaf
    lists in the caller's IR. `repr` is compared, so a changed key order or
    `True` turned into `[None]` counts. The contract tests cannot state this
    law: the named surfaces read a fresh IR, and only this door takes one a
    caller holds. `pipeline_result` renders relative output with `wrap=False`,
    so the bare doors are rows of their own.
    """

    @pytest.mark.parametrize(("fmt", "options"), _WRITER_DOORS)
    @pytest.mark.parametrize("name", list(_HAND_BUILT))
    def test_a_hand_built_ir_is_left_unchanged(
        self, name: str, fmt: str, options: dict[str, Any]
    ) -> None:
        spelling = _HAND_BUILT[name][0]
        ir = copy.deepcopy(spelling)
        output = from_dict(ir, fmt, **options)
        assert repr(ir) == repr(spelling)
        assert output == from_dict(copy.deepcopy(spelling), fmt, **options)

    @pytest.mark.parametrize(("fmt", "options"), [door for door in _WRITER_DOORS if door.values[1]])
    @pytest.mark.parametrize(
        "selection",
        [
            [{"explicit-priority": {}, "name": "198.51.100.9", "contents": [{"any": True}]}],
            [{"name": "198.51.100.10", "@": {"inactive": True}, "explicit-priority": True}],
            [True],
            {},
            True,
        ],
        ids=["a-list", "an-annotated-list", "a-list-of-true", "empty", "true"],
    )
    def test_a_bare_selection_is_left_unchanged(
        self, selection: Any, fmt: str, options: dict[str, Any]
    ) -> None:
        """A relative selection that is not a mapping is the writer's input too:
        its flags are spelled on the writer's copy (Test/Challenge finding 3)."""
        held = copy.deepcopy(selection)
        output = from_dict(held, fmt, **options)
        assert repr(held) == repr(selection)
        assert output == from_dict(copy.deepcopy(selection), fmt, **options)

    @pytest.mark.parametrize(
        "name", [name for name, (_, expected) in _HAND_BUILT.items() if expected is not None]
    )
    def test_the_json_writer_writes_the_device_spelling(self, name: str) -> None:
        """Purity is not bought by skipping a pass: the output stays normalized."""
        spelling, expected = _HAND_BUILT[name]
        output = json.loads(from_dict(copy.deepcopy(spelling), "json"))
        assert repr(output["configuration"]) == repr(expected)

    @pytest.mark.parametrize(
        ("source", "reader"),
        [
            pytest.param(text, reader, id=f"{shape.name}-{reader.value}")
            for shape in SHAPES
            for reader, text in shape.sources.items()
        ],
    )
    def test_a_read_ir_is_left_unchanged(self, source: str, reader: Format) -> None:
        ir = to_dict(source, reader.value)
        read = copy.deepcopy(ir)
        for writer in WRITERS:
            from_dict(ir, writer.value)
            assert repr(ir) == repr(read), f"after {writer.value}"


# ── JSON output ──────────────────────────────────────────────────────


class TestJsonOutput:
    def test_a_leaf_annotation_follows_its_leaf(self) -> None:
        """@leaf-name must appear directly after its leaf in JSON output (Junos spec)."""
        # Simulate IR where @virtual-gateway-address is inserted before the leaf
        # (the order _ensure_name_first used to produce).
        ir = {
            "interfaces": {
                "interface": [
                    {
                        "name": "irb",
                        "unit": [
                            {
                                "name": "20",
                                "family": {
                                    "inet": {
                                        "address": [
                                            {
                                                "@virtual-gateway-address": {"inactive": True},
                                                "name": "10.2.16.13/20",
                                                "virtual-gateway-address": "10.2.16.1",
                                            }
                                        ]
                                    }
                                },
                            }
                        ],
                    }
                ]
            }
        }
        output = from_dict(ir, "json")
        addr = json.loads(output)["configuration"]["interfaces"]["interface"][0]["unit"][0][
            "family"
        ]["inet"]["address"][0]
        keys = list(addr.keys())
        vga_idx = keys.index("virtual-gateway-address")
        at_vga_idx = keys.index("@virtual-gateway-address")
        assert at_vga_idx == vga_idx + 1, (
            "@virtual-gateway-address must immediately follow virtual-gateway-address"
        )


# ── Refusals ─────────────────────────────────────────────────────────


class TestAReaderRefusesADocumentWithoutAConfiguration:
    @pytest.mark.parametrize(
        ("fmt", "source", "match"),
        [
            ("json", '{"foo": "bar"}', "No 'configuration' key"),
            ("yaml", "foo: bar\n", "No 'configuration' key"),
            ("yaml", "", "empty"),
            ("xml", "<root><foo/></root>", "configuration"),
        ],
        ids=["json", "yaml", "empty-yaml", "xml"],
    )
    def test_the_reader_refuses(self, fmt: str, source: str, match: str) -> None:
        with pytest.raises(ValueError, match=match):
            to_dict(source, fmt)


class TestXmlOutputStub:
    def test_xml_output_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError, match="XML output"):
            from_dict({"system": {}}, "xml")


class TestUnknownFormat:
    def test_unknown_input_format(self) -> None:
        with pytest.raises(ValueError, match="Unknown input format"):
            to_dict("data", "protobuf")

    def test_unknown_output_format(self) -> None:
        with pytest.raises(ValueError, match="Unknown output format"):
            from_dict({}, "protobuf")


class TestAPolicyChainIsWrittenAsTheDevicesTokens:
    """Curly output of a policy chain writes each value as the device's token.

    `dict_walker`'s bracket path passed no node, so an expression in a chain
    was written as a quoted name, another policy (Test/Challenge F1; spec
    conversion/value-quoting). Reading it back from curly is specification
    challenge SC1 (`tests/unit/display/test_set_converter.py`).
    """

    def test_an_expression_in_a_chain_is_written_bare(self) -> None:
        config = {"protocols": {"bgp": {"group": [{"name": "G", "import": ["( P-A )", "P-B"]}]}}}
        output = from_dict(config, "structured")
        assert "import [ ( P-A ) P-B ];" in output
        assert '"( P-A )"' not in output


class TestAFlatHintPreservesRicherContent:
    @pytest.mark.parametrize("writer", ["set", "structured"])
    @pytest.mark.parametrize(
        "value",
        [{"nested": {"up": "100"}}, {"members": ["A", "B"]}],
        ids=["nested-mapping", "leaf-list"],
    )
    def test_nested_content_is_not_discarded(
        self, tmp_path: Path, writer: str, value: dict[str, Any]
    ) -> None:
        """NEW-B3: even a stale or external flat hint cannot discard a richer child."""
        tree = {
            "c": {
                "trigger": {
                    "fd": True,
                    "c": {"nested": {"c": {"up": {"l": True}}}, "members": {"l": True, "ll": True}},
                }
            }
        }
        config = {"trigger": value}
        with using_tree(tmp_path, tree):
            output = from_dict(config, writer)
            assert to_dict(output, writer) == config
            if "nested" in value:
                assert "100" in output
            else:
                assert "A" in output and "B" in output


class TestKeyedSingletonMetadata:
    """Device array paths use list traversal; no second-entry validity claim."""

    @pytest.mark.parametrize(
        "path",
        [
            (
                "forwarding-options",
                "port-mirroring",
                "family",
                "inet",
                "output",
                "routing-instance",
            ),
            ("protocols", "mpls", "label-range", "srgb-label-range"),
            ("protocols", "isis", "interface", "level", "application-specific", "attribute-group"),
        ],
    )
    @pytest.mark.parametrize("prefix", [(), ("groups", "group")])
    def test_device_backed_slots_are_lists(
        self, bundled_tree: dict, path: tuple, prefix: tuple
    ) -> None:
        node = bundled_tree
        for name in prefix + path:
            node = node["c"][name]
        assert node.get("L") is True
        assert node["c"]["name"].get("nk") is True
        assert len(node["c"]) > 1

    @pytest.mark.parametrize(
        "path",
        [
            ("routing-options", "transport-class"),
            ("snmp",),
            ("protocols", "bgp", "traceoptions", "file", "filename"),
            ("forwarding-options", "port-mirroring", "family"),
        ],
    )
    def test_ordinary_containers_keep_their_classification(
        self, bundled_tree: dict, path: tuple
    ) -> None:
        node = bundled_tree
        for name in path:
            node = node["c"][name]
        assert not node.get("L")


class TestKnownContainerNames:
    """A known container keeps keyworded name; missing schema keeps legacy fallback."""

    def test_name_and_siblings_are_written_separately(self) -> None:
        config = {"snmp": {"name": "sw1", "location": "lab"}}
        before = copy.deepcopy(config)
        assert from_dict(config, "set").splitlines() == [
            "set snmp name sw1",
            "set snmp location lab",
        ]
        assert config == before

    def test_an_unknown_schema_retains_the_entry_fallback(self) -> None:
        config = {"unknown-entry": {"name": "X", "location": "lab"}}
        before = copy.deepcopy(config)
        assert from_dict(config, "set") == "set unknown-entry X location lab\n"
        assert config == before


class TestKeyedSingletonValidation:
    """Committed device lines validate through runtime doors; XML XSD is not bundled."""

    @pytest.mark.parametrize(
        "shape_name",
        [
            "a-keyed-singleton-port-mirroring-entry",
            "a-keyed-singleton-srgb-range",
            "a-keyed-singleton-attribute-group",
        ],
    )
    @pytest.mark.parametrize("fmt", [Format.SET, Format.STRUCTURED, Format.JSON, Format.YAML])
    def test_supported_statement_validates(self, shape_name: str, fmt: Format) -> None:
        result = validate_config(BY_NAME[shape_name].sources[fmt], format=fmt)
        assert result.valid, result.errors


class TestSingletonNamePreservation:
    """Accepted SC1 C: preserve an existing single entry, without device/cardinality claims."""

    @pytest.mark.parametrize("prefix", ["", "groups G1 "])
    @pytest.mark.parametrize("writer", WRITERS)
    def test_a_scalar_positional_name_keeps_its_child_key(
        self, prefix: str, writer: Format
    ) -> None:
        source = "set " + prefix + "access securid-server SRV-A configuration-file sample-1\n"
        before = json.loads(convert_config(source, from_format=Format.SET, to_format=Format.JSON))[
            "configuration"
        ]
        output = convert_config(source, from_format=Format.SET, to_format=writer)
        assert (
            json.loads(convert_config(output, from_format=writer, to_format=Format.JSON))[
                "configuration"
            ]
            == before
        )
        if writer in (Format.SET, Format.STRUCTURED):
            assert convert_config(output, from_format=writer, to_format=Format.SET) == source
        if writer is Format.SET:
            assert output == source

    @pytest.mark.parametrize("writer", WRITERS)
    @pytest.mark.parametrize(
        "source",
        [
            "set snmp name sw1\nset snmp location lab\n",
            "set routing-options transport-class name gold color 4000\n"
            "set routing-options transport-class name bronze color 6000\n"
            "set routing-options transport-class auto-create\n",
        ],
    )
    def test_an_ordinary_name_child_keeps_all_children(self, source: str, writer: Format) -> None:
        before = json.loads(convert_config(source, from_format=Format.SET, to_format=Format.JSON))[
            "configuration"
        ]
        output = convert_config(source, from_format=Format.SET, to_format=writer)
        assert (
            json.loads(convert_config(output, from_format=writer, to_format=Format.JSON))[
                "configuration"
            ]
            == before
        )
        if writer in (Format.SET, Format.STRUCTURED):
            assert convert_config(output, from_format=writer, to_format=Format.SET) == source


class TestKnownNameChildShapes:
    """Independent SC1 C shape controls; ambiguity is preserved, not an identifier proof."""

    @pytest.mark.parametrize(
        "name_schema,value,expected",
        [
            ({"l": True}, "X", ["set node name X", "set node child Y"]),
            (
                {"L": True, "c": {"name": {"l": True, "nk": True}, "value": {"l": True}}},
                [{"name": "X", "value": "Z"}],
                ["set node name X value Z", "set node child Y"],
            ),
            (
                {"c": {"label": {"l": True}}},
                {"label": "X"},
                ["set node name label X", "set node child Y"],
            ),
            (
                {"l": True, "ll": True},
                ["X", "Z"],
                ["set node name X", "set node name Z", "set node child Y"],
            ),
            ({"p": True}, [None], ["set node name", "set node child Y"]),
            ({"l": True, "nk": True}, "X", ["set node X child Y"]),
        ],
    )
    def test_the_known_child_shape_keeps_meaning(
        self, tmp_path: Path, name_schema: dict, value: Any, expected: list[str]
    ) -> None:
        tree = {"c": {"node": {"c": {"name": name_schema, "child": {"l": True}}}}}
        config = {"node": {"name": value, "child": "Y"}}
        before = copy.deepcopy(config)
        with using_tree(tmp_path, tree):
            output = from_dict(config, "set")
        assert output.splitlines() == expected
        assert config == before

    def test_an_unkeyed_homogeneous_container_keeps_children(self, tmp_path: Path) -> None:
        tree = {"c": {"node": {"h": True, "c": {"child": {"l": True}}}}}
        with using_tree(tmp_path, tree):
            assert from_dict({"node": {"child": "Y"}}, "set") == "set node child Y\n"
