"""End-to-end integration tests for anonymization through the pipeline."""

from __future__ import annotations

import json

from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig


class TestPipelineIntegration:
    """Test anonymization through the full convert pipeline."""

    def test_json_to_json_with_anonymize_ips(self) -> None:
        """JSON -> JSON with --anonymize-ips end-to-end."""
        from junoscfg.convert import pipeline

        source = json.dumps(
            {
                "configuration": {
                    "system": {"host-name": "router1"},
                    "interfaces": {
                        "interface": [
                            {
                                "name": "ge-0/0/0",
                                "unit": [
                                    {
                                        "name": "0",
                                        "family": {
                                            "inet": {
                                                "address": [{"name": "10.1.2.3/24"}],
                                            },
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                },
            }
        )

        cfg = AnonymizeConfig(ips=True, salt="integration-test")
        result = pipeline(
            source, from_format="json", to_format="json", validate=False, anon_config=cfg
        )

        output = json.loads(result)
        addr = output["configuration"]["interfaces"]["interface"][0]["unit"][0]["family"]["inet"][
            "address"
        ][0]["name"]
        assert addr != "10.1.2.3/24"
        assert addr.startswith("10.")
        assert addr.endswith("/24")

        # Non-IP field preserved
        assert output["configuration"]["system"]["host-name"] == "router1"

    def test_json_to_set_with_anonymize_ips(self) -> None:
        """JSON -> set commands with anonymized IPs."""
        from junoscfg.convert import pipeline

        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "name-server": [{"name": "8.8.8.8"}],
                    },
                },
            }
        )

        cfg = AnonymizeConfig(ips=True, salt="set-test")
        result = pipeline(
            source, from_format="json", to_format="set", validate=False, anon_config=cfg
        )

        # Should contain a set command but with anonymized IP
        assert "set system name-server" in result
        assert "8.8.8.8" not in result

    def test_no_anon_config_passes_through(self) -> None:
        """Without anon_config, pipeline works as before."""
        from junoscfg.convert import pipeline

        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "name-server": [{"name": "8.8.8.8"}],
                    },
                },
            }
        )

        result = pipeline(
            source, from_format="json", to_format="json", validate=False, anon_config=None
        )
        output = json.loads(result)
        assert output["configuration"]["system"]["name-server"][0]["name"] == "8.8.8.8"

    def test_include_filter_limits_scope(self) -> None:
        """Include filter should limit anonymization to specified paths."""
        from junoscfg.convert import pipeline

        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "name-server": [{"name": "8.8.8.8"}],
                    },
                    "interfaces": {
                        "interface": [
                            {
                                "name": "ge-0/0/0",
                                "unit": [
                                    {
                                        "name": "0",
                                        "family": {
                                            "inet": {
                                                "address": [{"name": "10.1.2.3/24"}],
                                            },
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                },
            }
        )

        # Only anonymize within "interfaces"
        cfg = AnonymizeConfig(ips=True, salt="filter-test", include=["interfaces"])
        result = pipeline(
            source, from_format="json", to_format="json", validate=False, anon_config=cfg
        )
        output = json.loads(result)

        # system.name-server should NOT be anonymized
        assert output["configuration"]["system"]["name-server"][0]["name"] == "8.8.8.8"

        # interfaces address SHOULD be anonymized
        addr = output["configuration"]["interfaces"]["interface"][0]["unit"][0]["family"]["inet"][
            "address"
        ][0]["name"]
        assert addr != "10.1.2.3/24"

    def test_exclude_filter_skips_paths(self) -> None:
        """Exclude filter should skip specified paths."""
        from junoscfg.convert import pipeline

        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "name-server": [{"name": "8.8.8.8"}],
                    },
                    "interfaces": {
                        "interface": [
                            {
                                "name": "ge-0/0/0",
                                "unit": [
                                    {
                                        "name": "0",
                                        "family": {
                                            "inet": {
                                                "address": [{"name": "10.1.2.3/24"}],
                                            },
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                },
            }
        )

        # Exclude system — only interfaces should be anonymized
        cfg = AnonymizeConfig(ips=True, salt="exclude-test", exclude=["system"])
        result = pipeline(
            source, from_format="json", to_format="json", validate=False, anon_config=cfg
        )
        output = json.loads(result)

        # system.name-server should NOT be anonymized (excluded)
        assert output["configuration"]["system"]["name-server"][0]["name"] == "8.8.8.8"

        # interfaces address SHOULD be anonymized
        addr = output["configuration"]["interfaces"]["interface"][0]["unit"][0]["family"]["inet"][
            "address"
        ][0]["name"]
        assert addr != "10.1.2.3/24"


class TestPipelineDumpMapIntegration:
    """Test dump_map and revert_map through the full pipeline."""

    def test_dump_map_writes_file(self, tmp_path) -> None:
        """Pipeline writes a mapping file when dump_map is set."""
        from junoscfg.convert import pipeline

        source = json.dumps(
            {
                "configuration": {
                    "system": {"name-server": [{"name": "8.8.8.8"}]},
                },
            }
        )
        map_file = tmp_path / "map.json"
        cfg = AnonymizeConfig(ips=True, salt="dump-test", dump_map=str(map_file))
        result = pipeline(
            source, from_format="json", to_format="json", validate=False, anon_config=cfg
        )

        output = json.loads(result)
        assert output["configuration"]["system"]["name-server"][0]["name"] != "8.8.8.8"

        assert map_file.exists()
        mapping = json.loads(map_file.read_text())
        assert "ip" in mapping

    def test_revert_map_restores_originals(self, tmp_path) -> None:
        """Pipeline restores originals when revert_map is set."""
        from junoscfg.convert import pipeline

        source = json.dumps(
            {
                "configuration": {
                    "system": {"name-server": [{"name": "8.8.8.8"}]},
                },
            }
        )

        # Step 1: anonymize and dump map
        map_file = tmp_path / "map.json"
        cfg_anon = AnonymizeConfig(ips=True, salt="revert-test", dump_map=str(map_file))
        anon_result = pipeline(
            source, from_format="json", to_format="json", validate=False, anon_config=cfg_anon
        )
        assert "8.8.8.8" not in anon_result

        # Step 2: revert using the map
        cfg_revert = AnonymizeConfig(revert_map=str(map_file))
        reverted_result = pipeline(
            anon_result,
            from_format="json",
            to_format="json",
            validate=False,
            anon_config=cfg_revert,
        )
        reverted = json.loads(reverted_result)
        assert reverted["configuration"]["system"]["name-server"][0]["name"] == "8.8.8.8"

    def test_multi_rule_revert_through_pipeline(self, tmp_path) -> None:
        """Full round-trip with multiple rules through the pipeline."""
        from junoscfg.convert import pipeline

        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "host-name": "router1",
                        "name-server": [{"name": "8.8.8.8"}],
                        "login": {
                            "user": [
                                {
                                    "name": "admin",
                                    "full-name": "Admin User",
                                    "authentication": {
                                        "encrypted-password": "$6$abc$xyz",
                                    },
                                }
                            ]
                        },
                    },
                    "interfaces": {
                        "interface": [
                            {
                                "name": "ge-0/0/0",
                                "description": "Uplink",
                                "unit": [
                                    {
                                        "name": "0",
                                        "family": {"inet": {"address": [{"name": "10.1.2.3/24"}]}},
                                    }
                                ],
                            }
                        ]
                    },
                },
            }
        )

        map_file = tmp_path / "map.json"
        cfg_anon = AnonymizeConfig(
            ips=True,
            passwords=True,
            identities=True,
            descriptions=True,
            salt="multi-test",
            dump_map=str(map_file),
        )
        anon_output = pipeline(
            source, from_format="json", to_format="json", validate=False, anon_config=cfg_anon
        )

        # Verify anonymization happened
        anon_data = json.loads(anon_output)
        assert anon_data["configuration"]["system"]["name-server"][0]["name"] != "8.8.8.8"
        assert anon_data["configuration"]["system"]["login"]["user"][0]["name"] != "admin"

        # Revert
        cfg_revert = AnonymizeConfig(revert_map=str(map_file))
        reverted_output = pipeline(
            anon_output,
            from_format="json",
            to_format="json",
            validate=False,
            anon_config=cfg_revert,
        )
        reverted = json.loads(reverted_output)
        assert reverted["configuration"]["system"]["name-server"][0]["name"] == "8.8.8.8"
        assert reverted["configuration"]["system"]["login"]["user"][0]["name"] == "admin"
        assert reverted["configuration"]["system"]["login"]["user"][0]["full-name"] == "Admin User"
        assert reverted["configuration"]["interfaces"]["interface"][0]["description"] == "Uplink"


class TestPublicApiIntegration:
    """Test anonymization through the public convert_config API."""

    def test_convert_config_with_anon(self) -> None:
        from junoscfg import Format, convert_config

        source = json.dumps(
            {
                "configuration": {
                    "interfaces": {
                        "interface": [
                            {
                                "name": "ge-0/0/0",
                                "unit": [
                                    {
                                        "name": "0",
                                        "family": {
                                            "inet": {
                                                "address": [{"name": "10.1.2.3/24"}],
                                            },
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                },
            }
        )

        cfg = AnonymizeConfig(ips=True, salt="api-test")
        result = convert_config(
            source,
            from_format=Format.JSON,
            to_format=Format.JSON,
            validate=False,
            anon_config=cfg,
        )

        output = json.loads(result)
        addr = output["configuration"]["interfaces"]["interface"][0]["unit"][0]["family"]["inet"][
            "address"
        ][0]["name"]
        assert addr != "10.1.2.3/24"


class TestAsNumbersInStringsIntegration:
    """Test the as_numbers_in_strings second pass through anonymize()."""

    def test_as_in_community_name(self) -> None:
        """AS numbers embedded in community name values are replaced."""
        cfg = AnonymizeConfig(
            as_numbers=[64498, 64497],
            as_numbers_in_strings=True,
            salt="as-str-test",
        )
        ir = {
            "configuration": {
                "policy-options": {
                    "community": [
                        {"name": "large:64498:23456:401", "members": ["target:64498:100"]},
                    ],
                },
            },
        }
        result = anonymize(ir, cfg)
        comm = result.ir["configuration"]["policy-options"]["community"][0]
        assert "64498" not in comm["name"]
        assert "64498" not in comm["members"][0]

    def test_as_in_bgp_group_name(self) -> None:
        """AS numbers in BGP group names are replaced."""
        cfg = AnonymizeConfig(
            as_numbers=[64497],
            as_numbers_in_strings=True,
            salt="as-str-test",
        )
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "inet-Upstream-AS64497",
                                "peer-as": "64497",
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        group = result.ir["configuration"]["protocols"]["bgp"]["group"][0]
        assert "64497" not in group["name"]
        assert group["peer-as"] != "64497"

    def test_as_in_strings_disabled_by_default(self) -> None:
        """Without as_numbers_in_strings, embedded AS numbers are NOT replaced."""
        cfg = AnonymizeConfig(as_numbers=[64498], salt="as-str-test")
        ir = {
            "configuration": {
                "policy-options": {
                    "community": [
                        {"name": "large:64498:23456:401"},
                    ],
                },
            },
        }
        result = anonymize(ir, cfg)
        comm = result.ir["configuration"]["policy-options"]["community"][0]
        assert "64498" in comm["name"]

    def test_as_in_strings_without_as_numbers_is_noop(self) -> None:
        """as_numbers_in_strings without as_numbers list does nothing."""
        cfg = AnonymizeConfig(as_numbers_in_strings=True, ips=True, salt="test")
        ir = {
            "configuration": {
                "system": {"host-name": "router1"},
            },
        }
        result = anonymize(ir, cfg)
        assert result.ir["configuration"]["system"]["host-name"] == "router1"
