"""The IR doors: `to_dict`, `from_dict` and `find_configuration`.

That a reader and a writer agree on the IR, for every pair, is
`tests/contract/test_format_matrix.py`; this file keeps what the dispatch
doors decide themselves: where the configuration is found, the envelope a
writer wraps it in, the order of the JSON writer's keys, and what is refused.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
import yaml

from junoscfg.convert import find_configuration, from_dict, to_dict

if TYPE_CHECKING:
    from collections.abc import Callable

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
