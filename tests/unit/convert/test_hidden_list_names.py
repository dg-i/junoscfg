"""Device-hidden XML list names keep declared keys at the conversion doors.

DEV-10..14: narrow fragments of committed synthetic junoscfg-oracle vMX
23.2R2-S7.5 set/JSON/XML; QFX 25.2R2-S1.5 corroborates route filters, DHCP
and dynamic tunnels. The vMX capture alone supplies bridge domains and defaults.
Artificial boundary trees below prove conversion policy, not device syntax.
"""

from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING

import pytest
import yaml

from junoscfg.convert import from_dict, structured_set_lines, to_dict
from tests.support.artifacts import using_tree

if TYPE_CHECKING:
    from pathlib import Path

# Expected IR and set lines come from device captures, not a writer under test.
_CASES = {
    "route-filter-address-and-choice": (
        {
            "policy-options": {
                "route-filter-list": [
                    {
                        "name": "RFL-MIXED",
                        "rf_list": [
                            {"address": "10.10.0.0/18", "upto": "/32"},
                            {"address": "198.51.100.0/24", "exact": [None]},
                        ],
                    }
                ]
            }
        },
        "set policy-options route-filter-list RFL-MIXED 10.10.0.0/18 upto /32\n"
        "set policy-options route-filter-list RFL-MIXED 198.51.100.0/24 exact",
        "policy-options { route-filter-list RFL-MIXED { 10.10.0.0/18 upto /32; "
        "198.51.100.0/24 exact; } }",
        "<policy-options><route-filter-list><name>RFL-MIXED</name><rf_list>"
        "<address>10.10.0.0/18</address><upto>/32</upto></rf_list><rf_list>"
        "<address>198.51.100.0/24</address><exact/></rf_list></route-filter-list></policy-options>",
    ),
    "nested-dhcp-names-and-addresses": (
        {
            "routing-instances": {
                "instance": [
                    {
                        "name": "VRF-A",
                        "forwarding-options": {
                            "dhcp-relay": {
                                "server-group": {
                                    "server-group": [
                                        {
                                            "name": "SG-A",
                                            "address": [
                                                {"name": "10.0.100.200"},
                                                {"name": "10.0.100.201"},
                                            ],
                                        }
                                    ]
                                }
                            }
                        },
                    }
                ]
            }
        },
        "set routing-instances VRF-A forwarding-options dhcp-relay server-group SG-A 10.0.100.200\n"
        "set routing-instances VRF-A forwarding-options dhcp-relay server-group SG-A 10.0.100.201",
        "routing-instances { VRF-A { forwarding-options { dhcp-relay { "
        "server-group { SG-A { 10.0.100.200; 10.0.100.201; } } } } } }",
        "<routing-instances><instance><name>VRF-A</name><forwarding-options><dhcp-relay>"
        "<server-group><server-group><name>SG-A</name><address><name>10.0.100.200</name>"
        "</address><address><name>10.0.100.201</name></address></server-group></server-group>"
        "</dhcp-relay></forwarding-options></instance></routing-instances>",
    ),
    "predefined-variable-name-and-value": (
        {
            "dynamic-profiles": [
                {
                    "name": "DP-PROBE",
                    "predefined-variable-defaults": {
                        "other-variables": [
                            {"name": "routing-instances", "default-value": "VRF-A"}
                        ],
                    },
                }
            ]
        },
        "set dynamic-profiles DP-PROBE predefined-variable-defaults routing-instances VRF-A",
        "dynamic-profiles { DP-PROBE { predefined-variable-defaults { "
        "routing-instances VRF-A; } } }",
        "<dynamic-profiles><name>DP-PROBE</name><predefined-variable-defaults><other-variables>"
        "<name>routing-instances</name><default-value>VRF-A</default-value></other-variables>"
        "</predefined-variable-defaults></dynamic-profiles>",
    ),
    "bridge-domain-name": (
        {
            "bridge-domains": {
                "domain": [
                    {"name": "BD-100", "vlan-id": "100"},
                    {"name": "BD-200", "vlan-id": "200"},
                ]
            }
        },
        "set bridge-domains BD-100 vlan-id 100\nset bridge-domains BD-200 vlan-id 200",
        "bridge-domains { BD-100 { vlan-id 100; } BD-200 { vlan-id 200; } }",
        "<bridge-domains><domain><name>BD-100</name><vlan-id>100</vlan-id></domain>"
        "<domain><name>BD-200</name><vlan-id>200</vlan-id></domain></bridge-domains>",
    ),
    "dynamic-tunnel-name": (
        {
            "routing-options": {
                "dynamic-tunnels": {
                    "dynamic-tunnel": [
                        {"name": "DT-GRE", "source-address": "10.255.0.1", "gre": [None]},
                    ]
                }
            }
        },
        "set routing-options dynamic-tunnels DT-GRE source-address 10.255.0.1\n"
        "set routing-options dynamic-tunnels DT-GRE gre",
        "routing-options { dynamic-tunnels { DT-GRE { source-address 10.255.0.1; gre; } } }",
        "<routing-options><dynamic-tunnels><dynamic-tunnel><name>DT-GRE</name>"
        "<source-address>10.255.0.1</source-address><gre/></dynamic-tunnel>"
        "</dynamic-tunnels></routing-options>",
    ),
}


def _source(case: str, fmt: str) -> str:
    ir, lines, curly, xml = _CASES[case]
    if fmt == "set":
        return lines
    if fmt == "structured":
        return curly
    if fmt == "xml":
        return f"<configuration>{xml}</configuration>"
    wrapped = {"configuration": ir}
    return json.dumps(wrapped) if fmt == "json" else yaml.safe_dump(wrapped)


class TestAHiddenListKeepsItsDeviceKey:
    @pytest.mark.parametrize("case", _CASES)
    @pytest.mark.parametrize("fmt", ["set", "structured", "json", "yaml", "xml"])
    def test_every_reader_keeps_the_key(self, case: str, fmt: str) -> None:
        assert to_dict(_source(case, fmt), fmt) == _CASES[case][0]

    @pytest.mark.parametrize("case", _CASES)
    @pytest.mark.parametrize("fmt", ["set", "structured"])
    def test_every_writer_omits_the_hidden_name(self, case: str, fmt: str) -> None:
        ir, device_lines, _, _ = _CASES[case]
        original = copy.deepcopy(ir)
        rendered = from_dict(ir, fmt)
        if fmt == "set":
            assert set(rendered.splitlines()) == set(device_lines.splitlines())
        else:
            # A second check cannot replace the independent device-set oracle.
            assert to_dict(rendered, fmt) == ir
            statements = structured_set_lines(rendered)
            assert set(statements.lines) == set(device_lines.splitlines())
            assert not statements.incomplete
            assert not statements.notes
        assert ir == original


class TestAHiddenListUsesTheWholeKey:
    def test_choice_keys_remain_distinct(self) -> None:
        prefix = "set policy-options route-filter-list RFL-DEFAULT 0.0.0.0/0 "
        expected = {
            "policy-options": {
                "route-filter-list": [
                    {
                        "name": "RFL-DEFAULT",
                        "rf_list": [
                            {"address": "0.0.0.0/0", "exact": [None]},
                            {"address": "0.0.0.0/0", "orlonger": [None]},
                        ],
                    }
                ]
            }
        }
        # The capture proves both choices. Combining them pins identity without
        # claiming another device probe or broadening accepted match choices.
        assert (
            to_dict("\n".join(prefix + choice for choice in ["exact", "orlonger", "exact"]), "set")
            == expected
        )


class TestKeywordChildrenPrecedeHiddenKeys:
    def test_the_keyword_is_not_an_entry_name(self, tmp_path: Path) -> None:
        tree = {
            "c": {
                "box": {
                    "c": {
                        "enabled": {"p": True},
                        "entry": {
                            "L": True,
                            "nk": True,
                            "c": {
                                "name": {"l": True, "nk": True},
                                "value": {"l": True},
                            },
                        },
                    }
                }
            }
        }
        with using_tree(tmp_path, tree):
            assert to_dict("set box enabled", "set") == {"box": {"enabled": [None]}}
            assert to_dict("set box operator value kept", "set") == {
                "box": {"entry": [{"name": "operator", "value": "kept"}]},
            }


class TestUnrelatedModelsKeepTheirMeaning:
    @pytest.mark.parametrize(
        "kind", ["keyword-list", "leaf", "unkeyed-container", "unkeyed-list", "unknown"]
    )
    def test_models_outside_the_hidden_key_rule_are_preserved(
        self, tmp_path: Path, kind: str
    ) -> None:
        models = {
            "keyword-list": (
                {"L": True, "c": {"name": {"l": True, "nk": True}}},
                [{"name": "operator"}],
                "set box entry operator",
            ),
            "leaf": ({"l": True}, "operator", "set box entry operator"),
            "unkeyed-container": (
                {"nk": True, "c": {"value": {"l": True}}},
                {"value": "kept"},
                "set box entry value kept",
            ),
            "unkeyed-list": (
                {"L": True, "nk": True, "c": {"value": {"l": True}}},
                [{"value": "kept"}],
                "set box entry value kept",
            ),
            "unknown": (None, "operator", "set box entry operator"),
        }
        model, value, line = models[kind]
        children = {} if model is None else {"entry": model}
        ir = {"box": {"entry": value}}
        with using_tree(tmp_path, {"c": {"box": {"c": children}}}):
            assert from_dict(ir, "set").strip() == line
            if kind in {"keyword-list", "leaf"}:
                assert to_dict(line, "set") == ir
