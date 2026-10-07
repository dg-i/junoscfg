"""Tests for ArtifactBuilder pipeline."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from junoscfg.display import find_artifact, read_artifact_text
from junoscfg.validate.artifact_builder import (
    _BOOL_FLAG_KEYS,
    _VALUE_FLAG_KEYS,
    ArtifactBuilder,
    read_structure_tree,
    write_structure_tree,
)
from junoscfg.validate.grammar_generator import generate_lark_grammar
from junoscfg.validate.schema_node import Combinator, SchemaNode

SAMPLE_XSD = """\
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:junos="http://xml.juniper.net/junos/21.4R0/junos"
            elementFormDefault="qualified">
  <xsd:element name="configuration">
    <xsd:complexType>
      <xsd:sequence>
        <xsd:choice minOccurs="0" maxOccurs="unbounded">
          <xsd:element name="system" minOccurs="0">
            <xsd:complexType>
              <xsd:sequence>
                <xsd:choice minOccurs="0" maxOccurs="unbounded">
                  <xsd:element name="host-name" type="xsd:string" minOccurs="0"/>
                  <xsd:element name="services" minOccurs="0">
                    <xsd:complexType>
                      <xsd:sequence>
                        <xsd:choice minOccurs="0" maxOccurs="unbounded">
                          <xsd:element name="ssh" minOccurs="0">
                            <xsd:complexType/>
                          </xsd:element>
                        </xsd:choice>
                      </xsd:sequence>
                    </xsd:complexType>
                  </xsd:element>
                </xsd:choice>
              </xsd:sequence>
            </xsd:complexType>
          </xsd:element>
        </xsd:choice>
      </xsd:sequence>
    </xsd:complexType>
  </xsd:element>
</xsd:schema>"""

SAMPLE_NETCONF = f"""\
<rpc-reply>
{SAMPLE_XSD}
</rpc-reply>
"""


class TestArtifactBuilder:
    def test_build_from_xsd_creates_all_artifacts(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)

            assert "json-schema" in artifacts
            assert "yaml-schema" in artifacts
            assert "lark-grammar" in artifacts
            assert "metadata" in artifacts

            for path in artifacts.values():
                assert Path(path).exists()

    def test_json_schema_is_valid_json(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)
            schema = json.loads(read_artifact_text(artifacts["json-schema"]))
            assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
            assert "configuration" in schema["properties"]

    def test_yaml_schema_has_pattern_properties(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)
            schema = json.loads(read_artifact_text(artifacts["yaml-schema"]))
            config = schema["properties"]["configuration"]
            assert "patternProperties" in config

    def test_lark_grammar_has_start_rule(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)
            grammar = read_artifact_text(artifacts["lark-grammar"])
            assert "start:" in grammar
            assert "SET" in grammar

    def test_metadata_has_stats(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build_from_xsd(SAMPLE_XSD, tmpdir)
            meta = json.loads(read_artifact_text(artifacts["metadata"]))
            assert "junos_version" in meta
            assert "stats" in meta
            assert meta["stats"]["total_nodes"] > 0

    def test_build_from_netconf_dump(self):
        builder = ArtifactBuilder()
        # Write NETCONF dump to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_NETCONF)
            netconf_path = f.name
        with tempfile.TemporaryDirectory() as tmpdir:
            artifacts = builder.build(netconf_path, tmpdir)
            assert len(artifacts) == 5
            for path in artifacts.values():
                assert Path(path).exists()

    def test_output_dir_created_if_missing(self):
        builder = ArtifactBuilder()
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "subdir" / "deep"
            artifacts = builder.build_from_xsd(SAMPLE_XSD, new_dir)
            assert new_dir.exists()
            assert len(artifacts) == 5


# One payload per key of `_VALUE_FLAG_KEYS`, so the round-trip test can build
# a node for each. `test_the_value_flag_samples_cover_the_table` fails if a key
# arrives without one.
_VALUE_FLAG_SAMPLES = {
    "t": "interface",
    "fe": "k:last",
}


def _rich_tree() -> SchemaNode:
    """A tree touching every field the structure tree format carries."""
    vlan_id = SchemaNode(name="vlan-id", is_leaf=True, enums=["none", "vlan-id"])
    vlan_id.flags.update({"nokeyword", "freeform-nk"})

    unit = SchemaNode(
        name="unit",
        is_list=True,
        children={"vlan-id": vlan_id, "mtu": SchemaNode(name="mtu", is_leaf=True)},
    )
    interface = SchemaNode(name="interface", is_list=True, children={"unit": unit})
    interface.flags.add("nokeyword")
    interfaces = SchemaNode(name="interfaces", children={"interface": interface})
    interfaces.flags.add("transparent:interface")

    name_leaf = SchemaNode(
        name="name",
        is_leaf=True,
        is_mandatory=True,
        pattern="^[a-z]+$",
        type_ref="string-type",
    )
    term = SchemaNode(name="term", is_list=True, children={"name": name_leaf})
    term.flags.update({"oneliner", "positional-key", "flat-entry:k:0"})

    negated = SchemaNode(name="not-this", is_leaf=True, pattern="^bad$", pattern_negated=True)
    extras = SchemaNode(name="extras", children={"not-this": negated, "term": term})
    extras.flags.update({"transparent-list-key", "positional-key-flat", "flat-dict"})

    return SchemaNode(
        name="configuration",
        children={"interfaces": interfaces, "extras": extras},
    )


class TestStructureTreeRoundTrip:
    """`read_structure_tree` is the inverse of `write_structure_tree`.

    A grammar can only be rebuilt from the bundled artifacts if this holds;
    the XSD dump the artifacts came from is not in the repository.
    """

    @staticmethod
    def _round_trip(tree: SchemaNode) -> SchemaNode:
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "tree.json")
            write_structure_tree(tree, path)
            return read_structure_tree(path)

    def test_grammar_is_identical(self) -> None:
        """What this is for: the rebuilt tree generates the same grammar."""
        tree = _rich_tree()
        assert generate_lark_grammar(self._round_trip(tree)) == generate_lark_grammar(tree)

    def test_every_carried_field_survives(self) -> None:
        back = self._round_trip(_rich_tree())

        iface = back.children["interfaces"].children["interface"]
        assert iface.is_list and "nokeyword" in iface.flags
        assert "transparent:interface" in back.children["interfaces"].flags

        vlan = iface.children["unit"].children["vlan-id"]
        assert vlan.is_leaf and vlan.enums == ["none", "vlan-id"]
        assert vlan.flags == {"nokeyword", "freeform-nk"}

        term = back.children["extras"].children["term"]
        assert term.flags == {"oneliner", "positional-key", "flat-entry:k:0"}
        name = term.children["name"]
        assert name.is_mandatory and name.pattern == "^[a-z]+$"
        assert name.type_ref == "string-type"

        negated = back.children["extras"].children["not-this"]
        assert negated.pattern == "^bad$" and negated.pattern_negated

        extras = back.children["extras"]
        assert extras.flags == {"transparent-list-key", "positional-key-flat", "flat-dict"}

    def test_every_flag_the_tables_name_survives(self) -> None:
        """Driven off the tables, so a flag with no writer fails here.

        `test_every_carried_field_survives` walks a fixed sample tree, so a
        flag added to `_BOOL_FLAG_KEYS` and wired into the reader but not the
        writer passed it. That was the live state: the reader was table-driven
        and the writer was a hand-written if/elif chain.
        """
        tree = SchemaNode(name="configuration")
        for key, flag in _BOOL_FLAG_KEYS.items():
            # A named list with children: the shape `o`'s guard requires, so
            # every key is tested on a node that may legitimately carry it.
            node = SchemaNode(
                name=f"bool-{key}",
                is_list=True,
                children={"leaf": SchemaNode(name="leaf", is_leaf=True)},
            )
            node.flags.add(flag)
            tree.children[node.name] = node

        for key, payload in _VALUE_FLAG_SAMPLES.items():
            node = SchemaNode(
                name=f"value-{key}",
                children={"leaf": SchemaNode(name="leaf", is_leaf=True)},
            )
            node.flags.add(_VALUE_FLAG_KEYS[key].prefix + payload)
            tree.children[node.name] = node

        back = self._round_trip(tree)

        for key, flag in _BOOL_FLAG_KEYS.items():
            assert flag in back.children[f"bool-{key}"].flags, f"{key} lost"
        for key, payload in _VALUE_FLAG_SAMPLES.items():
            expected = _VALUE_FLAG_KEYS[key].prefix + payload
            assert expected in back.children[f"value-{key}"].flags, f"{key} lost"

    def test_the_value_flag_samples_cover_the_table(self) -> None:
        """A new value flag with no sample above leaves itself untested."""
        assert set(_VALUE_FLAG_SAMPLES) == set(_VALUE_FLAG_KEYS)

    def test_the_bundled_tree_survives_a_round_trip_exactly(self) -> None:
        """Reader and writer are inverses over the artefact we actually ship.

        13 MB and 428,000 nodes, which is the only sample that covers every
        flag combination the XSD produces. Equality is on the parsed data, not
        the bytes: the writer emits its keys in table order now, where it used
        to iterate a set.
        """
        import junoscfg.validate as validate_pkg

        src = find_artifact(
            Path(validate_pkg.__file__).parent / "data", "junos-structure-tree.json"
        )
        original = json.loads(read_artifact_text(src))
        with tempfile.TemporaryDirectory() as d:
            out = str(Path(d) / "tree.json")
            write_structure_tree(read_structure_tree(src), out)
            rebuilt = json.loads(Path(out).read_text(encoding="utf-8"))
        assert rebuilt == original

    def test_the_three_fields_the_format_drops(self) -> None:
        """Pinned so nobody reads this tree as a faithful copy.

        `_serialize_node` writes none of these, so the loader cannot restore
        them. The docstring of `read_structure_tree` says the same.
        """
        tree = SchemaNode(name="configuration")
        tree.children["seq"] = SchemaNode(name="seq", combinator=Combinator.SEQUENCE)
        tree.children["keyed"] = SchemaNode(name="keyed", is_key=True, is_leaf=True)
        presence_with_children = SchemaNode(name="groups", is_presence=True)
        presence_with_children.children["g"] = SchemaNode(name="g", is_leaf=True)
        tree.children["groups"] = presence_with_children

        back = self._round_trip(tree)

        assert back.children["seq"].combinator is Combinator.CHOICE
        assert back.children["keyed"].is_key is False
        assert back.children["groups"].is_presence is False
