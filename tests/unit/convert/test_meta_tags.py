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
Specs: openspec/specs/conversion/{curly-meta-tags,tag-acceptance,meta-tags}/.

That a tagged shape reads as one IR from every input and round-trips through
every writer is the shape catalogue (`tests/support/shapes.py`, the meta-tag
rows) under `tests/contract/test_format_matrix.py`. This file keeps where a tag
lands in the IR, how structured output writes it, and what is reported or
refused. It also holds what the meta-tag-placement and xml-inactive-leaf test
challenges (openspec/changes/archive/2026-10-10-*/test-challenge.md) added.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from junoscfg import Format, convert_config, convert_config_result
from junoscfg.cli import main
from tests.support.shapes import BY_NAME

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


def _nest(path: list[str], body: str) -> str:
    """Wrap *body* in the curly blocks *path* opens, four spaces a level."""
    text = body
    for depth, opener in reversed(list(enumerate(path))):
        pad = "    " * depth
        text = f"{pad}{opener} {{\n{text}{pad}}}\n"
    return text


def _set_source(shape: str) -> str:
    return BY_NAME[shape].sources[Format.SET]


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

    def test_stacked_curly_tags_mark_one_entry_in_either_order(self) -> None:
        def route(tags: str) -> dict:
            curly = _nest(
                ["routing-options", "static"],
                f"        {tags} route 0.0.0.0/0 next-hop 10.0.0.1;\n",
            )
            return _ir(curly, Format.STRUCTURED)["routing-options"]["static"]["route"][0]

        expected = {"inactive": True, "protect": "protect"}
        assert route("protect: inactive:")["@"] == route("inactive: protect:")["@"] == expected
        assert "@next-hop" not in route("protect: inactive:")


class TestStructuredOutputPutsATagFirst:
    def test_an_inactive_family_inet(self) -> None:
        curly = convert_config(
            _set_source("an-inactive-family-inet"),
            from_format=Format.SET,
            to_format=Format.STRUCTURED,
        )
        assert "inactive: family inet {" in curly
        assert "family inactive:" not in curly

    def test_a_tagged_child_is_not_joined(self) -> None:
        curly = convert_config(
            _set_source("an-inactive-accept-under-then"),
            from_format=Format.SET,
            to_format=Format.STRUCTURED,
        )
        lines = [line.strip() for line in curly.splitlines()]
        assert "inactive: accept;" in lines
        assert not any(" inactive: " in line or " protect: " in line for line in lines)
        # Meaning, not layout: read back, only `accept` is inactive.
        assert _ir(curly, Format.STRUCTURED) == _ir(
            _set_source("an-inactive-accept-under-then"), Format.SET
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
    Format.STRUCTURED: (
        "interfaces {\n    xe-0/0/0 {\n        unit 0 {\n            inactive: family {\n"
        "                inet {\n                    address 10.0.0.1/24;\n"
        "                }\n            }\n        }\n    }\n}\n"
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

    def test_a_family_block_holding_two_families_is_reported_once(self) -> None:
        curly = _nest(
            ["interfaces", "xe-0/0/0", "unit 0"],
            "            inactive: family {\n                inet {\n"
            "                    address 10.0.0.1/24;\n                }\n"
            "                inet6;\n            }\n",
        )
        result = convert_config_result(curly, from_format=Format.STRUCTURED, to_format=Format.SET)
        unplaced = [
            d for d in result.diagnostics if "family" in d.render() and "placed" in d.render()
        ]
        assert len(unplaced) == 1

    def test_set_output_repeats_a_sibling_family_tag_from_json(self) -> None:
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


class TestOnlyTagsCountAsTags:
    def test_metadata_on_family_is_not_a_tag(self) -> None:
        doc = json.dumps(
            {
                "configuration": {
                    "interfaces": {
                        "interface": [
                            {
                                "name": "xe-0/0/0",
                                "unit": [
                                    {
                                        "name": "0",
                                        "family": {"@": {"junos:group": "G1"}, "inet": {}},
                                    }
                                ],
                            }
                        ]
                    }
                }
            }
        )
        result = convert_config_result(doc, from_format=Format.JSON, to_format=Format.SET)
        assert not [d for d in result.diagnostics if "placed" in d.render()]

    def test_uneven_tags_on_apply_groups_are_refused(self) -> None:
        curly = "system {\n    apply-groups G1;\n    inactive: apply-groups G2;\n}\n"
        with pytest.raises(ValueError, match="apply-groups"):
            _ir(curly, Format.STRUCTURED)

    def test_a_family_tag_written_twice_is_repeated_once(self) -> None:
        doc = json.loads(
            convert_config(
                FAMILY_TAGGED[Format.JSON], from_format=Format.JSON, to_format=Format.JSON
            )
        )
        unit = doc["configuration"]["interfaces"]["interface"][0]["unit"][0]
        unit["@family"] = {"inactive": True}
        out = convert_config(json.dumps(doc), from_format=Format.JSON, to_format=Format.SET)
        assert out.splitlines().count("deactivate interfaces xe-0/0/0 unit 0 family") == 1


class TestATagDoesNotGrowOverActiveConfiguration:
    def test_a_tag_on_apply_macro_data_does_not_tag_the_macro(self) -> None:
        curly = _nest(["system", "apply-macro M1"], "        k1 v1;\n        inactive: k2 v2;\n")
        macro = _ir(curly, Format.STRUCTURED)["system"]["apply-macro"][0]
        assert "@" not in macro


# One value of a leaf-list tagged and its sibling not: no IR holds it (one
# `@members` tags the whole leaf-list), so every input refuses it.
PARTLY_TAGGED_XML = (
    "<configuration><policy-options><community><name>C1</name><members>64496:1</members>"
    '<members inactive="inactive">64496:2</members></community></policy-options>'
    "</configuration>"
)


class TestATagOnOneValueOfALeafListIsRefused:
    def test_a_per_value_tag_in_curly_is_refused_as_in_xml(self) -> None:
        curly = _nest(
            ["policy-options", "community C1"],
            "        members 64496:1;\n        inactive: members 64496:2;\n",
        )
        with pytest.raises(ValueError, match="members"):
            _ir(curly, Format.STRUCTURED)

    def test_a_partly_inactive_leaf_list_is_refused_by_convert_config_result(self) -> None:
        with pytest.raises(ValueError, match="members"):
            convert_config_result(PARTLY_TAGGED_XML, from_format=Format.XML, to_format=Format.SET)

    def test_a_partly_inactive_leaf_list_exits_two_on_the_cli(self) -> None:
        result = CliRunner().invoke(
            main, ["convert", "-i", "xml", "-e", "set"], input=PARTLY_TAGGED_XML
        )
        assert result.exit_code == 2
        assert "members" in result.output


#: One value of a leaf-list tagged, as JSON or YAML input may give it.
PER_VALUE_TAG = json.dumps(
    {
        "configuration": {
            "system": {
                "domain-search": ["a.example", "b.example"],
                "@domain-search": [None, {"inactive": True}],
            }
        }
    }
)
_VALUE_NOTE = "tag(s) on single values of a leaf-list dropped"


class TestAPerValueLeafListTagIsNoted:
    """Junos tags a leaf-list only as a whole: the QFX5120 25.2R2-S1.5 refuses
    `deactivate ... community 64496:2` ("syntax error, expecting ';', [Enter],
    or '|'") and prints `"community": ["64496:1", "64496:2"]` with no per-value
    annotation (probe A2). Set and structured text have no form for such a tag,
    so they write every value and note the tag they drop, where they dropped it
    silently; json, yaml and yaml-new keep it (LEAF-LIST-VALUE-TAGS-001, change
    device-probe-fixes)."""

    @pytest.mark.parametrize(
        "to_format", [Format.SET, Format.STRUCTURED], ids=["set", "structured"]
    )
    @pytest.mark.parametrize("path", [None, "system", "system.domain-search"])
    def test_set_and_structured_note_it(self, to_format: Format, path: str | None) -> None:
        result = convert_config_result(
            PER_VALUE_TAG, from_format=Format.JSON, to_format=to_format, path=path
        )
        assert "a.example" in result.output and "b.example" in result.output
        assert "deactivate" not in result.output and "inactive" not in result.output
        notes = [d.message for d in result.diagnostics if _VALUE_NOTE in d.message]
        assert notes == [f"note: 1 {_VALUE_NOTE}: Junos tags a leaf-list only as a whole"]

    def test_one_note_counts_every_tag_of_every_value(self) -> None:
        """One note for the whole output, counting each tag of each value; a
        comment on a value is no tag (Test/Challenge N7)."""
        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "domain-search": ["a.example", "b.example"],
                        "@domain-search": [{"inactive": True, "protect": "protect"}, None],
                        "authentication-order": ["password", "radius"],
                        "@authentication-order": [{"comment": "/* first */"}, {"inactive": True}],
                    }
                }
            }
        )
        for to_format in (Format.SET, Format.STRUCTURED):
            result = convert_config_result(source, from_format=Format.JSON, to_format=to_format)
            notes = [d.message for d in result.diagnostics if _VALUE_NOTE in d.message]
            assert notes == [f"note: 3 {_VALUE_NOTE}: Junos tags a leaf-list only as a whole"]

    @pytest.mark.parametrize(
        "to_format", [Format.JSON, Format.YAML, Format.YAML_NEW], ids=["json", "yaml", "yaml-new"]
    )
    def test_json_yaml_and_yaml_new_keep_it(self, to_format: Format) -> None:
        result = convert_config_result(PER_VALUE_TAG, from_format=Format.JSON, to_format=to_format)
        assert not [d for d in result.diagnostics if _VALUE_NOTE in d.message]
        written = convert_config(result.output, from_format=to_format, to_format=Format.JSON)
        assert json.loads(written)["configuration"]["system"]["@domain-search"] == [
            None,
            {"inactive": True},
        ]
