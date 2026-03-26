"""Cross-format consistency tests.

Verifies that the convert/ pipeline produces consistent results across
different format conversion paths and preserves content through round-trips.
"""

from __future__ import annotations

import json

import pytest

from junoscfg.convert.input import to_dict
from junoscfg.convert.output import from_dict

# Sample configs of varying complexity
SAMPLE_CONFIGS = [
    '{"configuration": {"system": {"host-name": "r1"}}}',
    '{"configuration": {"system": {"services": {"ssh": {"root-login": "deny"}}}}}',
    """{"configuration": {"interfaces": {"interface": [
        {"name": "ge-0/0/0", "description": "uplink"},
        {"name": "ge-0/0/1", "description": "downlink"}
    ]}}}""",
    """{"configuration": {"interfaces": {"interface": [
        {"name": "ge-0/0/0", "unit": [
            {"name": "0", "family": {"inet": {"address": [{"name": "10.0.0.1/24"}]}}}
        ]}
    ]}}}""",
    """{"configuration": {"system": {
        "host-name": "r1",
        "domain-name": "example.com",
        "name-server": ["8.8.8.8", "8.8.4.4"]
    }}}""",
    """{"configuration": {"system": {
        "@": {"inactive": true},
        "host-name": "r1"
    }}}""",
    """{"configuration": {"routing-options": {
        "static": {"route": [
            {"name": "0.0.0.0/0", "next-hop": "10.0.0.1"}
        ]}
    }}}""",
    """{"configuration": {"firewall": {"family": {"inet": {
        "filter": [{"name": "PROTECT", "term": [
            {"name": "accept-ssh", "from": {"protocol": "tcp", "destination-port": "ssh"},
             "then": {"accept": [null]}}
        ]}]
    }}}}}""",
]


class TestSetOutputConsistency:
    """Pipeline dict_to_set produces valid set commands for all sample configs."""

    @pytest.mark.parametrize("source", SAMPLE_CONFIGS)
    def test_json_to_set_produces_output(self, source: str) -> None:
        ir = to_dict(source, "json")
        result = from_dict(ir, "set")
        assert result.strip(), f"Empty set output for input: {source[:80]}..."
        for line in result.strip().splitlines():
            assert line.startswith(("set ", "deactivate ", "delete ")), f"Invalid set line: {line}"


class TestStructuredOutputConsistency:
    """Pipeline dict_to_structured produces valid structured output for all sample configs."""

    @pytest.mark.parametrize("source", SAMPLE_CONFIGS)
    def test_json_to_structured_produces_output(self, source: str) -> None:
        ir = to_dict(source, "json")
        result = from_dict(ir, "structured")
        assert result.strip(), f"Empty structured output for input: {source[:80]}..."


class TestJsonRoundTripConsistency:
    """JSON→dict→JSON preserves the configuration content."""

    @pytest.mark.parametrize("source", SAMPLE_CONFIGS)
    def test_roundtrip_preserves_content(self, source: str) -> None:
        original = json.loads(source)["configuration"]
        ir = to_dict(source, "json")
        output = from_dict(ir, "json")
        roundtripped = json.loads(output)["configuration"]
        assert roundtripped == original
