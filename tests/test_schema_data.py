"""Tests that need a real device schema.

A user needs none of this. A developer should sync one or more NETCONF XSD
dumps into ``private_test_data/schemas/`` (gitignored); these then run with
``pytest --schema``, once per dump.

They exist because a fixture this project can author cannot answer questions
about what a device actually emits. The synthetic ``examples/router1.*`` pins
conversion behaviour well and told us nothing about the 85 OpenConfig element
names that stop a real XSD compiling.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.schema


class TestFixesApply:
    """Every registered XSD fix should do something on a real schema.

    Both 23.2R2 and 24.4R0 report 38 of 41 applied, so the same three never
    fire on either release. A fix that never fires is dead code or a matcher
    that stopped matching, and either way the bundled artifacts are missing a
    correction someone thought was needed.
    """

    def test_most_fixes_apply(self, parsed_schema: object) -> None:
        assert parsed_schema.fixes_applied > 0
        assert parsed_schema.fixes_applied <= parsed_schema.fixes_registered

    def test_report_which_fixes_never_fire(self, parsed_schema: object) -> None:
        """Names the unapplied fixes rather than leaving a bare count.

        Not an assertion that all of them apply: three do not, and this records
        which, so the number stops being a mystery and a change to it is
        visible.
        """
        from junoscfg.validate.xsd_extractor import extract_xsd
        from junoscfg.validate.xsd_fixes import ALL_FIXES
        from junoscfg.validate.xsd_parser import parse_xsd

        # a fresh tree: apply_all_fixes has already run on parsed_schema.tree
        tree = parse_xsd(extract_xsd(parsed_schema.path.read_text(errors="replace")))
        unapplied = [fix.id for fix in ALL_FIXES if not fix.apply(tree)]

        assert len(unapplied) == parsed_schema.fixes_registered - parsed_schema.fixes_applied
        # Recorded, not asserted empty. Change this list when a fix is fixed.
        print(f"\n{parsed_schema.version}: fixes that never fire: {unapplied}")


class TestPipelineIntegrity:
    """The generator survives a real schema and produces usable artifacts."""

    def test_structure_is_plausible(self, parsed_schema: object) -> None:
        from junoscfg.validate.artifact_builder import _count_stats

        stats = _count_stats(parsed_schema.tree)
        # A real Junos schema is hundreds of thousands of nodes. A collapse to
        # a few thousand means the parser silently stopped descending.
        assert stats["total_nodes"] > 100_000
        assert stats["leaf_nodes"] > 50_000
        assert stats["enum_values"] > 50_000
        assert stats["container_nodes"] > stats["list_nodes"]

    def test_generated_grammar_compiles(self, parsed_schema: object, tmp_path: Path) -> None:
        """The Lark grammar is generated, not written, so it can be invalid."""
        import lark

        from junoscfg.validate.grammar_generator import write_lark_grammar

        grammar_path = tmp_path / "junos-set.lark"
        write_lark_grammar(parsed_schema.tree, str(grammar_path))
        assert grammar_path.stat().st_size > 100_000

        lark.Lark(grammar_path.read_text(), start="start")

    def test_generated_json_schema_is_valid(self, parsed_schema: object, tmp_path: Path) -> None:
        """A JSON Schema that is not itself valid rejects everything."""
        import jsonschema

        from junoscfg.validate.schema_generator import write_json_schema

        path = tmp_path / "junos-json-schema.json"
        write_json_schema(parsed_schema.tree, str(path), variant="json")
        schema = json.loads(path.read_text())

        jsonschema.Draft202012Validator.check_schema(schema)


class TestRawXsdDoesNotCompile:
    """The limitation that makes ``validate_xml`` unusable, pinned.

    ``junos-validated.xsd`` means a *cleaned* XSD. A raw NETCONF dump is not
    one: lxml rejects element names carrying an OpenConfig prefix, because a
    colon is not valid in an ``xs:NCName``. If Juniper ever stops emitting
    them, or someone writes the cleaning step, this test says so.
    """

    def test_raw_xsd_is_rejected_by_lxml(self, parsed_schema: object, tmp_path: Path) -> None:
        from lxml import etree

        path = tmp_path / "raw.xsd"
        path.write_text(parsed_schema.xsd_text)

        with pytest.raises(etree.XMLSchemaParseError) as caught:
            etree.XMLSchema(etree.parse(str(path)))
        assert "NCName" in str(caught.value)

    def test_the_offending_names_are_namespace_prefixed(self, parsed_schema: object) -> None:
        import re

        bad = re.findall(r'<xsd:element name="([^"]*:[^"]*)"', parsed_schema.xsd_text)
        assert bad, "no prefixed element names: the XSD may now compile"
        assert all(":" in name for name in bad)
        print(f"\n{parsed_schema.version}: {len(bad)} prefixed element names block compilation")


class TestConversionAgainstRealArtifacts:
    """Conversion driven by a real schema rather than the bundled one.

    The schema decides how set commands nest, so a conversion bug can hide
    behind the bundled 24.4 artifacts and appear on another release.
    """

    @pytest.fixture(scope="class")
    def real_artifacts(
        self, parsed_schema: object, tmp_path_factory: pytest.TempPathFactory
    ) -> Path:
        from junoscfg.validate.artifact_builder import ArtifactBuilder

        out = tmp_path_factory.mktemp("real-artifacts")
        ArtifactBuilder().build_from_xsd(parsed_schema.xsd_text, out)
        return out

    def test_roundtrip_against_this_release(
        self, real_artifacts: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """structured -> set -> structured survives on real artifacts."""
        monkeypatch.setenv("JUNOSCFG_ARTIFACTS", str(real_artifacts))

        from junoscfg import Format, convert_config

        source = Path("examples/router1.conf").read_text()
        as_set = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.SET)
        back = convert_config(as_set, from_format=Format.SET, to_format=Format.STRUCTURED)

        assert "host-name router1;" in back
        assert "ge-0/0/0 {" in back
        again = convert_config(back, from_format=Format.STRUCTURED, to_format=Format.SET)
        assert set(again.strip().splitlines()) == set(as_set.strip().splitlines())

    def test_json_and_set_agree_on_real_artifacts(
        self, real_artifacts: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("JUNOSCFG_ARTIFACTS", str(real_artifacts))

        from junoscfg import Format, convert_config

        source = Path("examples/router1.conf").read_text()
        via_json = convert_config(
            convert_config(source, from_format=Format.STRUCTURED, to_format=Format.JSON),
            from_format=Format.JSON,
            to_format=Format.SET,
        )
        direct = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.SET)
        assert via_json == direct
