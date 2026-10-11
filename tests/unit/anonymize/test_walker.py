"""Tests for the schema-guided anonymization walker.

Every test goes through ``walk``, the walker's door, against the bundled tree,
with test rules that decide on the schema node the walker hands them.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

import pytest
from click.testing import CliRunner

from junoscfg import Format, convert_config
from junoscfg.anonymize import AnonymizeConfig, Rule, anonymize, apply_revert, walk
from junoscfg.cli import main

if TYPE_CHECKING:
    from pathlib import Path

#: The types the bundled tree declares for the address leaves used below.
_ADDRESS_TYPES = frozenset({"ipaddr", "ipv4prefix"})


class StubRule(Rule):
    """Test rule that matches on the leaf's declared address type and marks values."""

    name = "stub"
    priority = 10

    def __init__(self, match_types: frozenset[str] = _ADDRESS_TYPES) -> None:
        self.match_types = match_types
        self.seen: list[str] = []

    def matches(self, value: Any, schema_node: dict[str, Any], path: list[str]) -> bool:
        return schema_node.get("atr", schema_node.get("tr")) in self.match_types

    def transform(self, value: str) -> str:
        self.seen.append(value)
        return f"ANON_{value}"

    def get_mapping(self) -> dict[str, str]:
        return {v: f"ANON_{v}" for v in self.seen}


def _walk(ir: dict[str, Any], *rules: Rule) -> dict[str, Any]:
    """Walk *ir*, wrapped as a configuration, with *rules*; return the configuration."""
    wrapped = {"configuration": ir}
    walk(wrapped, list(rules), AnonymizeConfig())
    return wrapped["configuration"]


def _address_ir(address: str, interface: str = "ge-0/0/0") -> dict[str, Any]:
    return {
        "interfaces": {
            "interface": [
                {
                    "name": interface,
                    "unit": [
                        {
                            "name": "0",
                            "family": {"inet": {"address": [{"name": address}]}},
                        },
                    ],
                },
            ],
        },
    }


def _address(ir: dict[str, Any]) -> str:
    return ir["interfaces"]["interface"][0]["unit"][0]["family"]["inet"]["address"][0]["name"]


class TestRulesAtALeaf:
    """Which rule the walker applies to a leaf it reaches."""

    def test_a_matching_rule_transforms_the_leaf(self) -> None:
        ir = _walk(_address_ir("10.1.2.3/24"), StubRule())
        assert _address(ir) == "ANON_10.1.2.3/24"

    def test_a_leaf_no_rule_matches_is_unchanged(self) -> None:
        ir = _walk({"system": {"host-name": "hello"}}, StubRule())
        assert ir == {"system": {"host-name": "hello"}}

    def test_the_first_matching_rule_wins(self) -> None:
        rule1 = StubRule()
        rule1.priority = 10
        rule2 = StubRule()
        rule2.priority = 20
        ir = _walk({"system": {"name-server": [{"name": "10.0.0.1"}]}}, rule1, rule2)
        assert ir["system"]["name-server"][0]["name"] == "ANON_10.0.0.1"
        assert len(rule1.seen) == 1
        assert len(rule2.seen) == 0


class TestTheWalkerTraversal:
    """The walker reaches every leaf the tree declares, through lists and containers."""

    def test_walks_leaf_with_matching_type(self) -> None:
        ir = _walk(_address_ir("10.1.2.3/24"), StubRule())
        # The IP address should have been transformed
        assert _address(ir) == "ANON_10.1.2.3/24"

    def test_walks_named_list(self) -> None:
        ir = _walk(
            {"system": {"name-server": [{"name": "8.8.8.8"}, {"name": "8.8.4.4"}]}},
            StubRule(),
        )
        assert ir["system"]["name-server"][0]["name"] == "ANON_8.8.8.8"
        assert ir["system"]["name-server"][1]["name"] == "ANON_8.8.4.4"

    def test_skips_non_matching_leaves(self) -> None:
        ir = _walk({"system": {"host-name": "router1"}}, StubRule())
        assert ir["system"]["host-name"] == "router1"

    def test_skips_attribute_keys(self) -> None:
        ir = _walk(
            {"@": {"xmlns": "http://example.com"}, "system": {"host-name": "router1"}},
            StubRule(),
        )
        # @ keys should be preserved unchanged
        assert ir["@"] == {"xmlns": "http://example.com"}

    def test_transparent_container_traversal(self) -> None:
        ir = _walk(_address_ir("192.168.1.1/32", interface="lo0"), StubRule())
        assert _address(ir) == "ANON_192.168.1.1/32"

    def test_an_unwrapped_ir_is_walked_from_the_configuration_root(self) -> None:
        """An IR without the ``configuration`` wrapper is walked as its content."""
        ir = {"system": {"name-server": [{"name": "10.0.0.1"}]}}
        walk(ir, [StubRule()], AnonymizeConfig())
        assert ir["system"]["name-server"][0]["name"] == "ANON_10.0.0.1"


class RecordingRule(Rule):
    """Sees every leaf the walker offers; matches none."""

    name = "recording"
    priority = 1

    def __init__(self) -> None:
        self.seen: list[tuple[str, dict[str, Any], tuple[str, ...]]] = []

    def matches(self, value: Any, schema_node: dict[str, Any], path: list[str]) -> bool:
        self.seen.append((value, schema_node, tuple(path)))
        return False

    def transform(self, value: str) -> str:  # pragma: no cover - never matched
        return value


def _bundled_tree() -> dict[str, Any]:
    from junoscfg.display import load_schema_tree

    tree = load_schema_tree()
    assert tree is not None
    return tree


def _schema_at(*path: str) -> dict[str, Any]:
    current = _bundled_tree()
    for name in path:
        current = current["c"][name]
    return current


def _walked(ir: dict[str, Any]) -> RecordingRule:
    rule = RecordingRule()
    walk({"configuration": ir}, [rule], AnonymizeConfig())
    return rule


_FROM = ("policy-options", "policy-statement", "term", "from")


def _term(where: str, slot: str, entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy-options": {
            "policy-statement": [
                {"name": "SAMPLE-POLICY", "term": [{"name": "T1", where: {slot: [entry]}}]}
            ]
        }
    }


class TestKeyFieldsAreLeaves:
    """A list entry's key fields are the leaves the tree declares for them.

    Spec: ``openspec/specs/anonymization/keyed-entries`` (from the
    identifier-key-fields change). Through `walk` against the bundled tree,
    with a rule that records what it is asked and changes nothing.
    """

    def test_a_key_field_carries_the_trees_type(self) -> None:
        rule = _walked(
            _term(
                "from", "as-path-neighbors", {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"}
            )
        )
        declared = _schema_at(*_FROM, "as-path-neighbors")["c"]
        seen = {value: (schema, path) for value, schema, path in rule.seen}
        assert "SAMPLE-AS-LIST" in seen, "list-name was never offered to a rule"
        schema, path = seen["SAMPLE-AS-LIST"]
        assert schema is declared["list-name"]
        assert path[-2:] == ("as-path-neighbors", "list-name")

        rule = _walked(
            _term("from", "route-filter", {"address": "198.51.100.0/24", "exact": [None]})
        )
        seen = {value: schema for value, schema, _ in rule.seen}
        declared = _schema_at(*_FROM, "route-filter")["c"]["address"]
        assert seen["198.51.100.0/24"] is declared
        assert seen["198.51.100.0/24"].get("tr") == declared.get("tr")

    def test_a_key_choice_keyword_passes_unchanged(self) -> None:
        entry = {"address": "198.51.100.0/24", "exact": [None], "accept": [None]}
        community = {"add": [None], "community-name": "SAMPLE-COMM"}
        ir = _term("from", "route-filter", entry)
        ir["policy-options"]["policy-statement"][0]["term"][0]["then"] = {"community": [community]}
        config = AnonymizeConfig(
            ips=True,
            passwords=True,
            communities=True,
            ssh_keys=True,
            identities=True,
            groups=True,
            descriptions=True,
            as_numbers=[64496],
            salt="s",
        )
        result = anonymize({"configuration": ir}, config)
        term = result.ir["configuration"]["policy-options"]["policy-statement"][0]["term"][0]
        anonymized = term["from"]["route-filter"][0]
        assert anonymized["exact"] == [None] and anonymized["accept"] == [None]
        assert list(anonymized) == ["address", "exact", "accept"]
        assert term["then"]["community"][0]["add"] == [None]
        assert list(term["then"]["community"][0]) == ["add", "community-name"]
        # The keywords are no leaves, so no rule is offered them.
        rule = _walked(_term("from", "route-filter", entry))
        assert [v for v, _, p in rule.seen if p[-1] in ("exact", "accept")] == []
        assert "198.51.100.0/24" in [v for v, _, _ in rule.seen]

    def test_no_name_leaf_is_synthesised(self) -> None:
        rule = _walked({"policy-options": {"policy-statement": [{"name": "SAMPLE-POLICY"}]}})
        declared = _schema_at("policy-options", "policy-statement")
        offered = [schema for value, schema, _ in rule.seen if value == "SAMPLE-POLICY"]
        assert len(offered) == 1
        assert offered[0] is declared["c"]["name"], "a leaf built from the list node"

    def test_an_enum_key_passes_unchanged(self) -> None:
        ir = _term(
            "from",
            "as-path-neighbors",
            {"list-type": "as-list-group", "list-name": "SAMPLE-AS-LIST"},
        )
        rule = _walked(ir)
        offered = {value: schema for value, schema, _ in rule.seen}
        assert "as-list-group" in offered, "list-type was never offered to a rule"
        enums = _bundled_tree()["_enums"][offered["as-list-group"]["e"]]
        assert enums == ["as-list", "as-list-group"]

        config = AnonymizeConfig(
            ips=True,
            passwords=True,
            communities=True,
            identities=True,
            groups=True,
            descriptions=True,
            as_numbers=[64496],
            sensitive_words=["as-list"],
            salt="s",
        )
        result = anonymize({"configuration": ir}, config)
        entry = result.ir["configuration"]["policy-options"]["policy-statement"][0]["term"][0][
            "from"
        ]["as-path-neighbors"][0]
        assert entry["list-type"] == "as-list-group"
        assert set(entry) == {"list-type", "list-name"}


class TestTheWalkerReachesEveryPlacedValue:
    """Every value the tree places is offered to the rules, wherever it stands.

    The walker returned at a key its node's children did not name, so a
    universal statement below the root was never seen (NEW-A-N1, NEW-A-N2);
    it replaced a transparent container by its transparent child, so
    `interface-range` beside `interface` was never seen (NEW-A-N3, ANON-P2,
    NEW-C11); and it entered only a dict under a container that is no list, so
    the port-mirroring `routing-instance` JSON holds as a one-entry list was
    never seen (ANON-P2). Spec anonymization/placed-values. Through `walk`
    against the bundled tree.
    """

    @staticmethod
    def _offered(ir: dict[str, Any]) -> dict[tuple[str, ...], Any]:
        return {path: value for value, _, path in _walked(ir).seen}

    def test_a_universal_statement_below_the_root(self) -> None:
        offered = self._offered(
            {
                "system": {
                    "apply-groups": ["SAMPLE-GROUP"],
                    "apply-macro": [
                        {"name": "M2", "data": [{"name": "peer", "value": "203.0.114.8"}]}
                    ],
                },
                "interfaces": {"apply-groups-except": ["SAMPLE-GROUP"]},
            }
        )
        assert offered[("system", "apply-groups")] == "SAMPLE-GROUP"
        assert offered[("interfaces", "apply-groups-except")] == "SAMPLE-GROUP"
        assert offered[("system", "apply-macro", "data", "value")] == "203.0.114.8"
        assert offered[("system", "apply-macro", "data", "name")] == "peer"

    def test_a_transparent_containers_other_children(self) -> None:
        """With and without the transparent child beside them."""
        siblings = {
            "interface-range": [{"name": "IR1", "description": "access range"}],
            "interface-set": [{"name": "IS1", "interface": [{"name": "ge-0/0/1"}]}],
        }
        for interfaces in (siblings, {"interface": [{"name": "ge-0/0/0"}], **siblings}):
            offered = self._offered({"interfaces": interfaces})
            assert offered[("interfaces", "interface-range", "description")] == "access range"
            assert offered[("interfaces", "interface-set", "interface", "name")] == "ge-0/0/1"
        offered = self._offered({"interfaces": {"interface": [{"name": "ge-0/0/0"}], **siblings}})
        assert offered[("interfaces", "name")] == "ge-0/0/0"

    def test_each_entry_of_a_list_a_container_holds(self) -> None:
        """`routing-instance` is a container the tree marks homogeneous, no
        list; JSON holds it as the device wrote it, a list of one entry."""
        assert not _schema_at(
            "forwarding-options", "port-mirroring", "family", "inet", "output", "routing-instance"
        ).get("L")
        output = {"routing-instance": [{"name": "VRF-A", "ip-address": "203.0.114.10"}]}
        offered = self._offered(
            {"forwarding-options": {"port-mirroring": {"family": {"inet": {"output": output}}}}}
        )
        path = ("forwarding-options", "port-mirroring", "family", "inet", "output")
        assert offered[(*path, "routing-instance", "ip-address")] == "203.0.114.10"

    def test_a_key_field_the_tree_holds_no_leaf_for(self) -> None:
        """`apply-macro` is keyed `name`, which the tree holds no leaf for: the
        rules see the name with no type, never a leaf built from the list node."""
        assert "name" not in _schema_at("apply-macro").get("c", {})
        rule = _walked({"apply-macro": [{"name": "SAMPLE-MACRO", "data": [{"name": "k"}]}]})
        offered = [(schema, path) for value, schema, path in rule.seen if value == "SAMPLE-MACRO"]
        assert offered == [({}, ("apply-macro", "name"))]


def _ir(text: str, fmt: Format = Format.SET) -> dict[str, Any]:
    """The IR the reader of *fmt* gives for *text*."""
    return json.loads(convert_config(text, from_format=fmt, to_format=Format.JSON, validate=False))


def _flags(options: dict[str, Any]) -> list[str]:
    """The `junoscfg convert` options that switch *options* on."""
    flags = {
        "ips": ["--anonymize-ips"],
        "identities": ["--anonymize-identities"],
        "passwords": ["--anonymize-passwords"],
        "ips_in_strings": ["--anonymize-ips-in-strings"],
        "as_numbers_in_strings": ["--anonymize-as-numbers-in-strings"],
    }
    found: list[str] = []
    for name, value in options.items():
        if name == "as_numbers":
            found += ["--anonymize-as-numbers", ",".join(str(asn) for asn in value)]
        else:
            found += flags[name]
    return found


#: Hand-written free text, which no device capture exercises (the how-to's
#: device-evidence checks: the substitute for corpus coverage of lexical
#: scanning). Each row: the text, its reader, the rules on, the originals that
#: must be gone from the output, and the text around them that must stay.
_FREE_TEXT: dict[str, tuple[str, Format, dict[str, Any], set[str], set[str]]] = {
    "a-one-line-block": (
        "system { login { user operator { class super-user; } } archival { configuration { "
        'archive-sites { "scp://operator@203.0.114.5/path"; } } } }\n',
        Format.STRUCTURED,
        {"ips": True, "identities": True},
        {"203.0.114.5", "operator"},
        {"scp://", "/path", "super-user"},
    ),
    "a-list-across-lines": (
        "system {\n    archival {\n        configuration {\n"
        '            archive-sites [ "scp://operator@203.0.114.5/a"\n'
        '                "scp://admin@203.0.114.6/b" ];\n        }\n    }\n}\n',
        Format.STRUCTURED,
        {"ips": True, "identities": True},
        {"203.0.114.5", "203.0.114.6", "operator", "admin"},
        {"scp://", "/a", "/b"},
    ),
    "a-value-across-lines": (
        'interfaces {\n    ge-0/0/0 {\n        description "uplink to\n203.0.114.6 port 3";\n'
        "    }\n}\n",
        Format.STRUCTURED,
        {"ips": True},
        {"203.0.114.6"},
        {"uplink to", " port 3"},
    ),
    "comments-holding-syntax": (
        '/* note; { } "quoted" 203.0.114.7 */\nsystem {\n'
        '    # a ; { } " comment 203.0.114.8\n    archival {\n        configuration {\n'
        '            archive-sites {\n                "ftp://operator:secret99@203.0.114.6/x";'
        " /* ; } */\n            }\n        }\n    }\n}\n",
        Format.STRUCTURED,
        {"ips": True, "identities": True, "passwords": True},
        {"203.0.114.6", "203.0.114.7", "203.0.114.8", "operator", "secret99"},
        {"ftp://", "/x"},
    ),
    "a-template": (
        'set system apply-macro M1 url "scp://operator@203.0.114.10/${node}/cfg"\n',
        Format.SET,
        {"ips": True, "identities": True},
        {"203.0.114.10", "operator"},
        {"scp://", "/${node}/cfg"},
    ),
    "prose": (
        'set interfaces ge-0/0/0 description "Link to 203.0.114.6; ask operator {primary} '
        'host:203.0.114.9 lo_203.0.114.9"\n',
        Format.SET,
        {"ips": True},
        {"203.0.114.6", "203.0.114.9"},
        {"Link to ", "; ask operator {primary} host:", " lo_"},
    ),
    "address-forms-inside-words": (
        "set routing-instances VRF-A route-distinguisher 10.255.0.1:100\n"
        "set routing-instances VRF-B route-distinguisher 203.0.114.65:100\n"
        "set routing-instances VRF-B vrf-target target:203.0.114.65:100\n",
        Format.SET,
        {"ips": True},
        {"10.255.0.1", "203.0.114.65"},
        {"target:", ":100"},
    ),
    "an-as-number-inside-a-name": (
        "set protocols bgp group AS64496-PEERS peer-as 64496\n"
        'set interfaces ge-0/0/0 description "transit AS64496, see 203.0.114.6"\n',
        Format.SET,
        {"ips": True, "as_numbers": [64496], "as_numbers_in_strings": True},
        {"64496", "203.0.114.6"},
        {"-PEERS", "transit AS", ", see "},
    ),
}

_CLI_FORMAT = {Format.SET: "set", Format.STRUCTURED: "structured"}


class TestValuesInsideFreeText:
    """A value written inside free text is the value of the rule that claims
    it, as it is standing alone: under `--anonymize-ips` an address in a URL or
    a description survived unless `--anonymize-ips-in-strings` was on
    (ANON-P5); a URL's user survived `--anonymize-identities` (NEW-A-N4) and
    its password `--anonymize-passwords` (NEW-R16). The strings passes after
    the walk rewrote digits inside an address or another rule's replacement
    and ignored `include`/`exclude` (NEW-R17). One chain now rewrites each
    shape inside a value, rule by rule, never offering one rule's text to
    another; a shape that is the whole value is its rule's to take
    (specification challenge S1 of change anonymize-embedded-values). Spec
    anonymization/embedded-values.
    """

    @pytest.mark.parametrize("door", ["conversion", "cli"])
    @pytest.mark.parametrize("row", list(_FREE_TEXT))
    def test_each_value_inside_it_is_replaced(self, row: str, door: str) -> None:
        text, fmt, options, gone, kept = _FREE_TEXT[row]
        if door == "conversion":
            out = convert_config(
                text,
                from_format=fmt,
                to_format=Format.SET,
                validate=False,
                anon_config=AnonymizeConfig(salt="s", **options),
            )
        else:
            result = CliRunner().invoke(
                main,
                ["convert", "-i", _CLI_FORMAT[fmt], "-e", "set", "--no-field-validate"]
                + [*_flags(options), "--anonymize-salt", "s"],
                input=text,
            )
            assert result.exit_code == 0, result.output
            out = result.stdout
        assert out.strip(), "the row reads to configuration"
        assert not {original for original in gone if original in out}, out
        assert not {around for around in kept if around not in out}, out

    @pytest.mark.parametrize("row", list(_FREE_TEXT))
    def test_the_mapping_restores_each_row(self, row: str, tmp_path: Path) -> None:
        text, fmt, options, _, _ = _FREE_TEXT[row]
        dumped = tmp_path / "map.json"
        out = convert_config(
            text,
            from_format=fmt,
            to_format=Format.JSON,
            validate=False,
            anon_config=AnonymizeConfig(salt="s", dump_map=str(dumped), **options),
        )
        reverted = convert_config(
            out,
            from_format=Format.JSON,
            to_format=Format.JSON,
            validate=False,
            anon_config=AnonymizeConfig(revert_map=str(dumped)),
        )
        assert json.loads(reverted) == _ir(text, fmt)

    def test_the_url_user_takes_the_login_users_pseudonym(self) -> None:
        text, fmt, options, _, _ = _FREE_TEXT["a-one-line-block"]
        result = anonymize(_ir(text, fmt), AnonymizeConfig(salt="s", **options))
        assert f"//{result.mapping['identity']['operator']}@" in json.dumps(result.ir)

    @pytest.mark.parametrize(
        "line",
        [
            "set snmp view V oid 1.3.6.1 include",
            "set policy-options policy-statement P term T from area 0.0.0.0",
        ],
        ids=["snmp-oid", "from-area"],
    )
    def test_an_address_that_is_the_whole_value_answers_by_the_type(self, line: str) -> None:
        """An OID and an area are syntax shaped like an address: alone in a
        value of a leaf whose type holds no address, they stay. A pin: the
        base kept them too. With `ips_in_strings` an address that is a whole
        value is replaced on any leaf."""
        out = convert_config(
            line,
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(ips=True, salt="s"),
        )
        assert out.strip() == line
        location = "set snmp location 203.0.114.9"
        out = convert_config(
            location,
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(ips=True, ips_in_strings=True, salt="s"),
        )
        assert "203.0.114.9" not in out

    def test_an_address_is_no_as_number(self) -> None:
        """`AS100` is the AS number; `10.100.0.1` stays whole (NEW-R17)."""
        out = convert_config(
            'set interfaces ge-0/0/0 description "via 10.100.0.1 AS100"\n',
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(as_numbers=[100], as_numbers_in_strings=True, salt="s"),
        )
        assert "10.100.0.1" in out
        assert "AS100" not in out

    def test_text_one_rule_wrote_is_never_rewritten(self) -> None:
        """A replaced address is no text for a sensitive pattern, and a group's
        pseudonym none for an AS number: each keeps the replacement its rule
        gives it everywhere (NEW-R17; the base chained a sensitive pattern over
        the address the IP rule wrote, and the AS strings pass rewrote digits
        in any pseudonym)."""
        text = (
            "set protocols bgp group transit neighbor 203.0.114.7\n"
            "set routing-options router-id 203.0.114.7\n"
        )
        result = anonymize(
            _ir(text), AnonymizeConfig(ips=True, sensitive_patterns=[r"\d{3}"], salt="s")
        )
        replacement = result.mapping["ip"]["203.0.114.7"]
        cfg = result.ir["configuration"]
        assert cfg["routing-options"]["router-id"] == replacement
        assert cfg["protocols"]["bgp"]["group"][0]["neighbor"][0]["name"] == replacement

        salt, digits = next(
            (salt, run)
            for salt in (f"salt-{n}" for n in range(200))
            for run in re.findall(
                r"(?<!\d)[1-9]\d{2,4}(?!\d)",
                anonymize(_ir(text), AnonymizeConfig(groups=True, salt=salt)).mapping["group"][
                    "transit"
                ],
            )
        )
        alone = anonymize(_ir(text), AnonymizeConfig(groups=True, salt=salt))
        both = anonymize(
            _ir(text),
            AnonymizeConfig(
                groups=True, as_numbers=[int(digits)], as_numbers_in_strings=True, salt=salt
            ),
        )
        [group] = both.ir["configuration"]["protocols"]["bgp"]["group"]
        assert group["name"] == alone.mapping["group"]["transit"]

    def test_the_filters_apply_inside_free_text(self) -> None:
        """`exclude` keeps a path's free text as written, the in-strings options
        included; the strings pass after the walk ignored it (NEW-R17)."""
        text = (
            'set system archival configuration archive-sites "scp://admin@203.0.114.5/path"\n'
            "set routing-options router-id 203.0.114.6\n"
        )
        result = anonymize(
            _ir(text),
            AnonymizeConfig(ips=True, ips_in_strings=True, exclude=["system.archival"], salt="s"),
        )
        dumped = json.dumps(result.ir)
        assert "203.0.114.5" in dumped
        assert "203.0.114.6" not in dumped


def _prefix_list(path: str, name: str = "PL") -> str:
    return f'set policy-options prefix-list {name} apply-path "{path}"\n'


def _apply_path(result: Any) -> str:
    [entry] = result.ir["configuration"]["policy-options"]["prefix-list"]
    return str(entry["apply-path"])


class TestAnApplyPathNamesConfiguration:
    """`apply-path` is a configuration path: its keywords are syntax and the
    word after a list's keyword is a name of that list. The rules never saw
    those names, so `apply-path "protocols bgp group EBGP neighbor <*>"` kept a
    renamed group's name and selected nothing, and a sensitive word rewrote
    its keywords (NEW-A-N7). Device evidence: the vMX 23.2R2-S7.5 and
    QFX5120 25.2R2-S1.5 `junoscfg-oracle` captures hold
    `apply-path "protocols bgp group <*> neighbor <*>"`. Spec
    anonymization/embedded-values.
    """

    @pytest.mark.parametrize(
        ("text", "path", "options", "rule", "original"),
        [
            (
                "set protocols bgp group EBGP neighbor 203.0.114.7\n",
                "protocols bgp group EBGP neighbor <*>",
                {"groups": True},
                "group",
                "EBGP",
            ),
            (
                "set protocols bgp group EBGP neighbor 203.0.114.7\n",
                "protocols bgp group EBGP neighbor 203.0.114.7",
                {"ips": True},
                "ip",
                "203.0.114.7",
            ),
            (
                "set snmp community public-ro clients 203.0.114.0/24\n",
                "snmp community public-ro clients <*>",
                {"communities": True},
                "community",
                "public-ro",
            ),
        ],
        ids=["group", "address", "community"],
    )
    def test_a_name_in_it_takes_the_names_pseudonym(
        self, text: str, path: str, options: dict[str, Any], rule: str, original: str
    ) -> None:
        result = anonymize(_ir(text + _prefix_list(path)), AnonymizeConfig(salt="s", **options))
        assert _apply_path(result) == path.replace(original, result.mapping[rule][original])
        assert original not in json.dumps(result.ir)

    def test_its_keywords_stay(self) -> None:
        text = "set protocols bgp group EBGP neighbor 203.0.114.7\n" + _prefix_list(
            "protocols bgp group EBGP neighbor <*>"
        )
        result = anonymize(_ir(text), AnonymizeConfig(sensitive_words=["bgp"], salt="s"))
        [group] = result.ir["configuration"]["protocols"]["bgp"]["group"]
        assert group["name"] != "EBGP"
        assert _apply_path(result) == f"protocols bgp group {group['name']} neighbor <*>"

    @pytest.mark.parametrize(
        ("text", "path", "options", "reported"),
        [
            (
                "set protocols bgp group EBGP neighbor 203.0.114.7\n",
                "protocols bgp group <*> neighbor <*>",
                {
                    "ips": True,
                    "passwords": True,
                    "communities": True,
                    "identities": True,
                    "groups": True,
                    "descriptions": True,
                    "sensitive_words": ["customer"],
                },
                False,
            ),
            (
                "set protocols bgp group IBGP neighbor 203.0.114.7\n",
                "protocols bgp group IBGP neighbor <203.0.114.*>",
                {"ips": True},
                False,
            ),
            (
                "set protocols bgp group EBGP-A neighbor 203.0.114.7\n",
                "protocols bgp group <EBGP-*> neighbor <*>",
                {"groups": True},
                True,
            ),
        ],
        ids=["match-all", "an-address-pattern", "a-renamed-name-pattern"],
    )
    def test_a_wildcard_in_it_is_a_pattern(
        self, text: str, path: str, options: dict[str, Any], reported: bool
    ) -> None:
        """`<*>` passes; an address pattern of whole octets takes its prefix's
        replacement and keeps selecting the replaced neighbour; a pattern a
        renamed name cannot keep is reported by the apply-path's schema path,
        as a wildcard name is (spec anonymization/wildcard-names). The
        match-all row is a pin: the base kept it too."""
        result = anonymize(_ir(text + _prefix_list(path)), AnonymizeConfig(salt="s", **options))
        anonymized = _apply_path(result)
        assert "203.0.114" not in anonymized and "EBGP" not in anonymized
        if "<*>" in path:
            assert anonymized.endswith("neighbor <*>")
        if path.endswith("<203.0.114.*>"):
            pattern = anonymized.rsplit(" ", 1)[1][1:-1]
            [group] = result.ir["configuration"]["protocols"]["bgp"]["group"]
            assert re.fullmatch(
                pattern.replace(".", r"\.").replace("*", ".*"), group["neighbor"][0]["name"]
            )
        expected = ("policy-options.prefix-list.apply-path",) if reported else ()
        assert result.patterns == expected

    def test_a_path_the_tree_cannot_read_is_named(self) -> None:
        """A path the tree cannot read to its end is content the walk cannot
        place: its addresses replaced by shape, its place named (owner
        answer 5)."""
        result = anonymize(
            _ir(_prefix_list("protocols bgp bogus-knob EBGP 203.0.114.7")),
            AnonymizeConfig(ips=True, salt="s"),
        )
        assert "203.0.114.7" not in json.dumps(result.ir)
        assert "policy-options.prefix-list.apply-path" in result.unplaced

    def test_the_mapping_restores_it(self) -> None:
        """A pin for the base's output, which left the path as written."""
        text = (
            "set protocols bgp group EBGP neighbor 203.0.114.7\n"
            + _prefix_list("protocols bgp group EBGP neighbor 203.0.114.7")
            + _prefix_list("protocols bgp group <EBGP-*> neighbor <203.0.114.*>", "PL2")
        )
        source = _ir(text)
        result = anonymize(
            source, AnonymizeConfig(ips=True, groups=True, sensitive_words=["bgp"], salt="s")
        )
        assert apply_revert(result.ir, result.mapping) == source
