"""Tests for the ``@`` annotation behavior documented in docs/guide/annotations.md.

The matrix tests lock in the documented per-conversion behavior. The
``TestKnownBugs`` class carries strict xfail regressions for confirmed bugs
(B1-B6); each marker is removed in the phase that fixes the bug.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from junoscfg import Format, convert_config
from junoscfg.convert import to_dict


def _json(config: dict[str, Any]) -> str:
    return json.dumps({"configuration": config})


def _to_set(source: str, from_format: Format = Format.JSON) -> str:
    return convert_config(source, from_format=from_format, to_format=Format.SET)


def _to_structured(source: str, from_format: Format = Format.JSON) -> str:
    return convert_config(source, from_format=from_format, to_format=Format.STRUCTURED)


class TestContainerAnnotationsToSet:
    """Container ``"@"`` annotations from JSON input rendered as set meta commands."""

    @pytest.mark.parametrize(
        ("attrs", "expected"),
        [
            ({"inactive": True}, "deactivate system"),
            ({"active": "active"}, "activate system"),
            ({"protect": "protect"}, "protect system"),
        ],
    )
    def test_meta_command_emitted(self, attrs: dict[str, Any], expected: str) -> None:
        source = _json({"system": {"@": attrs, "host-name": "r1", "location": "dc-a"}})
        lines = _to_set(source).strip().splitlines()
        assert expected in lines
        assert "set system host-name r1" in lines
        assert "set system location dc-a" in lines

    def test_replace_dropped_in_set_output(self) -> None:
        """Display-set syntax has no replace command; the annotation is dropped."""
        source = _json({"system": {"@": {"operation": "replace"}, "host-name": "r1"}})
        result = _to_set(source)
        assert "replace" not in result
        assert "set system host-name r1" in result


class TestContainerAnnotationsToStructured:
    """Container ``"@"`` annotations from JSON input rendered as structured prefixes."""

    @pytest.mark.parametrize(
        ("attrs", "prefix"),
        [
            ({"inactive": True}, "inactive: system {"),
            ({"protect": "protect"}, "protect: system {"),
            ({"operation": "replace"}, "replace: system {"),
        ],
    )
    def test_prefix_rendered(self, attrs: dict[str, Any], prefix: str) -> None:
        source = _json({"system": {"@": attrs, "host-name": "r1", "location": "dc-a"}})
        result = _to_structured(source)
        assert prefix in result
        assert "host-name r1;" in result

    def test_active_has_no_structured_marker(self) -> None:
        """Active is the default state; structured format carries no marker."""
        annotated = _json({"system": {"@": {"active": "active"}, "host-name": "r1"}})
        plain = _json({"system": {"host-name": "r1"}})
        assert _to_structured(annotated) == _to_structured(plain)


class TestLeafAnnotations:
    """Sibling ``"@leaf-name"`` annotations apply to a single leaf."""

    def test_inactive_leaf_to_set(self) -> None:
        source = _json({"system": {"host-name": "r1", "@host-name": {"inactive": True}}})
        lines = _to_set(source).strip().splitlines()
        set_idx = lines.index("set system host-name r1")
        deact_idx = lines.index("deactivate system host-name")
        assert deact_idx == set_idx + 1

    def test_inactive_leaf_to_structured(self) -> None:
        source = _json(
            {
                "system": {
                    "host-name": "r1",
                    "@host-name": {"inactive": True},
                    "location": "dc-a",
                }
            }
        )
        assert "inactive: host-name r1;" in _to_structured(source)


class TestYamlAnnotations:
    """YAML input/output parity for annotations."""

    def test_yaml_input_parity(self) -> None:
        source = "configuration:\n  system:\n    '@':\n      inactive: true\n    host-name: r1\n"
        result = _to_set(source, from_format=Format.YAML)
        assert "deactivate system" in result.strip().splitlines()

    def test_yaml_output_quotes_annotation_keys(self) -> None:
        source = _json(
            {
                "system": {
                    "@": {"inactive": True},
                    "host-name": "r1",
                    "@host-name": {"inactive": True},
                }
            }
        )
        result = convert_config(source, from_format=Format.JSON, to_format=Format.YAML)
        assert "'@':" in result
        assert "'@host-name':" in result


class TestPassThrough:
    """Uninterpreted annotation content passes through JSON<->YAML verbatim."""

    CONFIG: dict[str, Any] = {
        "system": {
            "@": {
                "inactive": True,
                "comment": "/* managed by ansible */",
                "junos:commit-seconds": "1500000000",
                "junos:commit-user": "admin",
            },
            "host-name": "r1",
        }
    }

    def test_json_yaml_json_identity(self) -> None:
        yaml_out = convert_config(
            _json(self.CONFIG), from_format=Format.JSON, to_format=Format.YAML
        )
        json_out = convert_config(yaml_out, from_format=Format.YAML, to_format=Format.JSON)
        assert json.loads(json_out)["configuration"] == self.CONFIG

    def test_unrecognized_attrs_dropped_in_set_output(self) -> None:
        result = _to_set(_json(self.CONFIG))
        assert "junos:" not in result
        assert "managed by ansible" not in result
        assert "deactivate system" in result

    def test_unrecognized_attrs_dropped_in_structured_output(self) -> None:
        result = _to_structured(_json(self.CONFIG))
        assert "junos:" not in result
        assert "managed by ansible" not in result
        assert "inactive:" in result


class TestSetInputCanonicalSpellings:
    """Set-input meta commands produce the canonical IR annotation spellings."""

    @pytest.mark.parametrize(
        ("meta_line", "expected"),
        [
            ("deactivate system", {"inactive": True}),
            ("activate system", {"active": "active"}),
            ("protect system", {"protect": "protect"}),
            ("delete system", {"operation": "delete"}),
        ],
    )
    def test_canonical_ir(self, meta_line: str, expected: dict[str, Any]) -> None:
        ir = to_dict(f"set system host-name r1\n{meta_line}\n", "set")
        assert ir["system"]["@"] == expected


class TestStructuredInputPrefixes:
    """Conf-input operational prefixes are parsed into IR annotations."""

    def test_inactive_container_prefix(self) -> None:
        source = "system {\n    inactive: ntp {\n        server 10.0.0.1;\n    }\n}\n"
        ir = to_dict(source, "structured")
        assert ir["system"]["ntp"]["@"] == {"inactive": True}

    def test_protect_container_prefix(self) -> None:
        source = "protect: system {\n    host-name r1;\n}\n"
        ir = to_dict(source, "structured")
        assert ir["system"]["@"] == {"protect": "protect"}


class TestKnownBugs:
    """Strict xfail regressions for confirmed bugs; markers removed as fixes land."""

    def test_conf_leaf_inactive_targets_leaf(self) -> None:
        source = "system {\n    inactive: host-name r1;\n    location dc-a;\n}\n"
        lines = _to_set(source, from_format=Format.STRUCTURED).strip().splitlines()
        assert "deactivate system host-name" in lines
        assert "deactivate system" not in lines

    def test_conf_quoted_value_not_corrupted(self) -> None:
        source = (
            'interfaces {\n    ge-0/0/0 {\n        description "inactive: do not use";\n    }\n}\n'
        )
        ir = to_dict(source, "structured")
        assert ir == {
            "interfaces": {
                "interface": [{"name": "ge-0/0/0", "description": "inactive: do not use"}]
            }
        }
        result = _to_set(source, from_format=Format.STRUCTURED)
        assert 'set interfaces ge-0/0/0 description "inactive: do not use"' in result
        assert "deactivate" not in result

    def test_delete_only_node_emits_only_delete(self) -> None:
        source = _json({"system": {"ntp": {"@": {"operation": "delete"}}}})
        lines = _to_set(source).strip().splitlines()
        assert lines == ["delete system ntp"]

    def test_container_deactivate_after_content(self) -> None:
        source = _json({"system": {"@": {"inactive": True}, "host-name": "r1"}})
        lines = _to_set(source).strip().splitlines()
        assert lines.index("set system host-name r1") < lines.index("deactivate system")

    def test_container_delete_after_content(self) -> None:
        source = _json(
            {
                "system": {
                    "ntp": {
                        "@": {"operation": "delete"},
                        "server": [{"name": "10.0.0.1"}],
                    }
                }
            }
        )
        lines = _to_set(source).strip().splitlines()
        assert lines.index("set system ntp server 10.0.0.1") < lines.index("delete system ntp")

    @pytest.mark.xfail(
        reason="B4: annotation-only leaf dict triggers a spurious field-validate warning",
        strict=True,
    )
    def test_no_field_validate_warning_for_annotation_only_leaf(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        source = _json({"system": {"host-name": {"@": {"operation": "delete"}}}})
        _to_set(source)
        assert "field-validate" not in capsys.readouterr().err

    @pytest.mark.xfail(
        reason="B5: structured output renders a non-Junos delete: prefix",
        strict=True,
    )
    def test_no_delete_prefix_in_structured_output(self) -> None:
        source = _json({"system": {"ntp": {"@": {"operation": "delete"}}}})
        assert "delete:" not in _to_structured(source)

    def test_conf_replace_prefix_reaches_ir(self) -> None:
        source = "replace: system {\n    host-name r1;\n}\n"
        ir = to_dict(source, "structured")
        assert ir["system"]["@"] == {"operation": "replace"}
