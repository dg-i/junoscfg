"""Where a Junos meta tag lands, read and written.

A tag (`inactive:`, `protect:`, `replace:`, `delete:`) marks the node its
statement starts: a list entry, which ends after its key; a leaf, never its
value; a container; and for an unkeyed `homogeneous` container such as
`family`, which the device never tags, the child after it. Device evidence
(23.2R2-S7.5): `inactive: route ::/0 apply-groups [ … ];` is `<route
inactive="inactive">`, `inactive: family inet {` is `<inet inactive=…>`,
`protect: route 0.0.0.0/0 next-hop 10.0.0.1;` is `<route protect=…>`, and
`deactivate … family` and `protect … family` are rejected. Layout is free
(ARCHITECTURE.md section 1); what is asserted here is meaning.
Spec: openspec/changes/meta-tag-placement/specs/conversion/meta-tags/spec.md.
"""

from __future__ import annotations

import json

import pytest

from junoscfg import Format, convert_config, convert_config_result

# The IR spelling of each tag: what `deactivate`, `protect` and the
# `replace:` and `delete:` operations write.
TAGS = {
    "inactive": {"inactive": True},
    "protect": {"protect": "protect"},
    "replace": {"operation": "replace"},
    "delete": {"operation": "delete"},
}


def _ir(text: str, fmt: Format) -> dict:
    return json.loads(convert_config(text, from_format=fmt, to_format=Format.JSON))["configuration"]


def _static_route(curly_statement: str) -> dict:
    ir = _ir(
        f"routing-options {{\n    static {{\n        {curly_statement}\n    }}\n}}\n",
        Format.STRUCTURED,
    )
    return ir["routing-options"]["static"]["route"][0]


class TestACurlyTagMarksTheStatementStart:
    @pytest.mark.parametrize("tag", list(TAGS))
    @pytest.mark.parametrize(
        ("content", "child"),
        [("apply-groups [ G_LOC G_DEF ]", "apply-groups"), ("next-hop 10.0.0.1", "next-hop")],
    )
    def test_every_tag_on_a_one_line_entry(self, tag: str, content: str, child: str) -> None:
        route = _static_route(f"{tag}: route 0.0.0.0/0 {content};")
        assert route["@"] == TAGS[tag]
        assert f"@{child}" not in route
        assert child in route

    def test_a_transparent_list_entry(self) -> None:
        ir = _ir("interfaces {\n    inactive: xe-0/0/0 description uplink;\n}\n", Format.STRUCTURED)
        interface = ir["interfaces"]["interface"][0]
        assert interface["@"] == {"inactive": True}
        assert interface["description"] == "uplink"
        assert "@description" not in interface

    def test_an_entry_keyed_by_two_fields(self) -> None:
        ir = _ir(
            "policy-options {\n    policy-statement P1 {\n        term T1 {\n            from {\n"
            "                inactive: route-filter 198.51.100.0/24 exact accept;\n"
            "            }\n        }\n    }\n}\n",
            Format.STRUCTURED,
        )
        entry = ir["policy-options"]["policy-statement"][0]["term"][0]["from"]["route-filter"][0]
        assert entry["@"] == {"inactive": True}
        assert entry["address"] == "198.51.100.0/24"
        assert "exact" in entry and "accept" in entry
        assert not any(key.startswith("@") and key != "@" for key in entry)

    def test_set_input_still_marks_the_last_node(self) -> None:
        ir = _ir(
            "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
            "deactivate routing-options static route 0.0.0.0/0 next-hop\n",
            Format.SET,
        )
        route = ir["routing-options"]["static"]["route"][0]
        assert route["@next-hop"] == {"inactive": True}
        assert "@" not in route


# Each tagged shape as set input; the round trips start from here.
SHAPES = {
    "one-line route, apply-groups": (
        "set routing-options rib inet6.0 bgp-static route ::/0 apply-groups G_LOC\n"
        "set routing-options rib inet6.0 bgp-static route ::/0 apply-groups G_DEF\n"
        "deactivate routing-options rib inet6.0 bgp-static route ::/0\n"
    ),
    "protected route": (
        "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
        "protect routing-options static route 0.0.0.0/0\n"
    ),
    "inactive next-hop": (
        "set routing-options static route 0.0.0.0/0 next-hop 10.0.0.1\n"
        "deactivate routing-options static route 0.0.0.0/0 next-hop\n"
    ),
    "inactive family inet": (
        "set interfaces xe-0/0/0 unit 751 family inet filter input FILTER-V4\n"
        "set interfaces xe-0/0/0 unit 751 family inet address 198.51.100.1/24\n"
        "deactivate interfaces xe-0/0/0 unit 751 family inet\n"
    ),
    "inactive address under family": (
        "set interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
        "deactivate interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
        "protect interfaces xe-0/0/0 unit 0 family inet\n"
    ),
    "inactive leaf and unit": (
        "set interfaces xe-0/0/0 unit 751 vlan-id 751\n"
        "deactivate interfaces xe-0/0/0 unit 751 vlan-id\n"
        "deactivate interfaces xe-0/0/0 unit 751\n"
    ),
    "inactive route-filter entry": (
        "set policy-options policy-statement P1 term T1 from "
        "route-filter 198.51.100.0/24 exact accept\n"
        "deactivate policy-options policy-statement P1 term T1 from "
        "route-filter 198.51.100.0/24 exact\n"
    ),
    "inactive accept under then": (
        "set policy-options policy-statement P1 term T1 then accept\n"
        "deactivate policy-options policy-statement P1 term T1 then accept\n"
    ),
}


class TestStructuredOutputPutsATagFirst:
    def test_an_inactive_family_inet(self) -> None:
        curly = convert_config(
            SHAPES["inactive family inet"], from_format=Format.SET, to_format=Format.STRUCTURED
        )
        assert "inactive: family inet {" in curly
        assert "family inactive:" not in curly

    def test_a_tagged_child_is_not_joined(self) -> None:
        curly = convert_config(
            SHAPES["inactive accept under then"],
            from_format=Format.SET,
            to_format=Format.STRUCTURED,
        )
        lines = [line.strip() for line in curly.splitlines()]
        assert "then {" in lines
        assert "inactive: accept;" in lines
        assert not any(" inactive: " in line or " protect: " in line for line in lines)

    @pytest.mark.parametrize("shape", list(SHAPES))
    def test_round_trips_keep_the_ir(self, shape: str) -> None:
        before = _ir(SHAPES[shape], Format.SET)
        curly = convert_config(SHAPES[shape], from_format=Format.SET, to_format=Format.STRUCTURED)
        assert _ir(curly, Format.STRUCTURED) == before
        again = convert_config(curly, from_format=Format.STRUCTURED, to_format=Format.SET)
        assert _ir(again, Format.SET) == before
        assert (
            _ir(
                convert_config(again, from_format=Format.SET, to_format=Format.STRUCTURED),
                Format.STRUCTURED,
            )
            == before
        )


FAMILY_TAGGED = {
    Format.SET: (
        "set interfaces xe-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
        "deactivate interfaces xe-0/0/0 unit 0 family\n"
    ),
    Format.XML: (
        "<configuration><interfaces><interface><name>xe-0/0/0</name><unit><name>0</name>"
        '<family inactive="inactive"><inet><address><name>10.0.0.1/24</name></address></inet>'
        "</family></unit></interface></interfaces></configuration>"
    ),
    Format.JSON: json.dumps(
        {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "xe-0/0/0",
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {
                                        "@": {"inactive": True},
                                        "inet": {"address": [{"name": "10.0.0.1/24"}]},
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        }
    ),
    Format.YAML: (
        "configuration:\n  interfaces:\n    interface:\n    - name: xe-0/0/0\n      unit:\n"
        "      - name: '0'\n        family:\n          '@':\n            inactive: true\n"
        "          inet:\n            address:\n            - name: 10.0.0.1/24\n"
    ),
}


class TestATagOnFamilyIsReported:
    @pytest.mark.parametrize("fmt", list(FAMILY_TAGGED), ids=lambda f: f.value)
    def test_every_input_reports_it(self, fmt: Format) -> None:
        result = convert_config_result(FAMILY_TAGGED[fmt], from_format=fmt, to_format=Format.SET)
        unplaced = [
            d for d in result.diagnostics if "family" in d.render() and "placed" in d.render()
        ]
        assert len(unplaced) == 1

    def test_set_output_repeats_it(self) -> None:
        out = convert_config(
            FAMILY_TAGGED[Format.SET], from_format=Format.SET, to_format=Format.SET
        )
        assert "deactivate interfaces xe-0/0/0 unit 0 family" in out.splitlines()

    def test_structured_output_drops_it_with_a_note(self) -> None:
        result = convert_config_result(
            FAMILY_TAGGED[Format.SET], from_format=Format.SET, to_format=Format.STRUCTURED
        )
        assert "inactive:" not in result.output
        assert "family inet {" in result.output
        notes = [d for d in result.diagnostics if d.severity == "note" and "family" in d.message]
        assert len(notes) == 1
