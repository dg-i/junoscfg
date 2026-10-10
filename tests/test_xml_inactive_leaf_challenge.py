"""Test/Challenge: adversarial tests for xml-inactive-leaf.

Written by the independent Test/Challenge role, not the Builder. Every test
asserts meaning (the IR, or set output), never layout.

Tests marked ``xfail(strict=True)`` fail today. Each reason starts with
``PRODUCT DEFECT`` (behaviour the spec, the one-IR rule or the device
evidence already rules on) or ``TEST IDEA`` (the expected value waits on an
owner decision or a device artefact). Strict means a fix flips them to XPASS
and fails the run, so they are promoted, not forgotten.

Report: openspec/changes/xml-inactive-leaf/test-challenge.md.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from junoscfg import Format, convert_config, convert_config_result
from junoscfg.cli import main


def _ir(text: str, fmt: Format) -> dict:
    return json.loads(convert_config(text, from_format=fmt, to_format=Format.JSON))["configuration"]


def _xml(body: str) -> str:
    return f"<configuration>{body}</configuration>"


# ── An empty tagged element that is a container, not a presence flag ──
#
# Change A reads every childless element as a leaf. For a presence flag that
# is the IR set input gives (`[null]` + `@no-redirects`); for a container
# with nothing in it, set and structured input give `{"@": {...}}` and so
# did XML input before this change.


@pytest.mark.parametrize(
    ("xml_body", "set_text", "path"),
    [
        (
            '<protocols><lldp inactive="inactive"/></protocols>',
            "set protocols lldp\ndeactivate protocols lldp\n",
            ("protocols",),
        ),
        (
            '<system><services inactive="inactive"/></system>',
            "set system services\ndeactivate system services\n",
            ("system",),
        ),
    ],
    ids=["protocols lldp", "system services"],
)
def test_an_empty_inactive_container_matches_set_input(
    xml_body: str, set_text: str, path: tuple[str, ...]
) -> None:
    from_xml, from_set = _ir(_xml(xml_body), Format.XML), _ir(set_text, Format.SET)
    for key in path:
        from_xml, from_set = from_xml[key], from_set[key]
    assert from_xml == from_set


def test_an_empty_inactive_container_keeps_its_meaning_in_set_output() -> None:
    """Guard: whatever the IR, the set lines are the device's."""
    out = convert_config(
        _xml('<protocols><lldp inactive="inactive"/></protocols>'),
        from_format=Format.XML,
        to_format=Format.SET,
    )
    assert out.splitlines() == ["set protocols lldp", "deactivate protocols lldp"]


# ── Whole inactive leaf-list through every writer ────────────────────

LEAF_LIST_XML = _xml(
    "<policy-options><community><name>C1</name>"
    '<members inactive="inactive">64496:1</members>'
    '<members inactive="inactive">64496:2</members>'
    "</community></policy-options>"
)


def test_an_inactive_leaf_list_from_xml_writes_the_device_set_lines() -> None:
    """deactivate6.txt: one `deactivate … members` after both values."""
    out = convert_config(LEAF_LIST_XML, from_format=Format.XML, to_format=Format.SET)
    assert out.splitlines() == [
        "set policy-options community C1 members 64496:1",
        "set policy-options community C1 members 64496:2",
        "deactivate policy-options community C1 members",
    ]


@pytest.mark.xfail(
    strict=True,
    reason="PRODUCT DEFECT (writer, pre-existing, now reachable from XML): structured "
    "output writes `members [ … ];` without `inactive:` and without a diagnostic; the device "
    "shows `inactive: members [ … ];` (deactivate6.txt). Owned by the curly writer (change B)",
)
def test_an_inactive_leaf_list_from_xml_survives_structured_output() -> None:
    curly = convert_config(LEAF_LIST_XML, from_format=Format.XML, to_format=Format.STRUCTURED)
    assert _ir(curly, Format.STRUCTURED) == _ir(LEAF_LIST_XML, Format.XML)


def test_a_one_value_inactive_leaf_list_matches_set_and_json() -> None:
    xml = _xml(
        "<policy-options><community><name>C1</name>"
        '<members inactive="inactive">64496:1</members></community></policy-options>'
    )
    set_text = (
        "set policy-options community C1 members 64496:1\n"
        "deactivate policy-options community C1 members\n"
    )
    device_json = json.dumps(
        {
            "configuration": {
                "policy-options": {
                    "community": [
                        {"name": "C1", "members": ["64496:1"], "@members": {"inactive": True}}
                    ]
                }
            }
        }
    )
    assert _ir(xml, Format.XML) == _ir(set_text, Format.SET) == _ir(device_json, Format.JSON)


# ── Attribute spellings and wrappers ─────────────────────────────────


def test_a_namespaced_inactive_attribute_marks_the_leaf() -> None:
    xml = (
        '<configuration xmlns:junos="http://xml.juniper.net/junos/23.2R2/junos">'
        '<system><host-name junos:inactive="inactive">router1</host-name></system>'
        "</configuration>"
    )
    assert _ir(xml, Format.XML)["system"] == {
        "host-name": "router1",
        "@host-name": {"inactive": True},
    }


def test_an_inactive_leaf_inside_undocumented_marks_the_leaf() -> None:
    xml = _xml(
        '<system><undocumented><host-name inactive="inactive">router1</host-name>'
        "</undocumented></system>"
    )
    assert _ir(xml, Format.XML)["system"] == {
        "host-name": "router1",
        "@host-name": {"inactive": True},
    }


# ── The device's own JSON (number values) ────────────────────────────


def test_device_json_with_a_number_value_writes_the_same_set_lines_as_xml() -> None:
    """deactivate6.txt writes `"vlan-id" : 751` (a number); the spec fixture uses a string."""
    device_json = json.dumps(
        {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "xe-0/0/0",
                            "unit": [
                                {"name": "751", "vlan-id": 751, "@vlan-id": {"inactive": True}}
                            ],
                        }
                    ]
                }
            }
        }
    )
    xml = _xml(
        "<interfaces><interface><name>xe-0/0/0</name><unit><name>751</name>"
        '<vlan-id inactive="inactive">751</vlan-id></unit></interface></interfaces>'
    )
    assert convert_config(device_json, from_format=Format.JSON, to_format=Format.SET) == (
        convert_config(xml, from_format=Format.XML, to_format=Format.SET)
    )


# ── The refusal at every door ────────────────────────────────────────

PARTLY_TAGGED = _xml(
    "<policy-options><community><name>C1</name><members>64496:1</members>"
    '<members inactive="inactive">64496:2</members></community></policy-options>'
)


def test_a_partly_inactive_leaf_list_is_refused_by_convert_config_result() -> None:
    with pytest.raises(ValueError, match="members"):
        convert_config_result(PARTLY_TAGGED, from_format=Format.XML, to_format=Format.SET)


def test_a_partly_inactive_leaf_list_exits_two_on_the_cli() -> None:
    result = CliRunner().invoke(main, ["convert", "-i", "xml", "-e", "set"], input=PARTLY_TAGGED)
    assert result.exit_code == 2
    assert "members" in result.output
