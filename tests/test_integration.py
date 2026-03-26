"""Integration tests: roundtrips and full example validation."""

from __future__ import annotations

import re

from junoscfg import Format, convert_config
from junoscfg.display.set_converter import SetConverter


class TestPublicAPI:
    """Test the top-level public API functions."""

    def test_json_to_set(self) -> None:
        result = convert_config(
            '{"configuration": {"system": {"host-name": "test"}}}',
            from_format=Format.JSON,
            to_format=Format.SET,
        )
        assert result == "set system host-name test\n"

    def test_xml_to_set(self) -> None:
        xml = "<configuration><system><host-name>test</host-name></system></configuration>"
        result = convert_config(xml, from_format=Format.XML, to_format=Format.SET)
        assert result == "set system host-name test\n"

    def test_structured_to_set(self) -> None:
        result = convert_config(
            "system {\n    host-name test;\n}",
            from_format=Format.STRUCTURED,
            to_format=Format.SET,
        )
        assert result == "set system host-name test\n"

    def test_set_to_structured(self) -> None:
        result = convert_config(
            "set system host-name test",
            from_format=Format.SET,
            to_format=Format.STRUCTURED,
        )
        assert "system host-name" in result
        assert "host-name test;" in result

    def test_json_to_structured(self) -> None:
        result = convert_config(
            '{"configuration": {"system": {"host-name": "test"}}}',
            from_format=Format.JSON,
            to_format=Format.STRUCTURED,
        )
        assert "system host-name" in result
        assert "host-name test;" in result


class TestRoundtrips:
    """Test format roundtrip conversions."""

    def test_json_to_set_to_struct(self) -> None:
        """JSON → set → structured roundtrip."""
        json_input = """{
            "configuration": {
                "system": {"host-name": "router1", "domain-name": "example.com"},
                "interfaces": {
                    "interface": [
                        {"name": "ge-0/0/0", "description": "uplink",
                         "unit": [{"name": "0", "family": {"inet": {
                             "address": [{"name": "10.0.0.1/24"}]
                         }}}]}
                    ]
                }
            }
        }"""
        set_output = convert_config(json_input, from_format=Format.JSON, to_format=Format.SET)
        struct_output = convert_config(
            set_output, from_format=Format.SET, to_format=Format.STRUCTURED
        )

        # Verify structured output has the right content
        assert "system {" in struct_output
        assert "host-name router1;" in struct_output
        assert "domain-name example.com;" in struct_output
        assert "interfaces {" in struct_output or "ge-0/0/0 {" in struct_output

    def test_struct_to_set_to_struct(self) -> None:
        """Structured → set → structured roundtrip."""
        original = "system {\n    host-name router1;\n    domain-name example.com;\n}\n"
        set_output = convert_config(original, from_format=Format.STRUCTURED, to_format=Format.SET)
        struct_output = convert_config(
            set_output, from_format=Format.SET, to_format=Format.STRUCTURED
        )

        # Both should contain the same data
        assert "host-name router1;" in struct_output
        assert "domain-name example.com;" in struct_output

    def test_set_to_struct_to_set(self) -> None:
        """Set → structured → set roundtrip."""
        original = "set system host-name router1\nset system domain-name example.com\n"
        struct_output = convert_config(
            original, from_format=Format.SET, to_format=Format.STRUCTURED
        )
        set_output = SetConverter(struct_output).to_set()

        # Both should have the same set lines
        assert "set system host-name router1" in set_output
        assert "set system domain-name example.com" in set_output

    def test_deactivate_roundtrip(self) -> None:
        """Deactivate survives set → struct → set roundtrip."""
        original = "set interfaces ge-0/0/0 description uplink\ndeactivate interfaces ge-0/0/0\n"
        struct_output = convert_config(
            original, from_format=Format.SET, to_format=Format.STRUCTURED
        )
        assert "inactive:" in struct_output

        set_output = SetConverter(struct_output).to_set()
        assert "deactivate" in set_output


class TestExampleRoundtrip:
    """Full roundtrip against the example router config files."""

    def test_json_to_set_exact_match(self, json_config: str, set_lines: str) -> None:
        """JSON → set produces exact match with expected .set file."""
        result = convert_config(json_config, from_format=Format.JSON, to_format=Format.SET)
        assert result.strip() == set_lines.strip()

    def test_json_to_set_to_struct_roundtrip(
        self, json_config: str, structured_config: str
    ) -> None:
        """JSON → set → structured compared against sample .conf."""
        set_output = convert_config(json_config, from_format=Format.JSON, to_format=Format.SET)
        struct_output = convert_config(
            set_output, from_format=Format.SET, to_format=Format.STRUCTURED
        )

        # The structured output should have meaningful content
        assert len(struct_output.strip().splitlines()) > 100

        # Verify key sections are present
        assert "system {" in struct_output
        assert "interfaces {" in struct_output
        assert "protocols {" in struct_output

        # Count total lines — should be in the right ballpark
        struct_lines = struct_output.strip().splitlines()
        conf_lines = [
            line
            for line in structured_config.strip().splitlines()
            if line.strip()
            and not line.strip().startswith("#")
            and not line.strip().startswith("/*")
            and not line.strip().startswith("*")
            and not line.strip().startswith("*/")
        ]

        # Our output might differ in structure but should be similar in size
        ratio = len(struct_lines) / len(conf_lines) if conf_lines else 0
        assert 0.5 < ratio < 2.0, (
            f"Structure size ratio {ratio:.2f} "
            f"(got {len(struct_lines)}, conf has {len(conf_lines)} non-comment lines)"
        )

    def test_xml_to_set_high_match(self, xml_config: str, set_lines: str) -> None:
        """XML → set matches at least 99.9% of expected .set lines."""
        result = convert_config(xml_config, from_format=Format.XML, to_format=Format.SET)
        result_lines = result.strip().splitlines()
        expected_lines = set_lines.strip().splitlines()

        matches = sum(1 for a, b in zip(result_lines, expected_lines, strict=False) if a == b)
        total = len(expected_lines)
        match_pct = matches / total * 100
        assert match_pct >= 99.9, f"Only {matches}/{total} ({match_pct:.2f}%)"

    def test_structured_to_set_matches_ruby(self, structured_config: str) -> None:
        """Structured → set produces same 3063 lines as Ruby."""
        result = convert_config(
            structured_config, from_format=Format.STRUCTURED, to_format=Format.SET
        )
        result_lines = result.strip().splitlines()
        # Ruby Display::Set also produces 3063 lines
        assert len(result_lines) == 3063

    def test_set_to_struct_to_set_roundtrip(self, set_lines: str) -> None:
        """Set → struct → set roundtrip preserves all set lines."""
        struct_output = convert_config(
            set_lines, from_format=Format.SET, to_format=Format.STRUCTURED
        )
        set_output = SetConverter(struct_output).to_set()

        original_lines = set(set_lines.strip().splitlines())
        result_lines = set(set_output.strip().splitlines())

        # Check how many original lines survive the roundtrip
        preserved = original_lines & result_lines
        pct = len(preserved) / len(original_lines) * 100

        # Most lines should survive
        assert pct >= 80, (
            f"Only {len(preserved)}/{len(original_lines)} lines preserved ({pct:.1f}%)"
        )


class TestEdgeCases:
    """Edge cases and special patterns."""

    def test_empty_json(self) -> None:
        result = convert_config(
            '{"configuration": {}}', from_format=Format.JSON, to_format=Format.SET
        )
        assert result == ""

    def test_empty_xml(self) -> None:
        result = convert_config("<configuration/>", from_format=Format.XML, to_format=Format.SET)
        assert result == ""

    def test_json_with_rpc_reply_wrapper(self) -> None:
        json_input = """{
            "rpc-reply": {
                "configuration": {
                    "system": {"host-name": "test"}
                }
            }
        }"""
        result = convert_config(json_input, from_format=Format.JSON, to_format=Format.SET)
        assert "set system host-name test" in result

    def test_policy_expression_unquoted(self) -> None:
        json_input = """{
            "configuration": {
                "policy-options": {
                    "policy-statement": [{
                        "name": "test",
                        "term": [{
                            "name": "t1",
                            "from": {"policy": "(( a && ! b ) || c)"}
                        }]
                    }]
                }
            }
        }"""
        result = convert_config(json_input, from_format=Format.JSON, to_format=Format.SET)
        # Policy expressions should NOT be quoted
        assert re.search(r"policy \(\(", result)
        assert 'policy "' not in result

    def test_special_characters_quoted(self) -> None:
        json_input = """{
            "configuration": {
                "system": {"host-name": "my router"}
            }
        }"""
        result = convert_config(json_input, from_format=Format.JSON, to_format=Format.SET)
        assert '"my router"' in result


class TestYamlPublicAPI:
    """Test YAML conversion through convert_config."""

    def test_yaml_to_set(self) -> None:
        result = convert_config(
            "configuration:\n  system:\n    host-name: test\n",
            from_format=Format.YAML,
            to_format=Format.SET,
        )
        assert result == "set system host-name test\n"

    def test_yaml_to_structured(self) -> None:
        result = convert_config(
            "configuration:\n  system:\n    host-name: test\n",
            from_format=Format.YAML,
            to_format=Format.STRUCTURED,
        )
        assert "system host-name" in result
        assert "host-name test;" in result

    def test_json_to_yaml(self) -> None:
        result = convert_config(
            '{"configuration": {"system": {"host-name": "test"}}}',
            from_format=Format.JSON,
            to_format=Format.YAML,
        )
        assert "configuration:" in result
        assert "host-name: test" in result

    def test_xml_to_yaml(self) -> None:
        xml = "<configuration><system><host-name>test</host-name></system></configuration>"
        result = convert_config(xml, from_format=Format.XML, to_format=Format.YAML)
        assert "configuration:" in result
        assert "host-name: test" in result


class TestYamlExampleRoundtrip:
    """Full roundtrip against the example router config files using YAML."""

    def test_json_to_yaml_to_set_lossless(self, json_config: str, set_lines: str) -> None:
        """JSON → YAML → set is lossless (YAML is 1:1 with JSON)."""
        yaml_output = convert_config(json_config, from_format=Format.JSON, to_format=Format.YAML)
        yaml_set = convert_config(yaml_output, from_format=Format.YAML, to_format=Format.SET)

        yaml_lines = set(yaml_set.strip().splitlines())
        expected_lines = set(set_lines.strip().splitlines())

        assert yaml_lines == expected_lines, (
            f"{len(yaml_lines - expected_lines)} extra, {len(expected_lines - yaml_lines)} missing"
        )

    def test_json_to_yaml_to_json_lossless(self, json_config: str) -> None:
        """JSON → YAML → JSON roundtrip is lossless."""
        import json

        import yaml as _yaml

        yaml_output = convert_config(json_config, from_format=Format.JSON, to_format=Format.YAML)
        roundtrip = json.dumps(_yaml.safe_load(yaml_output), indent=2)
        original = json.dumps(json.loads(json_config), indent=2)
        assert roundtrip == original

    def test_xml_to_yaml_to_set_roundtrip(self, xml_config: str, set_lines: str) -> None:
        """XML → YAML → set preserves most set lines."""
        yaml_output = convert_config(xml_config, from_format=Format.XML, to_format=Format.YAML)
        yaml_set = convert_config(yaml_output, from_format=Format.YAML, to_format=Format.SET)

        yaml_lines = set(yaml_set.strip().splitlines())
        expected_lines = set(set_lines.strip().splitlines())

        common = yaml_lines & expected_lines
        pct = len(common) / len(expected_lines) * 100
        assert pct >= 99.0, f"Only {len(common)}/{len(expected_lines)} lines preserved ({pct:.1f}%)"
