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

from junoscfg import Format, convert_config
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
    #: What a rule leaves in the output today. PRODUCT DEFECT, no
    #: known-differences class (the record is of set renderings): the IP rule
    #: skips an address in a leaf the schema types `hostname` (`system
    #: tacplus-server 203.0.114.49 source-address 10.255.0.1`) and in the
    #: inactive port-mirroring `routing-instance VRF-A ip-address 10.0.0.1`,
    #: which the JSON reader keeps as a one-entry list; the walker enters a
    #: transparent container's own child only, so nothing under `interfaces
    #: interface-range` is seen.
    MISSED = {
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
            missing = values - self.MISSED.get(rule, set()) - set(result.mapping.get(rule, {}))
            assert not missing, f"{rule} does not replace {sorted(missing)}"
        left = _strings(result.ir)
        for rule, replaced in result.mapping.items():
            kept = {
                value for value, by in replaced.items() if by != value and not value.startswith("<")
            }
            kept = (kept & left) - self.MISSED.get(rule, set())
            assert not kept, f"{rule} leaves {sorted(kept)} in the output"

    @pytest.mark.xfail(strict=True, reason="PRODUCT DEFECT: no known-differences class; see MISSED")
    @pytest.mark.parametrize("rule", ["ip", "description"])
    def test_what_a_rule_misses_today_is_replaced(self, rule: str, json_config: str) -> None:
        result = anonymize(json.loads(json_config), self._every_rule())
        assert self.MISSED[rule] <= set(result.mapping.get(rule, {}))
        assert not self.MISSED[rule] & _strings(result.ir)

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
        refuses a configuration holding one. The pin leaves out the wildcard
        `<*>` the group rule replaces (`test_a_wildcard_group_name_passes_the_group_rule`).
        The IR is restored through JSON output here; through set output it is
        `test_the_mapping_restores_the_set_output`.
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
            == "b8c3da0573385b58ec1f9a156d3e2ad62f279e92084beaf6dd3b36ee26aace99"
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
