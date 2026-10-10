"""Tests for the apply_rules public API."""

from __future__ import annotations

from junoscfg.edityaml import apply_rules


class TestApplyRules:
    def test_does_not_mutate_input(self) -> None:
        data = {"configuration": {"system": {"host-name": "r1"}}}
        ruleset = {
            "rules": [
                {
                    "path": "configuration.system",
                    "transforms": [
                        {"type": "static", "target": "_new", "value": True},
                    ],
                }
            ]
        }
        result = apply_rules(data, ruleset)
        assert "_new" in result["configuration"]["system"]
        assert "_new" not in data["configuration"]["system"]

    def test_multiple_rules_applied(self) -> None:
        data = {
            "configuration": {
                "system": {"host-name": "r1"},
                "interfaces": {"interface": [{"name": "eth0"}]},
            }
        }
        ruleset = {
            "rules": [
                {
                    "path": "configuration.system",
                    "transforms": [
                        {"type": "static", "target": "_a", "value": 1},
                    ],
                },
                {
                    "path": "configuration.interfaces.interface[*]",
                    "transforms": [
                        {"type": "copy", "source": "name", "target": "_b"},
                    ],
                },
            ]
        }
        result = apply_rules(data, ruleset)
        assert result["configuration"]["system"]["_a"] == 1
        assert result["configuration"]["interfaces"]["interface"][0]["_b"] == "eth0"

    def test_empty_ruleset(self) -> None:
        data = {"a": {"b": 1}}
        result = apply_rules(data, {"rules": []})
        assert result == data

    def test_end_to_end_bgp_peername(self) -> None:
        data = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "overlay",
                                "neighbor": [
                                    {
                                        "name": "10.0.0.1",
                                        "description": "overlay: spine1",
                                    },
                                    {
                                        "name": "10.0.0.2",
                                        "description": "overlay: spine2",
                                    },
                                ],
                            }
                        ]
                    }
                }
            }
        }
        ruleset = {
            "rules": [
                {
                    "path": "configuration.protocols.bgp.group[*].neighbor[*]",
                    "transforms": [
                        {
                            "type": "regex_extract",
                            "source": "description",
                            "pattern": r"overlay: (\w+)",
                            "target": "_ansible_bgp_peername",
                        },
                    ],
                }
            ]
        }
        result = apply_rules(data, ruleset)
        neighbors = result["configuration"]["protocols"]["bgp"]["group"][0]["neighbor"]
        assert neighbors[0]["_ansible_bgp_peername"] == "spine1"
        assert neighbors[1]["_ansible_bgp_peername"] == "spine2"
