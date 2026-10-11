"""Tests for the revert dictionary: export, import, and apply.

That the dumped mapping restores the original for every rule, through
``convert_config`` and the CLI, is `tests/contract/test_every_rule.py`; this
file holds the three functions themselves.
"""

from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING

import pytest

from junoscfg.anonymize import (
    AnonymizeConfig,
    anonymize,
    apply_revert,
    export_mapping,
    load_mapping,
)

if TYPE_CHECKING:
    from pathlib import Path


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


class TestRevertInvertsTheMapping:
    """apply_revert reads ``{rule: {original: anonymized}}`` backwards, over every rule."""

    def test_single_rule(self) -> None:
        ir = {"configuration": {"system": {"name-server": [{"name": "10.200.50.3"}]}}}
        apply_revert(ir, {"ip": {"10.0.0.1": "10.200.50.3"}})
        assert ir == {"configuration": {"system": {"name-server": [{"name": "10.0.0.1"}]}}}

    def test_multiple_rules(self) -> None:
        mapping = {
            "ip": {"10.0.0.1": "10.200.50.3"},
            "identity": {"admin": "user_a1b2c3d4"},
        }
        ir = {
            "configuration": {
                "system": {
                    "name-server": [{"name": "10.200.50.3"}],
                    "login": {"user": [{"name": "user_a1b2c3d4"}]},
                }
            }
        }
        apply_revert(ir, mapping)
        assert ir["configuration"]["system"]["name-server"] == [{"name": "10.0.0.1"}]
        assert ir["configuration"]["system"]["login"]["user"] == [{"name": "admin"}]

    def test_empty_mapping(self) -> None:
        ir = {"configuration": {"system": {"host-name": "user_a1b2c3d4"}}}
        original = copy.deepcopy(ir)
        assert apply_revert(ir, {}) is ir
        assert ir == original


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
    """Full round-trip: anonymize -> export -> revert -> compare to original.

    One rule at a time, for every rule, is the contract test's
    ``test_the_dumped_mapping_restores_the_original``; this one runs the
    library functions with several rules at once.
    """

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

    def test_multi_rule_round_trip(self, tmp_path: Path) -> None:
        """Full round-trip with multiple rules enabled."""
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


class TestRevertRestoresKeys:
    """Content the anonymizer cannot place has the addresses in its keys
    replaced too -- a 0.16.1 joined key, a statement kept whole in the record
    `junoscfg:unplaced`, its tag -- so revert restores a key's words as it
    restores a value; a word no pseudonym spells stays. The record used to be
    refused by anonymization and passed revert unchanged (change
    kept-whole-statements); owner answer 5, spec anonymization/placed-values,
    specification challenge S1 of change anonymize-every-placed-value."""

    def test_an_address_in_a_key_is_restored(self) -> None:
        ir = {
            "configuration": {
                "system": {
                    "name-server": ["198.0.2.1"],
                    "bogus 198.0.2.1 G-SECRET": [None],
                    "198.0.2.1": {"peer": "198.0.2.1"},
                    "junoscfg:unplaced": {
                        "nonsense 198.0.2.1": True,
                        '@nonsense "198.0.2.1" x': {"inactive": True},
                    },
                }
            }
        }
        apply_revert(ir, {"ip": {"203.0.114.9": "198.0.2.1"}})
        assert ir == {
            "configuration": {
                "system": {
                    "name-server": ["203.0.114.9"],
                    "bogus 203.0.114.9 G-SECRET": [None],
                    "203.0.114.9": {"peer": "203.0.114.9"},
                    "junoscfg:unplaced": {
                        "nonsense 203.0.114.9": True,
                        '@nonsense "203.0.114.9" x': {"inactive": True},
                    },
                }
            }
        }
        assert list(ir["configuration"]["system"]) == [
            "name-server",
            "bogus 203.0.114.9 G-SECRET",
            "203.0.114.9",
            "junoscfg:unplaced",
        ]

    @pytest.mark.parametrize(
        "word",
        [
            "http://{}:8080/x",
            "{}:179",
            "host:{}",
            "lo_{}",
            "peer={}",
            "scp://u@{}/f",
            "{}/rack-4",
        ],
    )
    def test_an_address_inside_a_word_of_a_key_is_restored(self, word: str) -> None:
        """The forward pass replaces the address inside the word, so revert
        splits the key as the walk does and restores the address token, not
        the word (Reviewer finding 2)."""
        ir = {"configuration": {"system": {f"bogus {word.format('198.0.2.1')}": [None]}}}
        apply_revert(ir, {"ip": {"203.0.114.9": "198.0.2.1"}})
        assert ir == {"configuration": {"system": {f"bogus {word.format('203.0.114.9')}": [None]}}}

    def test_an_ipv6_address_inside_a_word_of_a_key_is_restored(self) -> None:
        ir = {"configuration": {"system": {"bogus [3ffe:b00::1]:179": [None]}}}
        apply_revert(ir, {"ip": {"3ffe:0b00::9": "3ffe:b00::1"}})
        assert ir == {"configuration": {"system": {"bogus [3ffe:0b00::9]:179": [None]}}}


def _described(text: str) -> dict:
    return {
        "configuration": {"interfaces": {"interface": [{"name": "ge-0/0/0", "description": text}]}}
    }


def _description(ir: dict) -> str:
    return str(ir["configuration"]["interfaces"]["interface"][0]["description"])


class TestRevertUndoesEachReplacementOnce:
    """Revert undid a replacement left inside a word by a substring search over
    the whole mapping, entry after entry: blind to digit boundaries, so a
    number inside a longer one or inside an address was rewritten, and
    dependent on the mapping's order, so a replacement that is another entry's
    original was undone twice (NEW-A-N5). It now undoes each replacement once,
    in one pass, longest first, a number only between non-digits and never
    inside an address. Spec anonymization/embedded-values.
    """

    def test_a_number_is_restored_only_between_non_digits(self) -> None:
        ir = _described("AS64497 and AS6449712")
        apply_revert(ir, {"as_number": {"64496": "64497"}})
        assert _description(ir) == "AS64496 and AS6449712"

    def test_the_order_of_the_mapping_does_not_matter(self) -> None:
        """`--anonymize-as-numbers 64496:64497,64497:64498` wrote `AS64497`
        for `AS64496` and `64498` for `64497`."""
        pairs = [("64496", "64497"), ("64497", "64498")]
        for ordered in (pairs, pairs[::-1]):
            ir = _described("AS64497 and 64498")
            apply_revert(ir, {"as_number": dict(ordered)})
            assert _description(ir) == "AS64496 and 64497", ordered

    def test_a_number_inside_an_address_is_no_number(self) -> None:
        ir = _described("via 10.100.0.1 AS100")
        apply_revert(ir, {"as_number": {"65001": "100"}})
        assert _description(ir) == "via 10.100.0.1 AS65001"

    def test_a_replacement_inside_a_word_is_restored(self) -> None:
        """A pseudonym inside a word another hand wrote around it comes back,
        as with the substring search. A pin: the base did this too."""
        ir = _described("scp://user_9d7736b55bab1f75da2d5868@host.example/x")
        apply_revert(ir, {"identity": {"operator": "user_9d7736b55bab1f75da2d5868"}})
        assert _description(ir) == "scp://operator@host.example/x"

    @pytest.mark.parametrize("reverse", [False, True], ids=["in-order", "reversed"])
    def test_replacements_sharing_a_prefix_revert_longest_first(self, reverse: bool) -> None:
        """`netconanRemoved1` is the start of `netconanRemoved10`; URL
        passwords put such replacements inside free text (Test/Challenge T5)."""
        pairs = [("first-secret", "netconanRemoved1"), ("tenth-secret", "netconanRemoved10")]
        ir = _described("ftp://operator:netconanRemoved10@198.51.100.1/x")
        apply_revert(ir, {"password": dict(pairs[::-1] if reverse else pairs)})
        assert _description(ir) == "ftp://operator:tenth-secret@198.51.100.1/x"

    @pytest.mark.parametrize("reverse", [False, True], ids=["in-order", "reversed"])
    def test_a_number_inside_a_pseudonym_is_no_number(self, reverse: bool) -> None:
        """An AS replacement spelled inside another rule's pseudonym belongs to
        the pseudonym (Test/Challenge T5)."""
        mapping = {
            "identity": {"operator": "user_ab64497cd0123456789abcde"},
            "as_number": {"64496": "64497"},
        }
        if reverse:
            mapping = dict(reversed(list(mapping.items())))
        ir = _described("scp://user_ab64497cd0123456789abcde@198.51.100.1/x AS64497")
        apply_revert(ir, mapping)
        assert _description(ir) == "scp://operator@198.51.100.1/x AS64496"
