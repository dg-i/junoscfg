"""End-to-end integration tests for anonymization through the pipeline.

The dump-map and revert-map round trip, for every rule and for rules
together, is `tests/contract/test_every_rule.py`.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import shlex
from typing import TYPE_CHECKING, Any

import pytest

from junoscfg import Format, convert_config, convert_config_result
from junoscfg.anonymize import AnonymizeConfig, anonymize, build_config_from_cli
from tests.support.devices import example, placed_only

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def _leaves(node: Any, wanted: Callable[[str], bool]) -> set[str]:
    """Every string under a key *wanted* accepts, anywhere in *node*."""
    found: set[str] = set()
    if isinstance(node, list):
        for item in node:
            found |= _leaves(item, wanted)
    elif isinstance(node, dict):
        for key, value in node.items():
            if wanted(key):
                found |= _strings(value)
            else:
                found |= _leaves(value, wanted)
    return found


def _strings(node: Any) -> set[str]:
    """Every value in *node*, as text; tags (``@`` keys) are not values."""
    if isinstance(node, str):
        return {node}
    if isinstance(node, int) and not isinstance(node, bool):
        return {str(node)}
    if isinstance(node, list):
        return set().union(*(_strings(item) for item in node))
    if isinstance(node, dict):
        return set().union(*(_strings(v) for k, v in node.items() if not k.startswith("@")))
    return set()


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
    """A keyed entry keeps its keys whole through every rule.

    Spec: ``openspec/specs/anonymization/keyed-entries`` (from the
    identifier-key-fields change), "An AS-list reference survives
    anonymization" and "No value anonymized before escapes".
    """

    @pytest.mark.parametrize(
        "line",
        [
            (
                "set policy-options policy-statement SAMPLE-POLICY term T1 from route-filter "
                "203.0.114.0/24 exact accept"
            ),
            "set protocols ospf area 0.0.0.0 area-range 203.0.114.0/24",
        ],
        ids=["route-filter", "ospf-area-range"],
    )
    def test_simple_content_ip_keys_are_anonymized(self, line: str) -> None:
        from junoscfg import Format, convert_config

        out = convert_config(
            line + "\n",
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(ips=True, salt="simple-content"),
        )
        assert "203.0.114.0/24" not in out
        assert " route-filter " in out or " area-range " in out

    @pytest.mark.parametrize(
        "line",
        [
            (
                "set policy-options policy-statement SAMPLE-POLICY term T1 from route-filter "
                "$ROUTE_PREFIX exact accept"
            ),
            "set protocols ospf area 0.0.0.0 area-range $AREA_RANGE",
        ],
        ids=["route-filter", "ospf-area-range"],
    )
    def test_simple_content_template_keys_add_no_ip_diagnostic(self, line: str) -> None:
        from junoscfg import Format, convert_config_result

        result = convert_config_result(
            line + "\n",
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(ips=True, salt="simple-content-template"),
        )
        messages = [diagnostic.message for diagnostic in result.diagnostics]
        assert not [message for message in messages if "not a valid IP" in message]
        template = "$" + line.rsplit("$", 1)[1].split()[0]
        assert template in result.output

    def test_an_as_list_reference_survives_anonymize_all(self) -> None:
        from junoscfg import Format, convert_config

        for source, fmt in ((_GROUPED, Format.STRUCTURED), (_GROUPED_SET, Format.SET)):
            cfg = build_config_from_cli(anonymize_all=True, anonymize_salt="keyed")
            out = convert_config(source, from_format=fmt, to_format=Format.SET, anon_config=cfg)
            found = _neighbor_lines(out)
            assert len(found) == 1, out
            list_type, list_name = found[0]
            assert list_type == "as-list"
            assert list_name, "the list name was lost"
            assert "SAMPLE-GROUP" not in out, "the group was not anonymized"

    def test_an_as_list_reference_survives_anonymize_all_with_as_numbers(self) -> None:
        """`--anonymize-all --anonymize-as-numbers 64496` on structured input.

        The reported defect wrote `as-path-neighbors as-list` with the list
        name gone; this is the third flag set the CLI test of it ran.
        """
        from junoscfg import Format, convert_config

        cfg = build_config_from_cli(
            anonymize_all=True, anonymize_as_numbers="64496", anonymize_salt="keyed"
        )
        out = convert_config(
            _GROUPED, from_format=Format.STRUCTURED, to_format=Format.SET, anon_config=cfg
        )
        found = _neighbor_lines(out)
        assert len(found) == 1, out
        list_type, list_name = found[0]
        assert list_type == "as-list"
        assert list_name, "the list name was lost"
        assert "SAMPLE-GROUP" not in out, "the group was not anonymized"
        assert "members 64496" not in out

    def test_as_numbers_leave_the_as_list_reference_whole(self) -> None:
        from junoscfg import Format, convert_config
        from tests.support.keyed_entries import as_json, ir

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

    @pytest.mark.parametrize(
        ("line", "word"),
        [
            (
                "set policy-options policy-statement SAMPLE-POLICY term T1 from as-path-neighbors"
                " as-list-group SAMPLE-NAMES",
                "as-list",
            ),
            ("set policy-options policy-statement SAMPLE-POLICY term T1 from protocol bgp", "bgp"),
        ],
    )
    def test_a_value_from_its_leafs_enum_passes_every_rule(self, line: str, word: str) -> None:
        """A leaf's own enum value is configuration syntax: no rule rewrites it.

        The sensitive word matches the enum value, and the IR comes out as it
        went in. Release 0.14.0 wrote `from protocol word_<hash>`, which the
        device rejects (anonymizer-bugs rows 4 and 5).
        """
        from junoscfg import Format, convert_config

        cfg = AnonymizeConfig(sensitive_words=[word], salt="keyed")
        anonymized = convert_config(
            line + "\n", from_format=Format.SET, to_format=Format.JSON, anon_config=cfg
        )
        plain = convert_config(line + "\n", from_format=Format.SET, to_format=Format.JSON)
        assert json.loads(anonymized) == json.loads(plain)
        assert word in plain

    #: What each rule must replace in `examples/junoscfg-oracle.json`, written
    #: from the example, not from the anonymizer's output. Addresses, passwords
    #: and SSH keys are read from the example itself (`_must_replace`).
    MUST_REPLACE = {
        "identity": {"admin", "operator"},
        "group": {
            *("GR-SYSTEM", "GR-EDGE-INTF", "GR-BGP", "GR-VRF", "GR-MACRO", "GR-ISIS-TPL"),
            *("GR-ACCESS-PORT", "GR-OMIT", "GR-UNUSED", "GR-PROTECTED"),
            *("CE", "EBGP", "EXPR", "IBGP", "RR", "TRANSIT"),
        },
        "description": {
            "set by GR-EDGE-INTF",
            "rack 4, row B",
            "access range",
            "access ports",
            'uplink to sw1 "core"',
            "uplink to sw1",
            "a;b {c} #d /* e */",
            "transit provider",
            "rr1 (route reflector)",
            "users",
        },
        "community": {"example-ro"},
        "as_number": {"64496", "64497", "64498", "64499", "64511"},
        "sensitive_word": {"CM-CUSTOMER"},
    }
    #: What a rule left in the output until change anonymize-every-placed-value
    #: (ANON-P2, NEW-C11): the IP rule skipped an address in a leaf the schema
    #: types `hostname` (`system tacplus-server 203.0.114.49 source-address
    #: 10.255.0.1`) and in the inactive port-mirroring `routing-instance VRF-A
    #: ip-address 10.0.0.1`, which the JSON reader keeps as a one-entry list;
    #: the walker entered a transparent container's own child only, so nothing
    #: under `interfaces interface-range` was seen. Now a regression row.
    ONCE_MISSED = {
        "ip": {"203.0.114.49", "10.255.0.1", "10.0.0.1"},
        "description": {"access range", "access ports"},
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
            as_numbers=[64496, 64497, 64498, 64499, 64511],
            sensitive_words=["customer"],
            salt="pinned-salt",
        )

    @classmethod
    def _must_replace(cls, source: dict) -> dict[str, set[str]]:
        """`MUST_REPLACE`, with every address of the device's set and every secret."""
        addresses = set()
        for line in example().device_set():
            for word in shlex.split(line):
                try:
                    ipaddress.ip_network(word, strict=False)
                except ValueError:
                    continue
                addresses.add(word)
        return {
            **cls.MUST_REPLACE,
            "ip": addresses,
            "password": _leaves(source, lambda key: key in {"encrypted-password", "secret"}),
            "ssh_key": _leaves(source, lambda key: key.startswith("ssh-")),
        }

    def test_no_value_anonymized_before_escapes(self, json_config: str) -> None:
        """Every value a rule covers in the example is replaced, everywhere it is.

        A fix may add, never drop. The floor was the values release 0.14.0
        replaced in the synthetic `examples/router1.json`; the example is now
        the device's, and the floor what it holds. A value a rule maps to
        itself is one it keeps by design (`0.0.0.0/0`, the RFC 1918 and
        documentation prefixes); a wildcard is `test_a_wildcard_group_name_passes_the_group_rule`.
        """
        source = json.loads(json_config)
        must = self._must_replace(source)
        assert all(must.values()), "a rule has nothing to replace in the example"
        result = anonymize(source, self._every_rule())
        for rule, values in must.items():
            missing = values - set(result.mapping.get(rule, {}))
            assert not missing, f"{rule} does not replace {sorted(missing)}"
        left = _strings(result.ir)
        for rule, replaced in result.mapping.items():
            kept = {
                value for value, by in replaced.items() if by != value and not value.startswith("<")
            }
            kept = kept & left
            assert not kept, f"{rule} leaves {sorted(kept)} in the output"

    @pytest.mark.parametrize("rule", ["ip", "description"])
    def test_what_a_rule_once_missed_is_replaced(self, rule: str, json_config: str) -> None:
        result = anonymize(json.loads(json_config), self._every_rule())
        assert self.ONCE_MISSED[rule] <= set(result.mapping.get(rule, {}))
        assert not self.ONCE_MISSED[rule] & _strings(result.ir)

    @pytest.mark.xfail(
        strict=True,
        reason="PRODUCT DEFECT: no known-differences class: the group rule replaces the "
        "wildcard `<*>` of `groups GR-BGP protocols bgp group <*>`, so the group then "
        "matches no BGP group",
    )
    def test_a_wildcard_group_name_passes_the_group_rule(self, json_config: str) -> None:
        mapping = anonymize(json.loads(json_config), self._every_rule()).mapping
        assert not [name for name in mapping.get("group", {}) if name.startswith("<")]

    def _anonymized(self, source: str, to_format: Format, dumped: Path) -> str:
        """*source* (JSON) in *to_format* with every rule on, its mapping dumped."""
        config = self._every_rule()
        config.dump_map = str(dumped)
        return convert_config(
            source, from_format=Format.JSON, to_format=to_format, validate=False, anon_config=config
        )

    @staticmethod
    def _reverted(text: str, fmt: Format, dumped: Path) -> object:
        """The IR *text* reads to with the mapping reverted."""
        revert = AnonymizeConfig(revert_map=str(dumped))
        return json.loads(
            convert_config(
                text, from_format=fmt, to_format=Format.JSON, validate=False, anon_config=revert
            )
        )

    def test_name_keyed_output_is_unchanged(self, tmp_path: Path, json_config: str) -> None:
        """For a fixed salt, every rule replaces the same values with the same values.

        Pinned before the identifier-key-fields change touched the walker, as
        a SHA-256 of the whole set output, and it held across the change. What
        is kept here is the anonymizer's share of that output. The dumped
        mapping is pinned byte for byte, because that is a requirement: the
        same input and the same salt give the same replacements on every run
        and every machine (`src/junoscfg/anonymize/CONTRACT.md`; a
        configuration anonymized on one machine has to match one anonymized on
        another, `rules/password.py`). The rest is meaning: the anonymized
        configuration differs from the original only by those replacements,
        so the mapping restores its IR.

        The input is the example, re-pinned when it became the device's,
        without the statements junoscfg cannot place
        (`tests/support/devices.py` `UNPLACED_IN_THE_EXAMPLE`): anonymization
        names each by its schema path. The pin leaves out the wildcard
        `<*>` the group rule replaces (`test_a_wildcard_group_name_passes_the_group_rule`).
        The IR is restored through JSON output here; through set output it is
        `test_the_mapping_restores_the_set_output`.

        Re-pinned by change anonymize-every-placed-value (`b8c3da05…` to
        `8e13d961…`): 92 entries became 95, none dropped or altered. Added:
        `description` `access range` and `access ports`, the `interface-range`
        descriptions beside `interface` the walker never saw (NEW-C11); `ip`
        `203.0.114.49`, the `tacplus-server` key the tree types `hostname`
        (NEW-A-N6). `10.255.0.1` and `10.0.0.1`, also once missed, were mapped
        already from their other occurrences.
        """
        source = json.dumps(placed_only(json.loads(json_config)))
        self._anonymized(source, Format.SET, tmp_path / "map.json")
        mapping = json.loads((tmp_path / "map.json").read_text(encoding="utf-8"))
        pinned = {
            rule: {value: by for value, by in values.items() if not value.startswith("<")}
            for rule, values in mapping.items()
        }
        assert (
            hashlib.sha256(json.dumps(pinned, sort_keys=True).encode()).hexdigest()
            == "8e13d961b885c80dae3cdbad1e999012b81af51c9ea7eda3cd1148570974cb93"
        )

        out = self._anonymized(source, Format.JSON, tmp_path / "json-map.json")
        plain = convert_config(source, from_format=Format.JSON, to_format=Format.JSON)
        assert self._reverted(out, Format.JSON, tmp_path / "json-map.json") == json.loads(plain)

    @pytest.mark.xfail(
        strict=True,
        reason="PRODUCT DEFECT: escaped-quote-lost: the plain set output writes ge-0/0/0's "
        "description with its inner quotes bare, which reads back as another value; the "
        "anonymized output carries a pseudonym there instead",
    )
    def test_the_mapping_restores_the_set_output(self, tmp_path: Path, json_config: str) -> None:
        """Reverted, the anonymized set output reads to the IR the plain set output reads to."""
        source = json.dumps(placed_only(json.loads(json_config)))
        out = self._anonymized(source, Format.SET, tmp_path / "map.json")
        plain = convert_config(
            source, from_format=Format.JSON, to_format=Format.SET, validate=False
        )
        original = convert_config(
            plain, from_format=Format.SET, to_format=Format.JSON, validate=False
        )
        assert self._reverted(out, Format.SET, tmp_path / "map.json") == json.loads(original)


class TestGroupReferencesResolve:
    """A group and every `apply-groups` or `apply-groups-except` naming it get
    one replacement, at every level and whichever rules are on.

    A second pass rewrote every reference after the walk, so with the group
    and sensitive-word rules on the root's reference named no group and revert
    failed (ANON-P1, NEW-C13); below the root the walker never saw a
    reference, so a sensitive word survived there (NEW-A-N1). Spec
    anonymization/placed-values.
    """

    _IR: dict[str, Any] = {
        "configuration": {
            "apply-groups": ["acme-base"],
            "groups": [{"name": "acme-base", "system": {"host-name": "router1"}}],
            "system": {"apply-groups": ["acme-base"]},
            "interfaces": {
                "apply-groups-except": ["acme-base"],
                "interface": [{"name": "ge-0/0/0", "apply-groups": ["acme-base"]}],
            },
            "protocols": {"bgp": {"group": [{"name": "EBGP", "apply-groups": ["acme-base"]}]}},
        }
    }

    @staticmethod
    def _references(ir: dict[str, Any]) -> list[str]:
        cfg = ir["configuration"]
        return [
            *cfg["apply-groups"],
            *cfg["system"]["apply-groups"],
            *cfg["interfaces"]["apply-groups-except"],
            *cfg["interfaces"]["interface"][0]["apply-groups"],
            *cfg["protocols"]["bgp"]["group"][0]["apply-groups"],
        ]

    @pytest.mark.parametrize(
        "options",
        [
            {"groups": True},
            {"sensitive_words": ["acme"]},
            {"groups": True, "sensitive_words": ["acme"]},
        ],
        ids=["groups", "sensitive-words", "both"],
    )
    def test_every_reference_names_the_renamed_group(self, options: dict[str, Any]) -> None:
        from junoscfg.anonymize import apply_revert

        source = json.loads(json.dumps(self._IR))
        result = anonymize(json.loads(json.dumps(self._IR)), AnonymizeConfig(salt="s", **options))
        group = result.ir["configuration"]["groups"][0]["name"]
        assert group != "acme-base"
        assert self._references(result.ir) == [group] * 5
        assert apply_revert(result.ir, result.mapping) == source


class TestAGroupJunosReservesKeepsItsName:
    """`re0`, `re1` (`lcc<N>-re<N>`, `sfc<N>-re<N>` in a routing matrix),
    `node0`, `node1`, `member<N>` name a group Junos applies to that Routing
    Engine, cluster node or Virtual Chassis member, and `${node}`
    is expanded by Junos at commit (Junos OS "Configuration Groups"
    documentation). Renamed, they apply nowhere: they pass the group rule as a
    group and as a reference (ruling on Test/Challenge finding 7). No committed
    device capture holds one."""

    def test_the_reserved_names_pass(self) -> None:
        names = ["re0", "re1", "node0", "node1", "member0", "member1", "lcc0-re0", "sfc0-re1"]
        ir = {
            "configuration": {
                "groups": [{"name": name, "system": {"host-name": "router1"}} for name in names]
                + [{"name": "SAMPLE-GROUP", "system": {"host-name": "router1"}}],
                "apply-groups": [*names, "${node}", "SAMPLE-GROUP"],
            }
        }
        result = anonymize(json.loads(json.dumps(ir)), AnonymizeConfig(groups=True, salt="s"))
        cfg = result.ir["configuration"]
        assert [group["name"] for group in cfg["groups"]][:-1] == names
        assert cfg["apply-groups"][:-1] == [*names, "${node}"]
        assert cfg["apply-groups"][-1] == cfg["groups"][-1]["name"] != "SAMPLE-GROUP"


#: Content the walk cannot place, as the library door meets it: the IR, the
#: schema paths `AnonymizeResult.unplaced` names, one per piece ("" for the top
#: level), and the words other than addresses that stay as written.
_UNPLACED: dict[str, tuple[dict[str, Any], tuple[str, ...], set[str]]] = {
    "unknown-leaf": (
        {"protocols": {"bgp": {"group": [{"name": "G1", "unknown-knob": "203.0.114.9"}]}}},
        ("protocols.bgp.group",),
        {"unknown-knob"},
    ),
    "unknown-container": (
        {
            "protocols": {
                "bgp": {
                    "group": [
                        {"name": "G1", "unknown-box": {"peer": "203.0.114.9", "note": "G-SECRET"}}
                    ]
                }
            }
        },
        ("protocols.bgp.group",),
        {"unknown-box", "peer", "G-SECRET"},
    ),
    "unknown-top-level": ({"made-up": {"x": ["203.0.114.9"]}}, ("",), {"made-up"}),
    "joined-key-0.16.1": (
        {"system": {"bogus 203.0.114.9 G-SECRET": [None]}},
        ("system",),
        {"bogus", "G-SECRET"},
    ),
    "joined-key-inactive": (
        {
            "system": {
                "bogus 203.0.114.9 G-SECRET": [None],
                "@bogus 203.0.114.9 G-SECRET": {"inactive": True},
            }
        },
        ("system",),
        {"bogus", "G-SECRET", "inactive"},
    ),
    "address-as-key": ({"system": {"203.0.114.9": {"peer": "x"}}}, ("system",), {"peer"}),
    "ipv6-as-key": ({"system": {"3ffe:0b00::9": {"peer": "x"}}}, ("system",), {"peer"}),
    "prefix-as-key": ({"system": {"203.0.114.0/24": [None]}}, ("system",), set()),
    "kept-statement": (
        {
            "system": {
                "junoscfg:unplaced": {
                    'nonsense 203.0.114.9 "G-SECRET"': True,
                    '@nonsense 203.0.114.9 "G-SECRET"': {"inactive": True},
                }
            }
        },
        ("system",),
        {"nonsense", "G-SECRET"},
    ),
    "kept-statement-quoted": (
        {
            "system": {
                "junoscfg:unplaced": {
                    'bogus "203.0.114.9"': True,
                    'bogus "peer 203.0.114.10"': True,
                }
            }
        },
        ("system", "system"),
        {"bogus", "peer"},
    ),
    "scalar-on-a-container": ({"system": {"services": "203.0.114.9"}}, ("system.services",), set()),
    "scalar-in-a-keyed-list": (
        {"protocols": {"bgp": {"group": [{"name": "G1", "neighbor": ["203.0.114.9"]}]}}},
        ("protocols.bgp.group.neighbor",),
        set(),
    ),
    "dict-on-a-leaf": (
        {"system": {"host-name": {"203.0.114.9": "203.0.114.10"}}},
        ("system.host-name",),
        set(),
    ),
    "list-of-dicts-on-a-leaf": (
        {"system": {"host-name": [{"peer": "203.0.114.9"}]}},
        ("system.host-name",),
        {"peer"},
    ),
    "unknown-list-of-dicts": (
        {"system": {"bogus": [{"peer": "203.0.114.9"}, {"peer": "203.0.114.10"}]}},
        ("system",),
        {"bogus", "peer"},
    ),
    "ipv6-and-prefix": (
        {"system": {"bogus": ["3ffe:0b00::9", "peer 203.0.114.0/24"]}},
        ("system",),
        {"bogus", "peer"},
    ),
    "url-port-in-a-key": (
        {"system": {"bogus http://203.0.114.9:8080/x": [None]}},
        ("system",),
        {"bogus"},
    ),
    "url-port-in-a-value": (
        {"system": {"bogus": "http://203.0.114.9:8080/x"}},
        ("system",),
        {"bogus"},
    ),
    "address-port-in-a-key": (
        {"system": {"bogus 203.0.114.9:179": [None]}},
        ("system",),
        {"bogus"},
    ),
    "address-port-in-a-value": ({"system": {"bogus": "203.0.114.9:179"}}, ("system",), {"bogus"}),
    "host-address-in-a-key": (
        {"system": {"bogus host:203.0.114.9": [None]}},
        ("system",),
        {"bogus"},
    ),
    "host-address-in-a-value": ({"system": {"bogus": "host:203.0.114.9"}}, ("system",), {"bogus"}),
    "lo-address-in-a-key": (
        {"system": {"bogus lo_203.0.114.9": [None]}},
        ("system",),
        {"bogus"},
    ),
    "lo-address-in-a-value": ({"system": {"bogus": "lo_203.0.114.9"}}, ("system",), {"bogus"}),
    "peer-equals-in-a-key": (
        {"system": {"bogus peer=203.0.114.9": [None]}},
        ("system",),
        {"bogus"},
    ),
    "peer-equals-in-a-value": ({"system": {"bogus": "peer=203.0.114.9"}}, ("system",), {"bogus"}),
    "scp-url-in-a-key": (
        {"system": {"bogus scp://u@203.0.114.9/f": [None]}},
        ("system",),
        {"bogus"},
    ),
    "scp-url-in-a-value": ({"system": {"bogus": "scp://u@203.0.114.9/f"}}, ("system",), {"bogus"}),
    "address-rack-in-a-key": (
        {"system": {"bogus 203.0.114.9/rack-4": [None]}},
        ("system",),
        {"bogus"},
    ),
    "address-rack-in-a-value": (
        {"system": {"bogus": "203.0.114.9/rack-4"}},
        ("system",),
        {"bogus"},
    ),
    "bracketed-ipv6-port-in-a-key": (
        {"system": {"bogus [3ffe:0b00::9]:179": [None]}},
        ("system",),
        {"bogus"},
    ),
    "bracketed-ipv6-port-in-a-value": (
        {"system": {"bogus": "[3ffe:0b00::9]:179"}},
        ("system",),
        {"bogus"},
    ),
    "a-switch-spelling-holding-a-value": (
        {"interfaces": {"interface": [{"name": "ge-0/0/0", "disable": "203.0.114.9"}]}},
        ("interfaces",),
        {"disable"},
    ),
}

_ADDRESSES = ("203.0.114.9", "203.0.114.10", "3ffe:0b00::9", "203.0.114.0/24")


class TestContentTheWalkCannotPlace:
    """Owner answer 5: under a path the schema does not know, the addresses
    are replaced by their shape (never a keyword) and the path is named.

    The walker returned at a key its node did not name, so `anonymize()`
    passed an unknown key's addresses with no word (ARCH-C05, NEW-R5: a
    0.16.1 joined key, an unknown leaf), and refused a statement kept whole
    (`junoscfg:unplaced`), which the same statement from JSON is not
    (specification challenge S1 of change anonymize-every-placed-value). The
    path is the schema's names from the root: the unknown key, entry names
    and values are withheld (lesson #1 of the makeover run). Spec
    anonymization/placed-values.
    """

    @staticmethod
    def _source(shape: str) -> dict[str, Any]:
        content = json.loads(json.dumps(_UNPLACED[shape][0]))
        content["routing-options"] = {"router-id": "203.0.114.9"}
        return {"configuration": content}

    @pytest.mark.parametrize("shape", list(_UNPLACED))
    def test_its_addresses_are_replaced(self, shape: str) -> None:
        result = anonymize(self._source(shape), AnonymizeConfig(ips=True, salt="s"))
        text = json.dumps(result.ir)
        for address in _ADDRESSES:
            assert address not in text
        assert "203.0.114.9" in result.mapping["ip"]
        pseudonym = result.mapping["ip"]["203.0.114.9"]
        assert pseudonym == result.ir["configuration"]["routing-options"]["router-id"]
        if "203.0.114.9" in json.dumps(_UNPLACED[shape][0]):
            assert text.count(pseudonym) >= 2, "the unplaced address took another pseudonym"

    @pytest.mark.parametrize("shape", list(_UNPLACED))
    def test_its_schema_path_is_named(self, shape: str) -> None:
        result = anonymize(self._source(shape), AnonymizeConfig(ips=True, salt="s"))
        assert result.unplaced == _UNPLACED[shape][1]
        named = " ".join(result.unplaced)
        for original in (*_ADDRESSES, "G-SECRET", "G1", "unknown", "bogus", "nonsense", "made-up"):
            assert original not in named

    @pytest.mark.parametrize("shape", list(_UNPLACED))
    def test_every_other_word_is_left_as_written(self, shape: str) -> None:
        result = anonymize(self._source(shape), AnonymizeConfig(ips=True, salt="s"))
        text = json.dumps(result.ir)
        for word in _UNPLACED[shape][2]:
            assert word in text

    @pytest.mark.parametrize("shape", list(_UNPLACED))
    def test_the_mapping_restores_it(self, shape: str) -> None:
        from junoscfg.anonymize import apply_revert

        result = anonymize(self._source(shape), AnonymizeConfig(ips=True, salt="s"))
        assert apply_revert(result.ir, result.mapping) == self._source(shape)

    @pytest.mark.parametrize("shape", list(_UNPLACED))
    def test_without_the_ip_rule_it_is_still_named(self, shape: str) -> None:
        result = anonymize(self._source(shape), AnonymizeConfig(descriptions=True, salt="s"))
        assert result.ir == self._source(shape)
        assert result.unplaced == _UNPLACED[shape][1]
        converted = convert_config_result(
            json.dumps(self._source(shape)),
            from_format=Format.JSON,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(descriptions=True, salt="s"),
        )
        warnings = [d.message for d in converted.diagnostics if d.source == "anonymize"]
        assert warnings, "the conversion names what it could not place"
        assert all("no active rule replaces a word" in w for w in warnings)
        assert not any("address" in w for w in warnings), "it claimed a replacement"

    @pytest.mark.parametrize(
        ("options", "replaced"),
        [
            ({"ips": True}, "each address in it is replaced"),
            ({"passwords": True}, "each password hash in it is replaced"),
            ({"sensitive_words": ["acme"]}, "each sensitive word in it is replaced"),
            (
                {"ips": True, "passwords": True, "sensitive_words": ["acme"]},
                "each address or password hash or sensitive word in it is replaced",
            ),
        ],
        ids=["address", "password-hash", "sensitive-word", "all-three"],
    )
    def test_the_warning_names_each_shape_it_replaces(
        self, options: dict[str, Any], replaced: str
    ) -> None:
        """The warning reads "each address ... in it is replaced", not "each an
        address" (cosmetic carry-forward of change anonymize-every-placed-value,
        its review)."""
        converted = convert_config_result(
            json.dumps({"configuration": {"system": {"bogus-knob": "x"}}}),
            from_format=Format.JSON,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(salt="s", **options),
        )
        warnings = [d.message for d in converted.diagnostics if d.source == "anonymize"]
        assert warnings == [
            "1 statement(s) here the schema does not place: "
            f"{replaced}, every other word is left as written"
        ]

    @pytest.mark.parametrize(
        "content",
        [
            {"bogus": "$9$ExAmPlEhAsH.KEY acme-site"},
            {"junoscfg:unplaced": {'bogus "$9$ExAmPlEhAsH.KEY" acme-site': True}},
        ],
        ids=["unknown-key", "kept-statement"],
    )
    def test_a_password_hash_and_a_sensitive_word_are_replaced_by_shape(
        self, content: dict[str, Any]
    ) -> None:
        """The rules that know a word by its shape alone -- a password hash, a
        sensitive word -- rewrite it as the address rule does; a keyword
        never (ruling on Test/Challenge finding 8, specification challenge S2
        of change anonymize-every-placed-value)."""
        from junoscfg.anonymize import apply_revert

        source = {"configuration": {"system": content}}
        config = AnonymizeConfig(passwords=True, sensitive_words=["acme"], salt="s")
        result = anonymize(json.loads(json.dumps(source)), config)
        text = json.dumps(result.ir)
        assert "ExAmPlEhAsH" not in text
        assert "acme" not in text
        assert "bogus" in text
        assert result.unplaced == ("system",)
        assert apply_revert(result.ir, result.mapping) == source

    @pytest.mark.parametrize(
        "content",
        [
            {"bogus": "acme-203.0.114.9"},
            {"bogus": "203.0.114.9-acme"},
            {"bogus acme-203.0.114.9": [None]},
            {
                "apply-macro": [
                    {"name": "M", "data": [{"name": "peer", "value": "203.0.114.9-acme"}]}
                ]
            },
        ],
        ids=["value-word-address", "value-address-word", "key", "nested-apply-macro-value"],
    )
    def test_every_shape_in_one_word_is_replaced(self, content: dict[str, Any]) -> None:
        """The rules apply in turn to the same word: the address rule keeps the
        text around the address, so the sensitive-word rule still sees `acme`
        (Reviewer finding 5)."""
        from junoscfg.anonymize import apply_revert

        source = {"configuration": {"system": content}}
        config = AnonymizeConfig(ips=True, sensitive_words=["acme"], salt="s")
        result = anonymize(json.loads(json.dumps(source)), config)
        text = json.dumps(result.ir)
        assert "acme" not in text
        assert "203.0.114.9" not in text
        assert apply_revert(result.ir, result.mapping) == source

    def test_without_a_rule_nothing_changes(self) -> None:
        source = self._source("kept-statement")
        result = anonymize(self._source("kept-statement"), AnonymizeConfig())
        assert result.ir == source
        assert result.unplaced == ()


#: One statement the schema does not place, through every input door: the
#: format, the source, and the schema path the warning names.
_SECRET_LEAF = "203.0.114.9 G-SECRET"
_DOORS: dict[str, tuple[Format, str, str]] = {
    "set": (
        Format.SET,
        "set protocols bgp group SAMPLE-PEERS unknown-knob 203.0.114.9 G-SECRET\n"
        "deactivate protocols bgp group SAMPLE-PEERS unknown-knob 203.0.114.9 G-SECRET\n",
        "protocols.bgp.group",
    ),
    "structured": (
        Format.STRUCTURED,
        "protocols {\n    bgp {\n        group SAMPLE-PEERS {\n"
        "            unknown-knob 203.0.114.9 G-SECRET;\n        }\n    }\n}\n",
        "protocols.bgp.group",
    ),
    "json": (
        Format.JSON,
        json.dumps(
            {
                "configuration": {
                    "protocols": {
                        "bgp": {"group": [{"name": "SAMPLE-PEERS", "unknown-knob": _SECRET_LEAF}]}
                    }
                }
            }
        ),
        "protocols.bgp.group",
    ),
    "yaml": (
        Format.YAML,
        "configuration:\n  protocols:\n    bgp:\n      group:\n        - name: SAMPLE-PEERS\n"
        f"          unknown-knob: {_SECRET_LEAF}\n",
        "protocols.bgp.group",
    ),
    "xml": (
        Format.XML,
        "<configuration><protocols><bgp><group><name>SAMPLE-PEERS</name>"
        f"<unknown-knob>{_SECRET_LEAF}</unknown-knob></group></bgp></protocols></configuration>",
        "protocols.bgp.group",
    ),
    "json-joined-key": (
        Format.JSON,
        json.dumps({"configuration": {"system": {"bogus 203.0.114.9 G-SECRET": [None]}}}),
        "system",
    ),
    "json-joined-key-inactive": (
        Format.JSON,
        json.dumps(
            {
                "configuration": {
                    "system": {
                        "bogus 203.0.114.9 G-SECRET": [None],
                        "@bogus 203.0.114.9 G-SECRET": {"inactive": True},
                    }
                }
            }
        ),
        "system",
    ),
}
#: The doors whose statement is deactivated: their output keeps the tag.
_DEACTIVATED = ("set", "json-joined-key-inactive")


class TestEveryDoorGivesOneAnswer:
    """Every input door and both anonymizing doors give owner rule 5's answer.

    The conversion refused every statement the schema could not place, the
    library passed it unchanged (NEW-R5). Now both replace its addresses and
    name its schema path in a warning; no message of the run -- the warning,
    field validation's `UNPLACED` report, the `--strict` error -- carries the
    address, the word beside it, the group's name or the unknown key, since
    the text no rule rewrote is original (lesson #1 of the makeover run).
    Spec anonymization/placed-values.
    """

    @staticmethod
    def _config() -> AnonymizeConfig:
        return AnonymizeConfig(ips=True, groups=True, salt="s")

    @pytest.mark.parametrize("to_format", [Format.SET, Format.STRUCTURED, Format.JSON, Format.YAML])
    @pytest.mark.parametrize("door", list(_DOORS))
    def test_no_address_passes_and_a_warning_names_the_path(
        self, door: str, to_format: Format
    ) -> None:
        from junoscfg import convert_config_result

        fmt, source, path = _DOORS[door]
        result = convert_config_result(
            source, from_format=fmt, to_format=to_format, anon_config=self._config()
        )
        assert "203.0.114.9" not in result.output
        assert "SAMPLE-PEERS" not in result.output
        assert "G-SECRET" in result.output, "a word that is no address is left as written"
        warnings = [d for d in result.diagnostics if d.source == "anonymize"]
        assert [(d.path, d.severity) for d in warnings] == [(path, "warning")]
        if door in _DEACTIVATED and to_format == Format.SET:
            # The tag follows the rewritten statement: still deactivated.
            assert [line for line in result.output.splitlines() if line.startswith("deactivate")]

    @pytest.mark.parametrize("door", list(_DOORS))
    def test_no_message_carries_an_original_value(self, door: str) -> None:
        from junoscfg import FieldValidationError, convert_config_result

        fmt, source, _ = _DOORS[door]
        originals = ("203.0.114.9", "G-SECRET", "SAMPLE-PEERS", "unknown-knob", "bogus")
        result = convert_config_result(
            source, from_format=fmt, to_format=Format.SET, anon_config=self._config()
        )
        assert result.diagnostics, "the run reports what it could not place"
        for diagnostic in result.diagnostics:
            for original in originals:
                assert original not in diagnostic.render()
        with pytest.raises(FieldValidationError) as raised:
            convert_config_result(
                source,
                from_format=fmt,
                to_format=Format.SET,
                anon_config=self._config(),
                strict=True,
            )
        messages = [str(raised.value)] + [
            f"{e.path} {e.message} {e.value}" for e in raised.value.result.errors
        ]
        for message in messages:
            for original in originals:
                assert original not in message


def _containers(node: Any) -> dict[int, Any]:
    """Every dict and list in *node*, by identity."""
    found: dict[int, Any] = {}
    if isinstance(node, (dict, list)):
        found[id(node)] = node
        for item in node.values() if isinstance(node, dict) else node:
            found |= _containers(item)
    return found


class TestAnonymizeLeavesItsInputAlone:
    """`anonymize()` copies its input once on entry and rewrites only the copy.

    It rewrote the caller's IR in place, which no document said (NEW-R3): a
    caller who kept the IR held the pseudonyms and lost the original. The
    writers copy once for the same reason (change json-writer-pure).
    `apply_revert` and `walk` document that they rewrite their argument and
    keep doing so: a copy would make a documented call whose result is
    ignored a silent no-op. Spec anonymization/placed-values.
    """

    _CONFIGS = {
        "no-rule": AnonymizeConfig(salt="s"),
        "ips": AnonymizeConfig(ips=True, salt="s"),
        "every-rule": AnonymizeConfig(
            ips=True,
            passwords=True,
            communities=True,
            ssh_keys=True,
            identities=True,
            groups=True,
            descriptions=True,
            ips_in_strings=True,
            as_numbers=[64496, 64497],
            as_numbers_in_strings=True,
            sensitive_words=["acme"],
            salt="s",
        ),
    }

    @staticmethod
    def _source() -> dict[str, Any]:
        source = json.loads(example().rendering("json"))
        source["configuration"]["system"]["bogus-knob 203.0.114.9"] = None
        return source

    @pytest.mark.parametrize("name", list(_CONFIGS))
    def test_the_callers_ir_is_unchanged(self, name: str) -> None:
        ir = self._source()
        result = anonymize(ir, self._CONFIGS[name])
        assert ir == self._source()
        if name != "no-rule":
            assert result.ir != ir, "the run anonymized nothing, so nothing was tested"

    @pytest.mark.parametrize("name", list(_CONFIGS))
    def test_the_result_shares_nothing_with_it(self, name: str) -> None:
        ir = self._source()
        result = anonymize(ir, self._CONFIGS[name])
        shared = _containers(ir).keys() & _containers(result.ir).keys()
        assert not shared, f"{len(shared)} dicts or lists are the caller's own"

    def test_revert_still_rewrites_in_place(self) -> None:
        from junoscfg.anonymize import apply_revert

        result = anonymize(self._source(), self._CONFIGS["ips"])
        restored = apply_revert(result.ir, result.mapping)
        assert restored is result.ir
        assert result.ir == self._source()
