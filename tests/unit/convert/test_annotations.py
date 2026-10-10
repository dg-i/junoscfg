"""How readers spell the ``@`` annotations of docs/guide/annotations.md.

What each writer keeps of an annotation, through every (reader, writer) pair,
is the shape catalogue (`tests/support/shapes.py`, the annotation and delete
rows) checked by `tests/contract/test_format_matrix.py`. This file keeps what
one reader or writer settles: the canonical IR spelling each input gives, the
variants it normalizes, and how YAML output quotes the keys.
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


class TestYamlAnnotations:
    """YAML output quotes annotation keys: a bare ``@`` starts no YAML scalar."""

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

    def test_replace_container_prefix(self) -> None:
        """`replace:` reaches the IR as the replace operation; it was once dropped."""
        source = "replace: system {\n    host-name r1;\n}\n"
        ir = to_dict(source, "structured")
        assert ir["system"]["@"] == {"operation": "replace"}


class TestVariantNormalization:
    """Documented variant annotation spellings are normalized at input."""

    @pytest.mark.parametrize(
        ("attrs", "canonical"),
        [
            ({"inactive": "inactive"}, {"inactive": True}),
            ({"protect": True}, {"protect": "protect"}),
            ({"active": True}, {"active": "active"}),
            ({"active": False}, {"inactive": True}),
            ({"junos-configuration-metadata:active": False}, {"inactive": True}),
            ({"junos-configuration-metadata:active": True}, {"active": "active"}),
            ({"junos-configuration-metadata:protect": True}, {"protect": "protect"}),
            ({"junos-configuration-metadata:comment": "/* x */"}, {"comment": "/* x */"}),
        ],
    )
    def test_variant_to_canonical_ir(
        self, attrs: dict[str, Any], canonical: dict[str, Any]
    ) -> None:
        source = _json({"system": {"@": attrs, "host-name": "r1"}})
        ir = to_dict(source, "json")
        assert ir["system"]["@"] == canonical

    def test_protect_false_removed(self) -> None:
        source = _json({"system": {"@": {"protect": False}, "host-name": "r1"}})
        ir = to_dict(source, "json")
        assert "@" not in ir["system"] or "protect" not in ir["system"]["@"]

    def test_variant_interpreted_in_set_output(self) -> None:
        """A device-style boolean protect now produces the protect command."""
        source = _json({"system": {"@": {"protect": True}, "host-name": "r1"}})
        assert "protect system" in _to_set(source).strip().splitlines()

    def test_leaf_variant_interpreted(self) -> None:
        source = _json({"system": {"host-name": "r1", "@host-name": {"inactive": "inactive"}}})
        assert "deactivate system host-name" in _to_set(source).strip().splitlines()

    def test_yaml_output_is_canonicalized(self) -> None:
        source = _json({"system": {"@": {"protect": True}, "host-name": "r1"}})
        result = convert_config(source, from_format=Format.JSON, to_format=Format.YAML)
        assert "protect: protect" in result
        assert "protect: true" not in result

    def test_unknown_attributes_untouched(self) -> None:
        attrs = {
            "operation": "merge",
            "junos:commit-user": "admin",
            "openconfig-metadata:protobuf-metadata": "AAAA",
        }
        source = _json({"system": {"@": dict(attrs), "host-name": "r1"}})
        ir = to_dict(source, "json")
        assert ir["system"]["@"] == attrs
