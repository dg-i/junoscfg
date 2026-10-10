"""Tests for the revert dictionary: export, import, and apply."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from junoscfg.anonymize import anonymize

if TYPE_CHECKING:
    from pathlib import Path
from junoscfg.anonymize.config import AnonymizeConfig
from junoscfg.anonymize.revert import (
    _build_reverse_map,
    apply_revert,
    export_mapping,
    load_mapping,
)


class TestExportMapping:
    def test_writes_json_file(self, tmp_path: Path) -> None:
        mapping = {"ip": {"10.0.0.1": "10.200.50.3"}}
        dest = tmp_path / "map.json"
        export_mapping(mapping, str(dest))
        assert dest.exists()
        loaded = json.loads(dest.read_text())
        assert loaded == mapping

    def test_sorted_keys(self, tmp_path: Path) -> None:
        mapping = {"ip": {"z.z.z.z": "a.a.a.a", "a.a.a.a": "z.z.z.z"}}
        dest = tmp_path / "map.json"
        export_mapping(mapping, str(dest))
        text = dest.read_text()
        # Keys should be sorted in the output
        assert text.index('"a.a.a.a"') < text.index('"z.z.z.z"')

    def test_empty_mapping(self, tmp_path: Path) -> None:
        dest = tmp_path / "map.json"
        export_mapping({}, str(dest))
        loaded = json.loads(dest.read_text())
        assert loaded == {}

    def test_multiple_rules(self, tmp_path: Path) -> None:
        mapping = {
            "ip": {"10.0.0.1": "10.200.50.3"},
            "password": {"$9$abc": "netconanRemoved0"},
            "identity": {"admin": "user_a1b2c3d4"},
        }
        dest = tmp_path / "map.json"
        export_mapping(mapping, str(dest))
        loaded = json.loads(dest.read_text())
        assert loaded == mapping


class TestLoadMapping:
    def test_round_trip(self, tmp_path: Path) -> None:
        mapping = {"ip": {"10.0.0.1": "10.200.50.3"}, "password": {"$9$x": "netconanRemoved0"}}
        dest = tmp_path / "map.json"
        export_mapping(mapping, str(dest))
        loaded = load_mapping(str(dest))
        assert loaded == mapping


class TestBuildReverseMap:
    def test_single_rule(self) -> None:
        mapping = {"ip": {"10.0.0.1": "10.200.50.3"}}
        reverse = _build_reverse_map(mapping)
        assert reverse == {"10.200.50.3": "10.0.0.1"}

    def test_multiple_rules(self) -> None:
        mapping = {
            "ip": {"10.0.0.1": "10.200.50.3"},
            "identity": {"admin": "user_a1b2c3d4"},
        }
        reverse = _build_reverse_map(mapping)
        assert reverse == {"10.200.50.3": "10.0.0.1", "user_a1b2c3d4": "admin"}

    def test_empty_mapping(self) -> None:
        assert _build_reverse_map({}) == {}


class TestApplyRevert:
    def test_exact_value_reverted(self) -> None:
        ir = {"configuration": {"system": {"host-name": "user_a1b2c3d4"}}}
        mapping = {"identity": {"admin": "user_a1b2c3d4"}}
        apply_revert(ir, mapping)
        assert ir["configuration"]["system"]["host-name"] == "admin"

    def test_nested_value_reverted(self) -> None:
        ir = {
            "configuration": {
                "interfaces": {"interface": [{"name": "ge-0/0/0", "description": "descr_aabbccdd"}]}
            }
        }
        mapping = {"description": {"Link to core": "descr_aabbccdd"}}
        apply_revert(ir, mapping)
        assert ir["configuration"]["interfaces"]["interface"][0]["description"] == "Link to core"

    def test_multiple_rules_reverted(self) -> None:
        ir = {
            "configuration": {
                "system": {
                    "host-name": "user_a1b2c3d4",
                    "name-server": [{"name": "10.200.50.3/32"}],
                }
            }
        }
        mapping = {
            "identity": {"admin": "user_a1b2c3d4"},
            "ip": {"8.8.8.8/32": "10.200.50.3/32"},
        }
        apply_revert(ir, mapping)
        assert ir["configuration"]["system"]["host-name"] == "admin"
        assert ir["configuration"]["system"]["name-server"][0]["name"] == "8.8.8.8/32"

    def test_substring_revert_for_sensitive_words(self) -> None:
        """Sensitive word replacements are substrings — revert should handle them."""
        ir = {"configuration": {"system": {"host-name": "word_aabb0011-router01"}}}
        mapping = {"sensitive_word": {"acmecorp-router01": "word_aabb0011-router01"}}
        apply_revert(ir, mapping)
        assert ir["configuration"]["system"]["host-name"] == "acmecorp-router01"

    def test_empty_mapping_no_change(self) -> None:
        ir = {"configuration": {"system": {"host-name": "router1"}}}
        apply_revert(ir, {})
        assert ir["configuration"]["system"]["host-name"] == "router1"

    def test_non_matching_values_unchanged(self) -> None:
        ir = {"configuration": {"system": {"host-name": "router1"}}}
        mapping = {"identity": {"admin": "user_a1b2c3d4"}}
        apply_revert(ir, mapping)
        assert ir["configuration"]["system"]["host-name"] == "router1"

    def test_list_values_reverted(self) -> None:
        ir = {"configuration": {"apply-groups": ["group_aabb", "group_ccdd"]}}
        mapping = {
            "group": {
                "MANAGEMENT": "group_aabb",
                "USERS": "group_ccdd",
            }
        }
        apply_revert(ir, mapping)
        assert ir["configuration"]["apply-groups"] == ["MANAGEMENT", "USERS"]


class TestAnonymizeRevertRoundTrip:
    """Full round-trip: anonymize -> export -> revert -> compare to original."""

    def _make_ir(self) -> dict:
        return {
            "configuration": {
                "system": {
                    "host-name": "router1",
                    "login": {
                        "user": [
                            {
                                "name": "admin",
                                "full-name": "Admin User",
                                "authentication": {
                                    "encrypted-password": "$6$abc123$xyzxyzxyz",
                                },
                            }
                        ]
                    },
                    "name-server": [{"name": "8.8.8.8"}],
                },
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "description": "Uplink to core",
                            "unit": [
                                {
                                    "name": "0",
                                    "family": {"inet": {"address": [{"name": "10.1.2.3/24"}]}},
                                }
                            ],
                        }
                    ]
                },
            }
        }

    def test_ip_round_trip(self, tmp_path: Path) -> None:
        ir = self._make_ir()
        original_ip = "10.1.2.3/24"

        cfg = AnonymizeConfig(ips=True, salt="round-trip")
        result = anonymize(ir, cfg)

        # IP should be anonymized
        addr = result.ir["configuration"]["interfaces"]["interface"][0]["unit"][0]["family"][
            "inet"
        ]["address"][0]["name"]
        assert addr != original_ip

        # Export and reload
        map_path = tmp_path / "map.json"
        export_mapping(result.mapping, str(map_path))
        loaded = load_mapping(str(map_path))

        # Revert
        apply_revert(result.ir, loaded)
        reverted_addr = result.ir["configuration"]["interfaces"]["interface"][0]["unit"][0][
            "family"
        ]["inet"]["address"][0]["name"]
        assert reverted_addr == original_ip

    def test_password_round_trip(self, tmp_path: Path) -> None:
        ir = self._make_ir()
        original_pw = "$6$abc123$xyzxyzxyz"

        cfg = AnonymizeConfig(passwords=True, salt="round-trip")
        result = anonymize(ir, cfg)

        ep = result.ir["configuration"]["system"]["login"]["user"][0]["authentication"][
            "encrypted-password"
        ]
        assert ep != original_pw

        map_path = tmp_path / "map.json"
        export_mapping(result.mapping, str(map_path))
        loaded = load_mapping(str(map_path))
        apply_revert(result.ir, loaded)

        reverted = result.ir["configuration"]["system"]["login"]["user"][0]["authentication"][
            "encrypted-password"
        ]
        assert reverted == original_pw

    def test_description_round_trip(self, tmp_path: Path) -> None:
        ir = self._make_ir()
        original_desc = "Uplink to core"

        cfg = AnonymizeConfig(descriptions=True, salt="round-trip")
        result = anonymize(ir, cfg)

        desc = result.ir["configuration"]["interfaces"]["interface"][0]["description"]
        assert desc != original_desc

        map_path = tmp_path / "map.json"
        export_mapping(result.mapping, str(map_path))
        loaded = load_mapping(str(map_path))
        apply_revert(result.ir, loaded)

        reverted = result.ir["configuration"]["interfaces"]["interface"][0]["description"]
        assert reverted == original_desc

    def test_identity_round_trip(self, tmp_path: Path) -> None:
        ir = self._make_ir()

        cfg = AnonymizeConfig(identities=True, salt="round-trip")
        result = anonymize(ir, cfg)

        username = result.ir["configuration"]["system"]["login"]["user"][0]["name"]
        assert username != "admin"

        map_path = tmp_path / "map.json"
        export_mapping(result.mapping, str(map_path))
        loaded = load_mapping(str(map_path))
        apply_revert(result.ir, loaded)

        assert result.ir["configuration"]["system"]["login"]["user"][0]["name"] == "admin"
        assert result.ir["configuration"]["system"]["login"]["user"][0]["full-name"] == "Admin User"

    def test_multi_rule_round_trip(self, tmp_path: Path) -> None:
        """Full round-trip with multiple rules enabled."""
        import copy

        ir = self._make_ir()
        original = copy.deepcopy(ir)

        cfg = AnonymizeConfig(
            ips=True,
            passwords=True,
            identities=True,
            descriptions=True,
            salt="multi-round-trip",
        )
        result = anonymize(ir, cfg)

        # Export and reload
        map_path = tmp_path / "map.json"
        export_mapping(result.mapping, str(map_path))
        loaded = load_mapping(str(map_path))

        # Revert
        apply_revert(result.ir, loaded)

        # Compare — should match original
        assert result.ir == original
