"""Tests for ArtifactBuilder pipeline."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator
from lark import Lark, UnexpectedInput

from junoscfg.display import entry_key_names, read_artifact_text
from junoscfg.validate import (
    ArtifactBuilder,
    Combinator,
    SchemaNode,
    generate_lark_grammar,
    parse_xsd,
    read_structure_tree,
    write_structure_tree,
)

# The structure tree's flag tables: the one list of what the writer must carry.
# An exception in `tools/check_test_doors.py`; see `test_every_flag_the_tables_name_survives`.
from junoscfg.validate.artifact_builder import _BOOL_FLAG_KEYS, _VALUE_FLAG_KEYS
from tests.support.artifacts import shipped
from tests.support.keyed_entries import KEYED_XSD, artifact_json, build_artifacts, node

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
    # A renamed element's name in XML and JSON (spec schema-pipeline/conversion-hints).
    "x": "end-range",
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
        anonymization_type_ref="ipaddr",
    )
    # Keyed by an identifier and a choice of identifiers (identifier-key-fields:
    # `k` replaced the retired `flat-entry:<key>:<position>` value flag).
    term = SchemaNode(
        name="term", is_list=True, children={"name": name_leaf}, key_fields=("k", ("a", "b"))
    )
    term.flags.update({"oneliner", "positional-key"})

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
        assert term.flags == {"oneliner", "positional-key"}
        assert term.key_fields == ("k", ("a", "b"))
        name = term.children["name"]
        assert name.is_mandatory and name.pattern == "^[a-z]+$"
        assert name.type_ref == "string-type"
        assert name.anonymization_type_ref == "ipaddr"

        negated = back.children["extras"].children["not-this"]
        assert negated.pattern == "^bad$" and negated.pattern_negated

        extras = back.children["extras"]
        assert extras.flags == {"transparent-list-key", "positional-key-flat", "flat-dict"}

    def test_a_oneliner_container_keeps_its_flag(self) -> None:
        """A container the XSD marks `oneliner`, `hold-time` among them, keeps
        `o`: the grammar takes its leaves on one line from it, as the device
        takes `hold-time up 0 down 0` (probe D1, SET-COMPACT-LEAVES-001). A
        flag holds nothing to put on one line and does not keep it."""
        hold_time = SchemaNode(
            name="hold-time",
            children={
                "up": SchemaNode(name="up", is_leaf=True),
                "down": SchemaNode(name="down", is_leaf=True),
            },
        )
        hold_time.flags.add("oneliner")
        flag = SchemaNode(name="now", is_presence=True)
        flag.flags.add("oneliner")
        back = self._round_trip(
            SchemaNode(name="configuration", children={"hold-time": hold_time, "now": flag})
        )
        assert "oneliner" in back.children["hold-time"].flags
        assert "oneliner" not in back.children["now"].flags

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

    def test_the_bundled_tree_survives_a_round_trip_exactly(self, bundled_tree: dict) -> None:
        """Reader and writer are inverses over the artefact we actually ship.

        13 MB and 428,000 nodes, which is the only sample that covers every
        flag combination the XSD produces. Equality is on the parsed data, not
        the bytes: the writer emits its keys in table order now, where it used
        to iterate a set.
        """
        with tempfile.TemporaryDirectory() as d:
            out = str(Path(d) / "tree.json")
            write_structure_tree(read_structure_tree(shipped("junos-structure-tree.json")), out)
            rebuilt = json.loads(Path(out).read_text(encoding="utf-8"))
        assert rebuilt == bundled_tree

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

    # ── Entry keys: the keys and the declared order ─────────────────────
    # Spec: openspec/changes/identifier-key-fields/specs/schema-pipeline/
    # entry-key-fields, "The structure tree carries the keys and the declared
    # order". Driven from an XSD, so the keys reach the tree however the
    # parser holds them.

    @staticmethod
    def _keyed_tree_files(tmp: Path) -> tuple[dict, dict]:
        """The tree the keyed XSD writes, and the tree read back and rewritten."""
        from tests.support.keyed_entries import KEYED_XSD

        first = tmp / "first.json"
        second = tmp / "second.json"
        write_structure_tree(parse_xsd(KEYED_XSD), str(first))
        write_structure_tree(read_structure_tree(first), str(second))
        return (
            json.loads(first.read_text(encoding="utf-8")),
            json.loads(second.read_text(encoding="utf-8")),
        )

    def test_ordered_entry_keys_survive(self, tmp_path: Path) -> None:
        written, rebuilt = self._keyed_tree_files(tmp_path)
        term = ("policy-options", "policy-statement", "term")
        expected = {
            (*term, "from", "as-path-neighbors"): ["list-type", "list-name"],
            (*term, "from", "route-filter"): ["address", ["exact", "orlonger"]],
            (*term, "then", "community"): [["add", "delete"], "community-name"],
            ("system", "ntp", "server"): ["address"],
            ("event-options", "policy", "attributes-match"): [
                "from-event-attribute",
                "condition",
                "to-event-attribute-value",
            ],
        }
        for path, keys in expected.items():
            assert node(written, *path).get("k") == keys, path
            assert node(rebuilt, *path).get("k") == keys, path
        for path in (term[:2], term, ("policy-options", "community")):
            assert "k" not in node(written, *path), f"{path}: keyed `name`, so no `k`"
            assert "k" not in node(rebuilt, *path), path
        assert rebuilt == written

    def test_declared_child_order_survives(self, tmp_path: Path) -> None:
        from tests.support.keyed_entries import node

        written, rebuilt = self._keyed_tree_files(tmp_path)
        term = ("policy-options", "policy-statement", "term")
        expected = {
            (*term, "from", "as-path-neighbors"): ["list-type", "list-name"],
            (*term, "from", "route-filter"): ["address", "exact", "orlonger", "accept", "reject"],
            (*term, "then", "community"): ["add", "delete", "community-name"],
            ("system", "ntp", "server"): ["address", "version", "prefer"],
            term[:2]: ["name", "term", "from", "then"],
        }
        for path, children in expected.items():
            assert list(node(written, *path)["c"]) == children, path
            assert list(node(rebuilt, *path)["c"]) == children, path

    def test_no_node_carries_fe(self, tmp_path: Path, bundled_tree: dict) -> None:
        """Neither a freshly built tree nor the bundled one holds `fe`.

        The scan counts what it walked, so an empty or unreadable tree fails
        rather than passing for want of nodes.
        """
        from tests.support.keyed_entries import KEYED_XSD, artifact_json, build_artifacts

        def carriers(tree: dict) -> tuple[int, list[str]]:
            seen = 0
            found: list[str] = []
            stack: list[tuple[str, dict]] = [("", tree)]
            while stack:
                path, current = stack.pop()
                seen += 1
                if "fe" in current:
                    found.append(path)
                for name, child in (current.get("c") or {}).items():
                    stack.append((f"{path}/{name}", child))
            return seen, found

        built = artifact_json(build_artifacts(KEYED_XSD, tmp_path), "junos-structure-tree.json")
        seen, found = carriers(built)
        assert seen > 30
        assert found == []

        seen, found = carriers(bundled_tree)
        assert seen > 400_000
        assert found == [], f"{len(found)} nodes carry fe, e.g. {found[:3]}"


class TestHomogeneousFlag:
    """The structure tree carries the XSD's `homogeneous` flag as `h`.

    An unkeyed `homogeneous` container -- `family` -- never carries a Junos
    tag and is written merged with its child (`inactive: family inet {`);
    readers and writers decide that from this flag, not from a name list.
    """

    def test_the_tree_carries_it(self, bundled_tree: dict) -> None:
        family = SchemaNode(name="family", flags={"homogeneous"})
        family.children["inet"] = SchemaNode(name="inet")
        root = SchemaNode(name="configuration")
        root.children["family"] = family
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "tree.json")
            write_structure_tree(root, path)
            assert json.loads(Path(path).read_text())["c"]["family"]["h"] is True
            assert "homogeneous" in read_structure_tree(path).children["family"].flags

        bundled = bundled_tree["c"]["interfaces"]["c"]["interface"]
        assert bundled["c"]["unit"]["c"]["family"].get("h") is True


class TestTheOneLineFlag:
    """`o` stands where the dump flags `oneliner`, and on the filter lists."""

    def test_the_one_line_flag_follows_the_dump(self, tmp_path: Path, bundled_tree: dict) -> None:
        """The rule, on the synthetic XSD: the element or type flags `oneliner`
        (`attributes-match`, `then community`, NTP `server`), or the list is one
        the filter-list fix names (`route-filter`); `oneliner-plus` alone
        (`as-path-neighbors`) is not `oneliner`.

        Owner decision on the identifier-key-fields review challenge (phase 5),
        replacing the pin of the 3,520 paths that carried `o` on 0.14.0. On the
        bundled tree, measured on regeneration: 4,736 nodes carry `o`, 1,216
        more than on 0.14.0 and none fewer. Every one gained is a list that was
        childless for want of its key fields; `o` joins an entry's key to its
        other children, so on a list whose only children are key fields it
        moves no rendering. The carriers that hold a child beyond their key
        fields are 0.14.0's own, less 56 whose children turned out to be their
        key: 24 flowspec `port-range`, 16 `tunnel-attribute` and 16 `then
        community` lists.

        Owner decision on challenge A (phase-6 review): any `maxOccurs` but 1
        is a list. Re-measured then: 102 nodes more carry `o`, none fewer,
        every one a node that became a list by it (48 `algorithm`, 16
        `host-discovery`, ...); 88 hold a child beyond their key fields.

        Keyed singleton correction: only root/group SRGB paths add `o`;
        the 1,286 key-only carriers stay unchanged. Independent whole-tree
        comparison binds the exact 3,554 non-key-carrier paths below.

        Change device-validation extends the correction to the routing-instance,
        logical-system and tenant copies of the same elements: their eight SRGB
        lists add `o` (3,562), the 1,286 key-only carriers unchanged.
        """
        tree = artifact_json(build_artifacts(KEYED_XSD, tmp_path), "junos-structure-tree.json")
        term = ("policy-options", "policy-statement", "term")
        carriers = {
            (*term, "then", "community"): True,
            ("system", "ntp", "server"): True,
            ("event-options", "policy", "attributes-match"): True,
            (*term, "from", "route-filter"): True,
            (*term, "from", "as-path-neighbors"): False,
            (*term, "from", "as-path-origins"): False,
            ("policy-options", "policy-statement"): False,
            ("policy-options", "community"): False,
        }
        for path, expected in carriers.items():
            assert bool(node(tree, *path).get("o")) is expected, path

        with_others: list[str] = []
        keys_only = 0
        stack: list[tuple[str, dict[str, Any]]] = [("", bundled_tree)]
        while stack:
            path, current = stack.pop()
            for name, child in (current.get("c") or {}).items():
                here = f"{path}/{name}" if path else name
                if child.get("o"):
                    assert child.get("c"), here
                    if set(child["c"]) - entry_key_names(child):
                        with_others.append(here)
                    else:
                        keys_only += 1
                stack.append((here, child))
        with_others.sort()
        assert (len(with_others), keys_only) == (3562, 1286)
        digest = hashlib.sha256("\n".join(with_others).encode()).hexdigest()
        assert digest == "b92e677bace7bd87acd4f1e22f3fd6e6ac036ea1e8f46321d253af5af7db861c"


# Deliberately synthetic: this exercises composition, not device correctness.
REPRESENTATIVE_NETCONF = """\
<rpc-reply>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema"
            xmlns:junos="http://xml.juniper.net/junos/25.2R2/junos">
  <xsd:complexType name="system-type">
    <xsd:sequence>
      <xsd:element name="host-name" type="xsd:string" minOccurs="0"/>
      <xsd:choice minOccurs="0" maxOccurs="unbounded">
        <xsd:element name="mode"><xsd:simpleType><xsd:restriction base="xsd:string">
          <xsd:enumeration value="active"/><xsd:enumeration value="passive"/>
        </xsd:restriction></xsd:simpleType></xsd:element>
        <xsd:element name="ssh"><xsd:complexType/></xsd:element>
        <xsd:element name="user" maxOccurs="unbounded">
          <xsd:annotation><xsd:appinfo><flag>oneliner</flag></xsd:appinfo></xsd:annotation>
          <xsd:complexType><xsd:sequence>
            <xsd:element name="username" type="xsd:string">
              <xsd:annotation><xsd:appinfo>
                <flag>identifier</flag><flag>nokeyword</flag><identifier/>
              </xsd:appinfo></xsd:annotation>
            </xsd:element>
            <xsd:element name="description" type="xsd:string" minOccurs="0"/>
          </xsd:sequence></xsd:complexType>
        </xsd:element>
        <xsd:element name="tag" type="xsd:string" maxOccurs="unbounded"/>
      </xsd:choice>
    </xsd:sequence>
  </xsd:complexType>
  <xsd:element name="configuration">
    <xsd:complexType><xsd:sequence><xsd:choice minOccurs="0" maxOccurs="unbounded">
      <xsd:element name="system" type="system-type"/>
      <xsd:element name="backup-system" type="system-type"/>
    </xsd:choice></xsd:sequence></xsd:complexType>
  </xsd:element>
</xsd:schema>
</rpc-reply>
"""


def test_public_build_produces_usable_reproducible_artifacts(tmp_path: Path) -> None:
    """Exercise extraction through consumers, without large private schema inputs."""
    source = tmp_path / "synthetic-netconf.xml"
    source.write_text(REPRESENTATIVE_NETCONF, encoding="utf-8")
    artifacts = ArtifactBuilder().build(source, tmp_path / "first")
    assert set(artifacts) == {
        "json-schema",
        "yaml-schema",
        "structure-tree",
        "lark-grammar",
        "metadata",
    }
    contents = {name: read_artifact_text(path) for name, path in artifacts.items()}
    tree = read_structure_tree(artifacts["structure-tree"])
    assert {"system", "backup-system", "apply-groups", "apply-flags"} <= set(tree.children)
    assert tree.children["apply-groups"].is_leaf
    assert tree.children["apply-flags"].children["omit"].is_presence
    for system in (tree.children["system"], tree.children["backup-system"]):
        assert system.type_ref == "system-type"
        assert set(system.children) == {"host-name", "mode", "ssh", "user", "tag"}
        assert system.children["host-name"].is_leaf
        assert system.children["mode"].enums == ["active", "passive"]
        assert system.children["ssh"].is_presence
        user = system.children["user"]
        assert user.is_list and "oneliner" in user.flags
        assert entry_key_names(user) == {"username"}
        tag = system.children["tag"]
        assert tag.is_list and tag.is_leaf and not tag.children

    valid = {
        "configuration": {
            "system": {
                "host-name": "router1",
                "mode": "active",
                "ssh": [None],
                "user": [{"username": "operator", "description": "sample"}],
                "tag": ["sample", "second"],
            },
            "backup-system": {"host-name": "router2"},
        }
    }
    for name in ("json-schema", "yaml-schema"):
        schema = json.loads(contents[name])
        Draft7Validator.check_schema(schema)
        validator = Draft7Validator(schema)
        validator.validate(valid)
        with_yaml_metadata = {
            "configuration": {"system": {"host-name": "router1", "_ansible_note": "sample"}}
        }
        assert validator.is_valid(with_yaml_metadata) is (name == "yaml-schema")
        for invalid in (
            {"configuration": {"unknown": {}}},
            {"configuration": {"system": {"unknown": "sample"}}},
            {"configuration": {"system": {"user": [{"unknown": "sample"}]}}},
            {"configuration": {"system": "not-a-container"}},
        ):
            assert not validator.is_valid(invalid), (name, invalid)

    grammar = contents["lark-grammar"]
    assert generate_lark_grammar(tree).strip() == grammar.strip()
    parser = Lark(grammar, parser="earley")
    for line in (
        "set system host-name router1",
        "set system mode active",
        "set system ssh",
        "set system user operator description sample",
        "set system tag sample",
        "set backup-system host-name router2",
    ):
        parser.parse(line)
    for line in ("set system unknown sample", "set system user", "set system mode"):
        with pytest.raises(UnexpectedInput):
            parser.parse(line)

    metadata = json.loads(contents["metadata"])
    assert metadata["junos_version"] == "25.2R2"
    assert metadata["stats"]["list_nodes"] >= 4
    assert 0 < metadata["fixes_applied"] <= metadata["fixes_registered"]
    assert metadata["stats"]["enum_values"] == 4
    assert metadata["generated_at"]
    second = ArtifactBuilder().build(source, tmp_path / "second")
    assert set(second) == set(artifacts)
    for name, path in second.items():
        rebuilt = read_artifact_text(path)
        if name == "metadata":
            second_metadata = json.loads(rebuilt)
            assert second_metadata.pop("generated_at")
            metadata.pop("generated_at")
            assert second_metadata == metadata
        else:
            assert rebuilt == contents[name], name
