"""Characterization tests pinning the public surface (onboarding phase 3).

These record what junoscfg does today, including behaviour that is wrong.  A
characterization test is not an assertion that the behaviour is correct; it is
a record that it was this before an agent touched the code.  Each test here was
seen to fail against a deliberate mutation before being committed.

Every defect these once pinned has since been fixed, and each pin was
rewritten rather than deleted: makedoc, validate_xml, rename-root ordering,
the XML/structured IR divergence and networks=["auto"]. They now pin the
working behaviour, which is what keeps the fixes fixed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from junoscfg import validate_xml
from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig
from junoscfg.cli import main
from junoscfg.display import read_artifact_text
from junoscfg.validate import SchemaLoadError

SIMPLE_XML = "<configuration><system><host-name>router1</host-name></system></configuration>"

MINIMAL_XSD = """<?xml version="1.0" encoding="UTF-8"?>
<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <xsd:element name="configuration">
    <xsd:complexType>
      <xsd:sequence>
        <xsd:element name="system" minOccurs="0">
          <xsd:complexType>
            <xsd:sequence>
              <xsd:element name="host-name" type="xsd:string" minOccurs="0"/>
            </xsd:sequence>
          </xsd:complexType>
        </xsd:element>
      </xsd:sequence>
    </xsd:complexType>
  </xsd:element>
</xsd:schema>
"""


class TestValidateXmlNeedsACleanedXsd:
    """``validate_xml`` needs ``junos-validated.xsd``, which nothing produces.

    The name is the point: a *validated* XSD is a cleaned one. A raw NETCONF
    dump does not compile. Measured on a real 163 MB dump at Junos 23.2R2,
    lxml refuses it with::

        Element 'xsd:element', attribute 'name': 'openconfig-lldp:lldp' is
        not a valid value of the atomic type 'xs:NCName'

    85 element names carry OpenConfig prefixes containing a colon, and that is
    only the first error lxml reports. `schema generate` briefly wrote the raw
    extract under this name; it was reverted, because a 156 MB file that does
    not compile is worse than an honest absence. Cleaning the XSD is real work
    and is not yet done.
    """

    def test_raises_when_the_xsd_is_absent(self, artifacts_dir: str) -> None:
        with pytest.raises(SchemaLoadError, match="XSD not found"):
            validate_xml(SIMPLE_XML, artifacts_dir=artifacts_dir)

    def test_bundled_artifacts_ship_no_xsd(self) -> None:
        """Intended: the XSD is per-device and per-release, not per-wheel."""
        import junoscfg.validate as validate_pkg

        data = Path(validate_pkg.__file__).parent / "data"
        assert data.is_dir()
        assert list(data.glob("*.xsd")) == []

    def test_schema_generate_does_not_claim_to_produce_one(self, tmp_path: Path) -> None:
        """It writes five artifacts and no XSD, which is honest."""
        xsd = tmp_path / "mini.xsd"
        xsd.write_text(MINIMAL_XSD)
        out = tmp_path / "artifacts"

        runner = CliRunner()
        assert runner.invoke(main, ["schema", "generate", str(xsd), "-o", str(out)]).exit_code == 0
        assert list(out.glob("*.xsd")) == []


class TestSchemaMakedocIsGone:
    """``junoscfg schema makedoc`` was removed; it had never worked.

    ``cli.py`` imported ``junoscfg.validate.schema_doc``, a module that never
    existed in the tree or in git history, so every invocation raised
    ModuleNotFoundError while ``docs/guide/cli.md`` documented the command with
    worked examples. Removed by openspec/changes/remove-dead-makedoc as a
    declared ``cli`` surface break. This test replaces the one that pinned the
    crash, and fails against the merge base, where the command still exists.
    """

    def test_makedoc_is_not_a_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["schema", "makedoc", "--help"])

        assert result.exit_code != 0
        assert "No such command" in result.output

    def test_schema_help_does_not_offer_it(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["schema", "--help"])

        assert result.exit_code == 0
        assert "makedoc" not in result.output
        # the commands that do work are still there
        assert "generate" in result.output
        assert "info" in result.output


class TestSchemaGenerateWritesOutsideTheRepo:
    """``schema generate -o DIR`` creates the directory and overwrites in it.

    This is the reachable file-writing surface, and it is intended: the caller
    names the directory.  Pinned so that a change to what gets written, or to
    the silent overwrite, is visible.
    """

    def test_creates_dir_and_writes_its_artifacts(self, tmp_path: Path) -> None:
        xsd = tmp_path / "mini.xsd"
        xsd.write_text(MINIMAL_XSD)
        out = tmp_path / "does-not-exist-yet"

        runner = CliRunner()
        result = runner.invoke(main, ["schema", "generate", str(xsd), "-o", str(out)])

        assert result.exit_code == 0
        assert out.is_dir()
        assert {p.name for p in out.iterdir()} == {
            "junos-structure-tree.json.gz",
            "junos-json-schema.json.gz",
            "junos-yaml-schema.json.gz",
            "junos-set.lark.gz",
            "junos-schema-meta.json.gz",
        }

    def test_existing_artifacts_are_overwritten_without_prompt(self, tmp_path: Path) -> None:
        xsd = tmp_path / "mini.xsd"
        xsd.write_text(MINIMAL_XSD)
        out = tmp_path / "artifacts"
        out.mkdir()
        stale = out / "junos-schema-meta.json.gz"
        stale.write_text("STALE")  # deliberately not valid gzip

        runner = CliRunner()
        result = runner.invoke(main, ["schema", "generate", str(xsd), "-o", str(out)])

        assert result.exit_code == 0
        # Artifacts ship compressed, so a readable one proves it was rewritten:
        # the stale bytes are not valid gzip and would raise.
        assert "junos_version" in read_artifact_text(stale)


class TestNetworksAutoNeedsSourceText:
    """``networks=["auto"]`` scans the configuration text for subnets.

    It used to read that text from ``_source_text``, attached dynamically by
    ``cli.py`` with a ``type: ignore`` and read back through ``hasattr``. A
    caller using the documented Python API never set it, so asking for
    auto-detection silently did nothing. ``source_text`` is a declared field
    now, and asking for auto without it is an error rather than a no-op.
    """

    IR = {
        "configuration": {
            "system": {"host-name": "router1"},
            "interfaces": {
                "interface": [
                    {
                        "name": "ge-0/0/0",
                        "unit": [
                            {
                                "name": "0",
                                "family": {"inet": {"address": [{"name": "203.0.114.1/24"}]}},
                            }
                        ],
                    }
                ]
            },
        }
    }

    def test_auto_without_source_text_is_an_error(self) -> None:
        config = AnonymizeConfig(ips=True, networks=["auto"], salt="pin-salt")
        config.expand_all()

        with pytest.raises(ValueError, match="source_text"):
            anonymize(self.IR, config)

    def test_auto_with_source_text_preserves_subnet_structure(self) -> None:
        """What `auto` is actually for: host bits survive within a subnet.

        Asserting only that the address changed would pass even if
        auto-detection found nothing, because plain IP anonymization changes it
        too. The point of `auto` is that two addresses in one subnet stay in
        one subnet, keeping their host bits.
        """
        ir = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {
                                        "inet": {
                                            "address": [
                                                {"name": "203.0.114.1/24"},
                                                {"name": "203.0.114.254/24"},
                                            ]
                                        }
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        }
        config = AnonymizeConfig(
            ips=True,
            networks=["auto"],
            salt="pin-salt",
            source_text=(
                "set interfaces ge-0/0/0 unit 0 family inet address 203.0.114.1/24\n"
                "set interfaces ge-0/0/0 unit 0 family inet address 203.0.114.254/24\n"
            ),
        )
        config.expand_all()

        result = anonymize(ir, config)
        addrs = [
            a["name"]
            for a in result.ir["configuration"]["interfaces"]["interface"][0]["unit"][0]["family"][
                "inet"
            ]["address"]
        ]
        assert addrs[0] != "203.0.114.1/24"
        # host bits kept, and both still in the same /24
        assert addrs[0].endswith(".1/24")
        assert addrs[1].endswith(".254/24")
        assert addrs[0].rsplit(".", 1)[0] == addrs[1].rsplit(".", 1)[0]

    def test_source_text_is_a_declared_field(self) -> None:
        import dataclasses

        names = {f.name for f in dataclasses.fields(AnonymizeConfig)}
        assert "source_text" in names
        assert "_source_text" not in names


class TestEdityamlSurfaceTheCollectionDrives:
    """``rename-root`` and ``ansibilize`` are driven by the Ansible collection.

    ``https://github.com/dg-i/ansible-collection-junos-config`` documents both
    in its group_vars pipelines, so their output shape is part of the declared
    ``cli`` surface.
    """

    @staticmethod
    def _yaml_config(tmp_path: Path) -> Path:
        from junoscfg import Format, convert_config

        src = Path("examples/router1.conf").read_text()
        out = tmp_path / "router1.yaml"
        out.write_text(convert_config(src, from_format=Format.STRUCTURED, to_format=Format.YAML))
        return out

    def test_rename_root_preserves_key_order(self, tmp_path: Path) -> None:
        """The new root is emitted first and configuration order is kept.

        This pinned the opposite until openspec/changes/yaml-key-order:
        cli.py called yaml.dump without sort_keys=False, so every edityaml
        command alphabetised its output while the code right above it said
        "Preserve key order by rebuilding dict".
        """
        cfg = self._yaml_config(tmp_path)
        runner = CliRunner()
        result = runner.invoke(main, ["edityaml", "rename-root", "--to", "junos_config", str(cfg)])

        assert result.exit_code == 0
        lines = result.output.splitlines()
        assert lines[0] == "junos_config:"
        children = [
            ln.strip().rstrip(":") for ln in lines if ln.startswith("  ") and ln.endswith(":")
        ]
        # system comes first in examples/router1.conf; firewall is last.
        assert children[0] == "system"
        assert children.index("system") < children.index("firewall")

    def test_ansibilize_emits_host_vars_then_group_vars(self, tmp_path: Path) -> None:
        """Output is host_vars, a '---' separator, then templated group_vars."""
        cfg = self._yaml_config(tmp_path)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "edityaml",
                "ansibilize",
                "-p",
                "hostname:configuration.system.host-name",
                str(cfg),
            ],
        )

        assert result.exit_code == 0
        assert result.output.startswith("hostname: router1\n")
        assert "\n---\n" in result.output


class TestXmlAndStructuredInputAgreeOnTheIr:
    """The same configuration gives one IR, whichever format it arrived in.

    It did not until openspec/changes/xml-ir-parity. ``KEY_ALIASES`` was
    consulted only in ``convert/input/set_input.py``, so ``<ieee-802.3ad>``
    stayed ``ieee-802.3ad`` where the structured path gave ``802.3ad``; and
    numeric leaves came back ``int`` from XML and ``str`` from structured.
    Set-side rendering hid both, which is why it went unnoticed.
    """

    @staticmethod
    def _irs() -> tuple[dict, dict]:
        import json

        from junoscfg import Format, convert_config

        conf = Path("examples/router1.conf").read_text()
        xml = Path("examples/router1.xml").read_text()
        return (
            json.loads(convert_config(conf, from_format=Format.STRUCTURED, to_format=Format.JSON)),
            json.loads(convert_config(xml, from_format=Format.XML, to_format=Format.JSON)),
        )

    def test_the_two_irs_are_identical(self) -> None:
        from_conf, from_xml = self._irs()
        assert from_conf == from_xml

    def test_key_aliases_are_applied_on_the_xml_path(self) -> None:
        from_conf, from_xml = self._irs()
        conf_eo = from_conf["configuration"]["interfaces"]["interface"][2]["ether-options"]
        xml_eo = from_xml["configuration"]["interfaces"]["interface"][2]["ether-options"]
        assert list(conf_eo) == ["802.3ad"]
        assert list(xml_eo) == ["802.3ad"]

    def test_numeric_leaves_are_strings_from_both_paths(self) -> None:
        """Junos JSON is string-valued; the IR follows it."""
        from_conf, from_xml = self._irs()
        conf_uid = from_conf["configuration"]["system"]["login"]["user"][0]["uid"]
        xml_uid = from_xml["configuration"]["system"]["login"]["user"][0]["uid"]
        assert conf_uid == "2000" and isinstance(conf_uid, str)
        assert xml_uid == "2000" and isinstance(xml_uid, str)

    def test_set_output_still_agrees(self) -> None:
        from junoscfg import Format, convert_config

        conf = Path("examples/router1.conf").read_text()
        xml = Path("examples/router1.xml").read_text()
        assert convert_config(
            conf, from_format=Format.STRUCTURED, to_format=Format.SET
        ) == convert_config(xml, from_format=Format.XML, to_format=Format.SET)


# ── identifier-key-fields ────────────────────────────────────────────
#
# Spec: openspec/changes/identifier-key-fields/specs/. A list entry is keyed
# by the fields the XSD declares, in order: `as-path-neighbors` by
# `list-type` and `list-name`, route-filter by its address and match type,
# `then community` by its action and `community-name`. The shapes are the
# ones a vMX on 23.2R2-S7.5 displayed for the same statements; the values
# are synthetic.

import hashlib  # noqa: E402
import re  # noqa: E402
from typing import Any  # noqa: E402

from junoscfg import Format, convert_config  # noqa: E402
from tests.keyed_entries import as_json, ir, set_ir, term_from, term_then, to_set  # noqa: E402

_LIST = "SAMPLE-AS-LIST"
_AS_LIST = {"list-type": "as-list", "list-name": _LIST}

#: Where a policy statement may stand: (set prefix, structured crumbs, wrap).
_PLACEMENTS: dict[str, tuple[str, list[str], Any]] = {
    "root": ("set", [], lambda po: {"policy-options": po}),
    "logical-system": (
        "set logical-systems SAMPLE-LS",
        ["logical-systems SAMPLE-LS"],
        lambda po: {"logical-systems": [{"name": "SAMPLE-LS", "policy-options": po}]},
    ),
    "group": (
        "set groups SAMPLE-GROUP",
        ["groups", "SAMPLE-GROUP"],
        lambda po: {"groups": [{"name": "SAMPLE-GROUP", "policy-options": po}]},
    ),
    "grouped-logical-system": (
        "set groups SAMPLE-GROUP logical-systems SAMPLE-LS",
        ["groups", "SAMPLE-GROUP", "logical-systems SAMPLE-LS"],
        lambda po: {
            "groups": [
                {
                    "name": "SAMPLE-GROUP",
                    "logical-systems": [{"name": "SAMPLE-LS", "policy-options": po}],
                }
            ]
        },
    ),
}


def _structured(crumbs: list[str], statement: str) -> str:
    """*statement* nested inside *crumbs*, one brace level each."""
    text = statement
    for crumb in reversed(crumbs):
        inner = "\n".join("    " + line for line in text.splitlines())
        text = f"{crumb} {{\n{inner}\n}}"
    return text + "\n"


def _xml(config: dict[str, Any]) -> str:
    """The device's XML for an IR: a list repeats its element, `[null]` is empty."""

    def element(name: str, value: Any) -> str:
        if isinstance(value, list):
            return "".join(f"<{name}/>" if item is None else element(name, item) for item in value)
        if isinstance(value, dict):
            inner = "".join(element(k, v) for k, v in value.items() if not k.startswith("@"))
            return f"<{name}>{inner}</{name}>"
        text = str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f"<{name}>{text}</{name}>"

    return element("configuration", config)


def _every_reader(set_text: str, structured: str, config: dict[str, Any]) -> dict[str, dict]:
    """The IR each door gives for one configuration."""
    return {
        "set": ir(set_text, Format.SET),
        "structured": ir(structured, Format.STRUCTURED),
        "json": ir(as_json(config), Format.JSON),
        "yaml": ir(
            convert_config(
                as_json(config), from_format=Format.JSON, to_format=Format.YAML, validate=False
            ),
            Format.YAML,
        ),
        "xml": ir(_xml(config), Format.XML),
    }


class TestEntryKeysComeFromTheTree:
    """One kernel helper answers an entry's keys; the tree carries them."""

    def test_the_helper_answers_the_key_tuple(self) -> None:
        from junoscfg import display
        from junoscfg.display import entry_keys

        assert "entry_keys" in display.__all__
        assert entry_keys({"L": True, "k": ["list-type", "list-name"]}) == (
            "list-type",
            "list-name",
        )
        assert entry_keys({"L": True, "k": ["address", ["exact", "orlonger"]]}) == (
            "address",
            ("exact", "orlonger"),
        )
        assert entry_keys({"L": True, "k": [["add", "delete"], "community-name"]}) == (
            ("add", "delete"),
            "community-name",
        )
        assert entry_keys({"L": True}) == ("name",)
        assert entry_keys({"L": True, "c": {"name": {"l": True}}}) == ("name",)

    def test_no_module_keeps_its_own_key(self) -> None:
        """No module under src/junoscfg reads a retired spelling, and two are banned.

        Read from the syntax tree, so a comment or a docstring that names a
        spelling to explain its retirement is not a reading of it.
        """
        import ast

        import tomllib

        retired_strings = {"fe", "values-only", "community-name"}
        retired_names = {"FLAT_ENTRY_ELEMENTS", "ENTRY_KEY_OVERRIDES", "get_flat_entry_config"}
        positional = re.compile(r"^_v\d+$")
        src = Path(__file__).resolve().parent.parent / "src" / "junoscfg"
        files = sorted(src.rglob("*.py"))
        assert len(files) > 60, "the scan found too little source to mean anything"

        found: list[str] = []
        for path in files:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            docstrings = {
                id(node.body[0].value)
                for node in ast.walk(tree)
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
                and node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
            }
            where = path.relative_to(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if id(node) in docstrings:
                        continue
                    if node.value in retired_strings or positional.match(node.value):
                        found.append(f"{where}:{node.lineno} {node.value!r}")
                elif isinstance(node, ast.JoinedStr):
                    head = node.values[0] if node.values else None
                    if isinstance(head, ast.Constant) and head.value == "_v":
                        found.append(f"{where}:{node.lineno} f'_v{{...}}'")
                elif isinstance(node, ast.Name) and node.id in retired_names:
                    found.append(f"{where}:{node.lineno} {node.id}")
                elif isinstance(node, ast.Attribute) and node.attr in retired_names:
                    found.append(f"{where}:{node.lineno} {node.attr}")
                elif isinstance(node, ast.alias) and node.name in retired_names:
                    found.append(f"{where}:{node.name}")
        assert found == [], found

        pyproject = tomllib.loads(
            (src.parent.parent / "pyproject.toml").read_text(encoding="utf-8")
        )
        banned = pyproject["tool"]["ruff"]["lint"]["flake8-tidy-imports"]["banned-api"]
        assert "junoscfg.display.ENTRY_KEY_OVERRIDES" in banned
        assert "junoscfg.display.get_flat_entry_config" in banned

    @staticmethod
    def _bundled() -> dict[str, Any]:
        from junoscfg.display import load_schema_tree

        tree = load_schema_tree()
        assert tree is not None
        return tree

    @staticmethod
    def _lists(tree: dict[str, Any]) -> list[tuple[tuple[str, ...], dict[str, Any]]]:
        found: list[tuple[tuple[str, ...], dict[str, Any]]] = []
        stack: list[tuple[tuple[str, ...], dict[str, Any]]] = [((), tree)]
        while stack:
            path, node = stack.pop()
            for name, child in (node.get("c") or {}).items():
                here = (*path, name)
                if child.get("L"):
                    found.append((here, child))
                stack.append((here, child))
        return found

    def test_the_bundled_tree_carries_the_declared_keys(self) -> None:
        lists = self._lists(self._bundled())
        assert len(lists) > 15_000, "the walk reached too few lists to mean anything"

        as_lists = [(p, n) for p, n in lists if n.get("tr") == "control-as-list-type"]
        assert len(as_lists) == 24
        where = set()
        for path, node in as_lists:
            assert node.get("k") == ["list-type", "list-name"], path
            assert list(node["c"])[:2] == ["list-type", "list-name"], path
            assert "p" not in node, path
            where.add((path[-1], "groups" in path, "logical-systems" in path, "term" in path))
        # root, logical systems, groups and grouped logical systems, with and
        # without a term, for each of the three lists: 3 x 8.
        assert len(where) == 24

        from junoscfg.display import entry_keys

        assert all(entry_keys(n) == ("list-type", "list-name") for _, n in as_lists)

        matches = [n for p, n in lists if p[-1] == "attributes-match"]
        assert len(matches) == 2
        for node in matches:
            assert node["k"] == ["from-event-attribute", "condition", "to-event-attribute-value"]

        filters = {
            "control-route-filter-type": "address",
            "control-source-address-filter-type": "address",
            "control-prefix-list-filter-type": "list_name",
        }
        for type_ref, first in filters.items():
            found = [(p, n) for p, n in lists if n.get("tr") == type_ref]
            assert len(found) == 8, type_ref
            for path, node in found:
                keys = entry_keys(node)
                assert len(keys) == 2 and keys[0] == first, path
                assert isinstance(keys[1], tuple) and {"exact", "orlonger"} <= set(keys[1])
                assert list(node["c"])[0] == first
            if type_ref != "control-prefix-list-filter-type":
                assert all("accept" in n["c"] for _, n in found), type_ref

        # Every list declaring an all-identifier action choice before
        # `community-name` is keyed by that choice, then the name: `then
        # community` and the `community` action of the filter lists' second
        # choice. 48 on 25.2R2, measured in phase 5 (owner decision): 8 under
        # `then`, 8 each under route-filter, prefix-list-filter,
        # source-address-filter and route-filter-list, 4 each under rf_list
        # and saf_list.
        actions = [
            (p, n)
            for p, n in lists
            if "community-name" in n.get("c", {}) and {"add", "delete", "set"} <= set(n["c"])
        ]
        assert len(actions) == 48
        for path, node in actions:
            keys = entry_keys(node)
            assert len(keys) == 2 and keys[-1] == "community-name", path
            # The key order is the declared order: the choice precedes the name.
            assert isinstance(keys[0], tuple) and {"add", "delete", "set"} <= set(keys[0]), path
        definitions = [n for p, n in lists if p[-2:] == ("policy-options", "community")]
        assert len(definitions) == 4
        assert all(entry_keys(n) == ("name",) and "k" not in n for n in definitions)

    def test_the_one_line_flag_follows_the_dump(self, tmp_path: Path) -> None:
        """`o` stands where the dump flags `oneliner`, and on the filter lists.

        Owner decision on the review.md challenge (phase 5), replacing the
        pin of the 3,520 paths that carried `o` on 0.14.0. The rule, on the
        synthetic XSD: the element or type flags `oneliner` (`attributes-match`,
        `then community`, NTP `server`), or the list is one the filter-list fix
        names (`route-filter`); `oneliner-plus` alone (`as-path-neighbors`) is
        not `oneliner`.

        On the bundled tree, measured on regeneration: 4,736 nodes carry `o`,
        1,216 more than on 0.14.0 and none fewer. Every one gained is a list
        that was childless for want of its key fields; `o` joins an entry's
        key to its other children, so on a list whose only children are key
        fields it moves no rendering. The carriers that hold a child beyond
        their key fields are 0.14.0's own, less 56 whose children turned out
        to be their key: 24 flowspec `port-range`, 16 `tunnel-attribute` and
        16 `then community` lists.

        Owner decision on challenge A (phase-6 review): any `maxOccurs` but 1
        is a list. Re-measured then: 102 nodes more carry `o`, none fewer,
        every one a node that became a list by it (48 `algorithm`, 16
        `host-discovery`, ...); 88 hold a child beyond their key fields.
        """
        from tests.keyed_entries import KEYED_XSD, artifact_json, build_artifacts, node

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

        from junoscfg.display import entry_key_names

        with_others: list[str] = []
        keys_only = 0
        stack: list[tuple[str, dict[str, Any]]] = [("", self._bundled())]
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
        assert (len(with_others), keys_only) == (3552, 1286)
        digest = hashlib.sha256("\n".join(with_others).encode()).hexdigest()
        assert digest == "b6e5fa4ba01787cdc0396e170b5a14884a423056017d4db7d8a9f644f1b17807"


class TestKeyedEntriesAgreeAcrossReaders:
    """Every reader gives the device's IR for a keyed entry; writers follow it."""

    @pytest.mark.parametrize("placement", list(_PLACEMENTS))
    @pytest.mark.parametrize("level", ["term", "policy"])
    @pytest.mark.parametrize("slot", ["as-path-neighbors", "as-path-origins", "as-path-transits"])
    def test_as_list_references_give_one_ir(self, slot: str, level: str, placement: str) -> None:
        prefix, crumbs, wrap = _PLACEMENTS[placement]
        # A wildcard name where a group may hold one.
        policy = "<*>" if placement == "group" else "SAMPLE-POLICY"
        where = ["policy-options", f"policy-statement {policy}"]
        set_where = f"policy-options policy-statement {policy}"
        if level == "term":
            where.append("term T1")
            set_where += " term T1"
        statement = f"{slot} as-list {_LIST}"
        entry = {"name": policy}
        body = {"from": {slot: [dict(_AS_LIST)]}}
        if level == "term":
            entry["term"] = [{"name": "T1", **body}]
        else:
            entry.update(body)
        config = wrap({"policy-options": {"policy-statement": [entry]}}["policy-options"])

        irs = _every_reader(
            f"{prefix} {set_where} from {statement}\n",
            _structured([*crumbs, *where, "from"], statement + ";"),
            config,
        )
        for door, got in irs.items():
            assert got == config, door
        assert to_set(as_json(config), Format.JSON) == [f"{prefix} {set_where} from {statement}"]

    def test_attributes_match_gives_its_three_fields(self) -> None:
        match = {
            "from-event-attribute": "ping.test-owner",
            "condition": "matches",
            "to-event-attribute-value": "^uptime$",
        }
        spaced = dict(match, **{"to-event-attribute-value": "^up time$"})
        config = {
            "event-options": {
                "policy": [{"name": "SAMPLE-EVENT-POLICY", "attributes-match": [match, spaced]}]
            }
        }
        lines = [
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
            'matches "^uptime$"',
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
            'matches "^up time$"',
        ]
        structured = _structured(
            ["event-options", "policy SAMPLE-EVENT-POLICY"],
            'attributes-match ping.test-owner matches "^uptime$";\n'
            'attributes-match ping.test-owner matches "^up time$";',
        )
        for door, got in _every_reader("\n".join(lines) + "\n", structured, config).items():
            entries = got["event-options"]["policy"][0]["attributes-match"]
            assert entries == [match, spaced], door
            for item in entries:
                assert not {"name", "_v0", "_v1"} & set(item), door
        assert to_set(as_json(config), Format.JSON) == lines

    def test_route_filter_holds_its_action(self) -> None:
        for slot in ("route-filter", "source-address-filter"):
            entry = {"address": "198.51.100.0/24", "exact": [None], "accept": [None]}
            config = {
                "policy-options": {
                    "policy-statement": [
                        {"name": "SAMPLE-POLICY", "term": [{"name": "T1", "from": {slot: [entry]}}]}
                    ]
                }
            }
            line = f"{_TERM} from {slot} 198.51.100.0/24 exact accept"
            structured = _structured(
                ["policy-options", "policy-statement SAMPLE-POLICY", "term T1", "from"],
                f"{slot} 198.51.100.0/24 exact accept;",
            )
            for door, got in _every_reader(line + "\n", structured, config).items():
                assert term_from(got)[slot] == [entry], (slot, door)
                assert list(term_from(got)[slot][0]) == ["address", "exact", "accept"], door

    @pytest.mark.parametrize("action", ["add", "delete"])
    def test_a_community_action_reads_in_either_order(self, action: str) -> None:
        expected = [{action: [None], "community-name": "SAMPLE-COMM"}]
        config = {
            "policy-options": {
                "policy-statement": [
                    {
                        "name": "SAMPLE-POLICY",
                        "term": [{"name": "T1", "then": {"community": expected}}],
                    }
                ]
            }
        }
        doors = {
            "action first": set_ir(f"{_TERM} then community {action} SAMPLE-COMM"),
            "key first": set_ir(f"{_TERM} then community SAMPLE-COMM {action}"),
            **_every_reader(
                f"{_TERM} then community {action} SAMPLE-COMM\n",
                _structured(
                    ["policy-options", "policy-statement SAMPLE-POLICY", "term T1", "then"],
                    f"community {action} SAMPLE-COMM;",
                ),
                config,
            ),
        }
        for door, got in doors.items():
            community = term_then(got)["community"]
            assert community == expected, door
            assert list(community[0]) == [action, "community-name"], door
        assert to_set(as_json(config), Format.JSON) == [
            f"{_TERM} then community {action} SAMPLE-COMM"
        ]

    def test_identity_is_the_key_tuple(self) -> None:
        got = term_from(
            set_ir(
                f"{_TERM} from as-path-neighbors as-list {_LIST}",
                f"{_TERM} from as-path-neighbors as-list {_LIST}",
                f"{_TERM} from as-path-neighbors as-list-group {_LIST}",
                f"{_TERM} from as-path-neighbors as-list SAMPLE-AS-LIST-2",
            )
        )
        assert got["as-path-neighbors"] == [
            {"list-type": "as-list", "list-name": _LIST},
            {"list-type": "as-list-group", "list-name": _LIST},
            {"list-type": "as-list", "list-name": "SAMPLE-AS-LIST-2"},
        ]
        # Device probe round 4 pending: one address, two match types.
        got = term_from(
            set_ir(
                f"{_TERM} from route-filter 198.51.100.0/24 exact",
                f"{_TERM} from route-filter 198.51.100.0/24 orlonger",
                f"{_TERM} from route-filter 198.51.100.0/24 exact accept",
            )
        )
        assert got["route-filter"] == [
            {"address": "198.51.100.0/24", "exact": [None], "accept": [None]},
            {"address": "198.51.100.0/24", "orlonger": [None]},
        ]

    @pytest.mark.parametrize("list_type", ["as-list", "as-list-group"])
    @pytest.mark.parametrize(
        "list_name",
        ["SAMPLE-AS-LIST", "as-list", "as-list-group", "64496", "SAMPLE AS LIST", "S_1.2-x"],
    )
    def test_device_ir_round_trips_through_set(self, list_type: str, list_name: str) -> None:
        """Device IR to set to IR, over both enum values and names of every
        shape a `list-name` takes: one spelling a keyword, one numeric, one
        quoted with spaces."""
        entry = {"list-type": list_type, "list-name": list_name}
        config = {
            "policy-options": {
                "policy-statement": [
                    {
                        "name": "SAMPLE-POLICY",
                        "term": [{"name": "T1", "from": {"as-path-neighbors": [entry]}}],
                    }
                ]
            }
        }
        lines = to_set(as_json(config), Format.JSON)
        assert len(lines) == 1
        assert ir("\n".join(lines) + "\n", Format.SET) == config

    @pytest.mark.parametrize("writer", [Format.SET, Format.STRUCTURED, Format.JSON, Format.YAML])
    def test_every_writer_reads_back_the_device_ir(self, writer: Format) -> None:
        """set -> IR -> each writer -> its reader, with order kept across entries."""
        lines = [
            f"{_TERM} from as-path-neighbors as-list SAMPLE-AS-LIST-2",
            f"{_TERM} from as-path-neighbors as-list-group {_LIST}",
            f"{_TERM} from as-path-neighbors as-list {_LIST}",
            f"{_TERM} from route-filter 198.51.100.128/25 orlonger",
            f"{_TERM} from route-filter 198.51.100.0/24 exact accept",
            f"{_TERM} then community delete SAMPLE-COMM-2",
            f"{_TERM} then community add SAMPLE-COMM",
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
            'matches "^up time$"',
        ]
        source = "\n".join(lines) + "\n"
        first = ir(source, Format.SET)
        written = convert_config(source, from_format=Format.SET, to_format=writer, validate=False)
        assert ir(written, writer) == first
        neighbors = term_from(first)["as-path-neighbors"]
        assert [e["list-name"] for e in neighbors] == ["SAMPLE-AS-LIST-2", _LIST, _LIST]
        assert to_set(written, writer) == lines

    def test_json_and_xml_write_the_device_set_lines(self) -> None:
        config = {
            "policy-options": {
                "policy-statement": [
                    {
                        "name": "SAMPLE-POLICY",
                        "term": [
                            {
                                "name": "T1",
                                "from": {
                                    "as-path-neighbors": [dict(_AS_LIST)],
                                    "route-filter": [
                                        {
                                            "address": "198.51.100.0/24",
                                            "exact": [None],
                                            "accept": [None],
                                        }
                                    ],
                                    "source-address-filter": [
                                        {
                                            "address": "198.51.100.0/24",
                                            "exact": [None],
                                            "accept": [None],
                                        }
                                    ],
                                },
                                "then": {
                                    "community": [{"add": [None], "community-name": "SAMPLE-COMM"}]
                                },
                            }
                        ],
                    }
                ]
            },
            "event-options": {
                "policy": [
                    {
                        "name": "SAMPLE-EVENT-POLICY",
                        "attributes-match": [
                            {
                                "from-event-attribute": "ping.test-owner",
                                "condition": "matches",
                                "to-event-attribute-value": "^uptime$",
                            }
                        ],
                    }
                ]
            },
        }
        expected = [
            f"{_TERM} from as-path-neighbors as-list {_LIST}",
            f"{_TERM} from route-filter 198.51.100.0/24 exact accept",
            f"{_TERM} from source-address-filter 198.51.100.0/24 exact accept",
            f"{_TERM} then community add SAMPLE-COMM",
            "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
            'matches "^uptime$"',
        ]
        assert to_set(as_json(config), Format.JSON) == expected
        assert to_set(_xml(config), Format.XML) == expected

    def test_structured_output_writes_the_keys_in_order(self) -> None:
        source = "\n".join(
            [
                f"{_TERM} from as-path-neighbors as-list {_LIST}",
                f"{_TERM} from as-path-origins as-list-group SAMPLE-AS-LIST-GROUP",
                f"{_TERM} from route-filter 198.51.100.0/24 exact accept",
                f"{_TERM} from source-address-filter 198.51.100.0/24 exact accept",
                f"{_TERM} then community add SAMPLE-COMM",
                "set event-options policy SAMPLE-EVENT-POLICY attributes-match ping.test-owner "
                'matches "^uptime$"',
            ]
        )
        out = convert_config(
            source, from_format=Format.SET, to_format=Format.STRUCTURED, validate=False
        )
        for text in (
            f"as-path-neighbors as-list {_LIST};",
            "as-path-origins as-list-group SAMPLE-AS-LIST-GROUP;",
            "route-filter 198.51.100.0/24 exact accept;",
            "source-address-filter 198.51.100.0/24 exact accept;",
            "community add SAMPLE-COMM;",
            'attributes-match ping.test-owner matches "^uptime$";',
        ):
            assert text in out, f"{text!r} missing from\n{out}"
        assert "list-type" not in out and "list-name" not in out

    @pytest.mark.parametrize(
        ("attribute", "word", "xml_attribute", "meta"),
        [
            ({"inactive": True}, "inactive:", 'inactive="inactive"', "deactivate"),
            ({"protect": "protect"}, "protect:", 'protect="protect"', "protect"),
        ],
    )
    def test_an_attribute_on_a_keyed_entry_agrees_across_readers(
        self, attribute: dict, word: str, xml_attribute: str, meta: str
    ) -> None:
        entry = {"@": attribute, **_AS_LIST}
        config = {
            "policy-options": {
                "policy-statement": [
                    {
                        "name": "SAMPLE-POLICY",
                        "term": [{"name": "T1", "from": {"as-path-neighbors": [entry]}}],
                    }
                ]
            }
        }
        line = f"{_TERM} from as-path-neighbors as-list {_LIST}"
        meta_line = f"{meta} {line[len('set ') :]}"
        structured = _structured(
            ["policy-options", "policy-statement SAMPLE-POLICY", "term T1", "from"],
            f"{word} as-path-neighbors as-list {_LIST};",
        )
        xml = _xml(config).replace("<as-path-neighbors>", f"<as-path-neighbors {xml_attribute}>")
        doors = {
            "set": ir(f"{line}\n{meta_line}\n", Format.SET),
            "structured": ir(structured, Format.STRUCTURED),
            "json": ir(as_json(config), Format.JSON),
        }
        # The XML reader drops `protect="protect"` on every element, keyed or
        # not: a separate gap, outside this change (see the phase-4 report).
        if meta != "protect":
            doors["xml"] = ir(xml, Format.XML)
        for door, got in doors.items():
            assert term_from(got)["as-path-neighbors"] == [entry], door
        assert to_set(as_json(config), Format.JSON) == [line, meta_line]

    def test_an_empty_list_writes_nothing(self) -> None:
        """Pinned as it is: no device writes it, and no output invents an entry."""
        config = {
            "policy-options": {
                "policy-statement": [
                    {
                        "name": "SAMPLE-POLICY",
                        "term": [
                            {
                                "name": "T1",
                                "from": {"as-path-neighbors": []},
                                "then": {"accept": [None]},
                            }
                        ],
                    }
                ]
            }
        }
        lines = to_set(as_json(config), Format.JSON)
        assert lines == [f"{_TERM} then accept"]


_TERM = "set policy-options policy-statement SAMPLE-POLICY term T1"


class TestNameKeyedListsAreUnchanged:
    """`name`-keyed lists render byte for byte as they did on 0.14.0.

    Pinned before the change and expected to pass on both sides of it: the
    guard against the change moving what it does not name. Digests of every
    output format from every input format of `examples/router1.*`, and of the
    committed set corpus less the lines the change rekeys.
    """

    _OUTPUTS = (Format.SET, Format.STRUCTURED, Format.JSON, Format.YAML)
    _REKEYED = (
        "route-filter",
        "prefix-list-filter",
        "source-address-filter",
        "attributes-match",
        "as-path-neighbors",
        "as-path-origins",
        "as-path-transits",
        " then community ",
        "apply-groups",
    )

    def _render(self, source: str, fmt: Format) -> str:
        parts = []
        for out in self._OUTPUTS:
            try:
                parts.append(convert_config(source, from_format=fmt, to_format=out, validate=False))
            except Exception as exc:  # noqa: BLE001 -- the failure itself is pinned
                parts.append(f"ERROR {type(exc).__name__}")
        return "\x00".join(parts)

    def test_corpus_output_is_byte_identical(self) -> None:
        examples = {
            "set": (Format.SET, "d09d9e47f09a48acf36e61ea48942e09a3d206d21aa32d763bfb9c1510e4de3a"),
            "conf": (
                Format.STRUCTURED,
                "d09d9e47f09a48acf36e61ea48942e09a3d206d21aa32d763bfb9c1510e4de3a",
            ),
            "json": (
                Format.JSON,
                "da3e1e578f8ec992f13d10a657745078d36f110e12639828b2f24bc435d30097",
            ),
            "xml": (Format.XML, "da3e1e578f8ec992f13d10a657745078d36f110e12639828b2f24bc435d30097"),
        }
        for suffix, (fmt, digest) in examples.items():
            source = Path(f"examples/router1.{suffix}").read_text(encoding="utf-8")
            rendered = self._render(source, fmt)
            assert hashlib.sha256(rendered.encode()).hexdigest() == digest, suffix

        lines = [
            line.strip()
            for line in Path("tests/data/set_corpus.txt").read_text().splitlines()
            if line.startswith("set ")
        ]
        kept = [line for line in lines if not any(k in line + " " for k in self._REKEYED)]
        assert (len(lines), len(kept)) == (117, 105)
        rendered = "\x01".join(self._render(line, Format.SET) for line in kept)
        assert (
            hashlib.sha256(rendered.encode()).hexdigest()
            == "dcbaa53f5b228b48f2855dcc4b1b8b0c94a09289ba48df59c26c812988e22c2c"
        )
