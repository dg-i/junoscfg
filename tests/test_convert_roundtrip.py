"""Round-trip tests for the convert/ pipeline.

Verifies that format→dict→same_format produces equivalent results.
"""

from __future__ import annotations

import json

import pytest
import yaml

from junoscfg.convert.input import to_dict
from junoscfg.convert.ir import find_configuration, wrap_configuration
from junoscfg.convert.output import from_dict

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


class TestWrapConfiguration:
    def test_wrap(self) -> None:
        config = {"system": {"host-name": "r1"}}
        assert wrap_configuration(config) == {"configuration": config}


# ── JSON round-trip ──────────────────────────────────────────────────


class TestJsonRoundTrip:
    def test_simple(self) -> None:
        original = {"system": {"host-name": "r1"}}
        source = json.dumps({"configuration": original})
        ir = to_dict(source, "json")
        assert ir == original

    def test_to_json_output(self) -> None:
        original = {"system": {"host-name": "r1"}}
        output = from_dict(original, "json")
        parsed = json.loads(output)
        assert parsed == {"configuration": original}

    def test_round_trip(self) -> None:
        original = {
            "system": {"host-name": "r1", "domain-name": "example.com"},
            "interfaces": {"interface": [{"name": "ge-0/0/0", "unit": [{"name": "0"}]}]},
        }
        source = json.dumps({"configuration": original})
        ir = to_dict(source, "json")
        output = from_dict(ir, "json")
        roundtripped = json.loads(output)
        assert roundtripped["configuration"] == original

    def test_with_attributes(self) -> None:
        original = {
            "system": {"host-name": "r1"},
            "@system": {"inactive": True},
        }
        source = json.dumps({"configuration": original})
        ir = to_dict(source, "json")
        output = from_dict(ir, "json")
        roundtripped = json.loads(output)
        assert roundtripped["configuration"] == original

    def test_missing_configuration_raises(self) -> None:
        with pytest.raises(ValueError, match="No 'configuration' key"):
            to_dict('{"foo": "bar"}', "json")


# ── YAML round-trip ──────────────────────────────────────────────────


class TestYamlRoundTrip:
    def test_simple(self) -> None:
        source = "configuration:\n  system:\n    host-name: r1\n"
        ir = to_dict(source, "yaml")
        assert ir == {"system": {"host-name": "r1"}}

    def test_to_yaml_output(self) -> None:
        original = {"system": {"host-name": "r1"}}
        output = from_dict(original, "yaml")
        parsed = yaml.safe_load(output)
        assert parsed == {"configuration": original}

    def test_round_trip(self) -> None:
        original = {
            "system": {"host-name": "r1", "domain-name": "example.com"},
        }
        source = yaml.dump({"configuration": original})
        ir = to_dict(source, "yaml")
        output = from_dict(ir, "yaml")
        roundtripped = yaml.safe_load(output)
        assert roundtripped["configuration"] == original

    def test_strips_ansible_meta_keys(self) -> None:
        source = (
            "configuration:\n"
            "  system:\n"
            "    host-name: r1\n"
            "  _ansible_version: '2.9'\n"
            "  _meta_timestamp: '2024-01-01'\n"
        )
        ir = to_dict(source, "yaml")
        assert "host-name" in ir["system"]
        assert "_ansible_version" not in ir
        assert "_meta_timestamp" not in ir

    def test_missing_configuration_raises(self) -> None:
        with pytest.raises(ValueError, match="No 'configuration' key"):
            to_dict("foo: bar\n", "yaml")

    def test_empty_yaml_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            to_dict("", "yaml")


# ── XML input ─────────────────────────────────────────────────────────


class TestXmlInput:
    def test_simple(self) -> None:
        source = "<configuration><system><host-name>r1</host-name></system></configuration>"
        ir = to_dict(source, "xml")
        assert ir == {"system": {"host-name": "r1"}}

    def test_empty_configuration_raises(self) -> None:
        with pytest.raises(ValueError, match="configuration"):
            to_dict("<root><foo/></root>", "xml")

    def test_with_attributes(self) -> None:
        source = (
            '<configuration><system inactive="inactive">'
            "<host-name>r1</host-name></system></configuration>"
        )
        ir = to_dict(source, "xml")
        assert ir["system"]["@"] == {"inactive": True}
        assert ir["system"]["host-name"] == "r1"


class TestXmlRoundTrip:
    def test_xml_to_dict_to_set(self) -> None:
        source = "<configuration><system><host-name>r1</host-name></system></configuration>"
        ir = to_dict(source, "xml")
        output = from_dict(ir, "set")
        assert "set system host-name r1" in output

    def test_xml_to_dict_to_structured(self) -> None:
        source = "<configuration><system><host-name>r1</host-name></system></configuration>"
        ir = to_dict(source, "xml")
        output = from_dict(ir, "structured")
        assert "host-name r1;" in output

    def test_xml_to_dict_to_json(self) -> None:
        source = "<configuration><system><host-name>r1</host-name></system></configuration>"
        ir = to_dict(source, "xml")
        output = from_dict(ir, "json")
        parsed = json.loads(output)
        assert parsed["configuration"]["system"]["host-name"] == "r1"


class TestXmlOutputStub:
    def test_xml_output_not_implemented(self) -> None:
        with pytest.raises(NotImplementedError, match="XML output"):
            from_dict({"system": {}}, "xml")


# ── Dict → Set output ────────────────────────────────────────────────


class TestDictToSet:
    def test_simple(self) -> None:
        config = {"system": {"host-name": "r1"}}
        result = from_dict(config, "set")
        assert "set system host-name r1" in result

    def test_with_deactivate(self) -> None:
        config = {
            "system": {"@": {"inactive": True}, "host-name": "r1"},
        }
        result = from_dict(config, "set")
        assert "set system host-name r1" in result
        assert "deactivate system" in result


# ── Dict → Structured output ────────────────────────────────────────


class TestDictToStructured:
    def test_simple(self) -> None:
        config = {"system": {"host-name": "r1"}}
        result = from_dict(config, "structured")
        assert "host-name r1;" in result


# ── Phase 3: set input ───────────────────────────────────────────────


class TestSetInputViaDispatcher:
    def test_set_input_produces_dict(self) -> None:
        ir = to_dict("set system host-name r1", "set")
        assert ir == {"system": {"host-name": "r1"}}


# ── Phase 4: structured input ────────────────────────────────────────


class TestStructuredInputViaDispatcher:
    def test_structured_input_produces_dict(self) -> None:
        ir = to_dict("system {\n    host-name r1;\n}", "structured")
        assert ir == {"system": {"host-name": "r1"}}

    def test_structured_to_set_roundtrip(self) -> None:
        source = "system {\n    host-name r1;\n    domain-name example.com;\n}"
        ir = to_dict(source, "structured")
        set_output = from_dict(ir, "set")
        assert "set system host-name r1" in set_output
        assert "set system domain-name example.com" in set_output


# ── Unknown format ───────────────────────────────────────────────────


class TestUnknownFormat:
    def test_unknown_input_format(self) -> None:
        with pytest.raises(ValueError, match="Unknown input format"):
            to_dict("data", "protobuf")

    def test_unknown_output_format(self) -> None:
        with pytest.raises(ValueError, match="Unknown output format"):
            from_dict({}, "protobuf")
