"""The convert_config() door, the Format enum, and what one reader or writer adds.

What holds for every (reader, writer) pair -- each conversion reads back as the
IR it was given -- is `tests/contract/test_format_matrix.py`, over the shape
catalogue; this file keeps what belongs to one door: refusals, path
selection, and the value shapes one reader or writer settles.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

import pytest
import yaml

from junoscfg import FieldValidationError, Format, convert_config, validate_config
from junoscfg.convert import pipeline, to_dict
from junoscfg.display import artifacts_dir as artifacts_in
from tests.support.artifacts import write_minimal_tree
from tests.support.shapes import read_ir

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
_WRITERS = [Format.SET, Format.STRUCTURED, Format.JSON, Format.YAML]
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


class TestPathFiltering:
    """`path=` keeps one subtree of the IR; `relative=True` writes it without the path.

    The CLI's `--path` and `--relative` pass these through
    (`tests/unit/cli/test_cli.py`); the per-format text filters are
    `tests/unit/display/test_display_filters.py`.
    """

    def test_pipeline_filters_ir_before_rendering(self, monkeypatch: pytest.MonkeyPatch) -> None:
        rendered: list[dict] = []

        def capture(
            config: dict,
            _format: str,
            *,
            wrap: bool = True,
            diagnostic_sink: object | None = None,
        ) -> str:
            rendered.append(config)
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
        assert rendered[-1] == {"file": [{"name": "messages"}]}

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
            (Format.SET, "set r1\n"),
            (Format.STRUCTURED, ""),
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
