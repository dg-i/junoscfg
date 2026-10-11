"""The display-set reader: set commands into the dict IR.

Read through the `junoscfg.convert` door, `to_dict(source, "set")`, and
written back with `from_dict(ir, "set")` where a case is a round trip. The
keyed-entry cases read through `convert_config`, the door the Ansible
collection drives, with the helpers in `tests/support/keyed_entries.py`. A case
that needs a schema other than the shipped one writes its structure tree into
an artifacts directory and points conversion at it with
`junoscfg.display.artifacts_dir`, as `--artifacts` does.

Grouped by grammar feature: lexing, leaves, nokeyword leaves, presence, named
lists, entry keys, key aliases, merging, meta commands, the `apply-*`
statements, statements kept whole, and round trips.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import pytest

from junoscfg import FieldValidationError, Format, convert_config_result
from junoscfg.convert import from_dict, to_dict
from tests.support.artifacts import using_tree
from tests.support.keyed_entries import as_json, ir, set_ir, term_from, to_set
from tests.support.shapes import UNPLACED_RECORD

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


def read_set(source: str) -> dict[str, Any]:
    """The IR the set reader gives for *source*."""
    return to_dict(source, "set")


def write_set(config: Any) -> str:
    """Display-set text for an IR."""
    return from_dict(config, "set")


@pytest.fixture
def schema_tree(tmp_path: Path) -> Callable[[dict[str, Any]], Any]:
    """Read and write against a hand-written structure tree for one block."""
    return lambda tree: using_tree(tmp_path, tree)


_TERM = "set policy-options policy-statement SAMPLE-POLICY term T1"

#: How `convert_config` renders a statement kept whole in JSON: a key of its
#: level's `junoscfg:unplaced` record, the value a bare statement's.
KEPT = [None]


def kept(*statements: str, value: Any = KEPT) -> dict[str, Any]:
    """A level's record of *statements*, kept whole, each as *value*."""
    return {UNPLACED_RECORD: dict.fromkeys(statements, value)}


def kept_in(parent: dict[str, Any]) -> dict[str, Any]:
    """The record of the statements *parent* keeps whole, empty if none."""
    return parent.get(UNPLACED_RECORD, {})


def _from(line: str) -> dict:
    """`from` of term T1, as `convert_config` reads *line*."""
    return term_from(set_ir(line))


def _round_trip(source: str) -> list[str]:
    """*source* read and written back as display set, through `convert_config`."""
    return to_set(source + "\n", Format.SET)


def _unplaced(source: str, fmt: str = "set") -> list[str]:
    """The `field-validate` unplaced messages a conversion reports."""
    result = convert_config_result(source, from_format=Format(fmt), to_format=Format.SET)
    return [
        d.message
        for d in result.diagnostics
        if d.source == "field-validate" and "could not be placed" in d.message
    ]


# ── Lexing ───────────────────────────────────────────────────────────


class TestTheReaderRejectsBracketSyntax:
    """`[ a b ]` is curly syntax, never display set; the reader refuses it.

    The lexical check is `junoscfg.input.find_unsupported_set_brackets`, which
    the reader applies before it builds the IR.
    """

    @pytest.mark.parametrize(
        "line",
        [
            "set system apply-groups [ foo bar ]",
            "delete system apply-groups [ foo bar ]",
            "deactivate system apply-groups [ foo bar ]",
            "activate system apply-groups [ foo bar ]",
            "protect system apply-groups [ foo bar ]",
            "replace system apply-groups [ foo bar ]",
            "set system apply-groups [foo bar]",
            "set system apply-groups []",
            "set system apply-groups [ ]",
            "set system apply-groups [",
            "set system apply-groups ]",
            "set system host-name [router1]",
            "  set system apply-groups [ foo bar ]  ",
        ],
    )
    def test_every_command_and_bracket_form_is_rejected(self, line: str) -> None:
        expected = f"Unsupported bracket syntax in set input on line 1:\n{line}"
        with pytest.raises(ValueError, match=re.escape(expected)):
            read_set(line)

    def test_quoted_brackets_and_comments_remain_ordinary_content(self) -> None:
        source = (
            "# ignored unmatched bracket [\n"
            'set policy-options community FOO members "64498:[2-6]....$"\n'
            "/* ignored closing bracket ] */"
        )

        result = read_set(source)

        assert result["policy-options"]["community"][0]["members"] == ["64498:[2-6]....$"]


# ── Leaves ───────────────────────────────────────────────────────────


class TestALeafTakesItsValue:
    def test_single_leaf(self) -> None:
        assert read_set("set system host-name r1") == {"system": {"host-name": "r1"}}

    def test_quoted_value(self) -> None:
        result = read_set('set system host-name "my router"')
        assert result == {"system": {"host-name": "my router"}}

    def test_nested_leaf(self) -> None:
        result = read_set("set system services ssh root-login deny")
        assert result == {"system": {"services": {"ssh": {"root-login": "deny"}}}}

    def test_the_rest_of_the_line_is_the_value(self) -> None:
        """Every token after a leaf with no schema sibling among them is its value."""
        result = read_set("set system host-name foo bar baz")
        assert result["system"]["host-name"] == "foo bar baz"

    def test_a_leaf_takes_one_token_before_a_sibling(self) -> None:
        """A leaf consumes one token when the next one is a schema sibling."""
        source = (
            "set system syslog file messages_firewall_any"
            " archive size 10m files 5 no-world-readable"
        )
        archive = read_set(source)["system"]["syslog"]["file"][0]["archive"]
        assert archive["size"] == "10m"
        assert archive["files"] == "5"
        assert archive["no-world-readable"] == [None]

    def test_an_entry_keeps_its_sibling_leaves(self) -> None:
        """An NTP server with `version`, `prefer` and `routing-instance` on one line."""
        source = "set system ntp server 198.51.100.1 version 4 prefer routing-instance mgmt_junos"
        server = read_set(source)["system"]["ntp"]["server"][0]
        assert server["name"] == "198.51.100.1"
        assert server["version"] == "4"
        assert server["prefer"] == [None]
        assert server["routing-instance"] == "mgmt_junos"


class TestARepeatedLeafAccumulates:
    """A leaf-list value given on several lines accumulates in order."""

    @pytest.mark.parametrize(
        "ciphers",
        [["aes128-ctr", "aes256-ctr"], ["aes128-ctr", "aes256-ctr", "aes128-gcm"]],
        ids=["two", "three"],
    )
    def test_repeated_values_accumulate_in_order(self, ciphers: list[str]) -> None:
        source = "".join(f"set system services ssh ciphers {c}\n" for c in ciphers)
        assert read_set(source)["system"]["services"]["ssh"]["ciphers"] == ciphers

    def test_confederation_members_accumulate(self) -> None:
        source = (
            "set routing-options confederation members 64529\n"
            "set routing-options confederation members 64530\n"
        )
        members = read_set(source)["routing-options"]["confederation"]["members"]
        assert members == ["64529", "64530"]


# ── Nokeyword leaves ─────────────────────────────────────────────────


class TestANokeywordLeafTakesAPositionalValue:
    """A nokeyword leaf's value stands where its keyword would, and the
    statement's other tokens stay its siblings."""

    def test_a_traceoptions_file_name_keeps_its_siblings(self) -> None:
        source = "set protocols bgp traceoptions file bgp-log size 10m files 10"
        f = read_set(source)["protocols"]["bgp"]["traceoptions"]["file"]
        assert f["filename"] == "bgp-log"
        assert f["size"] == "10m"
        assert f["files"] == "10"

    def test_a_maximum_prefixes_limit_keeps_its_siblings(self) -> None:
        source = "set routing-options maximum-prefixes 3000000 threshold 50 log-interval 5"
        mp = read_set(source)["routing-options"]["maximum-prefixes"]
        assert mp["limit"] == "3000000"
        assert mp["threshold"] == "50"
        assert mp["log-interval"] == "5"

    def test_a_flat_dict_trigger_keeps_its_count(self) -> None:
        """`trigger` is a flat dict (`fd`) whose nokeyword `count` is its value."""
        source = "set event-options policy test within 1800 trigger 1"
        trigger = read_set(source)["event-options"]["policy"][0]["within"][0]["trigger"]
        assert trigger["count"] == "1"

    def test_a_freeform_nokeyword_leaf_keeps_its_name(self) -> None:
        """`vlan-id` is nokeyword only so its value validates freeform."""
        result = read_set("set interfaces ge-0/0/1 unit 0 vlan-id 100")
        unit = result["interfaces"]["interface"][0]["unit"][0]
        assert unit["vlan-id"] == "100"

    def test_a_positional_nokeyword_leaf_keeps_its_name(self) -> None:
        """26,386 nokeyword leaves carry a value and must not be re-keyed."""
        entry = read_set("set policy-options prefix-list PL 10.0.0.0/8")["policy-options"][
            "prefix-list"
        ][0]
        assert entry["prefix-list-item"] == [{"name": "10.0.0.0/8"}]

    def test_a_freeform_nokeyword_key_keeps_its_keyword(self, schema_tree: Any) -> None:
        """A `frnk` key is written with its keyword, and the reader and the writer
        agree on it because they share the grammar rule."""
        tree = {
            "c": {
                "sample": {
                    "L": True,
                    "k": ["vlan-id"],
                    "c": {"vlan-id": {"l": True, "nk": True, "frnk": True}},
                }
            }
        }
        line = "set sample vlan-id 100"
        with schema_tree(tree):
            assert read_set(line) == {"sample": [{"vlan-id": "100"}]}
            assert write_set({"sample": [{"vlan-id": "100"}]}) == line + "\n"


class TestAnOnOffSwitchKeysOnTheStatement:
    """An on/off switch keys on the statement, not on the schema node.

    The schema folds `enable`/`disable` into one nokeyword leaf named
    `enable-disable` whose enum is `['disable']`, so the token in a
    configuration is the statement itself. A device renders it
    `"disable": [null]`; keying on the node name invented an `enable-disable`
    statement no Junos would accept, and it reached JSON and YAML output
    silently — no validation failure, just wrong output on the path the
    downstream Ansible collection renders through.

    Found by round-tripping a device's own `| display json` and diffing:
    147 of the differences were this.
    """

    def test_disable_keys_on_the_statement(self) -> None:
        assert read_set("set protocols ospf disable") == {
            "protocols": {"ospf": {"disable": [None]}}
        }

    def test_a_switch_is_still_the_statement(self) -> None:
        assert read_set("set interfaces ge-0/0/0 disable") == {
            "interfaces": {"interface": [{"name": "ge-0/0/0", "disable": [None]}]}
        }

    def test_a_switch_followed_by_a_sibling_still_parses(self) -> None:
        entry = read_set("set interfaces ge-0/0/0 disable mtu 9000")["interfaces"]["interface"][0]
        assert entry == {"name": "ge-0/0/0", "disable": [None], "mtu": "9000"}


# ── Presence ─────────────────────────────────────────────────────────


class TestPresenceStatements:
    """A statement without a value reads as `[null]`; a presence list (`L` and
    `p` together, `snmp filter-interfaces interfaces`) takes entries too."""

    def test_an_ordinary_presence_statement_is_unchanged(self) -> None:
        assert read_set("set system no-redirects") == {"system": {"no-redirects": [None]}}

    def test_a_presence_list_with_a_value_gives_a_name_entry(self) -> None:
        result = read_set('set snmp filter-interfaces interfaces "^ge-"')
        assert result["snmp"]["filter-interfaces"]["interfaces"] == [{"name": "^ge-"}]

    def test_a_presence_list_without_a_value_is_present(self) -> None:
        result = read_set("set snmp filter-interfaces interfaces")
        assert result["snmp"]["filter-interfaces"]["interfaces"] == [None]

    def test_a_presence_list_takes_many_entries(self) -> None:
        source = (
            'set snmp filter-interfaces interfaces "^ge-0/0/0"\n'
            'set snmp filter-interfaces interfaces "^ge-0/0/1"\n'
        )
        ifaces = read_set(source)["snmp"]["filter-interfaces"]["interfaces"]
        assert ifaces == [{"name": "^ge-0/0/0"}, {"name": "^ge-0/0/1"}]


# ── Named lists ──────────────────────────────────────────────────────


class TestNamedLists:
    def test_transparent_named_list(self) -> None:
        result = read_set("set interfaces ge-0/0/0 description uplink")
        assert result == {
            "interfaces": {"interface": [{"name": "ge-0/0/0", "description": "uplink"}]}
        }

    def test_transparent_named_list_no_children(self) -> None:
        result = read_set("set interfaces ge-0/0/0")
        assert result == {"interfaces": {"interface": [{"name": "ge-0/0/0"}]}}

    def test_multiple_transparent_entries(self) -> None:
        source = (
            "set interfaces ge-0/0/0 description uplink\n"
            "set interfaces ge-0/0/1 description downlink\n"
        )
        assert read_set(source) == {
            "interfaces": {
                "interface": [
                    {"name": "ge-0/0/0", "description": "uplink"},
                    {"name": "ge-0/0/1", "description": "downlink"},
                ]
            }
        }

    def test_regular_named_list(self) -> None:
        result = read_set("set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1")
        assert result == {
            "routing-options": {
                "static": {"route": [{"name": "0.0.0.0/0", "next-hop": ["10.0.0.1"]}]}
            }
        }

    def test_nested_named_lists(self) -> None:
        """Lists inside lists; the presence statement `then accept` reads `[null]`."""
        result = read_set("set firewall family inet filter PROTECT term accept-ssh then accept")
        assert result["firewall"]["family"]["inet"]["filter"] == [
            {"name": "PROTECT", "term": [{"name": "accept-ssh", "then": {"accept": [None]}}]}
        ]

    def test_a_list_with_children_gives_name_entries(self) -> None:
        """`name-server` has children in the schema (`routing-instance`,
        `source-address`), so its entries are always dicts keyed `name`."""
        source = "set system name-server 8.8.8.8\nset system name-server 8.8.4.4\n"
        assert read_set(source) == {
            "system": {"name-server": [{"name": "8.8.8.8"}, {"name": "8.8.4.4"}]}
        }

    @pytest.mark.parametrize("second", ["0", "testdb"])
    def test_a_list_without_children_gives_name_entries(self, second: str) -> None:
        """`ephemeral instance` is `{L: true}`, no children: dict entries, not bare strings."""
        source = (
            "set system configuration-database ephemeral instance dgipingtest\n"
            f"set system configuration-database ephemeral instance {second}\n"
        )
        instances = read_set(source)["system"]["configuration-database"]["ephemeral"]["instance"]
        assert instances == [{"name": "dgipingtest"}, {"name": second}]


class TestPartialConfigTransparentLookup:
    """When set commands lack the parent keyword (e.g., 'interfaces'),
    the child-scan logic should still resolve transparent named lists."""

    def test_interface_without_parent(self) -> None:
        """set ge-0/0/0 description 'foo' produces nested interfaces.interface."""
        result = read_set('set ge-0/0/0 description "foo"')
        assert result["interfaces"]["interface"] == [{"name": "ge-0/0/0", "description": "foo"}]

    def test_loopback_without_parent(self) -> None:
        """set lo0 unit 0 family inet address ... produces proper nesting."""
        iface = read_set("set lo0 unit 0 family inet address 10.0.36.103/32")["interfaces"][
            "interface"
        ]
        assert iface[0]["name"] == "lo0"
        assert iface[0]["unit"][0]["name"] == "0"
        assert iface[0]["unit"][0]["family"]["inet"]["address"] == [{"name": "10.0.36.103/32"}]

    def test_ae_without_parent(self) -> None:
        """set ae100 mtu 9192 works via child-scan."""
        iface = read_set("set ae100 mtu 9192")["interfaces"]["interface"]
        assert iface[0]["name"] == "ae100"
        assert iface[0]["mtu"] == "9192"

    def test_deactivate_without_parent(self) -> None:
        """deactivate ge-0/0/0 applies inactive attribute via child-scan."""
        source = 'set ge-0/0/0 description "uplink"\ndeactivate ge-0/0/0\n'
        entry = read_set(source)["interfaces"]["interface"][0]
        assert entry["@"]["inactive"] is True

    def test_unknown_token_still_flattens(self) -> None:
        """Truly unknown tokens still get the flat-key fallback."""
        result = read_set("set xyzzy-nonexistent-thing some-value")
        assert kept_in(result) == {"xyzzy-nonexistent-thing some-value": True}


class TestTransparentListKey:
    """Tests for transparent-list-key children (tk flag) like
    prefix-list-item and syslog file contents."""

    def test_prefix_list_item_single(self) -> None:
        """prefix-list-item entry is created for a single prefix."""
        pl = read_set("set policy-options prefix-list MY-LIST 127.0.0.1/32")["policy-options"][
            "prefix-list"
        ][0]
        assert pl["name"] == "MY-LIST"
        assert pl["prefix-list-item"] == [{"name": "127.0.0.1/32"}]

    def test_prefix_list_item_multiple(self) -> None:
        """Multiple prefixes accumulate in the same prefix-list-item list."""
        source = (
            "set policy-options prefix-list MY-LIST 127.0.0.1/32\n"
            "set policy-options prefix-list MY-LIST 10.0.0.0/8\n"
        )
        pl = read_set(source)["policy-options"]["prefix-list"][0]
        assert pl["name"] == "MY-LIST"
        assert pl["prefix-list-item"] == [{"name": "127.0.0.1/32"}, {"name": "10.0.0.0/8"}]

    def test_syslog_contents_with_level(self) -> None:
        """Syslog file contents entry preserves the facility and level."""
        result = read_set("set system syslog file messages interactive-commands any")
        contents = result["system"]["syslog"]["file"][0]["contents"]
        assert contents == [{"name": "interactive-commands", "any": [None]}]

    def test_syslog_contents_multiple_facilities(self) -> None:
        """Multiple syslog facilities create separate contents entries."""
        source = (
            "set system syslog file messages interactive-commands any\n"
            "set system syslog file messages any notice\n"
        )
        contents = read_set(source)["system"]["syslog"]["file"][0]["contents"]
        assert [c["name"] for c in contents] == ["interactive-commands", "any"]

    def test_deactivate_prefix_list_item(self) -> None:
        """Deactivate targets a prefix-list-item entry correctly."""
        source = (
            "set policy-options prefix-list MY-LIST 10.0.0.0/8\n"
            "deactivate policy-options prefix-list MY-LIST 10.0.0.0/8\n"
        )
        item = read_set(source)["policy-options"]["prefix-list"][0]["prefix-list-item"][0]
        assert item["name"] == "10.0.0.0/8"
        assert item["@"]["inactive"] is True


class TestUplinkFailureDetectionGroupIsAList:
    """`uplink-failure-detection group G ...` is a list entry, not a fused key.

    The XSD wraps the named list `ufd-group-name` in a `group` container, the
    shape `groups`/`group` takes, but no fix named the wrapper because `group`
    is also BGP's list. Every release held read the line as one key; the
    `ufd-group-transparent` fix scopes the flag to its parent.
    """

    SOURCE = (
        "set protocols uplink-failure-detection group G link-to-monitor ae0\n"
        "set protocols uplink-failure-detection group G link-to-disable ge-0/0/1\n"
    )

    def test_the_group_is_an_entry_with_its_links(self) -> None:
        entries = read_set(self.SOURCE)["protocols"]["uplink-failure-detection"]["group"][
            "ufd-group-name"
        ]
        assert entries == [
            {
                "name": "G",
                "link-to-monitor": [{"name": "ae0"}],
                "link-to-disable": [{"name": "ge-0/0/1"}],
            }
        ]

    def test_it_round_trips_to_set(self) -> None:
        assert write_set(read_set(self.SOURCE)).strip() == self.SOURCE.strip()

    def test_a_deactivate_keeps_the_group_name(self) -> None:
        """Under the fused key, `deactivate ... group G` lost its `G`."""
        source = self.SOURCE + "deactivate protocols uplink-failure-detection group G\n"
        assert write_set(read_set(source)).strip() == source.strip()


class TestANonListNodeNeverReplacesAnEntry:
    """Any `maxOccurs` but 1 is a list, and a nokeyword leaf never overwrites a
    present, different value. `forwarding-classes class` collapsed into its
    last class, without a word. Owner decision on challenge A, phase-6 review
    of identifier-key-fields."""

    def test_three_forwarding_classes_stay_three(self) -> None:
        source = (
            "class-of-service {\n    forwarding-classes {\n"
            "        class fc0 queue-num 0;\n        class fc1 queue-num 1;\n"
            "        class mcast-fc queue-num 2;\n    }\n}\n"
        )
        classes = ir(source, Format.STRUCTURED)["class-of-service"]["forwarding-classes"]["class"]
        assert classes == [
            {"name": "fc0", "queue-num": "0"},
            {"name": "fc1", "queue-num": "1"},
            {"name": "mcast-fc", "queue-num": "2"},
        ]
        assert to_set(source, Format.STRUCTURED) == [
            f"set class-of-service forwarding-classes class {name} queue-num {n}"
            for n, name in enumerate(("fc0", "fc1", "mcast-fc"))
        ]
        assert _unplaced(source, "structured") == []

    @pytest.mark.parametrize(
        "lines",
        [
            ["set system commit peers 10.0.0.1", "set system commit peers 10.0.0.2"],
            [
                "set system services http servers server S1 port 80",
                "set system services http servers server S2 port 81",
            ],
        ],
    )
    def test_two_entries_stay_two(self, lines: list[str]) -> None:
        source = "\n".join(lines) + "\n"
        assert _round_trip(source.strip()) == lines
        assert _unplaced(source) == []

    def test_a_second_value_of_a_nokeyword_leaf_is_kept_whole(self) -> None:
        """`access securid-server` is a single node keyed by a nokeyword `name`:
        a second, different name is kept whole from the node's keyword and
        reported, never written over the first."""
        first = "set access securid-server SAMPLE-SERVER configuration-file sample-1"
        second = "set access securid-server SAMPLE-SERVER-2 configuration-file sample-2"
        got = read_set(f"{first}\n{second}\n")["access"]
        assert got["securid-server"] == {"name": "SAMPLE-SERVER", "configuration-file": "sample-1"}
        assert kept_in(got)["securid-server SAMPLE-SERVER-2 configuration-file sample-2"] is True
        assert _round_trip(f"{first}\n{second}") == [first, second]
        assert len(_unplaced(f"{first}\n{second}\n")) == 1

    def test_the_same_value_again_is_one_statement(self) -> None:
        first = "set access securid-server SAMPLE-SERVER configuration-file sample-1"
        again = "set access securid-server SAMPLE-SERVER"
        assert read_set(f"{first}\n{again}\n") == read_set(first)


# ── Entry keys ───────────────────────────────────────────────────────


class TestAnEntryKeyedOtherThanByName:
    """A list whose key is not `name` keys its entries on the fields the
    structure tree's `k` names, and writes them back in that order."""

    def test_a_route_filter_keys_on_its_address(self) -> None:
        result = read_set(
            "set policy-options policy-statement FOO term BAR from route-filter 0.0.0.0/0 exact"
        )
        rf = result["policy-options"]["policy-statement"][0]["term"][0]["from"]["route-filter"]
        assert rf == [{"address": "0.0.0.0/0", "exact": [None]}]

    def test_a_prefix_list_filter_keys_on_its_list_name(self) -> None:
        result = read_set(
            "set policy-options policy-statement FOO term BAR from prefix-list-filter MY-LIST exact"
        )
        plf = result["policy-options"]["policy-statement"][0]["term"][0]["from"][
            "prefix-list-filter"
        ]
        assert plf == [{"list_name": "MY-LIST", "exact": [None]}]

    def test_attributes_match_keys_on_its_three_fields(self) -> None:
        """Keyed by its three identifiers, where `name`, `_v0` and `_v1` used to
        stand in for them (identifier-key-fields, owner answer 1)."""
        source = (
            "set event-options policy test-policy "
            'attributes-match ping_test_failed.test-owner matches "^inet6-ping-uptime$"'
        )
        am = read_set(source)["event-options"]["policy"][0]["attributes-match"]
        assert am == [
            {
                "from-event-attribute": "ping_test_failed.test-owner",
                "condition": "matches",
                "to-event-attribute-value": "^inet6-ping-uptime$",
            }
        ]

    def test_attributes_match_round_trips(self) -> None:
        source = (
            "set event-options policy test-policy "
            'attributes-match ping_test_failed.test-owner matches "^inet6-ping-uptime$"\n'
        )
        config = read_set(source)
        assert write_set(config) == source, f"IR was: {config}"

    def test_a_community_keys_on_its_action_and_name(self) -> None:
        """`then community add VALUE`: the action comes before the name."""
        source = (
            "set policy-options policy-statement STMT term T then community add COMM1\n"
            "set policy-options policy-statement STMT term T then community delete COMM2\n"
        )
        comms = read_set(source)["policy-options"]["policy-statement"][0]["term"][0]["then"][
            "community"
        ]
        assert comms == [
            {"community-name": "COMM1", "add": [None]},
            {"community-name": "COMM2", "delete": [None]},
        ]

    def test_a_community_round_trips_action_first(self) -> None:
        source = (
            "set policy-options policy-statement STMT term T then community add COMM1\n"
            "set policy-options policy-statement STMT term T then community delete COMM2\n"
        )
        config = read_set(source)
        assert write_set(config) == source, f"IR was: {config}"


class TestKeyValuesOfEveryShape:
    """A key value is one token, whatever it spells."""

    @pytest.mark.parametrize(
        ("tokens", "entry"),
        [
            ("as-list as-list", {"list-type": "as-list", "list-name": "as-list"}),
            ("as-list-group as-list", {"list-type": "as-list-group", "list-name": "as-list"}),
            ('as-list "SAMPLE AS LIST"', {"list-type": "as-list", "list-name": "SAMPLE AS LIST"}),
            ("as-list 64496", {"list-type": "as-list", "list-name": "64496"}),
            # Out of the enum: read by position, reported by validation.
            ("1 SAMPLE-AS-LIST", {"list-type": "1", "list-name": "SAMPLE-AS-LIST"}),
        ],
    )
    def test_each_key_value_is_one_token(self, tokens: str, entry: dict) -> None:
        line = f"{_TERM} from as-path-neighbors {tokens}"
        assert _from(line) == {"as-path-neighbors": [entry]}
        assert _round_trip(line) == [line]


class TestAKeyKeywordBeforeTheValues:
    """The device accepts `route-filter exact <address>` and stores it as
    `route-filter <address> exact` (device probe round 4, vMX 23.2R2-S7.5)."""

    def test_a_match_type_before_the_address(self) -> None:
        line = f"{_TERM} from route-filter exact 198.51.100.0/24"
        expected = {"route-filter": [{"address": "198.51.100.0/24", "exact": [None]}]}
        assert _from(line) == expected
        assert _from(f"{_TERM} from route-filter 198.51.100.0/24 exact") == expected
        assert _round_trip(line) == [f"{_TERM} from route-filter 198.51.100.0/24 exact"]


_AREA = "set protocols ospf area 0.0.0.0 virtual-link"


class TestKeyFieldsGivenByKeyword:
    """A key field whose leaf is not `nokeyword` is read as `keyword value`,
    those fields in any order among themselves, and written in declared order;
    a missing field, or a value without its keyword, is rejected. Owner
    decision on challenge B, device probe round 5 (vMX 23.2R2-S7.5)."""

    _ENTRY = {"neighbor-id": "10.255.255.2", "transit-area": "0.0.0.3"}

    def test_declared_order(self) -> None:
        line = f"{_AREA} neighbor-id 10.255.255.2 transit-area 0.0.0.3"
        area = read_set(line)["protocols"]["ospf"]["area"][0]
        assert area["virtual-link"] == [self._ENTRY]
        assert _round_trip(line) == [line]
        assert _unplaced(line + "\n") == []

    def test_the_reversed_order_gives_the_same_ir(self) -> None:
        reversed_line = f"{_AREA} transit-area 0.0.0.3 neighbor-id 10.255.255.2"
        declared = f"{_AREA} neighbor-id 10.255.255.2 transit-area 0.0.0.3"
        assert read_set(reversed_line) == read_set(declared)
        assert _round_trip(reversed_line) == [declared]

    @pytest.mark.parametrize(
        "statement",
        [
            "virtual-link neighbor-id 10.255.255.3",
            "virtual-link 10.255.255.4 0.0.0.2",
            "virtual-link neighbor-id 10.255.255.4 0.0.0.2",
            "virtual-link neighbor-id 10.255.255.4 neighbor-id 10.255.255.5",
        ],
    )
    def test_an_incomplete_key_is_kept_whole_and_reported(self, statement: str) -> None:
        line = f"set protocols ospf area 0.0.0.0 {statement}"
        area = read_set(line)["protocols"]["ospf"]["area"][0]
        assert "virtual-link" not in area
        assert kept_in(area)[statement] is True
        assert _round_trip(line) == [line]
        assert len(_unplaced(line + "\n")) == 1

    def test_device_json_keeps_the_keywords(self) -> None:
        config = {
            "protocols": {"ospf": {"area": [{"name": "0.0.0.0", "virtual-link": [self._ENTRY]}]}}
        }
        assert to_set(as_json(config), Format.JSON) == [
            f"{_AREA} neighbor-id 10.255.255.2 transit-area 0.0.0.3"
        ]

    @pytest.mark.parametrize(
        ("line", "entry"),
        [
            (
                "set services nat pool SAMPLE-POOL address-range low 198.51.100.1"
                " high 198.51.100.9",
                {"low": "198.51.100.1", "high": "198.51.100.9"},
            ),
            (
                "set class-of-service schedulers SAMPLE-SCHED drop-profile-map loss-priority low"
                " protocol any drop-profile SAMPLE-DP",
                {"loss-priority": "low", "protocol": "any", "drop-profile": "SAMPLE-DP"},
            ),
        ],
    )
    def test_other_keyword_keys(self, line: str, entry: dict) -> None:
        got = read_set(line)
        parent = (
            got["services"]["nat"]["pool"][0]
            if "services" in got
            else (got["class-of-service"]["schedulers"][0])
        )
        slot = "address-range" if "services" in got else "drop-profile-map"
        assert parent[slot] == [entry]
        assert _round_trip(line) == [line]
        assert _unplaced(line + "\n") == []


# ── Key aliases ──────────────────────────────────────────────────────


class TestAKeyAliasIsTheSchemaKeyword:
    """`ieee-802.3ad`, the JSON spelling, and `802.3ad`, the configuration's,
    are one statement; the IR and the set output use the schema keyword."""

    def test_a_lacp_statement_reads_under_its_interface(self) -> None:
        source = (
            "set interfaces ae0 aggregated-ether-options lacp force-up\n"
            "set interfaces ae0 aggregated-ether-options lacp active\n"
        )
        iface = read_set(source)["interfaces"]["interface"][0]
        assert iface["name"] == "ae0"
        assert "aggregated-ether-options" in iface

    def test_802_3ad_round_trips_with_its_nokeyword_bundle(self) -> None:
        source = "set interfaces ge-0/0/0 ether-options 802.3ad ae22\n"
        config = read_set(source)
        iface = config["interfaces"]["interface"][0]
        assert iface["ether-options"]["802.3ad"]["bundle"] == "ae22"
        assert write_set(config) == source, f"IR was: {config}"

    def test_the_json_spelling_is_written_as_the_schema_keyword(self) -> None:
        config = {
            "interfaces": {
                "interface": [
                    {"name": "ge-0/0/0", "ether-options": {"ieee-802.3ad": {"bundle": "ae22"}}}
                ]
            }
        }
        result = write_set(config)
        assert "802.3ad ae22" in result
        assert "ieee-802.3ad" not in result


# ── Merging ──────────────────────────────────────────────────────────


class TestMerging:
    def test_merge_siblings(self) -> None:
        source = "set system host-name r1\nset system domain-name example.com\n"
        assert read_set(source) == {"system": {"host-name": "r1", "domain-name": "example.com"}}

    def test_merge_named_list_entries(self) -> None:
        source = (
            "set firewall family inet filter PROTECT term accept-ssh from protocol tcp\n"
            "set firewall family inet filter PROTECT term accept-ssh from destination-port ssh\n"
            "set firewall family inet filter PROTECT term accept-ssh then accept\n"
        )
        term = read_set(source)["firewall"]["family"]["inet"]["filter"][0]["term"][0]
        assert term == {
            "name": "accept-ssh",
            "from": {"protocol": ["tcp"], "destination-port": ["ssh"]},
            "then": {"accept": [None]},
        }

    def test_merge_interface_children(self) -> None:
        source = "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
        iface = read_set(source)["interfaces"]["interface"][0]
        assert iface["name"] == "ge-0/0/0"
        assert iface["unit"][0]["name"] == "0"
        assert iface["unit"][0]["family"]["inet"]["address"] == [{"name": "10.0.0.1/24"}]


# ── Meta commands ────────────────────────────────────────────────────


class TestMetaCommands:
    def test_deactivate_container(self) -> None:
        source = "set system host-name r1\ndeactivate system\n"
        assert read_set(source) == {"system": {"@": {"inactive": True}, "host-name": "r1"}}

    def test_protect_container(self) -> None:
        source = "set system host-name r1\nprotect system\n"
        assert read_set(source)["system"]["@"]["protect"] == "protect"

    def test_delete_container(self) -> None:
        source = "set system host-name r1\ndelete system\n"
        assert read_set(source)["system"]["@"]["operation"] == "delete"

    def test_activate_container(self) -> None:
        source = "set system host-name r1\nactivate system\n"
        assert read_set(source)["system"]["@"]["active"] == "active"

    def test_deactivate_transparent_entry(self) -> None:
        source = "set interfaces ge-0/0/0 description uplink\ndeactivate interfaces ge-0/0/0\n"
        entry = read_set(source)["interfaces"]["interface"][0]
        assert entry["@"]["inactive"] is True


class TestDeactivateOrdering:
    """A meta command is written right after its statement, not at the end."""

    def test_deactivate_appears_near_set(self) -> None:
        source = (
            "set interfaces ge-0/0/0 description uplink\n"
            "deactivate interfaces ge-0/0/0\n"
            "set interfaces ge-0/0/1 description downlink\n"
        )
        lines = write_set(read_set(source)).strip().split("\n")
        deact_idx = next(
            idx
            for idx, line in enumerate(lines)
            if "ge-0/0/0" in line and line.startswith("deactivate")
        )
        other_set_idx = next(
            idx for idx, line in enumerate(lines) if "ge-0/0/1" in line and line.startswith("set")
        )
        assert deact_idx < other_set_idx, (
            f"deactivate at {deact_idx} should come before set ge-0/0/1 at {other_set_idx}"
        )

    def test_protect_appears_near_set(self) -> None:
        source = (
            "set system host-name r1\n"
            "protect system\n"
            "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
        )
        lines = write_set(read_set(source)).strip().split("\n")
        protect_idx = next(idx for idx, line in enumerate(lines) if line.startswith("protect"))
        route_idx = next(idx for idx, line in enumerate(lines) if "routing-options" in line)
        assert protect_idx < route_idx


class TestMetaCommandsOnAKeyedEntry:
    """`deactivate`, `delete` and `protect` address an entry by its whole key."""

    @pytest.mark.parametrize(
        ("command", "attribute"),
        [
            ("deactivate", {"inactive": True}),
            ("delete", {"operation": "delete"}),
            ("protect", {"protect": "protect"}),
        ],
    )
    @pytest.mark.parametrize(
        ("where", "statement", "entry"),
        [
            (
                "from",
                "as-path-neighbors as-list SAMPLE-AS-LIST",
                {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"},
            ),
            (
                "from",
                "route-filter 198.51.100.0/24 exact",
                {"address": "198.51.100.0/24", "exact": [None]},
            ),
            ("then", "community add SAMPLE-COMM", {"add": [None], "community-name": "SAMPLE-COMM"}),
        ],
    )
    def test_the_attribute_lands_on_the_entry(
        self, command: str, attribute: dict, where: str, statement: str, entry: dict
    ) -> None:
        set_line = f"{_TERM} {where} {statement}"
        meta_line = f"{command} {set_line[len('set ') :]}"
        term = set_ir(set_line, meta_line)["policy-options"]["policy-statement"][0]["term"][0]
        slot = statement.split()[0]
        assert term[where][slot] == [{"@": attribute, **entry}]
        if command != "delete":
            assert _round_trip(f"{set_line}\n{meta_line}") == [set_line, meta_line]


class TestAMetaCommandIsNeverPartiallyApplied:
    """A malformed meta path is data to report, never a shorter valid path."""

    _ATTRS = {
        "deactivate": {"inactive": True},
        "activate": {"active": "active"},
        "protect": {"protect": "protect"},
        "delete": {"operation": "delete"},
    }

    @pytest.mark.parametrize("command", _ATTRS)
    @pytest.mark.parametrize(
        "suffix",
        ["as-path-neighbors as-list", "as-path-neighbors as-list SAMPLE-AS-LIST extra"],
        ids=["partial-key", "surplus-token"],
    )
    def test_a_partial_or_surplus_key_is_kept_whole(self, command: str, suffix: str) -> None:
        set_line = f"{_TERM} from as-path-neighbors as-list SAMPLE-AS-LIST"
        meta_line = f"{command} {_TERM[4:]} from {suffix}"

        config = read_set(f"{set_line}\n{meta_line}")
        from_ = config["policy-options"]["policy-statement"][0]["term"][0]["from"]

        assert "@" not in from_
        assert "@" not in from_["as-path-neighbors"][0]
        assert kept_in(from_)[f"@{suffix}"] == self._ATTRS[command]
        assert len(_unplaced(f"{set_line}\n{meta_line}\n")) == 1
        assert meta_line in write_set(config).splitlines()

    def test_an_unknown_path_does_not_annotate_its_valid_parent(self) -> None:
        source = "set system host-name router1\ndeactivate system bogus-thing"
        config = read_set(source)

        assert "@" not in config["system"]
        assert "bogus-thing" not in config["system"]
        assert kept_in(config["system"]) == {"@bogus-thing": {"inactive": True}}
        assert len(_unplaced(source + "\n")) == 1
        assert write_set(config).splitlines() == source.splitlines()

    def test_meta_on_an_existing_unknown_prefix_reuses_its_unplaced_report(self) -> None:
        source = "set system bogus-thing value\ndeactivate system bogus-thing"
        config = read_set(source)

        assert "@" not in config["system"]
        assert kept_in(config["system"]) == {
            "bogus-thing value": True,
            "@bogus-thing": {"inactive": True},
        }
        assert len(_unplaced(source + "\n")) == 1
        assert write_set(config).splitlines() == source.splitlines()

    def test_meta_on_an_existing_positional_value_is_kept_whole(self) -> None:
        source = "set protocols isis SAMPLE-UNKNOWN\ndeactivate protocols isis SAMPLE-UNKNOWN"
        config = read_set(source)

        assert config["protocols"]["isis"]["enable-disable"] == "SAMPLE-UNKNOWN"
        assert config["protocols"]["isis"]["@SAMPLE-UNKNOWN"] == {"inactive": True}
        assert _unplaced(source + "\n") == []
        assert write_set(config).splitlines() == source.splitlines()

    @pytest.mark.parametrize("command", _ATTRS)
    @pytest.mark.parametrize(
        ("set_line", "list_path"),
        [
            (
                f"{_TERM} from as-path-neighbors as-list SAMPLE-AS-LIST",
                f"{_TERM[4:]} from as-path-neighbors",
            ),
            ("set system login user admin uid 2000", "system login user"),
        ],
        ids=["as-path-neighbors", "login-user"],
    )
    def test_a_meta_attribute_on_a_whole_list_is_written(
        self, command: str, set_line: str, list_path: str
    ) -> None:
        meta_line = f"{command} {list_path}"
        written = write_set(read_set(f"{set_line}\n{meta_line}")).splitlines()
        assert set_line in written
        assert meta_line in written


# ── apply-groups and apply-macro ─────────────────────────────────────


class TestApplyGroups:
    """`apply-groups` and `apply-groups-except` take one name per statement,
    at the top and inside any hierarchy level; anything else is a statement
    the device rejects, kept whole and reported."""

    def test_top_level_apply_groups(self) -> None:
        source = "set apply-groups FOO\nset apply-groups BAR\n"
        assert read_set(source) == {"apply-groups": ["FOO", "BAR"]}

    def test_embedded_apply_groups(self) -> None:
        source = "set system host-name r1\nset system apply-groups FOO\n"
        assert read_set(source)["system"]["apply-groups"] == ["FOO"]

    def test_one_name_inside_a_policy(self) -> None:
        line = "set policy-options policy-statement SAMPLE-POLICY apply-groups SAMPLE-GROUP"
        policy = set_ir(line)["policy-options"]["policy-statement"][0]
        assert policy["apply-groups"] == ["SAMPLE-GROUP"]

    @pytest.mark.parametrize("keyword", ["apply-groups", "apply-groups-except"])
    @pytest.mark.parametrize("prefix", ["set", "set policy-options policy-statement SAMPLE-POLICY"])
    def test_two_names_apply_no_group(self, keyword: str, prefix: str) -> None:
        """The device rejects `set apply-groups G1 G2` (vMX 23.2R2-S7.5); the
        reader applied G1 and dropped G2. Spec: identifier-key-fields,
        "A statement the reader cannot complete is kept whole"."""
        line = f"{prefix} {keyword} SAMPLE-GROUP SAMPLE-GROUP-2"
        kept = f"{keyword} SAMPLE-GROUP SAMPLE-GROUP-2"
        for got, value in ((set_ir(line), KEPT), (read_set(line), True)):
            parent = got if prefix == "set" else got["policy-options"]["policy-statement"][0]
            assert keyword not in parent
            assert kept_in(parent)[kept] == value
        assert _round_trip(line) == [line]

    @pytest.mark.parametrize("keyword", ["apply-groups", "apply-groups-except"])
    def test_a_bare_keyword_is_kept_whole_and_reported(self, keyword: str) -> None:
        """A bare `set apply-groups` names no group, a statement the device
        rejects (finding 6, phase-6 review of identifier-key-fields)."""
        line = f"set system {keyword}"
        assert read_set(line) == {"system": kept(keyword, value=True)}
        assert _round_trip(line) == [line]
        assert len(_unplaced(line + "\n")) == 1

    def test_a_group_after_a_bare_one_is_placed(self) -> None:
        """Both statements survive, and only the bare one is reported. The
        reader used to raise on the second, then kept it whole as well, under
        the bare one's key (OPEN-2, change kept-whole-statements)."""
        source = "set apply-groups\nset apply-groups SAMPLE-GROUP"
        assert read_set(source) == {
            **kept("apply-groups", value=True),
            "apply-groups": ["SAMPLE-GROUP"],
        }
        assert _round_trip(source) == ["set apply-groups SAMPLE-GROUP", "set apply-groups"]
        assert _unplaced(source + "\n") == [
            "'apply-groups' could not be placed in the schema: kept as written, not validated"
        ]


class TestApplyMacroTakesAtMostThreeValues:
    """`apply-macro` takes a name, then optionally a keyword and its value; the
    device rejects a fourth value (device probe round 5, vMX 23.2R2-S7.5),
    which the reader turned into a second data entry without a word."""

    @pytest.mark.parametrize(
        ("line", "entry"),
        [
            ("set apply-macro ABCDE", {"name": "ABCDE"}),
            ("set apply-macro ABCDE DEFGH", {"name": "ABCDE", "data": [{"name": "DEFGH"}]}),
            (
                'set groups SAMPLE-GROUP apply-macro 12345 "KADJBF KU!H" balks',
                {"name": "12345", "data": [{"name": "KADJBF KU!H", "value": "balks"}]},
            ),
        ],
    )
    def test_one_to_three_values(self, line: str, entry: dict) -> None:
        got = read_set(line)
        parent = got["groups"]["group"][0] if "groups" in got else got
        assert parent["apply-macro"] == [entry]
        assert _round_trip(line) == [line]
        assert _unplaced(line + "\n") == []

    @pytest.mark.parametrize(
        "statement",
        ['apply-macro 12345 "KADJBF KU!H" balks XXXXX', "apply-macro 12345 XXX XXXX XXX"],
    )
    def test_a_fourth_value_is_kept_whole_and_reported(self, statement: str) -> None:
        line = f"set groups SAMPLE-GROUP {statement}"
        group = read_set(line)["groups"]["group"][0]
        assert "apply-macro" not in group
        assert group == {"name": "SAMPLE-GROUP", **kept(statement, value=True)}
        assert _round_trip(line) == [line]
        assert len(_unplaced(line + "\n")) == 1


class TestApplyFlagsIsAContainerOfFlags:
    """`apply-flags` holds presence flags, at every level, as the device writes it.

    The device prints `set groups GR-OMIT system apply-flags omit`, XML
    `<apply-flags><omit/></apply-flags>` and JSON `"apply-flags": {"omit":
    [null]}` (vMX 23.2R2-S7.5, QFX5120 25.2R2-S1.5,
    `tests/data/device/synthetic/*/junoscfg-oracle.*`). The tree had a leaf, so
    the reader kept the line whole and reported it below the root, and read
    the leaf `"omit"` at the top (DEV-V2). `replace` is the spelling the
    grammar accepted from a production configuration (probe P8 for its JSON).
    Spec: schema-pipeline/universal-statements, change
    universal-statements-from-tree.
    """

    @pytest.mark.parametrize(
        "flag",
        [
            "omit",
            # EVIDENCE_BLOCKED on probe P8: the shape of `replace` is inferred
            # from `omit`; the grammar accepted it before, and still does.
            pytest.param("replace", id="replace-P8"),
        ],
    )
    @pytest.mark.parametrize(
        ("prefix", "blocks", "where"),
        [
            ("", [], ()),
            ("system ", ["system"], ("system",)),
            ("groups GR-OMIT system ", ["groups", "GR-OMIT", "system"], ("groups", 0, "system")),
            (
                "protocols bgp group G1 ",
                ["protocols", "bgp", "group G1"],
                ("protocols", "bgp", "group", 0),
            ),
        ],
        ids=["top", "system", "group", "bgp-group"],
    )
    @pytest.mark.parametrize("fmt", ["set", "structured"])
    def test_a_flag_reads_as_the_device_writes_it(
        self, flag: str, prefix: str, blocks: list[str], where: tuple[Any, ...], fmt: str
    ) -> None:
        line = f"set {prefix}apply-flags {flag}"
        if fmt == "set":
            source = line + "\n"
        else:
            source = f"apply-flags {flag};\n"
            for opener in reversed(blocks):
                inner = "".join("    " + row + "\n" for row in source.splitlines())
                source = f"{opener} {{\n{inner}}}\n"
        node = ir(source, Format(fmt))
        for step in where:
            node = node[step]
        assert node["apply-flags"] == {flag: [None]}
        assert UNPLACED_RECORD not in node
        assert to_set(source, Format(fmt)) == [line]
        assert _unplaced(source, fmt) == []

    @pytest.mark.parametrize(
        ("prefix", "where"),
        [("", ()), ("system ", ("system",)), ("groups GR-OMIT system ", ("groups", 0, "system"))],
        ids=["top", "system", "group"],
    )
    def test_another_word_is_kept_whole_and_reported(
        self, prefix: str, where: tuple[Any, ...]
    ) -> None:
        """Any other word is no flag the tree knows: kept from that word, as in
        any container, reported, and written back. At the top it used to be the
        leaf's value, read without a word."""
        line = f"set {prefix}apply-flags bogus"
        parent = set_ir(line)
        for step in where:
            parent = parent[step]
        assert parent["apply-flags"] == kept("bogus")
        assert _round_trip(line) == [line]
        assert len(_unplaced(line + "\n")) == 1

    @pytest.mark.parametrize(
        ("fmt", "source"),
        [
            ("set", "set system apply-flags\n"),
            ("structured", "system {\n    apply-flags;\n}\n"),
            ("json", '{"configuration": {"system": {"apply-flags": {}}}}'),
            ("json", '{"configuration": {"system": {"apply-flags": true}}}'),
            ("yaml", "configuration:\n  system:\n    apply-flags:\n"),
        ],
        ids=["set", "structured", "json-empty", "json-true", "yaml"],
    )
    def test_a_bare_keyword_is_reported(self, fmt: str, source: str) -> None:
        """`apply-flags` naming no flag says nothing the device's spelling does;
        reported, and rejected by the grammar, as the old leaf wanting a value
        was (Test/Challenge finding 7, Reviewer finding 2)."""
        assert len(_unplaced(source, fmt)) == 1
        assert to_set(source, Format(fmt)) == ["set system apply-flags"]

    def test_a_flag_known_only_by_its_tag_is_reported(self) -> None:
        """A lone `deactivate system apply-flags omit` sets no flag: the base kept
        it whole and reported it, and so is it reported now (Reviewer finding 2)."""
        assert len(_unplaced("deactivate system apply-flags omit\n")) == 1

    @pytest.mark.parametrize(
        ("fmt", "source", "line"),
        [
            (
                "set",
                "set system apply-flags apply-groups G1\n",
                "set system apply-flags apply-groups G1",
            ),
            (
                "set",
                "set system apply-flags apply-flags omit\n",
                "set system apply-flags apply-flags omit",
            ),
            (
                "structured",
                "system {\n    apply-flags {\n        apply-groups G1;\n    }\n}\n",
                "set system apply-flags apply-groups G1",
            ),
            (
                "json",
                '{"configuration": {"system": {"apply-flags": {"apply-groups": ["G1"]}}}}',
                "set system apply-flags apply-groups G1",
            ),
        ],
        ids=["set-apply-groups", "set-apply-flags", "structured", "json"],
    )
    def test_no_universal_statement_inside_apply_flags(
        self, fmt: str, source: str, line: str
    ) -> None:
        """A statement valid at every level is no flag: inside `apply-flags` it is
        reported and written back as read, never placed (Reviewer finding 1; spec
        schema-pipeline/universal-statements)."""
        assert len(_unplaced(source, fmt)) == 1
        assert to_set(source, Format(fmt)) == [line]


# ── Statements kept whole ────────────────────────────────────────────


class TestTokensTheReaderCannotPlaceAreKept:
    """No entry, no group and no dropped token from a line the device rejects.

    Spec: conversion/entry-keys, "A statement the reader cannot complete is
    kept whole" (change identifier-key-fields).
    """

    @pytest.mark.parametrize(
        "statement",
        [
            "as-path-neighbors as-list",
            "as-path-origins as-list-group",
            "route-filter 198.51.100.0/24",
            "route-filter 198.51.100.0/24 next-policy",
            "source-address-filter 198.51.100.0/24",
        ],
    )
    def test_a_partial_key_creates_no_entry(self, statement: str) -> None:
        line = f"{_TERM} from {statement}"
        assert _from(line) == kept(statement)
        assert _round_trip(line) == [line]

    @pytest.mark.parametrize("slot", ["as-path-neighbors", "as-path-origins", "as-path-transits"])
    def test_a_bare_list_keyword_creates_no_entry(self, slot: str) -> None:
        """A keyed list's keyword with no key value is a statement the reader
        cannot complete: kept whole, as written, and reported like a partial
        key (owner decision, phase 5; the device rejects the bare line)."""
        line = f"{_TERM} from {slot}"
        assert _from(line) == kept(slot)
        assert _round_trip(line) == [line]
        result = convert_config_result(
            line + "\n", from_format=Format.SET, to_format=Format.SET, validate=True
        )
        assert result.output.strip() == line
        messages = [d.message for d in result.diagnostics if d.source == "field-validate"]
        assert messages == [
            f"'{slot}' could not be placed in the schema: kept as written, not validated"
        ]

    def test_a_keyed_entry_after_a_bare_keyword_is_placed(self) -> None:
        """The bare keyword is kept and reported; the entry after it is placed.
        It used to be kept whole as well, under the bare keyword's key (OPEN-2,
        change kept-whole-statements)."""
        bare = f"{_TERM} from as-path-neighbors"
        full = f"{bare} as-list SAMPLE-AS-LIST"
        assert _from(f"{bare}\n{full}") == {
            "as-path-neighbors": [{"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"}],
            **kept("as-path-neighbors"),
        }
        assert _round_trip(f"{bare}\n{full}") == [full, bare]
        assert len(_unplaced(f"{bare}\n{full}\n")) == 1

    def test_a_partial_attributes_match_creates_no_entry(self) -> None:
        line = (
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner matches"
        )
        policy = set_ir(line)["event-options"]["policy"][0]
        assert policy == {
            "name": "SAMPLE-EVENT-POLICY",
            **kept("attributes-match ping.test-owner matches"),
        }
        assert _round_trip(line) == [line]

    @pytest.mark.parametrize(
        ("where", "statement"),
        [
            ("from", "as-path-neighbors as-list SAMPLE-AS-LIST SAMPLE-EXTRA"),
            ("from", "as-path-transits as-list-group SAMPLE-AS-LIST SAMPLE-EXTRA"),
            ("then", "community add SAMPLE-COMM SAMPLE-EXTRA"),
        ],
    )
    def test_a_surplus_after_a_terminal_entry_keeps_the_line_whole(
        self, where: str, statement: str
    ) -> None:
        line = f"{_TERM} {where} {statement}"
        term = set_ir(line)["policy-options"]["policy-statement"][0]["term"][0]
        assert term[where] == kept(statement)
        assert _round_trip(line) == [line]

    def test_a_surplus_after_attributes_match_keeps_the_line_whole(self) -> None:
        statement = 'attributes-match ping.test-owner matches "^uptime$" SAMPLE-EXTRA'
        line = f"set event-options policy SAMPLE-EVENT-POLICY {statement}"
        policy = set_ir(line)["event-options"]["policy"][0]
        assert "attributes-match" not in policy
        assert policy == {"name": "SAMPLE-EVENT-POLICY", **kept(statement)}
        assert _round_trip(line) == [line]

    def test_an_unknown_token_in_an_entry_with_children_is_unchanged(self) -> None:
        """Pinned as it is: after a complete key the entry is open, and an
        unknown token stays in it, as `set interfaces ge-0/0/0 nonsense` does."""
        line = f"{_TERM} from route-filter 198.51.100.0/24 exact SAMPLE-EXTRA"
        assert _from(line) == {
            "route-filter": [
                {"address": "198.51.100.0/24", "exact": [None], **kept("SAMPLE-EXTRA")}
            ]
        }


class TestAnUnmodelledStatementIsKeptWhole:
    """A statement the schema cannot place keeps every token, as one key.

    The nokeyword catch-all took an unknown token as the leaf's value and
    returned, so `set interfaces ge-0/0/0 nonsense alpha beta gamma` became
    `{"enable-disable": "nonsense"}` and three tokens vanished -- into a key
    the JSON schema accepts, so nothing anywhere said so. That is the
    mechanism that hid the defective 24.4R0 artifacts for five months. The
    rest of the line is now kept verbatim, as the unknown-token path always
    did, and field validation reports it.
    """

    def test_the_rest_of_the_line_is_not_dropped(self) -> None:
        entry = read_set("set interfaces ge-0/0/0 nonsense alpha beta gamma")["interfaces"][
            "interface"
        ][0]
        assert entry == {"name": "ge-0/0/0", **kept("nonsense alpha beta gamma", value=True)}

    def test_it_round_trips_to_set(self) -> None:
        source = "set interfaces ge-0/0/0 nonsense alpha beta gamma"
        assert write_set(read_set(source)).strip() == source

    def test_a_valid_line_with_two_positional_values_is_kept_whole(self) -> None:
        """The one case where the guard moves a valid Junos line: a nokeyword
        leaf takes one value, so the second used to vanish. 69 of 1.4 million
        jvd set lines, every one kept whole now and reported as unplaced."""
        source = "set protocols mpls label-range srgb-label-range 16000 23999"
        config = read_set(source)
        assert "23999" in str(config)
        assert write_set(config).strip() == source

    def test_a_schema_node_without_a_type_keeps_the_line_too(self, schema_tree: Any) -> None:
        """The last fallback took one token as the value and dropped the rest."""
        with schema_tree({"c": {"system": {"c": {"odd": {}}}}}):
            assert read_set("set system odd a b") == {"system": kept("odd a b", value=True)}


_SAMPLE_AS_LIST = {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST"}


def _in_from(**from_: Any) -> dict[str, Any]:
    """Term T1 of SAMPLE-POLICY whose `from` holds *from_*, as JSON renders it."""
    term = {"name": "T1", "from": from_}
    return {"policy-options": {"policy-statement": [{"name": "SAMPLE-POLICY", "term": [term]}]}}


class TestAKeptStatementHasARecordOfItsOwn:
    """A statement the reader cannot place goes to its level's
    `junoscfg:unplaced` record, as its own tokens, and never meets a node the
    reader placed.

    It used to be a key of its own at its parent's level, the tokens joined
    after their quotes were stripped. A bare keyword had the key of the node
    it names: `set apply-groups` after `set apply-groups G1` vanished, and
    before it the valid `G1` was kept and reported too (OPEN-2). A leaf with no
    value was not kept at all and replaced its value with `null` (NEW-C1). A
    quoted token came back as several words (OPEN-3). Spec: conversion/entry-keys,
    change kept-whole-statements; the device rejects every bare statement here
    (corpus CORRECTLY_REJECTED, vMX 23.2R2-S7.5).
    """

    @pytest.mark.parametrize(
        ("placed", "bare", "expected"),
        [
            (
                "set apply-groups SAMPLE-GROUP",
                "set apply-groups",
                {"apply-groups": ["SAMPLE-GROUP"], **kept("apply-groups")},
            ),
            (
                "set apply-groups-except SAMPLE-GROUP",
                "set apply-groups-except",
                {"apply-groups-except": ["SAMPLE-GROUP"], **kept("apply-groups-except")},
            ),
            (
                "set system apply-groups SAMPLE-GROUP",
                "set system apply-groups",
                {"system": {"apply-groups": ["SAMPLE-GROUP"], **kept("apply-groups")}},
            ),
            (
                f"{_TERM} from as-path-neighbors as-list SAMPLE-AS-LIST",
                f"{_TERM} from as-path-neighbors",
                _in_from(**{"as-path-neighbors": [_SAMPLE_AS_LIST], **kept("as-path-neighbors")}),
            ),
        ],
        ids=["apply-groups", "apply-groups-except", "inside-system", "keyed-list"],
    )
    @pytest.mark.parametrize("bare_first", [False, True], ids=["placed-first", "bare-first"])
    def test_a_bare_keyword_never_meets_its_placed_node(
        self, placed: str, bare: str, expected: dict, bare_first: bool
    ) -> None:
        lines = [bare, placed] if bare_first else [placed, bare]
        source = "\n".join(lines) + "\n"
        assert set_ir(*lines) == expected
        assert sorted(_round_trip(source.strip())) == sorted(lines)
        statement = bare.split()[-1]
        assert len(_unplaced(source)) == 1
        assert _unplaced(source)[0].startswith(f"'{statement}'")

    @pytest.mark.parametrize(
        ("placed", "kept_line", "expected"),
        [
            (
                "set apply-macro SAMPLE-MACRO a",
                "set apply-macro SAMPLE-MACRO a b c d",
                {
                    "apply-macro": [{"name": "SAMPLE-MACRO", "data": [{"name": "a"}]}],
                    **kept("apply-macro SAMPLE-MACRO a b c d"),
                },
            ),
            (
                "set apply-groups SAMPLE-GROUP",
                "set apply-groups SAMPLE-GROUP-1 SAMPLE-GROUP-2",
                {
                    "apply-groups": ["SAMPLE-GROUP"],
                    **kept("apply-groups SAMPLE-GROUP-1 SAMPLE-GROUP-2"),
                },
            ),
        ],
        ids=["apply-macro-fourth-value", "apply-groups-two-names"],
    )
    def test_a_kept_sibling_leaves_the_placed_node_alone(
        self, placed: str, kept_line: str, expected: dict
    ) -> None:
        """The negative side: a kept statement whose text never had the
        placed node's key changes nothing beside it, as before the record."""
        assert set_ir(placed, kept_line) == expected
        assert sorted(_round_trip(f"{placed}\n{kept_line}")) == sorted([placed, kept_line])
        assert len(_unplaced(f"{placed}\n{kept_line}\n")) == 1

    def test_each_kept_statement_is_reported(self) -> None:
        """Two statements in one record are two reports, each naming its own."""
        source = "set system bogus-a 1\nset system bogus-b 2\n"
        assert set_ir(*source.split("\n")[:2]) == {"system": kept("bogus-a 1", "bogus-b 2")}
        assert sorted(_unplaced(source)) == [
            f"'{statement}' could not be placed in the schema: kept as written, not validated"
            for statement in ("bogus-a 1", "bogus-b 2")
        ]

    def test_the_record_name_in_the_input_forges_nothing(self) -> None:
        """`junoscfg:unplaced` written in a set line is a word like any other:
        the statement it starts is kept in the record, never taken as one.
        A schema statement whose name holds a colon is placed as before."""
        line = "set system junoscfg:unplaced host-name"
        assert set_ir(line) == {"system": kept("junoscfg:unplaced host-name")}
        assert _round_trip(line) == [line]
        assert len(_unplaced(line + "\n")) == 1
        placed = "set ietf-netconf-acm:nacm enable-nacm true"
        assert read_set(placed) == {"ietf-netconf-acm:nacm": {"enable-nacm": "true"}}
        assert _unplaced(placed + "\n") == []

    @pytest.mark.parametrize(
        "statement",
        ["nonsense a;b", "nonsense }", "nonsense {", 'nonsense a"b'],
        ids=["semicolon", "close-brace", "open-brace", "inner-quote"],
    )
    def test_a_statement_no_writer_can_print_is_refused(self, statement: str) -> None:
        """Kept whole, the words are printed as written; one that curly text
        reads as structure would close or open a block there. Refused, as
        bracket syntax is, with a message that names no word."""
        line = f"set interfaces ge-0/0/0 {statement}"
        with pytest.raises(ValueError, match="not one line of words") as caught:
            read_set(line)
        assert "nonsense" not in str(caught.value)

    @pytest.mark.parametrize(
        ("valued", "bare", "expected"),
        [
            (
                "set system host-name router1",
                "set system host-name",
                {"system": {"host-name": "router1", **kept("host-name")}},
            ),
            (
                "set policy-options community SAMPLE-COMM members 64496:1",
                "set policy-options community SAMPLE-COMM members",
                {
                    "policy-options": {
                        "community": [
                            {"name": "SAMPLE-COMM", "members": ["64496:1"], **kept("members")}
                        ]
                    }
                },
            ),
        ],
        ids=["host-name", "members"],
    )
    @pytest.mark.parametrize("bare_first", [False, True], ids=["valued-first", "bare-first"])
    def test_a_leaf_without_its_value_never_replaces_it(
        self, valued: str, bare: str, expected: dict, bare_first: bool
    ) -> None:
        lines = [bare, valued] if bare_first else [valued, bare]
        source = "\n".join(lines) + "\n"
        assert set_ir(*lines) == expected
        assert sorted(_round_trip(source.strip())) == sorted(lines)
        assert len(_unplaced(source)) == 1
        with pytest.raises(FieldValidationError):
            convert_config_result(source, from_format=Format.SET, to_format=Format.SET, strict=True)

    def test_a_lone_leaf_without_its_value_is_kept_and_reported(self) -> None:
        line = "set system host-name"
        assert set_ir(line) == {"system": kept("host-name")}
        assert _round_trip(line) == [line]
        assert _unplaced(line + "\n") == [
            "'host-name' could not be placed in the schema: kept as written, not validated"
        ]

    def test_a_structured_leaf_without_its_value_never_replaces_it(self) -> None:
        source = "system {\n    host-name router1;\n    host-name;\n}\n"
        assert ir(source, Format.STRUCTURED) == {
            "system": {"host-name": "router1", **kept("host-name")}
        }
        assert sorted(to_set(source, Format.STRUCTURED)) == [
            "set system host-name",
            "set system host-name router1",
        ]
        assert len(_unplaced(source, "structured")) == 1

    @pytest.mark.parametrize(
        ("lines", "parent", "record"),
        [
            (
                ['set groups SAMPLE-GROUP apply-macro 12345 "KADJBF KU!H" balks XXXXX'],
                lambda got: got["groups"][0],
                {'apply-macro 12345 "KADJBF KU!H" balks XXXXX': KEPT},
            ),
            *(
                (
                    [f"set interfaces ge-0/0/0 {statement}"],
                    lambda got: got["interfaces"]["interface"][0],
                    {statement: KEPT},
                )
                for statement in (
                    'nonsense "alpha beta" gamma',
                    'nonsense "abc" gamma',
                    'nonsense "" gamma',
                    'nonsense "alpha  beta"',
                    'nonsense "say \\"hi\\""',
                )
            ),
            (
                [
                    'set system bogus-thing "alpha beta"',
                    'deactivate system bogus-thing "alpha beta"',
                ],
                lambda got: got["system"],
                {
                    'bogus-thing "alpha beta"': KEPT,
                    '@bogus-thing "alpha beta"': {"inactive": True},
                },
            ),
        ],
        ids=[
            "apply-macro",
            "spaced",
            "no-space",
            "empty",
            "two-spaces",
            "escaped-quote",
            "tagged-statement",
        ],
    )
    def test_a_kept_statement_keeps_its_quotes(
        self, lines: list[str], parent: Callable[[dict], dict], record: dict
    ) -> None:
        """Every writer writes it as it was read, and it reads back the same."""
        source = "\n".join(lines) + "\n"
        got = set_ir(*lines)
        assert kept_in(parent(got)) == record
        assert _round_trip(source.strip()) == lines
        for writer in (Format.STRUCTURED, Format.JSON, Format.YAML):
            output = convert_config_result(
                source, from_format=Format.SET, to_format=writer, validate=False
            ).output
            assert ir(output, writer) == got, writer.value
        assert len(_unplaced(source)) == 1

    @pytest.mark.parametrize(
        ("lines", "record"),
        [
            (
                ['deactivate system bogus-thing "alpha beta"'],
                {'@bogus-thing "alpha beta"': {"inactive": True}},
            ),
            (
                [
                    'set system bogus-thing "alpha beta" gamma',
                    'deactivate system bogus-thing "alpha beta"',
                ],
                {
                    'bogus-thing "alpha beta" gamma': KEPT,
                    '@bogus-thing "alpha beta"': {"inactive": True},
                },
            ),
        ],
        ids=["alone", "on-a-kept-prefix"],
    )
    def test_a_kept_meta_command_keeps_its_quotes(self, lines: list[str], record: dict) -> None:
        """Set, JSON and YAML output carry it as read. Structured text can tag
        only a statement it writes, so structured output leaves the command
        out and says so, where it used to drop it without a word or move the
        tag onto the longer statement."""
        source = "\n".join(lines) + "\n"
        got = set_ir(*lines)
        assert kept_in(got["system"]) == record
        assert _round_trip(source.strip()) == lines
        for writer in (Format.JSON, Format.YAML):
            output = convert_config_result(
                source, from_format=Format.SET, to_format=writer, validate=False
            ).output
            assert ir(output, writer) == got, writer.value
        assert len(_unplaced(source)) == 1
        result = convert_config_result(
            source, from_format=Format.SET, to_format=Format.STRUCTURED, validate=False
        )
        assert "inactive:" not in result.output
        notes = [d.message for d in result.diagnostics if d.source == "structured-output"]
        assert len(notes) == 1
        assert "kept whole" in notes[0]

    def test_the_display_door_names_the_record(self) -> None:
        from junoscfg.display import UNPLACED_STATEMENTS

        assert UNPLACED_STATEMENTS == UNPLACED_RECORD


# ── Round trips ──────────────────────────────────────────────────────


ROUND_TRIP_CONFIGS = [
    {"system": {"host-name": "r1"}},
    {"system": {"services": {"ssh": {"root-login": "deny"}}}},
    {
        "interfaces": {
            "interface": [
                {"name": "ge-0/0/0", "description": "uplink"},
                {"name": "ge-0/0/1", "description": "downlink"},
            ]
        }
    },
    {
        "interfaces": {
            "interface": [
                {
                    "name": "ge-0/0/0",
                    "unit": [
                        {
                            "name": "0",
                            "family": {"inet": {"address": [{"name": "10.0.0.1/24"}]}},
                        }
                    ],
                }
            ]
        }
    },
    {
        "system": {
            "host-name": "r1",
            "domain-name": "example.com",
            "name-server": ["8.8.8.8", "8.8.4.4"],
        }
    },
    {"system": {"@": {"inactive": True}, "host-name": "r1"}},
    {"routing-options": {"static": {"route": [{"name": "0.0.0.0/0", "next-hop": "10.0.0.1"}]}}},
    {
        "firewall": {
            "family": {
                "inet": {
                    "filter": [
                        {
                            "name": "PROTECT",
                            "term": [
                                {
                                    "name": "accept-ssh",
                                    "from": {
                                        "protocol": "tcp",
                                        "destination-port": "ssh",
                                    },
                                    "then": {"accept": [None]},
                                }
                            ],
                        }
                    ],
                }
            }
        }
    },
]


class TestDictSetDictRoundTrip:
    """dict→set→dict round-trip: the IR dict survives a set conversion.

    Because the set format is lossy (can't distinguish bare-string list
    entries from dict entries with only a 'name' key), we compare via
    set output rather than exact dict equality.
    """

    @pytest.mark.parametrize("config", ROUND_TRIP_CONFIGS)
    def test_roundtrip_via_set(self, config: dict) -> None:
        set_text = write_set(config)
        assert write_set(read_set(set_text)) == set_text, (
            f"Set output differs after round-trip:\n{set_text}"
        )


SET_ROUND_TRIP_SOURCES = [
    "set system host-name r1\n",
    "set system services ssh root-login deny\n",
    "set interfaces ge-0/0/0 description uplink\nset interfaces ge-0/0/1 description downlink\n",
    "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n",
    (
        "set system host-name r1\nset system domain-name example.com\n"
        "set system name-server 8.8.8.8\nset system name-server 8.8.4.4\n"
    ),
    "set system host-name r1\ndeactivate system\n",
    "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n",
    (
        "set firewall family inet filter PROTECT term accept-ssh from protocol tcp\n"
        "set firewall family inet filter PROTECT term accept-ssh from destination-port ssh\n"
        "set firewall family inet filter PROTECT term accept-ssh then accept\n"
    ),
]


class TestSetDictSetRoundTrip:
    """set→dict→set round-trip: set commands survive a dict conversion."""

    @pytest.mark.parametrize("source", SET_ROUND_TRIP_SOURCES)
    def test_roundtrip(self, source: str) -> None:
        config = read_set(source)
        assert write_set(config) == source, f"IR was: {config}"
