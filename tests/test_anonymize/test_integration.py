"""End-to-end integration tests for anonymization through the pipeline."""

from __future__ import annotations

import json

import pytest

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


# ── identifier-key-fields: keyed entries survive anonymization ───────
#
# Spec: openspec/changes/identifier-key-fields/specs/anonymization/
# keyed-entries, "An AS-list reference survives anonymization" and "No value
# anonymized before escapes".

_GROUPED = """\
groups {
    SAMPLE-GROUP {
        policy-options {
            as-list SAMPLE-AS-LIST members 64496;
            policy-statement SAMPLE-POLICY {
                term T1 {
                    from {
                        as-path-neighbors as-list SAMPLE-AS-LIST;
                    }
                    then accept;
                }
            }
        }
    }
}
apply-groups SAMPLE-GROUP;
"""

_GROUPED_SET = (
    "set groups SAMPLE-GROUP policy-options as-list SAMPLE-AS-LIST members 64496\n"
    "set groups SAMPLE-GROUP policy-options policy-statement SAMPLE-POLICY term T1 from "
    "as-path-neighbors as-list SAMPLE-AS-LIST\n"
    "set groups SAMPLE-GROUP policy-options policy-statement SAMPLE-POLICY term T1 then accept\n"
    "set apply-groups SAMPLE-GROUP\n"
)

_EVERY_FLAG = {
    "ips": {"ips": True},
    "passwords": {"passwords": True},
    "communities": {"communities": True},
    "ssh-keys": {"ssh_keys": True},
    "identities": {"identities": True},
    "groups": {"groups": True},
    "descriptions": {"descriptions": True},
    "as-numbers": {"as_numbers": [64496]},
    "sensitive-words": {"sensitive_words": ["SAMPLE-GROUP"]},
    "sensitive-patterns": {"sensitive_patterns": [r"SAMPLE-G\w+"]},
}


def _neighbor_lines(output: str) -> list[list[str]]:
    """The tokens after `as-path-neighbors` on every line that holds it."""
    return [
        line.split(" as-path-neighbors ", 1)[1].split()
        for line in output.splitlines()
        if " as-path-neighbors " in line
    ]


class TestKeyedEntriesSurvive:
    def test_an_as_list_reference_survives_anonymize_all(self) -> None:
        from junoscfg import Format, convert_config
        from junoscfg.anonymize.config import build_config_from_cli

        for source, fmt in ((_GROUPED, Format.STRUCTURED), (_GROUPED_SET, Format.SET)):
            cfg = build_config_from_cli(anonymize_all=True, anonymize_salt="keyed")
            out = convert_config(source, from_format=fmt, to_format=Format.SET, anon_config=cfg)
            found = _neighbor_lines(out)
            assert len(found) == 1, out
            list_type, list_name = found[0]
            assert list_type == "as-list"
            assert list_name, "the list name was lost"
            assert "SAMPLE-GROUP" not in out, "the group was not anonymized"

    def test_as_numbers_leave_the_as_list_reference_whole(self) -> None:
        from junoscfg import Format, convert_config
        from tests.keyed_entries import as_json, ir

        device = as_json(ir(_GROUPED_SET, Format.SET))
        for source, fmt in (
            (_GROUPED, Format.STRUCTURED),
            (_GROUPED_SET, Format.SET),
            (device, Format.JSON),
        ):
            cfg = AnonymizeConfig(as_numbers=[64496], salt="keyed")
            out = convert_config(source, from_format=fmt, to_format=Format.SET, anon_config=cfg)
            assert _neighbor_lines(out) == [["as-list", "SAMPLE-AS-LIST"]], (fmt, out)
            assert "members 64496" not in out

    @pytest.mark.parametrize("flag", list(_EVERY_FLAG))
    def test_every_rule_keeps_the_key_whole(self, flag: str) -> None:
        """Each `--anonymize-*` rule on its own keeps both key values."""
        from junoscfg import Format, convert_config

        cfg = AnonymizeConfig(salt="keyed", **_EVERY_FLAG[flag])
        out = convert_config(
            _GROUPED_SET, from_format=Format.SET, to_format=Format.SET, anon_config=cfg
        )
        found = _neighbor_lines(out)
        assert len(found) == 1 and len(found[0]) == 2, out
        assert found[0][0] == "as-list"

    def test_the_other_keyed_lists_keep_their_keys(self) -> None:
        from junoscfg import Format, convert_config
        from junoscfg.anonymize.config import build_config_from_cli

        term = "set policy-options policy-statement SAMPLE-POLICY term T1"
        source = (
            f"{term} from route-filter 198.51.100.0/24 exact accept\n"
            f"{term} from source-address-filter 198.51.100.0/24 orlonger\n"
            f"{term} then community add SAMPLE-COMM\n"
            "set policy-options community SAMPLE-COMM members 64496:100\n"
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
            'matches "^uptime$"\n'
        )
        cfg = build_config_from_cli(anonymize_all=True, anonymize_salt="keyed")
        out = convert_config(source, from_format=Format.SET, to_format=Format.SET, anon_config=cfg)
        lines = out.splitlines()
        assert any(" route-filter 198.51.100.0/24 exact accept" in line for line in lines), out
        assert any(" source-address-filter 198.51.100.0/24 orlonger" in line for line in lines)
        community = [line for line in lines if " then community " in line]
        assert len(community) == 1 and community[0].split(" then community ")[1].startswith("add ")
        match = [line for line in lines if " attributes-match " in line]
        assert len(match) == 1
        assert match[0].split(" attributes-match ")[1].split()[1] == "matches"

    #: Every value 0.14.0 replaced in examples/router1.json with every rule
    #: on, by rule. Measured before the change.
    BEFORE = {
        "password": ["$9$ExAmPlEhAsH.KEY"],
        "ip": [
            "0.0.0.0",
            "0.0.0.0/0",
            "10.0.0.0/8",
            "10.0.100.1/24",
            "10.0.200.1/24",
            "10.255.255.1",
            "10.255.255.1/32",
            "10.255.255.2",
            "192.168.0.10",
            "192.168.0.123",
            "192.168.0.53",
            "192.168.0.54",
            "198.51.100.1/30",
            "198.51.100.2",
            "2001:db8:100::1/126",
        ],
        "identity": ["admin", "operator"],
        "group": ["ebgp-peers", "ibgp-peers"],
        "description": [
            "bundled customer handoff",
            "core router",
            "customer handoff",
            "customer handoff backup",
            "downlink to access",
            "transit provider",
            "uplink to core",
        ],
        "as_number": ["64496", "64497"],
        "sensitive_word": ["customer-routes", "customers", "export-customers"],
    }

    @staticmethod
    def _every_rule() -> AnonymizeConfig:
        return AnonymizeConfig(
            ips=True,
            passwords=True,
            communities=True,
            ssh_keys=True,
            identities=True,
            groups=True,
            descriptions=True,
            as_numbers=[64496, 64497],
            sensitive_words=["customer"],
            salt="pinned-salt",
        )

    def test_no_value_anonymized_before_escapes(self) -> None:
        from pathlib import Path

        source = json.loads(Path("examples/router1.json").read_text(encoding="utf-8"))
        mapping = anonymize(source, self._every_rule()).mapping
        for rule, values in self.BEFORE.items():
            missing = set(values) - set(mapping.get(rule, {}))
            assert not missing, f"{rule} no longer replaces {sorted(missing)}"

    def test_name_keyed_output_is_unchanged(self) -> None:
        """Pinned before the change; expected to hold across it."""
        import hashlib
        from pathlib import Path

        from junoscfg import Format, convert_config

        source = Path("examples/router1.json").read_text(encoding="utf-8")
        out = convert_config(
            source,
            from_format=Format.JSON,
            to_format=Format.SET,
            validate=False,
            anon_config=self._every_rule(),
        )
        assert (
            hashlib.sha256(out.encode()).hexdigest()
            == "8cd6b3d38f7d82a2fdbb9dc1990dad6d9e880a4b2f76701afc47351409b000ad"
        )
