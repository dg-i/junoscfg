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

from junoscfg.convert import find_configuration, from_dict, to_dict
from tests.support.shapes import SHAPES, WRITERS

if TYPE_CHECKING:
    from collections.abc import Callable

    from junoscfg import Format

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

#: Every writer door; `wrap` reaches only the JSON and YAML writers.
_WRITER_DOORS = [
    pytest.param("set", {}, id="set"),
    pytest.param("structured", {}, id="structured"),
    pytest.param("json", {}, id="json"),
    pytest.param("json", {"wrap": False}, id="json-bare"),
    pytest.param("yaml", {}, id="yaml"),
    pytest.param("yaml", {"wrap": False}, id="yaml-bare"),
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
