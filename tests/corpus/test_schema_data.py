"""Tests that need a real device schema.

A user needs none of this. A developer should sync one or more NETCONF XSD
dumps into ``private_test_data/schemas/`` (gitignored); these then run with
``pytest --schema``, once per dump.

They exist because a fixture this project can author cannot answer questions
about what a device actually emits. The synthetic ``examples/router1.*`` of
the time pinned conversion behaviour well and told us nothing about the 85
OpenConfig element names that stop a real XSD compiling; the example is now a
vMX's own renderings (``examples/junoscfg-oracle.*``).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

# The schema tier tests the build-time pipeline stage by stage on a device
# dump; the named surfaces expose it only composed, as `schema generate`. The
# imports below are exceptions in `tools/check_test_doors.py`.
from junoscfg.display import entry_keys, read_artifact_text
from junoscfg.validate import (
    ALL_FIXES,
    ArtifactBuilder,
    extract_xsd,
    parse_xsd,
    write_json_schema,
    write_lark_grammar,
    write_structure_tree,
)
from tests.support.devices import example, recorded_lines
from tests.support.paths import EXAMPLES
from tests.support.shapes import read_ir

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.schema

_XSD_SEQUENCE = "{http://www.w3.org/2001/XMLSchema}sequence"


def assert_schema_set_parity(left: str, right: str) -> None:
    """Allow only the captured transport-class sibling placement difference.

    Both device captures place independent auto-create/fallback siblings beside
    ordered name entries. Keep all raw bytes, multiplicity and other order;
    the shared reader is only a supplementary check, never the sole oracle.
    """
    from junoscfg import Format

    def sibling_order(text: str) -> list[str]:
        lines = text.splitlines(keepends=True)
        prefix = "set routing-options transport-class "
        positions = [i for i, line in enumerate(lines) if line.startswith(prefix)]
        if not positions:
            return lines
        start, stop = positions[0], positions[-1] + 1
        if positions != list(range(start, stop)):
            return lines
        controls = {prefix + "auto-create\n", prefix + "fallback none\n"}
        block = lines[start:stop]
        return (
            lines[:start]
            + [line for line in block if line in controls]
            + [line for line in block if line not in controls]
            + lines[stop:]
        )

    assert sibling_order(left) == sibling_order(right)
    assert read_ir(left, Format.SET) == read_ir(right, Format.SET)


@pytest.fixture(scope="module")
def real_artifacts(parsed_schema: object, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Every artifact `schema generate` writes for this dump, built once per dump."""
    out = tmp_path_factory.mktemp("real-artifacts")
    ArtifactBuilder().build_from_xsd(parsed_schema.xsd_text, out)
    return out


class TestFixesApply:
    """Every registered XSD fix should do something on a real schema.

    25.2R2 reports 38 of 41 applied and 23.2R2 37 of 41: the same three never
    fire on either, and `ufd-group-transparent` fires only where
    `uplink-failure-detection` exists, which 23.2R2 lacks. A fix that never
    fires on every release is dead code or a matcher
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
        # a fresh tree: apply_all_fixes has already run on parsed_schema.tree
        tree = parse_xsd(extract_xsd(parsed_schema.path.read_text(errors="replace")))
        unapplied = [fix.id for fix in ALL_FIXES if not fix.apply(tree)]

        assert len(unapplied) == parsed_schema.fixes_registered - parsed_schema.fixes_applied
        # Recorded, not asserted empty. Change this list when a fix is fixed.
        print(f"\n{parsed_schema.version}: fixes that never fire: {unapplied}")


class TestPipelineIntegrity:
    """The generator survives a real schema and produces usable artifacts."""

    def test_structure_is_plausible(self, real_artifacts: Path) -> None:
        """Counted by the builder over the fixed tree, as the metadata records it."""
        meta = json.loads(read_artifact_text(real_artifacts / "junos-schema-meta.json.gz"))
        stats = meta["stats"]
        # A real Junos schema is hundreds of thousands of nodes. A collapse to
        # a few thousand means the parser silently stopped descending.
        assert stats["total_nodes"] > 100_000
        assert stats["leaf_nodes"] > 50_000
        assert stats["enum_values"] > 50_000
        assert stats["container_nodes"] > stats["list_nodes"]

    def test_generated_grammar_compiles(self, parsed_schema: object, tmp_path: Path) -> None:
        """The Lark grammar is generated, not written, so it can be invalid."""
        import lark

        grammar_path = tmp_path / "junos-set.lark"
        write_lark_grammar(parsed_schema.tree, str(grammar_path))
        assert grammar_path.stat().st_size > 100_000

        lark.Lark(grammar_path.read_text(), start="start")

    def test_generated_json_schema_is_valid(self, parsed_schema: object, tmp_path: Path) -> None:
        """A JSON Schema that is not itself valid rejects everything."""
        import jsonschema

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
    behind the bundled artifacts and appear on another release.
    """

    def test_roundtrip_against_this_release(
        self, real_artifacts: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """structured -> set -> structured survives on real artifacts.

        The example's curly is the vMX's; the set lines `known-differences.json`
        records for it are junoscfg's known misreadings, which do not read
        back, so the round trip starts from the set output without them.
        """
        monkeypatch.setenv("JUNOSCFG_ARTIFACTS", str(real_artifacts))

        from junoscfg import Format, convert_config

        source = (EXAMPLES / "junoscfg-oracle.conf").read_text(encoding="utf-8")
        skip = recorded_lines(example(), "conf")
        written = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.SET)
        as_set = "".join(f"{line}\n" for line in written.splitlines() if line not in skip)
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

        source = (EXAMPLES / "junoscfg-oracle.conf").read_text(encoding="utf-8")
        via_json = convert_config(
            convert_config(source, from_format=Format.STRUCTURED, to_format=Format.JSON),
            from_format=Format.JSON,
            to_format=Format.SET,
        )
        direct = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.SET)
        assert_schema_set_parity(via_json, direct)


class TestEntryKeysOnTheDump:
    """Every AS-list slot carries both keys, on each release's dump.

    Spec: identifier-key-fields, schema-pipeline/entry-key-fields. 24 slots,
    measured on 25.2R2-S1.5 and 23.2R2-S7.5 before the change (the three
    lists, at the root, in logical systems, in groups and in grouped logical
    systems, with and without a term), when every one of them was a childless
    presence list. A release not pinned here is skipped, not guessed.
    """

    SLOTS = {"25.2": 24, "23.2": 24}

    def test_the_as_list_slots_carry_both_keys(self, parsed_schema: object, tmp_path: Path) -> None:
        train = next((t for t in self.SLOTS if parsed_schema.version.startswith(t)), None)
        if train is None:
            pytest.skip(f"no pinned count for {parsed_schema.version}")
        path = tmp_path / "tree.json"
        write_structure_tree(parsed_schema.tree, str(path))
        tree = json.loads(path.read_text(encoding="utf-8"))

        slots = []
        stack = [tree]
        while stack:
            node = stack.pop()
            for child in (node.get("c") or {}).values():
                if child.get("L") and child.get("tr") == "control-as-list-type":
                    slots.append(child)
                stack.append(child)
        assert len(slots) == self.SLOTS[train]
        for node in slots:
            assert node["k"] == ["list-type", "list-name"]
            assert list(node["c"])[:2] == ["list-type", "list-name"]
            assert "p" not in node
        assert all(entry_keys(node) == ("list-type", "list-name") for node in slots)


class TestIdentifierCounts:
    """The sequences that declare identifiers, as the parser reads them.

    Spec: identifier-key-fields, schema-pipeline/entry-key-fields. Counted
    over every `xsd:sequence` of the dump with the parser's own rule: keyed
    `name` alone, by one other identifier, or by two to four; and the
    sequences keyed by a choice of identifiers. Measured before the change
    (proposal). A release not pinned here is skipped, not guessed.
    """

    COUNTS = {"25.2": (2800, 171, 64, 38), "23.2": (2851, 163, 65)}

    def test_the_counts_are_the_proposals(self, parsed_schema: object) -> None:
        from lxml import etree

        # The parser's own identifier rule, private: the counts are over the
        # dump's sequences, which no tree the parser builds still shows.
        import junoscfg.validate.xsd_parser as xsd_parser

        train = next((t for t in self.COUNTS if parsed_schema.version.startswith(t)), None)
        if train is None:
            pytest.skip(f"no pinned count for {parsed_schema.version}")
        root = etree.fromstring(parsed_schema.xsd_text.encode("utf-8"))
        name_only = one_other = several = choice_keyed = 0
        for seq in root.iter(_XSD_SEQUENCE):
            keys = xsd_parser._key_fields(seq)  # noqa: SLF001
            values = [k for k in keys if isinstance(k, str)]
            choice_keyed += any(isinstance(k, tuple) for k in keys)
            if values == ["name"]:
                name_only += 1
            elif len(values) == 1:
                one_other += 1
            elif values:
                several += 1
        expected = self.COUNTS[train]
        assert (name_only, one_other, several, choice_keyed)[: len(expected)] == expected

    def test_no_name_keyed_list_carries_k(self, parsed_schema: object, tmp_path: Path) -> None:
        path = tmp_path / "tree.json"
        write_structure_tree(parsed_schema.tree, str(path))
        stack = [json.loads(path.read_text(encoding="utf-8"))]
        keyed = 0
        while stack:
            node = stack.pop()
            if "k" in node:
                keyed += 1
                assert node["k"] != ["name"], node
            stack.extend((node.get("c") or {}).values())
        assert keyed > 0
