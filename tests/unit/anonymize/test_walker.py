"""Tests for the schema-guided anonymization walker.

Every test goes through ``walk``, the walker's door, against the bundled tree,
with test rules that decide on the schema node the walker hands them.
"""

from __future__ import annotations

import copy
import json
import re
from fnmatch import fnmatchcase
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element, SubElement, tostring

import pytest
from click.testing import CliRunner

from junoscfg import Format, convert_config, convert_config_result
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


def _reader_source(text: str, fmt: Format) -> str:
    """Synthetic all-reader controls; XML is an input format only."""
    if fmt != Format.XML:
        return convert_config(text, from_format=Format.SET, to_format=fmt, validate=False)
    root = Element("configuration")

    def children(parent: Any, values: dict[str, Any]) -> None:
        for key, value in values.items():
            for item in value if isinstance(value, list) else [value]:
                child = SubElement(parent, key)
                if isinstance(item, dict):
                    children(child, item)
                elif item is not None:
                    child.text = str(item)

    children(root, _ir(text)["configuration"])
    return tostring(root, encoding="unicode")


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
        elif name == "sensitive_patterns":
            for pattern in value:
                found += ["--anonymize-sensitive-patterns", pattern]
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
    "prose-v6": (
        'set interfaces ge-0/0/0 description "peer [3ffe:b00::1]:179 lo_3ffe:b00::2 '
        'host:3ffe:b00::3 see 3ffe:b00::4."\n',
        Format.SET,
        {"ips": True},
        {"b00::1", "b00::2", "b00::3", "b00::4"},
        {"peer [", "]:179 lo_", " host:", " see "},
    ),
    "prose-sentence": (
        'set interfaces ge-0/0/0 description "Uplink to 203.0.114.6. Backup 203.0.114.7..."\n',
        Format.SET,
        {"ips": True},
        {"203.0.114.6", "203.0.114.7"},
        {"Uplink to ", ". Backup ", "..."},
    ),
    "an-ipv4-inside-ipv6": (
        'set interfaces ge-0/0/0 description "nat64 64:ff9b::203.0.114.5 mapped ::ffff:198.0.2.5"\n'
        "set routing-options static route 198.51.100.0/24 next-hop ::ffff:203.0.114.8\n",
        Format.SET,
        {"ips": True},
        {"203.0.114.5", "198.0.2.5", "203.0.114.8"},
        {"nat64 64:ff9b::", " mapped ::ffff:", "next-hop ::ffff:"},
    ),
    "a-zero-padded-address": (
        'set interfaces ge-0/0/0 description "old 203.000.114.006, then 198.0.2.07"\n',
        Format.SET,
        {"ips": True},
        {"203.000.114.006", "198.0.2.07"},
        {"old ", ", then "},
    ),
    "a-hash-in-prose": (
        'set interfaces ge-0/0/0 description "rotated: old $9$ExAmPlEhAsH.KEY, '
        "(key=$9$ExAmPlEhAsH.KEZ) and '$1$salt$ExAmPlEhAsH' key:$9$ExAmPlEhAsH.KEX\"\n",
        Format.SET,
        {"passwords": True},
        {"ExAmPlEhAsH"},
        {"rotated: old $9$", ", (key=$9$", ") and '$1$", " key:$9$"},
    ),
    "url-shapes": (
        "set system login user operator class super-user\n"
        "set system archival configuration archive-sites "
        '"FTP://Operator:Secret99@203.0.114.6/x"\n'
        "set system archival configuration archive-sites "
        '"ssh://operator@203.0.114.5:2222/x"\n'
        "set system archival configuration archive-sites "
        '"https://admin:secret98@[3ffe:b00::5]:8443/x"\n'
        "set system archival configuration archive-sites "
        '"ftp://operator:p@ss:w0rd@198.0.2.6/x"\n'
        "set system archival configuration archive-sites "
        '"scp://${user}@198.0.2.10/cfg"\n',
        Format.SET,
        {"ips": True, "identities": True, "passwords": True},
        {
            "Operator",
            "operator@",
            "operator:",
            "admin",
            "Secret99",
            "secret98",
            "p@ss",
            "ss:w0rd",
            "${user}",
            "203.0.114.5",
            "203.0.114.6",
            "b00::5",
            "198.0.2.6",
            "198.0.2.10",
        },
        {"FTP://", "ssh://", ":2222/x", "https://", "]:8443/x", "scp://", "/cfg"},
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

    @pytest.mark.parametrize("fmt", list(Format))
    @pytest.mark.parametrize(
        ("user", "password"),
        [
            ("operator", "$9$ExAmPlEhAsH.KEY"),
            ("admin203.0.114.6", "secret99"),
            ("operator", "secret99"),
        ],
        ids=["hash-delimiter", "address-in-user", "ordinary-control"],
    )
    def test_original_url_credentials_keep_their_ownership(
        self, fmt: Format, user: str, password: str, tmp_path: Path
    ) -> None:
        """Fresh R2: original URL/login identity survives nested shapes and generated slashes."""
        text = (
            f"set system login user {user} class super-user\n"
            f'set interfaces ge-0/0/0 description "scp://{user}:{password}@198.51.100.1/path"\n'
        )
        options = {"passwords": True, "identities": True, "ips": True}
        source = _ir(text)
        unchanged = copy.deepcopy(source)
        result = anonymize(source, AnonymizeConfig(salt="s", **options))
        cfg = result.ir["configuration"]
        login = cfg["system"]["login"]["user"][0]["name"]
        description = cfg["interfaces"]["interface"][0]["description"]
        assert description.startswith(f"scp://{login}:")
        assert login == result.mapping["identity"][user]
        assert user not in json.dumps(result.ir) and password not in description
        assert source == unchanged
        restored = copy.deepcopy(result.ir)
        apply_revert(restored, result.mapping)
        assert restored == source
        rendered = _reader_source(text, fmt)
        dumped = tmp_path / "map.json"
        converted = convert_config_result(
            rendered,
            from_format=fmt,
            to_format=Format.JSON,
            validate=False,
            anon_config=AnonymizeConfig(salt="s", dump_map=str(dumped), **options),
        )
        cli = CliRunner().invoke(
            main,
            [
                "convert",
                "-i",
                fmt.value,
                "-e",
                "json",
                "--no-field-validate",
                *_flags(options),
                "--anonymize-salt",
                "s",
                "--anonymize-dump-map",
                str(dumped),
            ],
            input=rendered,
        )
        assert cli.exit_code == 0, cli.output
        for output in (converted.output, cli.stdout):
            cfg = json.loads(output)["configuration"]
            login = cfg["system"]["login"]["user"][0]["name"]
            assert cfg["interfaces"]["interface"][0]["description"].startswith(f"scp://{login}:")
            assert user not in output and password not in output
            restored_text = convert_config(
                output,
                from_format=Format.JSON,
                to_format=Format.JSON,
                validate=False,
                anon_config=AnonymizeConfig(revert_map=str(dumped)),
            )
            assert json.loads(restored_text) == json.loads(
                convert_config(
                    rendered,
                    from_format=fmt,
                    to_format=Format.JSON,
                    validate=False,
                )
            )
        assert not any(value in cli.stderr for value in (user, password))
        assert not any(value in str(converted.diagnostics) for value in (user, password))

    @pytest.mark.parametrize("door", ["conversion", "json-to-yaml", "cli"])
    @pytest.mark.parametrize("row", list(_FREE_TEXT))
    def test_each_value_inside_it_is_replaced(self, row: str, door: str) -> None:
        """Every door, and on the command line stdout and stderr both
        (Test/Challenge T11)."""
        text, fmt, options, gone, kept = _FREE_TEXT[row]
        if door == "conversion":
            out = convert_config(
                text,
                from_format=fmt,
                to_format=Format.SET,
                validate=False,
                anon_config=AnonymizeConfig(salt="s", **options),
            )
        elif door == "json-to-yaml":
            out = convert_config(
                json.dumps(_ir(text, fmt)),
                from_format=Format.JSON,
                to_format=Format.YAML,
                validate=False,
                anon_config=AnonymizeConfig(salt="s", **options),
            )
            kept = set()  # YAML lays statements out its own way; other doors check the text
        else:
            result = CliRunner().invoke(
                main,
                ["convert", "-i", _CLI_FORMAT[fmt], "-e", "set", "--no-field-validate"]
                + [*_flags(options), "--anonymize-salt", "s"],
                input=text,
            )
            assert result.exit_code == 0, result.output
            out = result.stdout + result.stderr
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

    @pytest.mark.parametrize("row", list(_FREE_TEXT))
    def test_the_same_salt_gives_the_same_output(self, row: str) -> None:
        """The AS numbers and plain-text secrets are numbered in the order met
        (Test/Challenge T12)."""
        text, fmt, options, _, _ = _FREE_TEXT[row]
        first, second = (
            anonymize(_ir(text, fmt), AnonymizeConfig(salt="s", **options)) for _ in range(2)
        )
        assert first.ir == second.ir
        assert first.mapping == second.mapping

    @pytest.mark.parametrize(
        "line",
        [
            'set system archival configuration archive-sites "scp://198.51.100.5/path"',
            'set interfaces ge-0/0/0 description "mail noc at example"',
            'set interfaces ge-0/0/0 description "see https://example.net/a@b"',
        ],
        ids=["a-url-without-a-user", "prose-without-a-shape", "an-at-after-the-host"],
    )
    def test_text_without_a_shape_stays(self, line: str) -> None:
        """No user, no password, no address the rule replaces: unchanged
        (Test/Challenge T9; 198.51.100.0/24 is kept by design). A pin: the base
        kept them too."""
        out = convert_config(
            line,
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(ips=True, identities=True, passwords=True, salt="s"),
        )
        assert _ir(out) == _ir(line)

    def test_the_url_user_takes_the_login_users_pseudonym(self) -> None:
        text, fmt, options, _, _ = _FREE_TEXT["a-one-line-block"]
        result = anonymize(_ir(text, fmt), AnonymizeConfig(salt="s", **options))
        assert f"//{result.mapping['identity']['operator']}@" in json.dumps(result.ir)

    @pytest.mark.parametrize(
        "line",
        [
            "set snmp view V oid 1.3.6.1 include",
            "set snmp view V oid 1.3.6.1.4.1.2636 include",
            "set policy-options policy-statement P term T from area 0.0.0.0",
            "set policy-options policy-statement P term T from area 198.0.2.1",
            'set interfaces ge-0/0/0 description "release 1.2.3.4.5"',
        ],
        ids=["snmp-oid", "a-longer-oid", "from-area-backbone", "from-area", "a-version"],
    )
    def test_an_address_that_is_the_whole_value_answers_by_the_type(self, line: str) -> None:
        """An OID and an area are syntax shaped like an address: an SNMP OID
        stays, and `areaid` takes no address, `ignore_reserved` on so that
        `0.0.0.0` is not kept by design (Test/Challenge T8); five numbers are
        no address. A pin: the base kept them too."""
        out = convert_config(
            line,
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(ips=True, ignore_reserved=True, salt="s"),
        )
        assert _ir(out) == _ir(line)

    @pytest.mark.parametrize(
        ("line", "address"),
        [
            ("set interfaces ge-0/0/0 description 203.0.114.9", "203.0.114.9"),
            ("set snmp location 203.0.114.9", "203.0.114.9"),
            ("set snmp contact 3ffe:b00::9", "3ffe:b00::9"),
        ],
        ids=["description", "snmp-location", "snmp-contact-v6"],
    )
    def test_an_address_alone_in_free_text_is_replaced(self, line: str, address: str) -> None:
        """An address that is the whole value of a free-text leaf survived
        `--anonymize-ips` with no word (specification challenge S4: the type
        cannot tell `description` from the SNMP OID, both `xsd:string`); an
        anonymized run replaces it, the SNMP OID aside."""
        out = convert_config(
            line,
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=AnonymizeConfig(ips=True, salt="s"),
        )
        assert address not in out
        assert out.startswith(line.rsplit(" ", 1)[0])

    @pytest.mark.parametrize("fmt", list(Format))
    @pytest.mark.parametrize("reverse_order", [False, True])
    @pytest.mark.parametrize(
        "spellings",
        [
            ("203.0.114.6", "203.000.114.006"),
            ("3ffe:b00::9", "3ffe:0b00:0:0:0:0:0:9"),
            ("3ffe:b00::a", "3FFE:B00::A"),
        ],
        ids=["padded-ipv4", "expanded-ipv6", "case-ipv6"],
    )
    def test_ambiguous_spellings_are_rejected_before_output(
        self, fmt: Format, reverse_order: bool, spellings: tuple[str, str], tmp_path: Path
    ) -> None:
        """S5 decision and independent final IPv6-alias counterexamples."""
        values = list(spellings)
        if reverse_order:
            values.reverse()
        text = f'set interfaces ge-0/0/0 description "via {values[0]} and {values[1]}"\n'
        source = _ir(text)
        unchanged = copy.deepcopy(source)
        with pytest.raises(ValueError, match="ambiguous") as error:
            anonymize(source, AnonymizeConfig(ips=True, salt="s"))
        assert source == unchanged
        assert not any(value in str(error.value) for value in values)
        rendered = _reader_source(text, fmt)
        dumped = tmp_path / "map.json"
        with pytest.raises(ValueError) as error:
            convert_config(
                rendered,
                from_format=fmt,
                to_format=Format.JSON,
                validate=False,
                anon_config=AnonymizeConfig(ips=True, salt="s", dump_map=str(dumped)),
            )
        assert not dumped.exists()
        assert error.value.__cause__ is None
        assert error.value.__context__ is None
        assert not any(value in str(error.value) for value in values)
        cli = CliRunner().invoke(
            main,
            [
                "convert",
                "-i",
                fmt.value,
                "-e",
                "json",
                "--no-field-validate",
                "--anonymize-ips",
                "--anonymize-salt",
                "s",
                "--anonymize-dump-map",
                str(dumped),
            ],
            input=rendered,
        )
        assert cli.exit_code != 0
        assert not cli.stdout.strip()
        assert "ambiguous" in cli.stderr
        assert not any(value in cli.stderr for value in values)
        assert not dumped.exists()

    @pytest.mark.parametrize("fmt", list(Format))
    def test_an_ambiguous_legacy_map_is_rejected_before_output(
        self, fmt: Format, tmp_path: Path
    ) -> None:
        """S5 final decision applies through conversion and CLI to old ambiguous flat maps."""
        dumped = tmp_path / "map.json"
        values = ["203.0.114.6", "203.000.114.006", "203.211.226.137"]
        dumped.write_text(json.dumps({"ip": {value: values[2] for value in values[:2]}}))
        rendered = _reader_source(
            'set interfaces ge-0/0/0 description "via 203.211.226.137"\n', fmt
        )
        with pytest.raises(ValueError, match="ambiguous") as error:
            convert_config(
                rendered,
                from_format=fmt,
                to_format=Format.JSON,
                validate=False,
                anon_config=AnonymizeConfig(revert_map=str(dumped)),
            )
        assert not any(value in str(error.value) for value in values)
        cli = CliRunner().invoke(
            main,
            [
                "convert",
                "-i",
                fmt.value,
                "-e",
                "json",
                "--no-field-validate",
                "--anonymize-revert-map",
                str(dumped),
            ],
            input=rendered,
        )
        assert cli.exit_code != 0
        assert not cli.stdout.strip()
        assert "ambiguous" in cli.stderr
        assert not any(value in cli.stderr for value in values)

    @pytest.mark.parametrize("fmt", list(Format))
    @pytest.mark.parametrize(
        "address",
        [
            "203.0.114.6",
            "203.000.114.006",
            "3ffe:b00::9",
            "3ffe:0b00:0:0:0:0:0:9",
            "3ffe:b00::a",
            "3FFE:B00::A",
        ],
    )
    def test_an_unambiguous_spelling_restores_exactly(
        self, fmt: Format, address: str, tmp_path: Path
    ) -> None:
        """S5 ordinary and one-spelling controls keep the legacy mapping format."""
        text = f'set interfaces ge-0/0/0 description "via {address} and {address}"\n'
        source = _ir(text)
        rendered = _reader_source(text, fmt)
        dumped = tmp_path / "map.json"
        writer = Format.JSON if fmt == Format.XML else fmt
        out = convert_config(
            rendered,
            from_format=fmt,
            to_format=writer,
            validate=False,
            anon_config=AnonymizeConfig(ips=True, salt="s", dump_map=str(dumped)),
        )
        pairs = json.loads(dumped.read_text())
        assert set(pairs) == {"ip"}
        assert set(pairs["ip"]) == {address}
        assert address not in out
        assert apply_revert(_ir(out, writer), pairs) == source
        cli = CliRunner().invoke(
            main,
            [
                "convert",
                "-i",
                writer.value,
                "-e",
                "json",
                "--no-field-validate",
                "--anonymize-revert-map",
                str(dumped),
            ],
            input=out,
        )
        assert cli.exit_code == 0, cli.output
        assert json.loads(cli.stdout) == source

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

    @pytest.mark.parametrize(
        ("options", "inside", "elsewhere"),
        [
            (
                {"ips": True, "ips_in_strings": True, "exclude": ["system.archival"]},
                "203.0.114.5",
                "203.0.114.6",
            ),
            ({"identities": True, "exclude": ["system.archival"]}, "//operator:", "operator"),
            ({"passwords": True, "exclude": ["system.archival"]}, "secret99", "secret99"),
            (
                {
                    "as_numbers": [64496],
                    "as_numbers_in_strings": True,
                    "exclude": ["system.archival"],
                },
                "AS64496",
                "64496",
            ),
            ({"sensitive_words": ["acme"], "exclude": ["system.archival"]}, "acme", "acme"),
            ({"ips": True, "include": ["routing-options"]}, "203.0.114.5", "203.0.114.6"),
        ],
        ids=["ips-in-strings", "identities", "passwords", "as-in-strings", "sensitive", "include"],
    )
    def test_the_filters_apply_inside_free_text(
        self, options: dict[str, Any], inside: str, elsewhere: str
    ) -> None:
        """`exclude` keeps a path's free text as written, and `include` keeps
        all but its paths; the strings passes after the walk ignored both
        (NEW-R17, Test/Challenge T10). The same value outside the filtered
        path is replaced."""
        text = (
            "set system login user operator class super-user\n"
            "set system archival configuration archive-sites "
            '"scp://operator:secret99@203.0.114.5/AS64496/acme"\n'
            "set routing-options router-id 203.0.114.6\n"
            'set interfaces ge-0/0/0 description "AS64496 acme"\n'
            "set protocols bgp group G authentication-key secret99\n"
        )
        dumped = json.dumps(anonymize(_ir(text), AnonymizeConfig(salt="s", **options)).ir)
        [site] = re.findall(r'"(scp://[^"]*)"', dumped)
        assert inside in site
        assert elsewhere not in dumped.replace(site, "")

    @pytest.mark.parametrize(
        ("line", "options", "rule", "original"),
        [
            (
                'set interfaces ge-0/0/0 description "via 203.0.114.7"\n'
                "set routing-options router-id 203.0.114.7\n",
                {"ips": True, "sensitive_patterns": [r"\d{3}"]},
                "ip",
                "203.0.114.7",
            ),
            (
                "set system login user operator class super-user\n"
                'set system archival configuration archive-sites "scp://operator@198.51.100.1/x"\n',
                {"identities": True, "sensitive_words": ["user"]},
                "identity",
                "operator",
            ),
            (
                "set system archival configuration archive-sites "
                '"ftp://operator:secret99@198.51.100.1/x"\n',
                {"passwords": True, "sensitive_patterns": [r"\d+"]},
                "password",
                "secret99",
            ),
        ],
        ids=["an-address", "a-url-user", "a-url-password"],
    )
    def test_text_one_rule_wrote_inside_free_text_is_never_rewritten(
        self, line: str, options: dict[str, Any], rule: str, original: str
    ) -> None:
        """Inside free text too, where the chain does its work (Test/Challenge
        T6): the replacement in the text is the rule's own, everywhere."""
        result = anonymize(_ir(line), AnonymizeConfig(salt="s", **options))
        replacement = result.mapping[rule][original]
        [text] = [
            value
            for value in re.findall(r'"([^"]*)"', json.dumps(result.ir))
            if "via " in value or "://" in value
        ]
        assert re.search(rf"(?<!\w){re.escape(replacement)}(?!\w)", text), text

    def test_a_pseudonym_inside_a_url_is_no_as_number(self) -> None:
        """The URL user's pseudonym keeps its digits under an AS number that
        spells some of them (NEW-R17 inside free text, Test/Challenge T6)."""
        text = (
            "set system login user operator class super-user\n"
            'set system archival configuration archive-sites "scp://operator@198.51.100.1/x"\n'
        )
        salt, digits = next(
            (salt, run)
            for salt in (f"salt-{n}" for n in range(200))
            for run in re.findall(
                r"(?<!\d)[1-9]\d{2,4}(?!\d)",
                anonymize(_ir(text), AnonymizeConfig(identities=True, salt=salt)).mapping[
                    "identity"
                ]["operator"],
            )
        )
        result = anonymize(
            _ir(text),
            AnonymizeConfig(
                identities=True, as_numbers=[int(digits)], as_numbers_in_strings=True, salt=salt
            ),
        )
        assert f"//{result.mapping['identity']['operator']}@" in json.dumps(result.ir)

    def test_a_hash_in_unplaced_prose_is_replaced(self) -> None:
        """The same prose where the schema places nothing (Test/Challenge T4)."""
        text, _, options, gone, _ = _FREE_TEXT["a-hash-in-prose"]
        prose = _ir(text)["configuration"]["interfaces"]["interface"][0]["description"]
        result = anonymize(
            {"configuration": {"system": {"bogus-knob": prose}}},
            AnonymizeConfig(salt="s", **options),
        )
        assert not {original for original in gone if original in json.dumps(result.ir)}

    @pytest.mark.parametrize("door", ["json", "yaml", "cli"])
    def test_an_annotation_is_free_text(self, door: str, tmp_path: Path) -> None:
        """A Junos annotation (`"@"`, `"@<leaf>"` `comment`) is free text the
        walk skipped, so every address, user, password and hash in it survived
        (Test/Challenge T1, specification challenge S3). Every door that keeps
        annotations: JSON and YAML, and the command line."""
        comment = (
            "/* peer 203.0.114.7 via scp://operator:secret99@203.0.114.8/x "
            "key $9$ExAmPlEhAsH.KEY */"
        )
        source = {
            "configuration": {
                "@": {"comment": "/* loopback 198.0.2.77 */"},
                "routing-options": {
                    "@router-id": {"comment": comment},
                    "router-id": "198.0.2.1",
                },
            }
        }
        options = {"ips": True, "identities": True, "passwords": True}
        gone = ("203.0.114.7", "203.0.114.8", "198.0.2.77", "operator", "secret99", "ExAmPlEhAsH")
        dumped = tmp_path / "map.json"
        if door == "cli":
            result = CliRunner().invoke(
                main,
                ["convert", "-i", "json", "-e", "json", "--no-field-validate", *_flags(options)]
                + ["--anonymize-salt", "s", "--anonymize-dump-map", str(dumped)],
                input=json.dumps(source),
            )
            assert result.exit_code == 0, result.output
            out = result.stdout + result.stderr
            anonymized = result.stdout
        else:
            fmt = Format.JSON if door == "json" else Format.YAML
            text = json.dumps(source)
            if fmt is Format.YAML:
                text = convert_config(
                    text, from_format=Format.JSON, to_format=Format.YAML, validate=False
                )
            out = convert_config(
                text,
                from_format=fmt,
                to_format=Format.JSON,
                validate=False,
                anon_config=AnonymizeConfig(salt="s", dump_map=str(dumped), **options),
            )
            anonymized = out
        assert "/* peer " in out and "loopback" in out, "the annotation is kept"
        assert not [original for original in gone if original in out], out
        reverted = convert_config(
            anonymized,
            from_format=Format.JSON,
            to_format=Format.JSON,
            validate=False,
            anon_config=AnonymizeConfig(revert_map=str(dumped)),
        )
        plain = convert_config(
            json.dumps(source), from_format=Format.JSON, to_format=Format.JSON, validate=False
        )
        assert json.loads(reverted) == json.loads(plain)

    def test_a_key_and_its_reference_take_one_replacement(self) -> None:
        """A name holding an address beside text, where it is defined and where
        it is used (Test/Challenge T12)."""
        text = (
            "set policy-options prefix-list PL-203.0.114.0/24 198.51.100.0/24\n"
            "set policy-options policy-statement P term T from prefix-list PL-203.0.114.0/24\n"
        )
        result = anonymize(_ir(text), AnonymizeConfig(ips=True, salt="s"))
        options = result.ir["configuration"]["policy-options"]
        [defined] = options["prefix-list"]
        used = options["policy-statement"][0]["term"][0]["from"]["prefix-list"]
        assert "203.0.114" not in json.dumps(result.ir)
        [used_name] = [entry["name"] if isinstance(entry, dict) else entry for entry in used]
        assert defined["name"] == used_name


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

    @pytest.mark.parametrize("fmt", list(Format))
    @pytest.mark.parametrize(
        "later",
        [
            {"sensitive_patterns": [r"\d{3}"]},
            {"as_numbers": [211], "as_numbers_in_strings": True},
            {},
        ],
        ids=["sensitive-pattern", "as-in-strings", "ip-only-control"],
    )
    def test_an_ip_wildcard_replacement_is_protected(
        self, fmt: Format, later: dict[str, Any], tmp_path: Path
    ) -> None:
        """Fresh R1: evaluate actual target selection through every public door."""
        text = "set protocols bgp group G neighbor 203.0.114.7\n" + _prefix_list(
            "protocols bgp group G neighbor <203.0.114.*>"
        )
        assert fnmatchcase("203.0.114.7", "203.0.114.*")
        options = {"ips": True, **later}
        source = _ir(text)
        unchanged = copy.deepcopy(source)
        result = anonymize(source, AnonymizeConfig(salt="s", **options))
        assert source == unchanged
        target = result.ir["configuration"]["protocols"]["bgp"]["group"][0]["neighbor"][0]["name"]
        assert fnmatchcase(target, _apply_path(result).split()[-1][1:-1])
        assert result.patterns == ()
        restored = copy.deepcopy(result.ir)
        apply_revert(restored, result.mapping)
        assert restored == source
        rendered = _reader_source(text, fmt)
        dumped = tmp_path / "map.json"
        converted = convert_config_result(
            rendered,
            from_format=fmt,
            to_format=Format.JSON,
            validate=False,
            anon_config=AnonymizeConfig(salt="s", dump_map=str(dumped), **options),
        )
        cli = CliRunner().invoke(
            main,
            [
                "convert",
                "-i",
                fmt.value,
                "-e",
                "json",
                "--no-field-validate",
                *_flags(options),
                "--anonymize-salt",
                "s",
                "--anonymize-dump-map",
                str(dumped),
            ],
            input=rendered,
        )
        assert cli.exit_code == 0, cli.output
        for output in (converted.output, cli.stdout):
            cfg = json.loads(output)["configuration"]
            target = cfg["protocols"]["bgp"]["group"][0]["neighbor"][0]["name"]
            selector = cfg["policy-options"]["prefix-list"][0]["apply-path"].split()[-1][1:-1]
            assert fnmatchcase(target, selector)
            restored_text = convert_config(
                output,
                from_format=Format.JSON,
                to_format=Format.JSON,
                validate=False,
                anon_config=AnonymizeConfig(revert_map=str(dumped)),
            )
            assert json.loads(restored_text) == json.loads(
                convert_config(
                    rendered,
                    from_format=fmt,
                    to_format=Format.JSON,
                    validate=False,
                )
            )
        assert converted.diagnostics == () and cli.stderr == ""

    def test_an_existing_custom_wildcard_rule_needs_no_new_hook(self) -> None:
        """An inherited default protects a custom rule's old two-item wildcard answer."""

        class Custom(StubRule):
            def wildcard(
                self, text: str, schema_node: dict[str, Any], path: list[str]
            ) -> tuple[str, bool] | None:
                return "marker_*", True

        class Later(StubRule):
            def spans(self, text: str) -> list[tuple[int, int]]:
                return [(0, 6)] if text.startswith("marker") else []

        source = _ir("set groups GR protocols bgp group G neighbor <203.0.114.*>\n")
        walk(source, [Custom(), Later()], AnonymizeConfig())
        name = source["configuration"]["groups"][0]["protocols"]["bgp"]["group"][0]["neighbor"][0][
            "name"
        ]
        assert name == "<marker_*>"

    def test_surrounding_original_text_still_reaches_later_rules(self) -> None:
        """Protect only the generated prefix; the original peer word is still sensitive."""
        text = "set protocols bgp group peer-203.0.114.7 neighbor 198.51.100.1\n" + _prefix_list(
            "protocols bgp group <peer-203.0.114.*> neighbor <*>"
        )
        result = anonymize(
            _ir(text),
            AnonymizeConfig(
                ips=True,
                sensitive_words=["peer"],
                sensitive_patterns=[r"\d{3}"],
                salt="s",
            ),
        )
        name = result.ir["configuration"]["protocols"]["bgp"]["group"][0]["name"]
        selector = _apply_path(result).split()[3][1:-1]
        assert "peer" not in name and "peer" not in selector
        assert fnmatchcase(name, selector)
        assert result.patterns == ()
        restored = copy.deepcopy(result.ir)
        apply_revert(restored, result.mapping)
        assert restored == _ir(text)

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
            (
                "set routing-instances CUST-A protocols bgp group G neighbor 203.0.114.7\n",
                "routing-instances CUST-A protocols bgp group <*> neighbor <*>",
                {"sensitive_words": ["cust", "instances"]},
                "sensitive_word",
                "CUST-A",
            ),
            (
                "set protocols bgp group neighbor neighbor 203.0.114.7\n",
                "protocols bgp group neighbor neighbor <*>",
                {"groups": True},
                "group",
                "neighbor",
            ),
            (
                "set protocols ospf area 0.0.0.0 interface ge-0/0/0.0\n",
                "protocols ospf area 0.0.0.0 interface <*>",
                {"ips": True, "ignore_reserved": True},
                "ip",
                "0.0.0.0",
            ),
        ],
        ids=["group", "address", "community", "a-routing-instance", "a-keyword-name", "ospf-area"],
    )
    def test_a_name_in_it_takes_the_names_pseudonym(
        self, text: str, path: str, options: dict[str, Any], rule: str, original: str
    ) -> None:
        """Through the transparent `routing-instances` too, a name that is
        also a keyword is a name where a name stands, and the backbone area
        takes the area's replacement (Test/Challenge T7). A path the tree reads
        to its end is no content the walk cannot place."""
        result = anonymize(_ir(text + _prefix_list(path)), AnonymizeConfig(salt="s", **options))
        words = path.split(" ")
        words[words.index(original)] = result.mapping[rule][original]
        assert _apply_path(result) == " ".join(words)
        if original != "neighbor":  # the keyword-named row's keyword stays
            assert original not in _apply_path(result).split(" ")
        assert result.unplaced == ()

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
                "set interfaces ge-0/0/0 unit 0 family inet address 203.0.114.1/24\n",
                "interfaces <*> unit <*> family inet address <*>",
                {"ips": True, "groups": True, "sensitive_words": ["inet"]},
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
        ids=["match-all", "through-interfaces", "an-address-pattern", "a-renamed-name-pattern"],
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
        if path.endswith("neighbor <*>"):
            assert anonymized.endswith("neighbor <*>")
        if path.endswith("<203.0.114.*>"):
            pattern = anonymized.rsplit(" ", 1)[1][1:-1]
            [group] = result.ir["configuration"]["protocols"]["bgp"]["group"]
            assert re.fullmatch(
                pattern.replace(".", r"\.").replace("*", ".*"), group["neighbor"][0]["name"]
            )
        expected = ("policy-options.prefix-list.apply-path",) if reported else ()
        assert result.patterns == expected
        assert result.unplaced == ()
        if "interfaces" in path:
            assert anonymized == path

    def test_the_filter_at_the_apply_path_governs_its_names(self) -> None:
        """The apply-path's own place decides (specification challenge S7,
        interim: the safe side): with `protocols.bgp` excluded the group keeps
        `EBGP`, and the path in scope still has the name replaced."""
        text = "set protocols bgp group EBGP neighbor 203.0.114.7\n" + _prefix_list(
            "protocols bgp group EBGP neighbor <*>"
        )
        result = anonymize(
            _ir(text), AnonymizeConfig(groups=True, exclude=["protocols.bgp"], salt="s")
        )
        assert result.ir["configuration"]["protocols"]["bgp"]["group"][0]["name"] == "EBGP"
        assert "EBGP" not in _apply_path(result)
        excluded = anonymize(
            _ir(text), AnonymizeConfig(groups=True, exclude=["policy-options"], salt="s")
        )
        assert _apply_path(excluded) == "protocols bgp group EBGP neighbor <*>"

    @pytest.mark.parametrize("fmt", list(Format))
    @pytest.mark.parametrize(
        "selector",
        [
            "protocols bgp group EBGP-A neighbor <*>",
            "protocols bgp group <*> neighbor 203.0.114.7",
            "protocols bgp group <*> neighbor <203.0.114.*>",
            "protocols bgp group <EBGP-*> neighbor <*>",
            "protocols bgp group <*> neighbor <*>",
        ],
    )
    @pytest.mark.parametrize(
        "filters",
        [
            {"exclude": ["protocols.bgp"]},
            {"include": ["policy-options"]},
            {"exclude": ["policy-options"]},
            {},
        ],
    )
    def test_filtered_selector_meaning_is_reported(
        self, fmt: Format, selector: str, filters: dict[str, Any]
    ) -> None:
        """S7 independent supplemental audit: both filter directions and harmless controls."""
        text = "set protocols bgp group EBGP-A neighbor 203.0.114.7\n" + _prefix_list(selector)
        source = _ir(text)
        unchanged = copy.deepcopy(source)
        rendered = _reader_source(text, fmt)
        options = {"groups": True, "ips": True, "salt": "s", **filters}
        result = anonymize(source, AnonymizeConfig(**options))
        assert source == unchanged
        group = result.ir["configuration"]["protocols"]["bgp"]["group"][0]
        after = _apply_path(result)
        if filters == {"exclude": ["policy-options"]}:
            assert after == selector
            assert group["name"] != "EBGP-A"
        elif filters:
            assert group["name"] == "EBGP-A"
            assert group["neighbor"][0]["name"] == "203.0.114.7"

        def selects(path: str, name: str, address: str) -> bool:
            words = path.split()
            return all(
                fnmatchcase(value, word[1:-1]) if word.startswith("<") else value == word
                for value, word in [(name, words[3]), (address, words[5])]
            )

        before_selected = selects(selector, "EBGP-A", "203.0.114.7")
        after_selected = selects(after, group["name"], group["neighbor"][0]["name"])
        risky = before_selected != after_selected
        assert bool(result.patterns) == risky
        assert set(result.patterns) <= {"policy-options.prefix-list.apply-path"}
        conversion = convert_config_result(
            rendered,
            from_format=fmt,
            to_format=Format.JSON,
            validate=False,
            anon_config=AnonymizeConfig(**options),
        )
        warnings = [d for d in conversion.diagnostics if d.source == "anonymize"]
        assert bool(warnings) == risky
        assert {d.path for d in warnings} <= {"policy-options.prefix-list.apply-path"}
        cli = CliRunner().invoke(
            main,
            [
                "convert",
                "-i",
                fmt.value,
                "-e",
                "json",
                "--no-field-validate",
                "--anonymize-groups",
                "--anonymize-ips",
                "--anonymize-salt",
                "s",
            ]
            + [
                arg
                for key, paths in filters.items()
                for path in paths
                for arg in ["--anonymize-" + key, path]
            ],
            input=rendered,
        )
        assert cli.exit_code == 0, cli.output
        assert bool(cli.stderr.strip()) == risky
        messages = " ".join(d.message for d in warnings) + cli.stderr
        if risky:
            assert "selector" in messages
        forbidden = ["EBGP-A", "203.0.114.7", "PL", group["name"], group["neighbor"][0]["name"]]
        assert not any(value in messages for value in forbidden)
        assert apply_revert(result.ir, result.mapping) == source

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
