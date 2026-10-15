"""The convert_config() door, the Format enum, and what one reader or writer adds.

What holds for every (reader, writer) pair -- each conversion reads back as the
IR it was given -- is `tests/contract/test_format_matrix.py`, over the shape
catalogue; this file keeps what belongs to one door: refusals, path
selection, and the value shapes one reader or writer settles.
"""

from __future__ import annotations

import copy
import datetime
import json
import random
import re
from typing import TYPE_CHECKING, Any

import pytest
import yaml
from click.testing import CliRunner

from junoscfg import (
    FieldValidationError,
    Format,
    convert_config,
    convert_config_result,
    validate_config,
)
from junoscfg.anonymize import AnonymizeConfig
from junoscfg.cli import main
from junoscfg.convert import FORMAT_IMPLEMENTATIONS, from_dict, pipeline, pipeline_result, to_dict
from junoscfg.display import artifacts_dir as artifacts_in
from tests.support.aliases import (
    ANCHORED_BESIDE,
    ANCHORED_BESIDE_WRITTEN_OUT,
    CYCLE,
    NESTED_ONCE,
    SHARED_BLOCK,
    SHARED_BLOCK_WRITTEN_OUT,
    alias_chain_yaml,
    hosts_sharing_contents,
    nested_ir,
    nested_yaml,
    shared_containers,
)
from tests.support.artifacts import write_minimal_tree
from tests.support.shapes import SHAPES, WRITERS, in_order, read_ir

if TYPE_CHECKING:
    from pathlib import Path


class TestSetBracketSyntaxRejection:
    def test_public_conversion_doors_reject_without_validation(self) -> None:
        line = "set system apply-groups [ foo bar ]"
        source = f"# ignored bracket [\n{line}"
        expected = f"Unsupported bracket syntax in set input on line 2:\n{line}"

        with pytest.raises(ValueError, match=re.escape(expected)):
            to_dict(source, "set")
        with pytest.raises(ValueError, match=re.escape(expected)):
            convert_config(
                source,
                from_format=Format.SET,
                to_format=Format.JSON,
                validate=False,
            )


class TestFormatEnum:
    def test_format_values(self) -> None:
        assert Format.SET.value == "set"
        assert Format.STRUCTURED.value == "structured"
        assert Format.JSON.value == "json"
        assert Format.YAML.value == "yaml"
        assert Format.XML.value == "xml"

    def test_format_from_string(self) -> None:
        assert Format("set") is Format.SET
        assert Format("json") is Format.JSON

    def test_every_format_has_one_implementation(self) -> None:
        """One table selects what each name reads and writes with
        (docs/decisions/2026-10-15-yaml-new-before-renaming-yaml.md): `yaml`
        keeps the IR dump, `yaml-new` is the Junos JSON object, and the
        planned rename edits the table and the enum only."""
        assert [f.value for f in Format] == list(FORMAT_IMPLEMENTATIONS)
        assert Format("yaml-new") is Format.YAML_NEW
        assert FORMAT_IMPLEMENTATIONS["yaml"] == "ir-yaml"
        assert FORMAT_IMPLEMENTATIONS["yaml-new"] == "junos-yaml"
        assert FORMAT_IMPLEMENTATIONS["json"] == "junos-json"

    def test_the_rename_is_a_change_to_the_table(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Rehearse the planned rename: with the two YAML rows swapped, every
        door follows the table, so the later change edits the table and
        `Format` only (Test/Challenge B5)."""
        monkeypatch.setitem(FORMAT_IMPLEMENTATIONS, "yaml", "junos-yaml")
        monkeypatch.setitem(FORMAT_IMPLEMENTATIONS, "yaml-new", "ir-yaml")
        source = "configuration:\n  system:\n    host-name: r1\n    _meta_x: y\n"
        assert to_dict(source, "yaml")["system"]["_meta_x"] == "y"
        assert "_meta_x" not in to_dict(source, "yaml-new")["system"]
        flag = {"system": {"services": {"ssh": True}}}
        assert "- null" in from_dict(flag, "yaml")
        assert "ssh: true" in from_dict(flag, "yaml-new")
        assert "- null" in convert_config(
            "set system services ssh\n", from_format=Format.SET, to_format=Format.YAML
        )
        assert validate_config(source, format=Format.YAML).valid is False
        assert validate_config(source, format=Format.YAML_NEW).valid is True
        cli = CliRunner().invoke(main, ["convert", "-i", "yaml", "-e", "json"], input=source)
        assert '"_meta_x": "y"' in cli.stdout

    def test_an_unknown_implementation_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A table row naming no implementation fails loudly, never as another one."""
        monkeypatch.setitem(FORMAT_IMPLEMENTATIONS, "set", "bogus")
        with pytest.raises(ValueError, match="Unknown implementation 'bogus'"):
            to_dict("set system host-name r1\n", "set")
        with pytest.raises(ValueError, match="Unknown implementation 'bogus'"):
            from_dict({"system": {}}, "set")

    @pytest.mark.parametrize("name", ["yaml-old", "YAML", "toml"])
    def test_an_unknown_name_is_refused(self, name: str) -> None:
        with pytest.raises(ValueError, match=f"Unknown input format: {name}"):
            to_dict("configuration: {}", name)
        with pytest.raises(ValueError, match=f"Unknown output format: {name}"):
            from_dict({"system": {}}, name)


class TestPartialStructuredConfig:
    """End-to-end: structured partial config (no parent wrapper) → JSON."""

    def test_interfaces_partial_to_json(self) -> None:
        source = (
            "ge-0/0/0 {\n"
            '    description "Core: srv06.dc1.example.net (igb0)";\n'
            "}\n"
            "lo0 {\n"
            "    unit 0 {\n"
            "        family inet {\n"
            "            address 10.0.36.103/32;\n"
            "        }\n"
            "    }\n"
            "}\n"
        )
        result = convert_config(source, from_format=Format.STRUCTURED, to_format=Format.JSON)
        parsed = json.loads(result)
        config = parsed["configuration"]
        assert "interfaces" in config
        ifaces = config["interfaces"]["interface"]
        assert isinstance(ifaces, list)
        names = [i["name"] for i in ifaces]
        assert "ge-0/0/0" in names
        assert "lo0" in names
        ge = next(i for i in ifaces if i["name"] == "ge-0/0/0")
        assert ge["description"] == "Core: srv06.dc1.example.net (igb0)"
        lo = next(i for i in ifaces if i["name"] == "lo0")
        assert lo["unit"][0]["family"]["inet"]["address"] == [{"name": "10.0.36.103/32"}]


class TestConvertUnsupported:
    def test_xml_output_not_supported(self) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        with pytest.raises(NotImplementedError, match="XML output"):
            convert_config(source, from_format=Format.JSON, to_format=Format.XML)


_PATH_FILTER_SOURCE = (
    '{"configuration": {"system": {"host-name": "r1",'
    ' "syslog": {"file": [{"name": "messages"}]}}, "interfaces": {}}}'
)


_SYSLOG = {"file": [{"name": "messages"}]}
#: The IR each path keeps of `_PATH_FILTER_SOURCE`.
_UNDER = {
    "system": {"system": {"host-name": "r1", "syslog": _SYSLOG}},
    "system.syslog": {"system": {"syslog": _SYSLOG}},
}
_WRITERS = [Format.SET, Format.STRUCTURED, Format.JSON, Format.YAML, Format.YAML_NEW]
_WRITER_IDS = [writer.value for writer in _WRITERS]


def _put_back(output: str, fmt: Format, path: str) -> object:
    """The IR of relative *output* once it is put back under *path*."""
    tokens = path.split(".")
    if fmt is Format.SET:
        prefix = "set " + " ".join(tokens) + " "
        lines = [prefix + line.removeprefix("set ") for line in output.splitlines()]
        return read_ir("\n".join(lines) + "\n", fmt)
    if fmt is Format.STRUCTURED:
        text = output
        for token in reversed(tokens):
            body = "".join("    " + line + "\n" for line in text.splitlines())
            text = f"{token} {{\n{body}}}\n"
        return read_ir(text, fmt)
    value = json.loads(output) if fmt is Format.JSON else yaml.safe_load(output)
    for token in reversed(tokens):
        value = {token: value}
    return value


#: The writers whose output is the Junos JSON object.
_OBJECT_WRITERS = [Format.JSON, Format.YAML_NEW]
_OBJECT_WRITER_IDS = [writer.value for writer in _OBJECT_WRITERS]

#: Presence flags spelled `{}`, `true` and `[true]`, `name` after a flag, and
#: annotations whose `true` is a boolean, for relative selections.
_SELECTED_SOURCE = json.dumps(
    {
        "configuration": {
            "system": {
                "services": {"ssh": True, "telnet": [True], "netconf": {"ssh": {}}},
                "syslog": {
                    "host": [
                        {"explicit-priority": {}, "name": "198.51.100.9"},
                        {"name": "198.51.100.10", "contents": [{"any": True, "name": "any"}]},
                        {
                            "@": {"inactive": True},
                            "name": "198.51.100.11",
                            "explicit-priority": True,
                            "@explicit-priority": {"inactive": True},
                        },
                    ]
                },
            }
        }
    }
)


def _relative_and_absolute(
    source: str,
    to_format: Format,
    path: str,
    *,
    from_format: Format = Format.JSON,
    at: str | None = None,
    anon_config: object | None = None,
) -> tuple[Any, Any]:
    """The loaded relative output for *path*, and the absolute output's value at
    *at* (default *path*), both written to *to_format*."""
    load = json.loads if to_format is Format.JSON else yaml.safe_load

    def written(relative: bool) -> Any:
        result = pipeline_result(
            source,
            from_format=from_format.value,
            to_format=to_format.value,
            validate=False,
            anon_config=anon_config,
            path=path,
            relative=relative,
        )
        return load(result.output)

    absolute = written(relative=False)["configuration"]
    for token in (at or path).split("."):
        absolute = absolute[token]
    return written(relative=True), absolute


class TestPathFiltering:
    """`path=` keeps one subtree of the IR; `relative=True` writes it without the path.

    The CLI's `--path` and `--relative` pass these through
    (`tests/unit/cli/test_cli.py`); the per-format text filters are
    `tests/unit/display/test_display_filters.py`.
    """

    def test_pipeline_filters_ir_before_rendering(self, monkeypatch: pytest.MonkeyPatch) -> None:
        rendered: list[dict] = []

        paths: list[list[str] | None] = []

        def capture(
            config: dict,
            _format: str,
            *,
            wrap: bool = True,
            below: list[str] | None = None,
            diagnostic_sink: object | None = None,
            withhold_values: bool = False,
        ) -> str:
            rendered.append(config)
            paths.append(below)
            return "rendered"

        monkeypatch.setattr("junoscfg.convert.from_dict", capture)

        assert (
            pipeline(
                _PATH_FILTER_SOURCE,
                from_format="json",
                to_format="json",
                validate=False,
                path="system",
            )
            == "rendered"
        )
        assert rendered[-1] == {
            "system": {"host-name": "r1", "syslog": {"file": [{"name": "messages"}]}}
        }

        assert (
            pipeline(
                _PATH_FILTER_SOURCE,
                from_format="json",
                to_format="json",
                validate=False,
                path="system.syslog",
                relative=True,
            )
            == "rendered"
        )
        assert rendered[-1] == {"system": {"syslog": {"file": [{"name": "messages"}]}}}
        assert paths[-1] == ["system", "syslog"]

        assert (
            pipeline(
                _PATH_FILTER_SOURCE,
                from_format="json",
                to_format="json",
                validate=False,
                path="missing",
            )
            == ""
        )
        assert len(rendered) == 2

    @pytest.mark.parametrize("path", sorted(_UNDER), ids=sorted(_UNDER))
    @pytest.mark.parametrize("to_format", _WRITERS, ids=_WRITER_IDS)
    def test_a_path_keeps_only_its_subtree(self, path: str, to_format: Format) -> None:
        """What lies outside the path, `interfaces` and siblings alike, is not written."""
        result = convert_config(
            _PATH_FILTER_SOURCE, from_format=Format.JSON, to_format=to_format, path=path
        )
        assert read_ir(result, to_format) == _UNDER[path]

    @pytest.mark.parametrize("path", sorted(_UNDER), ids=sorted(_UNDER))
    @pytest.mark.parametrize("to_format", _WRITERS, ids=_WRITER_IDS)
    def test_relative_output_is_the_subtree_without_the_path(
        self, path: str, to_format: Format
    ) -> None:
        """Put back under the path, the relative output reads as the absolute one."""
        result = convert_config(
            _PATH_FILTER_SOURCE,
            from_format=Format.JSON,
            to_format=to_format,
            path=path,
            relative=True,
        )
        assert _put_back(result, to_format, path) == _UNDER[path]

    @pytest.mark.parametrize(
        ("to_format", "expected"),
        [
            (Format.JSON, '"r1"\n'),
            (Format.YAML, "r1\n...\n"),
            (Format.YAML_NEW, "r1\n...\n"),
            (Format.SET, "set r1\n"),
            (Format.STRUCTURED, "r1;\n"),
        ],
    )
    def test_relative_leaf_preserves_output(self, to_format: Format, expected: str) -> None:
        result = convert_config(
            _PATH_FILTER_SOURCE,
            from_format=Format.JSON,
            to_format=to_format,
            path="system.host-name",
            relative=True,
            validate=False,
        )
        assert result == expected

    @pytest.mark.parametrize("to_format", _WRITERS, ids=_WRITER_IDS)
    def test_a_path_not_in_the_configuration_gives_no_output(self, to_format: Format) -> None:
        result = convert_config(
            _PATH_FILTER_SOURCE,
            from_format=Format.JSON,
            to_format=to_format,
            path="nonexistent",
        )
        assert result == ""

    @pytest.mark.parametrize(
        "path",
        [
            "system",
            "system.services",
            "system.services.ssh",
            "system.services.netconf",
            "system.services.netconf.ssh",
            "system.syslog",
            "system.syslog.host",
        ],
    )
    def test_a_relative_selection_is_the_bare_subtree(self, path: str) -> None:
        """Relative yaml-new output is the JSON writer's bare object: a selected
        presence flag, an empty container (`{}`) and a selected list included
        (spec conversion/junos-json-yaml; Test/Challenge B7)."""
        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "services": {"ssh": True, "netconf": {"ssh": {}}},
                        "syslog": {"host": [{"name": "198.51.100.9", "any": {}}]},
                    }
                }
            }
        )

        def selected(fmt: Format) -> str:
            return convert_config(
                source, from_format=Format.JSON, to_format=fmt, path=path, relative=True
            )

        assert yaml.safe_load(selected(Format.YAML_NEW)) == json.loads(selected(Format.JSON))

    @pytest.mark.parametrize("to_format", _OBJECT_WRITERS, ids=_OBJECT_WRITER_IDS)
    @pytest.mark.parametrize(
        "path",
        [
            "system",
            "system.syslog",
            "system.syslog.host",
            "system.services.ssh",
            "system.services.telnet",
            "system.services.netconf.ssh",
        ],
        ids=["a-mapping", "a-mapping-holding-a-list", "a-list", "true", "a-list-of-true", "empty"],
    )
    def test_a_relative_selection_is_spelled_as_absolute_output_spells_it(
        self, path: str, to_format: Format
    ) -> None:
        """Relative output spells presence flags and entry key order as absolute
        output does at the path: `{}` and `true` flags are `[null]` and `name` leads
        a list entry, in a selected list and as the selection itself, while an
        annotation's `true` stays a boolean (spec conversion/path-filtering; owner
        ruling on PO-1, yaml-new-format review B7; Test/Challenge findings 4, 5)."""
        relative, absolute = _relative_and_absolute(_SELECTED_SOURCE, to_format, path)
        assert json.dumps(relative) == json.dumps(absolute)

    @pytest.mark.parametrize("to_format", _OBJECT_WRITERS, ids=_OBJECT_WRITER_IDS)
    def test_an_annotation_in_a_selected_list_stays_boolean(self, to_format: Format) -> None:
        """`[null]` is a flag's spelling, never an annotation's: `inactive: true`
        turned into `[null]` would drop the deactivation (Test/Challenge finding 4)."""
        relative, _ = _relative_and_absolute(_SELECTED_SOURCE, to_format, "system.syslog.host")
        assert relative[2]["@"] == {"inactive": True}
        assert relative[2]["@explicit-priority"] == {"inactive": True}
        assert relative[2]["explicit-priority"] == [None]

    @pytest.mark.parametrize("to_format", _OBJECT_WRITERS, ids=_OBJECT_WRITER_IDS)
    def test_the_scenarios_are_written_as_specified(self, to_format: Format) -> None:
        """The literal outputs of the path-filtering scenarios (Test/Challenge finding 7)."""
        relative, _ = _relative_and_absolute(_SELECTED_SOURCE, to_format, "system.syslog.host")
        assert relative[0] == {"name": "198.51.100.9", "explicit-priority": [None]}
        empty, _ = _relative_and_absolute(
            _SELECTED_SOURCE, to_format, "system.services.netconf.ssh"
        )
        assert empty == [None]

    @pytest.mark.parametrize("to_format", _OBJECT_WRITERS, ids=_OBJECT_WRITER_IDS)
    def test_a_selected_group_list_from_set_input(self, to_format: Format) -> None:
        """The set reader's `{}` flags and `junoscfg:unplaced` `true` inside a selected
        `groups.group` are written as absolute output writes `groups` (Test/Challenge
        finding 6)."""
        source = (
            "set groups SAMPLE-GROUP system services ssh\n"
            "set groups SAMPLE-GROUP apply-macro 12345 XXX XXXX XXX\n"
        )
        relative, absolute = _relative_and_absolute(
            source, to_format, "groups.group", from_format=Format.SET, at="groups"
        )
        assert json.dumps(relative) == json.dumps(absolute)

    @pytest.mark.parametrize("to_format", _OBJECT_WRITERS, ids=_OBJECT_WRITER_IDS)
    @pytest.mark.parametrize(
        ("source", "path", "from_format"),
        [
            (_SELECTED_SOURCE, "system.syslog.host", Format.JSON),
            (
                "configuration:\n  system:\n    login:\n      user:\n      - name: admin\n"
                "        class: [super-user]\n",
                "system.login.user",
                Format.YAML,
            ),
            (
                '{"configuration": {"system": {"@": {"inactive": true}, "host-name": "r1"}}}',
                "system.@",
                Format.JSON,
            ),
        ],
        ids=["flags", "coercion", "annotation"],
    )
    def test_an_anonymized_selection_is_spelled_alike(
        self, to_format: Format, source: str, path: str, from_format: Format
    ) -> None:
        """Anonymizing changes values, not spellings (Test/Challenge finding 9;
        relative-selections TC7)."""
        anonymize = AnonymizeConfig(ips=True)
        relative, absolute = _relative_and_absolute(
            source, to_format, path, from_format=from_format, anon_config=anonymize
        )
        assert json.dumps(relative) == json.dumps(absolute)

    def test_an_anonymized_list_selection_in_set(self) -> None:
        """Anonymized, a selected list in set output is still its statements
        without the path (relative-selections TC7)."""
        source = "set interfaces ge-0/0/0 unit 0 family inet address 203.0.114.1/24\n"

        def written(relative: bool) -> str:
            return convert_config(
                source,
                from_format=Format.SET,
                to_format=Format.SET,
                path="interfaces.interface",
                relative=relative,
                anon_config=AnonymizeConfig(ips=True, salt="s"),
            )

        assert written(True) == written(False).replace("set interfaces ", "set ", 1)

    @pytest.mark.parametrize(
        ("to_format", "relative", "absolute"),
        [
            (Format.JSON, "null\n", None),
            (Format.YAML, "null\n...\n", None),
            (Format.YAML_NEW, "null\n...\n", None),
            (Format.SET, "set\n", "set system services netconf ssh\n"),
            (Format.STRUCTURED, "", "system {\n    services {\n        netconf ssh;\n    }\n}\n"),
        ],
        ids=["json", "yaml", "yaml-new", "set", "structured"],
    )
    def test_a_path_to_null_selects_it(
        self, to_format: Format, relative: str, absolute: str | None
    ) -> None:
        """A YAML `ssh:` is null: the path selects it relative too, where relative
        output wrote nothing; only a missing key writes nothing (PO-1 (c))."""
        source = "configuration:\n  system:\n    services:\n      netconf:\n        ssh:\n"

        def written(is_relative: bool) -> str:
            return convert_config(
                source,
                from_format=Format.YAML,
                to_format=to_format,
                path="system.services.netconf.ssh",
                relative=is_relative,
                validate=False,
            )

        assert written(True) == relative
        if absolute is None:
            load = json.loads if to_format is Format.JSON else yaml.safe_load
            document = load(written(False))
            assert document == {
                "configuration": {"system": {"services": {"netconf": {"ssh": None}}}}
            }
        else:
            assert written(False) == absolute

    @pytest.mark.parametrize(
        ("source", "path", "relative", "expected"),
        [
            (
                "set class-of-service classifiers ieee-802.1 C1 import default\n",
                "class-of-service.classifiers.ieee-802.1",
                False,
                "set class-of-service classifiers ieee-802.1 C1 import default\n",
            ),
            (
                "set class-of-service classifiers ieee-802.1 C1 import default\n",
                "class-of-service.classifiers.ieee-802.1",
                True,
                "set C1 import default\n",
            ),
            (
                "set routing-options dynamic-tunnels forwarding-rib inet.0 inet-import POL1\n",
                "routing-options.dynamic-tunnels.forwarding-rib.inet.0.inet-import",
                True,
                "set POL1\n",
            ),
        ],
        ids=["last-step-absolute", "last-step-relative", "mid-path"],
    )
    def test_a_key_holding_a_dot_is_selected(
        self, source: str, path: str, relative: bool, expected: str
    ) -> None:
        """A path is split at its dots and matched against the keys present, the
        exact key first: `ieee-802.1` and `inet.0` are selected with no new
        syntax, at the end of a path or within it (PO-1 (e))."""
        assert (
            convert_config(
                source, from_format=Format.SET, to_format=Format.SET, path=path, relative=relative
            )
            == expected
        )

    @pytest.mark.parametrize(
        ("path", "expected"),
        [("system.a.b", "exact"), ("system.a", {"b": "exact"}), ("system.c.d", "dotted")],
    )
    def test_the_exact_key_wins_over_a_dotted_one(self, path: str, expected: Any) -> None:
        """Only a path the exact keys cannot finish is matched by joining steps,
        so no path that selected a value before selects another; a dotted key
        beside a shorter key that does not lead on is still reached."""
        both = json.dumps(
            {
                "configuration": {
                    "system": {"a": {"b": "exact"}, "a.b": "dotted", "c": {"x": 1}, "c.d": "dotted"}
                }
            }
        )
        written = convert_config(
            both,
            from_format=Format.JSON,
            to_format=Format.JSON,
            path=path,
            relative=True,
            validate=False,
        )
        assert json.loads(written) == expected

    def test_a_path_through_a_list_or_a_leaf_selects_nothing(self) -> None:
        """A path addresses mapping keys only: one that steps into a list or a
        leaf names no key, and writes nothing, as at base."""
        source = "set system syslog host 198.51.100.9 any any\nset system host-name r1\n"
        for path in ("system.syslog.host.name", "system.host-name.r1"):
            assert (
                convert_config(source, from_format=Format.SET, to_format=Format.JSON, path=path)
                == ""
            )

    def test_the_kept_statements_key_writes_its_statements(self) -> None:
        """`junoscfg:unplaced` holds kept statements and is written as no word:
        selected, its statements are written without the path, as at base."""
        source = "set system no-such-statement 1\nset system host-name r1\n"

        def written(to_format: Format) -> str:
            return convert_config(
                source,
                from_format=Format.SET,
                to_format=to_format,
                path="system.junoscfg:unplaced",
                relative=True,
                validate=False,
            )

        assert written(Format.SET) == "set no-such-statement 1\n"
        assert written(Format.STRUCTURED) == "no-such-statement 1;\n"

    @pytest.mark.parametrize("to_format", _OBJECT_WRITERS, ids=_OBJECT_WRITER_IDS)
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("system.login", {"user": [{"name": "admin", "class": "super-user"}]}),
            ("system.login.user", [{"name": "admin", "class": "super-user"}]),
            ("system.host-name", "r1"),
        ],
        ids=["a-mapping", "a-list", "a-leaf"],
    )
    def test_a_relative_selection_keeps_its_schema_context(
        self, to_format: Format, path: str, expected: Any
    ) -> None:
        """A single leaf a `yaml` file gave as a list is coerced in a selected
        mapping, list or leaf, as the absolute output coerces it (PO-1 (a))."""
        source = (
            "configuration:\n  system:\n    host-name: [r1]\n    login:\n      user:\n"
            "      - name: admin\n        class: [super-user]\n"
        )
        relative, absolute = _relative_and_absolute(
            source, to_format, path, from_format=Format.YAML
        )
        assert relative == absolute == expected

    @pytest.mark.parametrize(
        ("source", "path", "to_format", "expected"),
        [
            (
                "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n",
                "interfaces",
                Format.SET,
                "set ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n",
            ),
            (
                "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n",
                "interfaces",
                Format.STRUCTURED,
                "ge-0/0/0 {\n    unit 0 {\n        family inet {\n"
                "            address 10.0.0.1/24;\n        }\n    }\n}\n",
            ),
            (
                "set interfaces ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
                "set interfaces ge-0/0/1 description uplink\n",
                "interfaces.interface",
                Format.SET,
                "set ge-0/0/0 unit 0 family inet address 10.0.0.1/24\n"
                "set ge-0/0/1 description uplink\n",
            ),
            (
                "set routing-options dynamic-tunnels DT1 source-address 10.255.0.1\n"
                "set routing-options dynamic-tunnels DT1 gre\n",
                "routing-options.dynamic-tunnels.dynamic-tunnel",
                Format.STRUCTURED,
                "DT1 {\n    source-address 10.255.0.1;\n    gre;\n}\n",
            ),
            (
                "set groups G1 system host-name r2\nset groups G1 system services ssh\n",
                "groups.group",
                Format.SET,
                "set G1 system host-name r2\nset G1 system services ssh\n",
            ),
            (
                "set groups G1 system host-name r2\nset groups G1 system services ssh\n",
                "groups.group",
                Format.STRUCTURED,
                "G1 {\n    system {\n        host-name r2;\n        services ssh;\n    }\n}\n",
            ),
        ],
        ids=[
            "interfaces-set",
            "interfaces-structured",
            "interface-list-set",
            "dynamic-tunnel-list-structured",
            "group-list-set",
            "group-list-structured",
        ],
    )
    def test_a_list_name_the_schema_hides_is_not_written(
        self, source: str, path: str, to_format: Format, expected: str
    ) -> None:
        """Set and structured output never print a list name the schema hides,
        relative as absolute: `set interface ge-0/0/0` loads nowhere under
        `edit interfaces` (PO-1 (a), measured on the device corpus)."""
        assert (
            convert_config(
                source, from_format=Format.SET, to_format=to_format, path=path, relative=True
            )
            == expected
        )

    def test_an_entry_named_like_a_hidden_list_keeps_its_name(self) -> None:
        """The words a path is written as come from the schema, not from the
        statements: an entry named `interface` under the hidden `interface`
        list is written with its name."""
        source = json.dumps(
            {
                "configuration": {
                    "interfaces": {"interface": [{"name": "interface", "description": "x"}]}
                }
            }
        )
        written = convert_config(
            source,
            from_format=Format.JSON,
            to_format=Format.SET,
            path="interfaces.interface",
            relative=True,
            validate=False,
        )
        assert written == "set interface description x\n"

    @pytest.mark.parametrize("to_format", _OBJECT_WRITERS, ids=_OBJECT_WRITER_IDS)
    def test_a_selected_groups_is_the_list_of_groups(self, to_format: Format) -> None:
        """`groups` from set input is `{"group": [...]}` in the IR and the list
        of groups in the Junos JSON object; selected, it is the list."""
        source = "set groups G1 system host-name r2\n"
        relative, absolute = _relative_and_absolute(
            source, to_format, "groups", from_format=Format.SET
        )
        assert relative == absolute == [{"name": "G1", "system": {"host-name": "r2"}}]

    @pytest.mark.parametrize(
        "to_format", [Format.SET, Format.STRUCTURED], ids=["set", "structured"]
    )
    @pytest.mark.parametrize(
        ("path", "list_word", "parents"),
        [
            ("system.login.user", "user", ["system", "login"]),
            ("system.syslog.host", "host", ["system", "syslog"]),
        ],
    )
    def test_a_selected_list_writes_its_statements(
        self, path: str, list_word: str, parents: list[str], to_format: Format
    ) -> None:
        """A selected list writes its entries' statements without the path, in
        set and structured output, never a Python repr or nothing (PO-1 (b));
        put back under the path they read as the absolute output."""
        source = (
            "set system login user admin class super-user\n"
            "set system syslog host 198.51.100.9 explicit-priority\n"
            "set system syslog host 198.51.100.9 any any\n"
            "set system syslog host 198.51.100.10 any any\n"
        )

        def written(to_format: Format, is_relative: bool) -> str:
            return convert_config(
                source, from_format=Format.SET, to_format=to_format, path=path, relative=is_relative
            )

        if to_format is Format.SET:
            prefix = " ".join([*parents, list_word])
            absolute = written(Format.SET, False)
            expected = "".join(
                line.replace(f"set {prefix} ", "set ", 1) + "\n" for line in absolute.splitlines()
            )
            assert written(Format.SET, True) == expected
            return
        relative = written(Format.STRUCTURED, True)
        assert relative and "[" not in relative
        entries = "".join(
            f"{list_word} {line}\n" if line and not line.startswith((" ", "}")) else line + "\n"
            for line in relative.splitlines()
        )
        for word in reversed(parents):
            entries = (
                f"{word} {{\n" + "".join(f"    {line}\n" for line in entries.splitlines()) + "}\n"
            )
        assert read_ir(entries, Format.STRUCTURED) == read_ir(
            written(Format.STRUCTURED, False), Format.STRUCTURED
        )

    @pytest.mark.parametrize("to_format", _OBJECT_WRITERS, ids=_OBJECT_WRITER_IDS)
    @pytest.mark.parametrize("path", ["system.@", "system.@host-name"])
    def test_an_annotation_selection_keeps_its_booleans(self, to_format: Format, path: str) -> None:
        """An annotation's `true` is a boolean, not a presence flag: selected, it
        is written as the absolute output holds it (PO-1 (d))."""
        source = json.dumps(
            {
                "configuration": {
                    "system": {
                        "@": {"inactive": True},
                        "host-name": "r1",
                        "@host-name": {"inactive": True},
                    }
                }
            }
        )
        relative, absolute = _relative_and_absolute(source, to_format, path)
        assert relative == absolute == {"inactive": True}

    def test_an_annotation_selection_in_set_and_structured(self) -> None:
        """The tag on the selected statement itself has no statement left to
        carry it: set writes the bare command (put back under the path it is
        `deactivate system`), structured writes nothing and says so in a note."""
        source = "set system host-name r1\ndeactivate system\n"

        def written(to_format: Format) -> Any:
            return convert_config_result(
                source, from_format=Format.SET, to_format=to_format, path="system.@", relative=True
            )

        assert written(Format.SET).output == "set\ndeactivate\n"
        structured = written(Format.STRUCTURED)
        assert structured.output == ""
        assert any(
            "tag(s) of the selected statement itself" in d.message for d in structured.diagnostics
        )

    def test_relative_without_path_raises(self) -> None:
        with pytest.raises(ValueError, match="relative.*requires.*path"):
            convert_config(
                _PATH_FILTER_SOURCE,
                from_format=Format.JSON,
                to_format=Format.SET,
                relative=True,
            )


class TestValidateConfig:
    """The unified validate_config() door accepts and rejects through every format.

    Validation behaviour, kept here until the validation tests take it in.
    """

    def test_validate_json_valid(self, artifacts_dir: str) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = validate_config(source, format="json", artifacts_dir=artifacts_dir)
        assert result.valid is True

    def test_validate_set_valid(self, artifacts_dir: str) -> None:
        source = "set system host-name r1"
        result = validate_config(source, format="set", artifacts_dir=artifacts_dir)
        assert result.valid is True

    def test_validate_json_invalid(self, artifacts_dir: str) -> None:
        source = '{"configuration": {"bogus-top-level": {"x": "y"}}}'
        result = validate_config(source, format="json", artifacts_dir=artifacts_dir)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_format_enum(self, artifacts_dir: str) -> None:
        source = '{"configuration": {"system": {"host-name": "r1"}}}'
        result = validate_config(source, format=Format.JSON, artifacts_dir=artifacts_dir)
        assert result.valid is True

    def test_a_yaml_new_shared_block_and_deep_document(self, artifacts_dir: str) -> None:
        """The public door: a shared block is judged written out, however it is
        reused; a value past 64 levels is an invalid result naming its path
        (owner rulings 2026-10-15 on SC-2 and SC-A)."""
        for shared, written_out in (
            (SHARED_BLOCK, SHARED_BLOCK_WRITTEN_OUT),
            (ANCHORED_BESIDE, ANCHORED_BESIDE_WRITTEN_OUT),
        ):
            assert validate_config(
                shared, format=Format.YAML_NEW, artifacts_dir=artifacts_dir
            ) == validate_config(written_out, format=Format.YAML_NEW, artifacts_dir=artifacts_dir)
        deep = validate_config(nested_yaml(62), format=Format.YAML_NEW, artifacts_dir=artifacts_dir)
        assert deep.valid is False
        assert [(e.message, e.path) for e in deep.errors] == [
            ("YAML value is nested deeper than 64 levels", "configuration.system.x" + ".0" * 62)
        ]
        cycle = validate_config(CYCLE, format=Format.YAML_NEW, artifacts_dir=artifacts_dir)
        assert [(e.message, e.path) for e in cycle.errors] == [
            ("YAML cycle has no JSON spelling", "configuration.system.x")
        ]

    def test_junos_yaml_is_judged_by_the_json_schema(self, artifacts_dir: str) -> None:
        """An Ansible meta key: the YAML schema allows it, JSON's does not, and
        yaml-new is the JSON object (spec validation/junos-json-yaml)."""
        source = "configuration:\n  system:\n    host-name: r1\n    _ansible_host: x\n"
        as_json = json.dumps(yaml.safe_load(source))
        result = validate_config(source, format=Format.YAML_NEW, artifacts_dir=artifacts_dir)
        assert result.valid is False
        assert (
            result.errors
            == validate_config(as_json, format="json", artifacts_dir=artifacts_dir).errors
        )
        assert validate_config(source, format="yaml-new", artifacts_dir=artifacts_dir) == result
        assert validate_config(source, format="yaml", artifacts_dir=artifacts_dir).valid is True

    def test_validate_auto_detect_set(self, artifacts_dir: str) -> None:
        source = "set system host-name r1"
        result = validate_config(source, format=None, artifacts_dir=artifacts_dir)
        assert result.valid is True

    def test_validate_auto_detect_structured(self, artifacts_dir: str) -> None:
        # Structured validation reads the structure tree for the conversion
        # walk that splits curly statements (change structured-one-line-blocks).
        write_minimal_tree(artifacts_dir)
        source = "system {\n    host-name r1;\n}"
        result = validate_config(source, format=None, artifacts_dir=artifacts_dir)
        assert result.valid is True


class TestFieldValidationErrorExport:
    """FieldValidationError is accessible from the public API."""

    def test_importable_from_top_level(self) -> None:
        assert FieldValidationError is not None
        assert issubclass(FieldValidationError, Exception)


class TestJsonNameFirst:
    """JSON output must put 'name' first in every named-list entry."""

    def test_yaml_with_uid_before_name(self) -> None:
        source = (
            "configuration:\n"
            "  system:\n"
            "    login:\n"
            "      user:\n"
            "        - uid: 2000\n"
            "          class: operator\n"
            "          name: john\n"
        )
        result = convert_config(source, from_format=Format.YAML, to_format=Format.JSON)
        parsed = json.loads(result)
        user = parsed["configuration"]["system"]["login"]["user"][0]
        assert list(user.keys())[0] == "name", "name must be first key in user list entry"

    def test_yaml_name_already_first_unchanged(self) -> None:
        source = (
            "configuration:\n"
            "  interfaces:\n"
            "    interface:\n"
            "      - name: ge-0/0/0\n"
            "        description: uplink\n"
        )
        result = convert_config(source, from_format=Format.YAML, to_format=Format.JSON)
        parsed = json.loads(result)
        iface = parsed["configuration"]["interfaces"]["interface"][0]
        assert list(iface.keys())[0] == "name"
        assert iface["name"] == "ge-0/0/0"

    def test_at_key_before_name_preserved(self) -> None:
        source = json.dumps(
            {
                "configuration": {
                    "interfaces": {
                        "interface": [
                            {
                                "description": "uplink",
                                "@": {"inactive": True},
                                "name": "ge-0/0/0",
                            }
                        ]
                    }
                }
            }
        )
        result = convert_config(source, from_format=Format.JSON, to_format=Format.JSON)
        parsed = json.loads(result)
        iface = parsed["configuration"]["interfaces"]["interface"][0]
        keys = list(iface.keys())
        at_idx = keys.index("@") if "@" in keys else -1
        name_idx = keys.index("name")
        assert name_idx == 0 or (at_idx != -1 and at_idx < name_idx), (
            "'name' must be first, or '@' must precede it"
        )


class TestUserClassSingle:
    """system.login.user.class must be a scalar string, not an array."""

    def test_set_user_class_scalar(self) -> None:
        source = "set system login user john class operator"
        result = convert_config(source, from_format=Format.SET, to_format=Format.JSON)
        parsed = json.loads(result)
        user = parsed["configuration"]["system"]["login"]["user"][0]
        assert user["name"] == "john"
        assert user["class"] == "operator", f"class must be a scalar string, got {user['class']!r}"
        assert not isinstance(user["class"], list)

    def test_yaml_user_class_roundtrip(self) -> None:
        source = (
            "configuration:\n"
            "  system:\n"
            "    login:\n"
            "      user:\n"
            "        - name: john\n"
            "          class: operator\n"
        )
        result = convert_config(source, from_format=Format.YAML, to_format=Format.JSON)
        parsed = json.loads(result)
        user = parsed["configuration"]["system"]["login"]["user"][0]
        assert user["class"] == "operator"
        assert not isinstance(user["class"], list)

    def test_yaml_user_class_as_list_coerced(self) -> None:
        """YAML with class as a single-element list must be coerced to scalar."""
        source = (
            "configuration:\n"
            "  groups:\n"
            "    group:\n"
            "      - name: global-users\n"
            "        system:\n"
            "          login:\n"
            "            user:\n"
            "              - name: john\n"
            "                uid: '2000'\n"
            "                class:\n"
            "                  - super-user\n"
        )
        result = convert_config(source, from_format=Format.YAML, to_format=Format.JSON)
        parsed = json.loads(result)
        group = parsed["configuration"]["groups"][0]
        user = group["system"]["login"]["user"][0]
        assert user["class"] == "super-user", (
            f"single-element class list must be coerced to scalar, got {user['class']!r}"
        )
        assert not isinstance(user["class"], list)


class TestLeafListPromotion:
    """Scalar leaf-list values are promoted only for adapters that require it."""

    def test_json_scalar_leaf_list_stays_scalar_without_loading_schema(
        self, tmp_path: Path
    ) -> None:
        """JSON retains its supplied shape and has no schema-artifact dependency.

        Read with the artifacts pointed at an empty directory: any schema load
        there raises, as the YAML read beside it shows.
        """
        source = '{"configuration":{"protocols":{"evpn":{"extended-vni-list":"3001000-3001100"}}}}'
        yaml_source = (
            "configuration:\n  protocols:\n    evpn:\n      extended-vni-list: 3001000-3001100\n"
        )

        with artifacts_in(tmp_path):
            assert to_dict(source, "json")["protocols"]["evpn"]["extended-vni-list"] == (
                "3001000-3001100"
            )
            with pytest.raises(ValueError, match="No junos-structure-tree"):
                to_dict(yaml_source, "yaml")

    def test_yaml_scalar_leaf_list_promoted_to_array(self) -> None:
        """YAML scalar extended-vni-list must become a single-element JSON array."""
        source = (
            "configuration:\n"
            "  protocols:\n"
            "    evpn:\n"
            "      encapsulation: vxlan\n"
            "      extended-vni-list: 3001000-3001100\n"
        )
        result = convert_config(source, from_format=Format.YAML, to_format=Format.JSON)
        parsed = json.loads(result)
        vni = parsed["configuration"]["protocols"]["evpn"]["extended-vni-list"]
        assert vni == ["3001000-3001100"], f"leaf-list scalar must be wrapped in array, got {vni!r}"

    def test_yaml_list_leaf_list_unchanged(self) -> None:
        """YAML list extended-vni-list with multiple entries must stay as an array."""
        source = (
            "configuration:\n"
            "  protocols:\n"
            "    evpn:\n"
            "      extended-vni-list:\n"
            "        - 3001000-3001100\n"
            "        - 3002000-3002100\n"
        )
        result = convert_config(source, from_format=Format.YAML, to_format=Format.JSON)
        parsed = json.loads(result)
        vni = parsed["configuration"]["protocols"]["evpn"]["extended-vni-list"]
        assert vni == ["3001000-3001100", "3002000-3002100"]

    def test_xml_scalar_leaf_list_promoted_without_yaml_bridge(self, monkeypatch) -> None:
        """XML reaches the normalized IR without serializing through YAML."""
        import junoscfg.display

        def fail_if_called(*args, **kwargs):
            raise AssertionError("XML input must not call xml_to_yaml()")

        monkeypatch.setattr(junoscfg.display, "xml_to_yaml", fail_if_called)
        source = (
            "<configuration><protocols><evpn>"
            "<extended-vni-list>3001000-3001100</extended-vni-list>"
            "</evpn></protocols></configuration>"
        )
        result = convert_config(source, from_format=Format.XML, to_format=Format.JSON)
        parsed = json.loads(result)
        assert parsed["configuration"]["protocols"]["evpn"]["extended-vni-list"] == [
            "3001000-3001100"
        ]

    @pytest.mark.xfail(
        strict=True,
        reason="ARCH-C10 carry-forward: JSON input keeps a scalar leaf-list as supplied; "
        "change 13 (one-ir-at-reader-boundary) reads it as the list the device writes",
    )
    def test_a_nested_json_scalar_universal_leaf_list_is_a_list(self) -> None:
        """XML and YAML read a nested `apply-groups` with one group as a list
        (change universal-statements-from-tree); JSON does not yet. The device
        writes the list (`"apply-groups" : ["GR-MACRO"]`,
        tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.json.gz).
        Pinned as the open defect, not as the answer."""
        source = '{"configuration": {"system": {"apply-groups": "SAMPLE-GROUP"}}}'
        result = json.loads(convert_config(source, from_format=Format.JSON, to_format=Format.JSON))
        assert result["configuration"]["system"]["apply-groups"] == ["SAMPLE-GROUP"]


class TestApplyFlagsSpellingsAreKept:
    """Spellings of `apply-flags` other than the device's are read or reported, never lost.

    0.17.0 wrote the top level's `set apply-flags omit` as the leaf
    `"apply-flags": "omit"`, and the downstream collection's example holds the
    kept key `apply-flags replace: true` that junoscfg wrote for a BGP group
    (`examples/playbook/group_vars/routers.yml` of
    dg-i/ansible-collection-junos-config). The tree now holds `apply-flags` as
    the device's container (DEV-V2). Change universal-statements-from-tree.
    """

    _SCALAR = {
        "json-top": (Format.JSON, '{"configuration": {"apply-flags": "omit"}}'),
        "json-system": (Format.JSON, '{"configuration": {"system": {"apply-flags": "omit"}}}'),
        "yaml-top": (Format.YAML, "configuration:\n  apply-flags: omit\n"),
        "yaml-system": (Format.YAML, "configuration:\n  system:\n    apply-flags: omit\n"),
        "xml-top": (Format.XML, "<configuration><apply-flags>omit</apply-flags></configuration>"),
        "xml-system": (
            Format.XML,
            "<configuration><system><apply-flags>omit</apply-flags></system></configuration>",
        ),
    }

    @pytest.mark.parametrize("door", list(_SCALAR))
    def test_the_old_scalar_spelling_is_not_lost(self, door: str) -> None:
        """Read as the container or reported, and the set line written as it was."""
        fmt, source = self._SCALAR[door]
        result = convert_config_result(source, from_format=fmt, to_format=Format.SET)
        prefix = "set system " if door.endswith("system") else "set "
        assert result.output == f"{prefix}apply-flags omit\n"
        ir = json.loads(convert_config(source, from_format=fmt, to_format=Format.JSON))
        flags = ir["configuration"]
        if door.endswith("system"):
            flags = flags["system"]
        reported = [d for d in result.diagnostics if "could not be placed" in d.message]
        assert flags["apply-flags"] == {"omit": [None]} or len(reported) == 1, reported

    def test_the_consumers_apply_flags_spelling_is_kept(self) -> None:
        """The kept key the collection's example holds (synthetic values) is
        written back as its set line and reported, as on 0.17.0: `replace`
        itself is EVIDENCE_BLOCKED on probe P8."""
        source = (
            "configuration:\n  protocols:\n    bgp:\n      group:\n"
            "      - name: G1\n        apply-flags replace: true\n        type: internal\n"
        )
        result = convert_config_result(source, from_format=Format.YAML, to_format=Format.SET)
        assert sorted(result.output.splitlines()) == [
            "set protocols bgp group G1 apply-flags replace",
            "set protocols bgp group G1 type internal",
        ]
        reported = [d for d in result.diagnostics if "could not be placed" in d.message]
        assert len(reported) == 1, reported


class TestARecordOfKeptStatementsIsInput:
    """JSON and YAML carry a level's record of kept statements
    (`junoscfg:unplaced`), as junoscfg writes it or as anyone writes it by hand.
    The set and structured writers print its statements verbatim, so a record
    whose text would write a second line or close a block, or whose shape is
    no record, is refused where it is read, and a writer handed one by hand
    refuses it too. The messages name no statement. Test/Challenge F3 and F4,
    change kept-whole-statements."""

    _RECORD = "junoscfg:unplaced"

    @pytest.mark.parametrize(
        "statement",
        [
            "bogus\nset system root-authentication encrypted-password $9$ExAmPlEhAsH.KEY",
            "bogus; } snmp { community public",
            "bogus a;b",
            "bogus {",
            "bogus }",
            "# bogus",
            "bogus /* note */",
            'bogus "open',
            'bogus a"b',
            "bogus\ttab",
            " bogus",
            "bogus  two",
            "",
            "bogus ]",
            "bogus <[gx]e-*>",
        ],
        ids=[
            "newline",
            "brace-escape",
            "semicolon",
            "open-brace",
            "close-brace",
            "hash",
            "comment",
            "open-quote",
            "inner-quote",
            "tab",
            "leading-space",
            "double-space",
            "empty",
            "close-bracket",
            "unquoted-bracket-word",
        ],
    )
    @pytest.mark.parametrize("fmt", ["json", "yaml"])
    def test_text_no_writer_can_print_is_refused_on_read(self, statement: str, fmt: str) -> None:
        config = {"system": {"host-name": "router1", self._RECORD: {statement: [None]}}}
        source = (
            json.dumps({"configuration": config})
            if fmt == "json"
            else yaml.safe_dump({"configuration": config})
        )
        with pytest.raises(ValueError, match="not one line of words") as caught:
            to_dict(source, fmt)
        assert "bogus" not in str(caught.value)
        assert "ExAmPlE" not in str(caught.value)

    @pytest.mark.parametrize(
        "record",
        [
            "host-name",
            ["host-name"],
            7,
            {"host-name": "router1"},
            {"host-name": ["router1"]},
            {"@host-name": True},
            {},
            {"@bogus": {}},
            {"@bogus": {"inactive": False}},
        ],
        ids=[
            "string",
            "list",
            "number",
            "a-value",
            "a-list-value",
            "a-tag-not-a-mapping",
            "empty",
            "an-empty-tag",
            "a-tag-no-writer-writes",
        ],
    )
    @pytest.mark.parametrize("fmt", ["json", "yaml"])
    def test_a_record_of_the_wrong_shape_is_refused_on_read(self, record: object, fmt: str) -> None:
        """An empty record would be written as `[null]`, a tag that names no
        meta command by no writer: neither reads back (Reviewer R5)."""
        config = {"system": {self._RECORD: record}}
        source = (
            json.dumps({"configuration": config})
            if fmt == "json"
            else yaml.safe_dump({"configuration": config})
        )
        with pytest.raises(ValueError, match=self._RECORD):
            to_dict(source, fmt)

    @pytest.mark.parametrize("writer", ["set", "structured"])
    def test_a_writer_refuses_a_record_it_cannot_print(self, writer: str) -> None:
        from junoscfg.convert import from_dict

        ir = {"system": {self._RECORD: {"bogus; } snmp { community public": True}}}
        with pytest.raises(ValueError, match="not one line of words"):
            from_dict(ir, writer)

    def test_validation_reports_a_malformed_record_once(self) -> None:
        from junoscfg.convert import UNPLACED, validate_ir

        ir = {"system": {self._RECORD: {"bogus\nsecond": True, "other": "value"}}}
        errors = validate_ir({"configuration": ir}).errors
        assert len(errors) == 1
        assert errors[0].expected == UNPLACED
        assert "bogus" not in errors[0].message

    def test_set_output_writes_one_line_per_statement(self) -> None:
        """The line-count bound: every record entry is one set line, no more."""
        record = {
            'nonsense "alpha beta" gamma': [None],
            'apply-macro 12345 "KADJBF KU!H" balks XXXXX': [None],
            "host-name": [None],
            "@nonsense other": {"inactive": True},
        }
        config = {"system": {"host-name": "router1", self._RECORD: record}}
        source = json.dumps({"configuration": config})
        output = convert_config(source, from_format=Format.JSON, to_format=Format.SET)
        assert sorted(output.splitlines()) == sorted(
            [
                "set system host-name router1",
                'set system nonsense "alpha beta" gamma',
                'set system apply-macro 12345 "KADJBF KU!H" balks XXXXX',
                "set system host-name",
                "deactivate system nonsense other",
            ]
        )
        structured = convert_config(source, from_format=Format.JSON, to_format=Format.STRUCTURED)
        assert read_ir(structured, Format.STRUCTURED)["system"][self._RECORD] == {
            k: v for k, v in record.items() if not k.startswith("@")
        }


class TestUnplacedContentKeepsItsKeywords:
    """Content the tree does not place is written with every keyword it holds.

    The Group-H flag helpers fell back to tables of element names when they
    met no node: `timeout`, `limit`, `filter-name` positional, `interfaces`
    transparent over `interface`, `prefix-list-item` a hidden list key. Every
    "lost context" they covered was a universal statement below the root or
    content the tree does not have, so where they fired they dropped the
    keyword of a statement already reported as unplaced (ARCH-C08: 678
    consultations, 0 firings over 236 device conversions). The helpers read
    the node only now. Spec: schema-pipeline/universal-statements, change
    universal-statements-from-tree.
    """

    _SOURCE = json.dumps(
        {
            "configuration": {
                "bogus-container": {
                    "timeout": "5",
                    "limit": "7",
                    "filter-name": "F1",
                    "interfaces": {"interface": [{"name": "ge-0/0/0", "description": "x"}]},
                    "prefix-list-item": [{"name": "198.51.100.0/24"}],
                }
            }
        }
    )

    def test_every_keyword_is_written(self) -> None:
        output = convert_config(self._SOURCE, from_format=Format.JSON, to_format=Format.SET)
        assert sorted(output.splitlines()) == [
            "set bogus-container filter-name F1",
            "set bogus-container interfaces interface ge-0/0/0 description x",
            "set bogus-container limit 7",
            "set bogus-container prefix-list-item 198.51.100.0/24",
            "set bogus-container timeout 5",
        ]

    def test_it_is_still_reported(self) -> None:
        """A guard: keeping the keywords places nothing."""
        with pytest.raises(FieldValidationError, match="'bogus-container' could not be placed"):
            convert_config(self._SOURCE, from_format=Format.JSON, to_format=Format.SET, strict=True)


class TestTheYamlWriterDumpsTheIr:
    """`yaml` stays what it was: the IR as read, dumped as YAML, key order
    included (owner instruction 2026-10-15: `yaml` unchanged; Test/Challenge B6).
    The format matrix reads output back through the JSON writer, which would
    hide a `yaml` writer that normalized as JSON does."""

    @pytest.mark.parametrize(
        ("source", "reader"),
        [
            pytest.param(text, reader, id=f"{shape.name}-{reader.value}")
            for shape in SHAPES
            for reader, text in shape.sources.items()
        ],
    )
    def test_the_output_is_the_ir_as_read(self, source: str, reader: Format) -> None:
        written = convert_config(source, from_format=reader, to_format=Format.YAML)
        expected = {"configuration": to_dict(source, reader.value)}
        assert in_order(yaml.safe_load(written)) == in_order(expected)


class TestIrYamlReader:
    """The `yaml` reader refuses what junoscfg's own recursion cannot walk, a
    cycle and a value past 64 levels, and reads everything else as before
    (owner ruling 2026-10-15 on C5; spec conversion/junos-json-yaml)."""

    @pytest.mark.parametrize(
        ("source", "said"),
        [
            (
                "configuration: &a\n  system:\n    host-name: acme-r1\n    x: *a\n",
                "Invalid input: a YAML cycle at configuration.system.x has no JSON spelling",
            ),
            (
                "configuration:\n  system: &s\n    _meta_acme: x\n    x: [*s]\n",
                "Invalid input: a YAML cycle at configuration.system.x.0 has no JSON spelling",
            ),
            (
                nested_yaml(62),
                "Invalid input: a YAML value at configuration.system.x"
                + ".0" * 62
                + " is nested deeper than 64 levels",
            ),
            (
                alias_chain_yaml(),
                "Invalid input: a YAML value at s3"
                + ".0" * 64
                + " is nested deeper than 64 levels",
            ),
        ],
        ids=["a-cycle", "a-cycle-beside-a-meta-key", "sixty-five-deep", "an-alias-chain"],
    )
    def test_a_cycle_or_a_value_past_64_levels_is_refused(self, source: str, said: str) -> None:
        """Before its meta-key cleanup walks the document, the reader refuses
        with the yaml-new reader's wording, kind and path, never a value: a
        ValueError, where the cleanup raised RecursionError."""
        for read in (
            lambda: to_dict(source, "yaml"),
            lambda: convert_config(source, from_format=Format.YAML, to_format=Format.SET),
        ):
            with pytest.raises(ValueError) as raised:
                read()
            assert str(raised.value) == said
            assert "acme" not in str(raised.value)

    @pytest.mark.parametrize(
        "source",
        [
            "configuration:\n  system:\n    host-name: r1\n    _meta_acme: "
            + "[" * 70
            + "x"
            + "]" * 70,
            "_ansible_acme: &a\n  x: *a\nconfiguration:\n  system:\n    host-name: r1\n",
        ],
        ids=["deep-under-a-meta-key", "a-cycle-under-an-ansible-key"],
    )
    def test_a_meta_key_subtree_is_not_walked(self, source: str) -> None:
        """The cleanup drops `_ansible_*` and `_meta_*` keys without walking them,
        so the reader does not refuse what they hold (Test/Challenge SC1): the
        rule fixes junoscfg's own recursion and nothing beyond it."""
        assert convert_config(source, from_format=Format.YAML, to_format=Format.SET) == (
            "set system host-name r1\n"
        )

    def test_a_deep_sibling_of_the_configuration_is_refused(self) -> None:
        """A key beside `configuration` is walked by the cleanup, so a value past
        64 levels there is refused at its path, as in yaml-new."""
        source = (
            "facts: "
            + "[" * 70
            + "x"
            + "]" * 70
            + "\nconfiguration:\n  system:\n    host-name: r1\n"
        )
        with pytest.raises(ValueError, match="value at facts" + r"(\.0){64} is nested deeper"):
            to_dict(source, "yaml")

    @pytest.mark.parametrize(
        ("source", "said"),
        [
            (
                "configuration:\n  system: &s\n    2026-10-15: [*s]\n",
                "a YAML cycle at configuration.system.<date key>.0 has no JSON spelling",
            ),
            (
                "configuration:\n  system:\n    64496: " + "[" * 62 + "x" + "]" * 62 + "\n",
                "a YAML value at configuration.system.<int key>"
                + ".0" * 62
                + " is nested deeper than 64 levels",
            ),
        ],
        ids=["a-date-key", "an-int-key"],
    )
    def test_a_key_that_is_not_a_string_is_named_by_its_kind(self, source: str, said: str) -> None:
        """A refusal's path never holds a key's value: a key that is not a
        string is named by its kind (Reviewer R3)."""
        with pytest.raises(ValueError) as raised:
            to_dict(source, "yaml")
        assert str(raised.value) == "Invalid input: " + said
        assert "2026" not in str(raised.value) and "64496" not in str(raised.value)

    def test_a_shared_block_and_a_date_read_as_before(self) -> None:
        """Only cycles and depth are refused: a shared block reads written out,
        an unquoted date stays a date, a value 64 levels deep reads, and a
        block anchored beside the configuration reads as yaml always read it."""
        assert to_dict(SHARED_BLOCK, "yaml") == to_dict(SHARED_BLOCK_WRITTEN_OUT, "yaml")
        assert shared_containers(to_dict(SHARED_BLOCK, "yaml")) == []
        dated = to_dict("configuration:\n  system:\n    host-name: 2026-10-15\n", "yaml")
        assert dated["system"]["host-name"] == datetime.date(2026, 10, 15)
        assert to_dict(nested_yaml(61), "yaml")["system"]["x"] is not None
        assert to_dict(ANCHORED_BESIDE, "yaml") == to_dict(ANCHORED_BESIDE_WRITTEN_OUT, "yaml")


class TestJunosYamlReader:
    """yaml-new input is read as the JSON reader reads the same object
    (spec conversion/junos-json-yaml; owner default 2026-10-15: the identical
    object to Junos JSON, so none of the yaml reader's conveniences)."""

    def test_meta_keys_are_kept_as_json_keeps_them(self) -> None:
        source = "configuration:\n  system:\n    host-name: r1\n    _meta_x: y\n"
        as_json = json.dumps(yaml.safe_load(source))
        assert to_dict(source, "yaml-new") == to_dict(as_json, "json")
        assert to_dict(source, "yaml-new")["system"]["_meta_x"] == "y"
        assert "_meta_x" not in to_dict(source, "yaml")["system"]

    def test_a_scalar_leaf_list_stays_scalar_without_loading_schema(self, tmp_path: Path) -> None:
        """Read with the artifacts pointed at an empty directory, as
        `TestLeafListPromotion` reads JSON: any schema load there raises."""
        source = (
            "configuration:\n  protocols:\n    evpn:\n      extended-vni-list: 3001000-3001100\n"
        )
        with artifacts_in(tmp_path):
            ir = to_dict(source, "yaml-new")
        assert ir["protocols"]["evpn"]["extended-vni-list"] == "3001000-3001100"

    @pytest.mark.parametrize(
        ("source", "kind", "where"),
        [
            ("configuration:\n  system:\n    host-name: 2026-10-15\n", "date", "system.host-name"),
            (
                "configuration:\n  system:\n    x: 2026-10-15 10:00:00\n",
                "datetime",
                "system.x",
            ),
            ("configuration:\n  system:\n    64496: x\n", "int key", "configuration.system"),
            ("configuration:\n  system:\n    on: x\n", "bool key", "configuration.system"),
            ("configuration:\n  system:\n    ~: x\n", "null key", "configuration.system"),
            ("configuration:\n  system:\n    1.5: x\n", "float key", "configuration.system"),
            ("configuration:\n  system:\n    2026-10-15: x\n", "date key", "configuration.system"),
            ("configuration:\n  system:\n    x: !!binary YWNtZQ==\n", "bytes", "system.x"),
            ("configuration:\n  system:\n    x: !!set {acme}\n", "set", "system.x"),
            ("configuration:\n  system:\n    x: !!omap [{acme: 1}]\n", "tuple", "system.x.0"),
            ("configuration:\n  system:\n    x: !!pairs [{acme: 1}]\n", "tuple", "system.x.0"),
            (
                "configuration:\n  interfaces:\n    interface:\n    - name: ge-0/0/0\n"
                "      description: 2026-01-01\n",
                "date",
                "interfaces.interface.0.description",
            ),
            (
                "version: 2026-10-15\nconfiguration:\n  system:\n    host-name: r1\n",
                "date",
                "at version",
            ),
            ("2026-10-15\n", "date", "at the top level"),
        ],
        ids=[
            "date",
            "datetime",
            "int-key",
            "bool-key",
            "null-key",
            "float-key",
            "date-key",
            "binary",
            "set",
            "omap",
            "pairs",
            "in-a-list",
            "beside-the-configuration",
            "the-document",
        ],
    )
    def test_a_value_json_cannot_hold_is_refused(self, source: str, kind: str, where: str) -> None:
        """A YAML-only value has no JSON spelling; it is refused by its kind and
        path, never quoted, instead of failing later in a writer. The whole
        document is checked, wrappers and siblings of `configuration` too
        (Test/Challenge B3, A5). A shared block is not such a value: it is read
        written out (owner ruling on PO-2/SC-1)."""
        with pytest.raises(ValueError, match="no JSON spelling") as raised:
            to_dict(source, "yaml-new")
        message = str(raised.value)
        assert f"YAML {kind} " in message
        assert where in message
        for value in ("2026", "acme", "64496", "1.5", "on:"):
            assert value not in message

    def test_a_shared_block_is_read_written_out(self) -> None:
        """A block shared through an alias reads as the document written out, and
        the IR holds no shared object (owner ruling on PO-2/SC-1)."""
        ir = to_dict(SHARED_BLOCK, "yaml-new")
        assert ir == to_dict(SHARED_BLOCK_WRITTEN_OUT, "yaml-new")
        first, second = ir["system"]["syslog"]["host"]
        assert first["contents"] == second["contents"]
        assert first["contents"] is not second["contents"]
        assert first["contents"][0] is not second["contents"][0]

    @pytest.mark.parametrize("writer", WRITERS, ids=[w.value for w in WRITERS])
    @pytest.mark.parametrize("anonymized", [False, True], ids=["plain", "anonymized"])
    def test_a_shared_block_converts_as_written_out(self, writer: Format, anonymized: bool) -> None:
        """Every later stage sees the document written out: an anonymizer or a
        writer meeting one object twice would treat it twice or anchor it
        (Test/Challenge finding 5)."""
        anon = AnonymizeConfig(ips=True, salt="s") if anonymized else None

        def converted(source: str) -> str:
            return convert_config_result(
                source, from_format=Format.YAML_NEW, to_format=writer, anon_config=anon
            ).output

        for shared, written_out in (
            (SHARED_BLOCK, SHARED_BLOCK_WRITTEN_OUT),
            (_SHARED_PREFIXES, _SHARED_PREFIXES_WRITTEN_OUT),
        ):
            assert converted(shared) == converted(written_out)

    def test_the_ir_of_a_shared_block_shares_nothing(self) -> None:
        for source in (SHARED_BLOCK, _SHARED_PREFIXES):
            assert shared_containers(to_dict(source, "yaml-new")) == []

    @pytest.mark.parametrize(
        ("source", "written_out"),
        [
            (ANCHORED_BESIDE, ANCHORED_BESIDE_WRITTEN_OUT),
            (NESTED_ONCE, None),
            (hosts_sharing_contents(11), None),
            (alias_chain_yaml(3, 20), None),
        ],
        ids=[
            "anchored-beside-the-configuration",
            "nested-anchors",
            "eleven-hosts",
            "a-chain-to-61",
        ],
    )
    def test_a_block_the_old_bounds_refused_is_read_written_out(
        self, source: str, written_out: str | None
    ) -> None:
        """Each row was refused by the size or the parsed-depth bound; with both
        gone (owner rulings on SC-2, SC-A) it reads as written out and shares
        nothing."""
        ir = to_dict(source, "yaml-new")
        assert shared_containers(ir) == []
        if written_out is not None:
            assert ir == to_dict(written_out, "yaml-new")

    @pytest.mark.parametrize(
        ("source", "said"),
        [
            (
                "configuration: &a\n  system:\n    host-name: acme-r1\n    x: *a\n",
                "Invalid input: a YAML cycle at configuration.system.x has no JSON spelling",
            ),
            (
                nested_yaml(62),
                "Invalid input: a YAML value at configuration.system.x"
                + ".0" * 62
                + " is nested deeper than 64 levels",
            ),
            (
                nested_yaml(400),
                "Invalid input: a YAML value at configuration.system.x"
                + ".0" * 62
                + " is nested deeper than 64 levels",
            ),
            (
                alias_chain_yaml(),
                "Invalid input: a YAML value at s3"
                + ".0" * 64
                + " is nested deeper than 64 levels",
            ),
        ],
        ids=["a-cycle", "sixty-five-deep", "four-hundred-deep", "an-alias-chain"],
    )
    def test_a_cycle_or_a_value_past_64_levels_is_refused(self, source: str, said: str) -> None:
        """A cycle is refused where it is reached again, a value past 64 levels at
        its path, before any later stage walks the document: a ValueError,
        never a RecursionError. Kind and path, never a value."""
        with pytest.raises(ValueError) as raised:
            to_dict(source, "yaml-new")
        assert str(raised.value) == said
        assert "acme" not in str(raised.value)
        assert to_dict(nested_yaml(61), "yaml-new")["system"]["x"] is not None

    def test_an_empty_document_is_refused(self) -> None:
        with pytest.raises(ValueError, match="No 'configuration' key found in YAML input"):
            to_dict("", "yaml-new")

    def test_a_malformed_document_raises_the_yaml_error(self) -> None:
        with pytest.raises(yaml.YAMLError):
            to_dict("configuration:\n  system: [r1\n", "yaml-new")

    @pytest.mark.parametrize(
        ("spelled", "loaded"),
        [("on", True), ("no", False), ("010", 8), ("1:30", 90), ("'on'", "on"), ("'010'", "010")],
    )
    def test_unquoted_words_are_read_as_pyyaml_reads_them(
        self, spelled: str, loaded: object
    ) -> None:
        """PyYAML's YAML 1.1 implicit types, as `yaml` reads them: an unquoted
        `on` is a boolean, `010` the number 8 (Test/Challenge A2; documented in
        the conversion guide). The writer quotes such strings."""
        ir = to_dict(f"configuration:\n  system:\n    location: {spelled}\n", "yaml-new")
        assert ir["system"]["location"] == loaded


#: Words YAML reads as something else unless quoted, words JSON and YAML share,
#: Ansible meta keys and a schema leaf-list (Test/Challenge A3, A6).
_TRICKY = [
    "010",
    "1:30",
    ".inf",
    ".nan",
    "1_000",
    "+.5",
    "<<",
    "Yes",
    "On",
    "_meta_x",
    "_ansible_y",
    "apply-groups",
    "yes",
    "no",
    "on",
    "off",
    "null",
    "~",
    "true",
    "1",
    "0o17",
    "0x1f",
    "1e3",
    "-",
    "?",
    "2026-10-15",
    "a: b",
    "#c",
    "'q'",
    '"d"',
    "",
    " sp",
    "x\ny",
    "a\x85b",
    "c\u2028d",
    "üñí",
    "*x",
    "&y",
    "!t",
    "%p",
    "@q",
    "[1]",
    "{a}",
    "r1",
    "ge-0/0/0",
    "10.0.0.1/24",
    "3ffe:b00::1",
]


def _value(rng: random.Random, depth: int) -> object:
    """A JSON value: a string, number, flag, list or object, keys from `_TRICKY`."""
    roll = rng.random()
    if depth > 3 or roll < 0.45:
        return rng.choice([*_TRICKY, 7, 2.5, float("inf"), True, None])
    if roll < 0.6:
        return [None]
    if roll < 0.75:
        return [_value(rng, depth + 1) for _ in range(rng.randint(1, 3))]
    keys = [k for k in rng.sample(_TRICKY, rng.randint(1, 4)) if not k.startswith("@")]
    return {k: _value(rng, depth + 1) for k in keys}


#: One prefix-list item list shared by two prefix lists through an alias.
_SHARED_PREFIXES = (
    "configuration:\n"
    "  policy-options:\n"
    "    prefix-list:\n"
    "    - name: PL-A\n"
    "      prefix-list-item: &items\n"
    "      - name: 203.0.114.0/24\n"
    "      - name: 198.0.2.0/24\n"
    "    - name: PL-B\n"
    "      prefix-list-item: *items\n"
)
_SHARED_PREFIXES_WRITTEN_OUT = _SHARED_PREFIXES.replace(
    "prefix-list-item: &items\n", "prefix-list-item:\n"
).replace(
    "      prefix-list-item: *items\n",
    "      prefix-list-item:\n      - name: 203.0.114.0/24\n      - name: 198.0.2.0/24\n",
)

#: An IR whose `system` holds itself, as only a caller sharing objects builds it.
_CYCLIC_IR: dict = {"system": {}}
_CYCLIC_IR["system"]["x"] = _CYCLIC_IR["system"]


class TestJunosYamlWriter:
    """yaml-new output is the JSON writer's object in YAML (spec conversion/junos-json-yaml)."""

    @pytest.mark.parametrize("wrap", [True, False], ids=["wrapped", "bare"])
    def test_a_shared_object_is_written_out_each_time(self, wrap: bool) -> None:
        """A selection holding one object in two places is written as two copies:
        no YAML anchor or alias, which JSON has no spelling for. A bare list is
        written as given, so only the dumper can keep the alias out
        (Test/Challenge B8)."""
        shared = {"host-name": "r1"}
        ir = [{"y": shared}, {"name": "h2", "x": shared}]
        written = from_dict(ir, "yaml-new", wrap=wrap)
        assert "&" not in written and "*" not in written
        assert yaml.safe_load(written) == json.loads(from_dict(ir, "json", wrap=wrap))

    @pytest.mark.parametrize("writer", ["json", "yaml-new"])
    def test_a_shared_object_is_spelled_in_each_of_its_contexts(self, writer: str) -> None:
        """The object stage writes a shared object out before it spells it: a
        login user's one-element `class` becomes a scalar there and nowhere
        else, as for the IR written out (a copy that kept the sharing coerced
        both)."""
        user = {"name": "admin", "class": ["super-user"]}
        shared = {"system": {"login": {"user": [user]}}, "unknown-acme": {"user": [user]}}
        written_out = copy.deepcopy(shared)
        written_out["unknown-acme"]["user"] = [copy.deepcopy(user)]
        assert from_dict(shared, writer) == from_dict(written_out, writer)

    def test_a_value_json_cannot_hold_is_refused_on_write(self) -> None:
        """A date a `yaml` file held unquoted reaches the IR as a date; yaml-new
        refuses to write it rather than write what its reader refuses
        (Reviewer finding 1). The path is named, the value is not."""
        ir = {"system": {"host-name": datetime.date(2026, 10, 15)}}
        with pytest.raises(ValueError, match="no JSON spelling") as raised:
            from_dict(ir, "yaml-new")
        assert "date at configuration.system.host-name" in str(raised.value)
        assert "2026" not in str(raised.value)

    @pytest.mark.parametrize("wrap", [True, False], ids=["wrapped", "bare"])
    @pytest.mark.parametrize(
        ("ir", "said"),
        [
            (_CYCLIC_IR, "the cycle at {top}system.x has no JSON spelling"),
            (
                {"system": nested_ir(64)},
                "the value at {top}system{deep} is nested deeper than 64 levels",
            ),
            (
                {"system": nested_ir(5000)},
                "the value at {top}system{deep} is nested deeper than 64 levels",
            ),
        ],
        ids=["a-cycle", "past-64", "five-thousand-deep"],
    )
    def test_a_cycle_or_a_value_past_64_levels_is_refused_on_write(
        self, ir: dict, said: str, wrap: bool
    ) -> None:
        """A caller's IR holding a cycle or a value past 64 levels (counted from
        the document as it will be written, `configuration` included when
        wrapped) is refused before the object stage walks it: a ValueError
        naming kind and path, not a RecursionError (owner rulings on SC-A and
        the cycle). No CLI path hands the writer a shared IR: every reader
        writes each place out."""
        deep = ".a" * (63 if wrap else 64)
        with pytest.raises(ValueError) as raised:
            from_dict(ir, "yaml-new", wrap=wrap)
        expected = said.format(top="configuration." if wrap else "", deep=deep)
        assert str(raised.value) == "Cannot write yaml-new: " + expected

    @pytest.mark.parametrize("flag", [True, {}], ids=["true", "empty-container"])
    def test_a_flag_at_step_64_is_refused_where_its_null_would_sit(self, flag: object) -> None:
        """The object stage spells a flag `[null]`, one step deeper than the IR
        holds it; the writer judges the document it writes, so it never writes
        what its own reader refuses (Reviewer R2)."""
        ir = {"system": nested_ir(62, flag)}
        with pytest.raises(ValueError) as raised:
            from_dict(ir, "yaml-new")
        assert str(raised.value) == (
            "Cannot write yaml-new: the value at configuration.system"
            + ".a" * 62
            + ".0 is nested deeper than 64 levels"
        )
        assert from_dict({"system": nested_ir(61, flag)}, "yaml-new")

    def test_json_input_past_64_levels_is_refused_as_yaml_new(self) -> None:
        """Any reader's IR reaches the writer's ceiling: JSON input nesting past
        64 levels converts to JSON as before and is refused as yaml-new with its
        path; an anonymizing conversion withholds it, as for every writer
        refusal (RuntimeError)."""
        source = json.dumps({"configuration": {"system": nested_ir(65)}})
        assert convert_config(source, from_format=Format.JSON, to_format=Format.JSON)
        with pytest.raises(ValueError) as raised:
            convert_config(source, from_format=Format.JSON, to_format=Format.YAML_NEW)
        assert str(raised.value) == (
            "Cannot write yaml-new: the value at configuration.system"
            + ".a" * 63
            + " is nested deeper than 64 levels"
        )
        with pytest.raises(RuntimeError) as withheld:
            convert_config(
                source,
                from_format=Format.JSON,
                to_format=Format.YAML_NEW,
                anon_config=AnonymizeConfig(ips=True, salt="s"),
            )
        assert "system" not in str(withheld.value)

    def test_an_ir_64_levels_deep_and_any_reuse_is_written(self) -> None:
        """The deepest accepted IR, wrapped, and a block shared at several depths
        and many times, are written as JSON writes them (owner rulings on SC-2,
        SC-A)."""
        block = {"host-name": "r1"}
        for ir in (
            {"system": nested_ir(62)},
            {"a": block, "b": [block, [block] * 5], "c": {"d": {"e": block}}},
        ):
            written = from_dict(ir, "yaml-new")
            assert "&" not in written and "*" not in written
            assert yaml.safe_load(written) == json.loads(from_dict(ir, "json"))

    @pytest.mark.parametrize("mark", ["\x85", "\u2028", "\u2029"], ids=["nel", "ls", "ps"])
    def test_a_yaml_only_line_break_reads_back_as_written(self, mark: str) -> None:
        """NEL, LINE SEPARATOR and PARAGRAPH SEPARATOR are line breaks to YAML
        and characters to JSON: written escaped, they read back as written
        (Reviewer A2; `yaml` keeps PyYAML's behaviour, owner decision PO-4)."""
        ir = {"system": {"host-name": f"a{mark}b"}}
        written = from_dict(ir, "yaml-new")
        assert yaml.safe_load(written) == json.loads(from_dict(ir, "json"))
        assert to_dict(written, "yaml-new") == ir

    def test_the_device_spellings_are_written_as_json_writes_them(self) -> None:
        """`groups` in its set-reader wrapper is the list of groups, a single
        leaf given as a one-element list is the scalar, a flag `[null]`."""
        ir = {
            "groups": {"group": [{"name": "G", "system": {"host-name": "r1"}}]},
            "system": {
                "login": {"user": [{"name": "admin", "class": ["super-user"]}]},
                "services": {"ssh": {}},
            },
        }
        written = yaml.safe_load(from_dict(copy.deepcopy(ir), "yaml-new"))
        assert written == json.loads(from_dict(ir, "json"))
        config = written["configuration"]
        assert config["groups"] == [{"name": "G", "system": {"host-name": "r1"}}]
        assert config["system"]["login"]["user"][0]["class"] == "super-user"
        assert config["system"]["services"]["ssh"] == [None]

    @pytest.mark.parametrize("seed", range(40))
    def test_any_json_object_survives_junos_yaml(self, seed: int) -> None:
        """The round-trip property: json -> yaml-new -> json is json -> json, for
        values derived from the JSON value type (no Hypothesis in the toolbox;
        a seeded generator), with YAML's quoting hazards as keys and values."""
        rng = random.Random(seed)
        body = {k: _value(rng, 1) for k in rng.sample(_TRICKY, 4) if not k.startswith("@")}
        source = json.dumps({"configuration": {"system": body}})

        def convert(text: str, reader: Format, writer: Format) -> str:
            return convert_config(text, from_format=reader, to_format=writer, validate=False)

        via_yaml = convert(
            convert(source, Format.JSON, Format.YAML_NEW), Format.YAML_NEW, Format.JSON
        )
        assert via_yaml == convert(source, Format.JSON, Format.JSON)
