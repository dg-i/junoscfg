"""Test/Challenge: adversarial tests for meta-tag-placement (and xml-inactive-leaf).

Written by the independent Test/Challenge role, not the Builder. Every test
asserts meaning (the IR, or a round trip back to it), never layout.

Tests marked ``xfail(strict=True)`` fail today. Each reason starts with
``PRODUCT DEFECT`` (behaviour the spec or the device evidence already rules
on) or ``TEST IDEA`` (the expected value waits on an owner decision or a
device artefact). Strict means a fix flips them to XPASS and fails the run,
so they are promoted, not forgotten.

Report: openspec/changes/meta-tag-placement/test-challenge.md.
"""

from __future__ import annotations

import json

import pytest

from junoscfg import Format, convert_config, convert_config_result


def _ir(text: str, fmt: Format) -> dict:
    return json.loads(convert_config(text, from_format=fmt, to_format=Format.JSON))["configuration"]


def _nest(path: list[str], body: str) -> str:
    """Wrap *body* in the curly blocks *path* opens, four spaces a level."""
    text = body
    for depth, opener in reversed(list(enumerate(path))):
        pad = "    " * depth
        text = f"{pad}{opener} {{\n{text}{pad}}}\n"
    return text


# ── Device layout: a list whose entries have no children ─────────────
#
# The device prints such a list as a block of entry names
# (`source-prefix-list { PL1; PL2; }`; the 23.2R2 re-export in
# private_test_data/anon/ uses this layout throughout). A tag on one entry
# leads that entry's line inside the block. Change A reads every case below
# correctly; change B raises "a tag inside a key or value".

BLOCK_LIST_ENTRIES = {
    "firewall source-prefix-list": (
        ["firewall", "family inet", "filter FILTER-V4", "term T1", "from", "source-prefix-list"],
        "PL1",
        "set firewall family inet filter FILTER-V4 term T1 from source-prefix-list PL1\n"
        "set firewall family inet filter FILTER-V4 term T1 from source-prefix-list PL2\n"
        "deactivate firewall family inet filter FILTER-V4 term T1 from source-prefix-list PL1\n",
    ),
    "firewall source-address": (
        ["firewall", "family inet", "filter FILTER-V4", "term T1", "from", "source-address"],
        "198.51.100.0/24",
        "set firewall family inet filter FILTER-V4 term T1 from source-address 198.51.100.0/24\n"
        "set firewall family inet filter FILTER-V4 term T1 from source-address 192.168.0.0/16\n"
        "deactivate firewall family inet filter FILTER-V4 term T1 from "
        "source-address 198.51.100.0/24\n",
    ),
    "system name-server": (
        ["system", "name-server"],
        "192.168.0.1",
        "set system name-server 192.168.0.1\n"
        "set system name-server 192.168.0.2\n"
        "deactivate system name-server 192.168.0.1\n",
    ),
    "snmp community clients": (
        ["snmp", "community public", "clients"],
        "10.0.0.0/8",
        "set snmp community public clients 10.0.0.0/8\n"
        "set snmp community public clients 192.168.0.0/16\n"
        "deactivate snmp community public clients 10.0.0.0/8\n",
    ),
}


def _block_list_curly(path: list[str], tagged: str, other: str) -> str:
    pad = "    " * len(path)
    return _nest(path, f"{pad}inactive: {tagged};\n{pad}{other};\n")


@pytest.mark.parametrize("shape", list(BLOCK_LIST_ENTRIES))
def test_a_tag_on_an_entry_inside_its_list_block(shape: str) -> None:
    path, tagged, set_text = BLOCK_LIST_ENTRIES[shape]
    other = set_text.splitlines()[1].rsplit(" ", 1)[1]
    assert _ir(_block_list_curly(path, tagged, other), Format.STRUCTURED) == _ir(
        set_text, Format.SET
    )


def test_control_a_transparent_list_entry_inside_its_block() -> None:
    """`prefix-list PL1 { inactive: 198.51.100.0/24; }` reads; the defect above is narrower."""
    curly = _nest(
        ["policy-options", "prefix-list PL1"],
        "        inactive: 198.51.100.0/24;\n        192.168.0.0/16;\n",
    )
    assert _ir(curly, Format.STRUCTURED) == _ir(
        "set policy-options prefix-list PL1 198.51.100.0/24\n"
        "set policy-options prefix-list PL1 192.168.0.0/16\n"
        "deactivate policy-options prefix-list PL1 198.51.100.0/24\n",
        Format.SET,
    )


# ── Leaf-lists: a tag on the whole leaf-list ─────────────────────────
#
# Device (deactivate6.txt, 23.2R2-S7.5): after `deactivate policy-options
# community C1 members` the curly display is `inactive: members [ … ];`, set
# writes one `deactivate … members`, XML tags every value, JSON one
# `@members`. Change A builds that IR from XML; structured output drops it.

LEAF_LISTS = {
    "community members, inactive": (
        "set policy-options community C1 members 64496:1\n"
        "set policy-options community C1 members 64496:2\n"
        "deactivate policy-options community C1 members\n"
    ),
    "community members, protect": (
        "set policy-options community C1 members 64496:1\n"
        "set policy-options community C1 members 64496:2\n"
        "protect policy-options community C1 members\n"
    ),
    "static route next-hop": (
        "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
        "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.2\n"
        "deactivate routing-options static route 0.0.0.0/0 next-hop\n"
    ),
    "ethernet-switching vlan members": (
        "set interfaces xe-0/0/0 unit 0 family ethernet-switching vlan members V10\n"
        "set interfaces xe-0/0/0 unit 0 family ethernet-switching vlan members V20\n"
        "deactivate interfaces xe-0/0/0 unit 0 family ethernet-switching vlan members\n"
    ),
}


@pytest.mark.parametrize("shape", list(LEAF_LISTS))
def test_a_tagged_leaf_list_survives_structured_output(shape: str) -> None:
    before = _ir(LEAF_LISTS[shape], Format.SET)
    curly = convert_config(LEAF_LISTS[shape], from_format=Format.SET, to_format=Format.STRUCTURED)
    assert _ir(curly, Format.STRUCTURED) == before


def test_an_inactive_leaf_list_from_xml_survives_structured_output() -> None:
    xml = (
        "<configuration><policy-options><community><name>C1</name>"
        '<members inactive="inactive">64496:1</members>'
        '<members inactive="inactive">64496:2</members>'
        "</community></policy-options></configuration>"
    )
    curly = convert_config(xml, from_format=Format.XML, to_format=Format.STRUCTURED)
    assert _ir(curly, Format.STRUCTURED) == _ir(xml, Format.XML)


def test_the_device_curly_of_an_inactive_leaf_list_reads() -> None:
    """`inactive: members [ … ];`, as deactivate6.txt shows it, reads as set input does."""
    curly = _nest(
        ["policy-options", "community C1"], "        inactive: members [ 64496:1 64496:2 ];\n"
    )
    assert _ir(curly, Format.STRUCTURED) == _ir(
        LEAF_LISTS["community members, inactive"], Format.SET
    )


# ── family: the refusal on every input ───────────────────────────────


def test_a_tag_on_a_family_block_is_reported_from_structured_input() -> None:
    curly = _nest(
        ["interfaces", "xe-0/0/0", "unit 0"],
        "            inactive: family {\n                inet {\n"
        "                    address 10.0.0.1/24;\n                }\n"
        "                inet6;\n            }\n",
    )
    result = convert_config_result(curly, from_format=Format.STRUCTURED, to_format=Format.SET)
    unplaced = [d for d in result.diagnostics if "family" in d.render() and "placed" in d.render()]
    assert len(unplaced) == 1


def test_set_output_repeats_a_sibling_family_tag_from_json() -> None:
    doc = {
        "configuration": {
            "interfaces": {
                "interface": [
                    {
                        "name": "xe-0/0/0",
                        "unit": [
                            {
                                "name": "0",
                                "family": {"inet": {"address": [{"name": "10.0.0.1/24"}]}},
                                "@family": {"inactive": True},
                            }
                        ],
                    }
                ]
            }
        }
    }
    out = convert_config(json.dumps(doc), from_format=Format.JSON, to_format=Format.SET)
    assert "deactivate interfaces xe-0/0/0 unit 0 family" in out.splitlines()


# ── Widening: a tag must not grow to cover active configuration ──────


def test_a_tag_on_apply_macro_data_does_not_tag_the_macro() -> None:
    curly = _nest(["system", "apply-macro M1"], "        k1 v1;\n        inactive: k2 v2;\n")
    macro = _ir(curly, Format.STRUCTURED)["system"]["apply-macro"][0]
    assert "@" not in macro


def test_a_per_value_tag_in_curly_is_refused_as_in_xml() -> None:
    curly = _nest(
        ["policy-options", "community C1"],
        "        members 64496:1;\n        inactive: members 64496:2;\n",
    )
    with pytest.raises(ValueError, match="members"):
        _ir(curly, Format.STRUCTURED)


# ── Shapes that hold today (regression guards) ───────────────────────

ROUND_TRIPS = {
    "protect and inactive on one route": (
        "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
        "protect routing-options static route 0.0.0.0/0\n"
        "deactivate routing-options static route 0.0.0.0/0\n"
    ),
    "route and its next-hop both inactive": (
        "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
        "deactivate routing-options static route 0.0.0.0/0\n"
        "deactivate routing-options static route 0.0.0.0/0 next-hop\n"
    ),
    "route-filter entry and its action inactive": (
        "set policy-options policy-statement P1 term T1 from "
        "route-filter 198.51.100.0/24 exact accept\n"
        "deactivate policy-options policy-statement P1 term T1 from "
        "route-filter 198.51.100.0/24 exact accept\n"
        "deactivate policy-options policy-statement P1 term T1 from "
        "route-filter 198.51.100.0/24 exact\n"
    ),
    "family inet with one terminal child, child inactive": (
        "set interfaces xe-0/0/0 unit 0 family inet dhcp\n"
        "deactivate interfaces xe-0/0/0 unit 0 family inet dhcp\n"
    ),
    "two families, one protected, one inactive": (
        "set interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
        "set interfaces xe-0/0/0 unit 0 family inet6 address 2001:db8::1/64\n"
        "protect interfaces xe-0/0/0 unit 0 family inet\n"
        "deactivate interfaces xe-0/0/0 unit 0 family inet6\n"
    ),
    "then holding one inactive child, then inactive too": (
        "set policy-options policy-statement P1 term T1 then accept\n"
        "deactivate policy-options policy-statement P1 term T1 then\n"
        "deactivate policy-options policy-statement P1 term T1 then accept\n"
    ),
    "group entry inactive": (
        "set groups G_LOC system host-name router1\ndeactivate groups G_LOC\n"
    ),
    "firewall filter term from inactive": (
        "set firewall family inet filter FILTER-V4 term T1 from protocol tcp\n"
        "set firewall family inet filter FILTER-V4 term T1 then accept\n"
        "deactivate firewall family inet filter FILTER-V4 term T1 from\n"
    ),
}


@pytest.mark.parametrize("shape", list(ROUND_TRIPS))
def test_more_round_trips_keep_the_ir(shape: str) -> None:
    before = _ir(ROUND_TRIPS[shape], Format.SET)
    curly = convert_config(ROUND_TRIPS[shape], from_format=Format.SET, to_format=Format.STRUCTURED)
    assert _ir(curly, Format.STRUCTURED) == before
    again = convert_config(curly, from_format=Format.STRUCTURED, to_format=Format.SET)
    assert _ir(again, Format.SET) == before


def test_stacked_curly_tags_mark_one_entry_in_either_order() -> None:
    def route(tags: str) -> dict:
        curly = _nest(
            ["routing-options", "static"], f"        {tags} route 0.0.0.0/0 next-hop 10.0.0.1;\n"
        )
        return _ir(curly, Format.STRUCTURED)["routing-options"]["static"]["route"][0]

    expected = {"inactive": True, "protect": "protect"}
    assert route("protect: inactive:")["@"] == route("inactive: protect:")["@"] == expected
    assert "@next-hop" not in route("protect: inactive:")


def test_the_device_protected_family_with_an_inactive_address_reaches_one_ir() -> None:
    """deactivate6.txt: `protect: family inet { inactive: address …; }`, `<inet protect>`."""
    irs = {
        Format.XML: (
            "<configuration><interfaces><interface><name>xe-0/0/0</name><unit><name>0</name>"
            '<family><inet protect="protect"><address inactive="inactive">'
            "<name>10.0.0.1/24</name></address></inet></family>"
            "</unit></interface></interfaces></configuration>"
        ),
        Format.SET: (
            "set interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
            "deactivate interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
            "protect interfaces xe-0/0/0 unit 0 family inet\n"
        ),
        Format.STRUCTURED: _nest(
            ["interfaces", "xe-0/0/0", "unit 0"],
            "            protect: family inet {\n"
            "                inactive: address 10.0.0.1/24;\n            }\n",
        ),
    }
    seen = {fmt: _ir(text, fmt) for fmt, text in irs.items()}
    assert seen[Format.XML] == seen[Format.SET] == seen[Format.STRUCTURED]


def test_a_quoted_value_that_reads_like_a_tag_is_a_value() -> None:
    curly = _nest(["interfaces", "xe-0/0/0"], '        description "inactive: route 10.0.0.0/8";\n')
    interface = _ir(curly, Format.STRUCTURED)["interfaces"]["interface"][0]
    assert interface == {"name": "xe-0/0/0", "description": "inactive: route 10.0.0.0/8"}


def test_an_xml_leaf_with_protect_and_inactive_keeps_both() -> None:
    xml = (
        "<configuration><system>"
        '<host-name protect="protect" inactive="inactive">router1</host-name>'
        "</system></configuration>"
    )
    assert _ir(xml, Format.XML) == _ir(
        "set system host-name router1\ndeactivate system host-name\nprotect system host-name\n",
        Format.SET,
    )
