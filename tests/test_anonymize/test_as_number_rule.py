"""Tests for the AS number anonymization rule."""

from __future__ import annotations

import warnings

from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig
from junoscfg.anonymize.rules.as_number import AsNumberRule


class TestAsNumberRuleMatches:
    def _make_rule(self, as_numbers: list[int] | None = None) -> AsNumberRule:
        return AsNumberRule(AnonymizeConfig(as_numbers=as_numbers or [64496, 64510], salt="test"))

    def test_matches_target_as(self) -> None:
        rule = self._make_rule()
        path = ["protocols", "bgp", "group", "peer-as"]
        assert rule.matches("64496", {"l": True}, path)

    def test_matches_second_target(self) -> None:
        rule = self._make_rule()
        path = ["protocols", "bgp", "group", "peer-as"]
        assert rule.matches("64510", {"l": True}, path)

    def test_no_match_on_non_target(self) -> None:
        rule = self._make_rule()
        path = ["protocols", "bgp", "group", "peer-as"]
        assert not rule.matches("65000", {"l": True}, path)

    def test_no_match_on_non_numeric(self) -> None:
        rule = self._make_rule()
        path = ["protocols", "bgp", "group", "name"]
        assert not rule.matches("PEERS", {"l": True}, path)

    def test_no_match_when_empty_list(self) -> None:
        rule = AsNumberRule(AnonymizeConfig(as_numbers=[], salt="test"))
        path = ["protocols", "bgp", "group", "peer-as"]
        assert not rule.matches("64496", {"l": True}, path)

    def test_matches_in_any_context(self) -> None:
        """AS number matching is purely value-based, works in any path."""
        rule = self._make_rule()
        path = ["routing-options", "autonomous-system", "as-number"]
        assert rule.matches("64496", {"l": True}, path)


class TestAsNumberRuleTransform:
    def _make_rule(
        self,
        as_numbers: list[int] | None = None,
        salt: str = "test-salt",
        as_number_map: dict[int, int] | None = None,
    ) -> AsNumberRule:
        return AsNumberRule(
            AnonymizeConfig(
                as_numbers=as_numbers or [64496, 64510],
                as_number_map=as_number_map or {},
                salt=salt,
            )
        )

    def test_result_is_numeric_string(self) -> None:
        rule = self._make_rule()
        result = rule.transform("64496")
        assert result.isdigit()
        assert result != "64496"

    def test_sequential_starts_at_64496(self) -> None:
        """First target AS maps to 64496 (unless 64496 is a target)."""
        # Use targets that won't collide with 64496
        rule = self._make_rule(as_numbers=[100, 200])
        assert rule.transform("100") == "64496"
        assert rule.transform("200") == "64497"

    def test_sequential_skips_targets(self) -> None:
        """Sequential counter skips target ASNs to avoid collision."""
        # Targets include 64496 and 64497 — counter should skip them
        rule = self._make_rule(as_numbers=[64496, 64497, 64498])
        r1 = rule.transform("64496")
        r2 = rule.transform("64497")
        r3 = rule.transform("64498")
        results = {r1, r2, r3}
        # None of the results should be one of the targets
        assert "64496" not in results
        assert "64497" not in results
        assert "64498" not in results

    def test_consistency(self) -> None:
        rule = self._make_rule()
        assert rule.transform("64496") == rule.transform("64496")

    def test_different_values(self) -> None:
        rule = self._make_rule()
        assert rule.transform("64496") != rule.transform("64510")

    def test_explicit_mapping(self) -> None:
        """Explicit original:replacement pairs are used."""
        rule = self._make_rule(
            as_numbers=[64496, 64510],
            as_number_map={64496: 100, 64510: 200},
        )
        assert rule.transform("64496") == "100"
        assert rule.transform("64510") == "200"

    def test_mixed_explicit_and_sequential(self) -> None:
        """Explicit mappings are used for specified ASes, sequential for the rest."""
        rule = self._make_rule(
            as_numbers=[64496, 64510, 64511],
            as_number_map={64496: 100},
        )
        assert rule.transform("64496") == "100"
        # 64510 and 64511 get sequential (starting at 64496, but skipping targets)
        r2 = rule.transform("64510")
        r3 = rule.transform("64511")
        assert r2.isdigit()
        assert r3.isdigit()
        assert r2 != r3

    def test_get_mapping(self) -> None:
        rule = self._make_rule()
        rule.transform("64496")
        rule.transform("64510")
        mapping = rule.get_mapping()
        assert "64496" in mapping
        assert "64510" in mapping


class TestAsNumberConflictDetection:
    """Tests for collision warnings."""

    def test_explicit_map_collision_warns(self) -> None:
        """Warn when an explicit replacement collides with a target AS."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            AsNumberRule(
                AnonymizeConfig(
                    as_numbers=[64496, 64497],
                    as_number_map={64496: 64497},
                    salt="test",
                )
            )
            assert len(w) == 1
            assert "collides" in str(w[0].message)
            assert "64497" in str(w[0].message)

    def test_explicit_map_no_collision_no_warn(self) -> None:
        """No warning when explicit replacement does not collide."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            AsNumberRule(
                AnonymizeConfig(
                    as_numbers=[64496],
                    as_number_map={64496: 100},
                    salt="test",
                )
            )
            assert len(w) == 0

    def test_sequential_overflow_warns(self) -> None:
        """Warn when sequential assignment exceeds RFC 5398 range."""
        # 17 targets (64496-64511 = 16 slots, so the 17th overflows)
        targets = list(range(1, 18))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            rule = AsNumberRule(AnonymizeConfig(as_numbers=targets, salt="test"))
            for t in targets:
                rule.transform(str(t))
            overflow_warnings = [x for x in w if "exceeds" in str(x.message)]
            assert len(overflow_warnings) >= 1


class TestAsNumberRuleReplaceAsInString:
    """Tests for replace_as_in_string (embedded AS number replacement)."""

    def _make_rule(
        self, as_numbers: list[int] | None = None, salt: str = "str-test"
    ) -> AsNumberRule:
        return AsNumberRule(AnonymizeConfig(as_numbers=as_numbers or [64498, 64497], salt=salt))

    def test_as_in_community(self) -> None:
        rule = self._make_rule()
        result = rule.replace_as_in_string("large:64498:23456:401")
        assert "64498" not in result
        assert ":23456:401" in result

    def test_as_in_policy_name(self) -> None:
        rule = self._make_rule()
        result = rule.replace_as_in_string("eBGP-AS64497-Rx")
        assert "64497" not in result
        assert result.startswith("eBGP-AS")

    def test_as_in_routing_instance(self) -> None:
        rule = self._make_rule()
        result = rule.replace_as_in_string("default_via_AS64497")
        assert "64497" not in result
        assert result.startswith("default_via_AS")

    def test_as_prepend_values(self) -> None:
        rule = self._make_rule()
        result = rule.replace_as_in_string("64498 64498 64498")
        assert "64498" not in result

    def test_no_partial_match_on_longer_number(self) -> None:
        """64498 should not match inside 644980."""
        rule = self._make_rule()
        result = rule.replace_as_in_string("AS644980-peer")
        assert result == "AS644980-peer"

    def test_no_match_when_not_target(self) -> None:
        rule = self._make_rule()
        result = rule.replace_as_in_string("AS12345-peer")
        assert result == "AS12345-peer"

    def test_empty_target_set_no_change(self) -> None:
        rule = AsNumberRule(AnonymizeConfig(as_numbers=[], salt="test"))
        result = rule.replace_as_in_string("AS64498-peer")
        assert result == "AS64498-peer"

    def test_deterministic(self) -> None:
        rule = self._make_rule()
        r1 = rule.replace_as_in_string("eBGP-AS64497-Rx")
        r2 = rule.replace_as_in_string("eBGP-AS64497-Rx")
        assert r1 == r2

    def test_multiple_as_in_one_string(self) -> None:
        rule = self._make_rule()
        result = rule.replace_as_in_string("from-AS64498-to-AS64497")
        assert "64498" not in result
        assert "64497" not in result

    def test_bgp_group_name(self) -> None:
        rule = self._make_rule()
        result = rule.replace_as_in_string("inet-Upstream-AS64497")
        assert "64497" not in result


class TestAsNumberAnonymizeIntegration:
    """Test the full anonymize() function with AS number rule."""

    def test_peer_as_anonymized(self) -> None:
        cfg = AnonymizeConfig(as_numbers=[64496], salt="test")
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "inet-Upstream-AS64496",
                                "type": "external",
                                "peer-as": "64496",
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        group = result.ir["configuration"]["protocols"]["bgp"]["group"][0]
        assert group["peer-as"] != "64496"
        assert group["peer-as"].isdigit()
        # name and type should NOT be anonymized
        assert group["name"] == "inet-Upstream-AS64496"
        assert group["type"] == "external"
        assert "as_number" in result.mapping

    def test_non_target_as_not_anonymized(self) -> None:
        """AS numbers not in the target list should be preserved."""
        cfg = AnonymizeConfig(as_numbers=[64496], salt="test")
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "peer1",
                                "peer-as": "64510",
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        group = result.ir["configuration"]["protocols"]["bgp"]["group"][0]
        assert group["peer-as"] == "64510"

    def test_local_as_anonymized(self) -> None:
        cfg = AnonymizeConfig(as_numbers=[64561], salt="test")
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "peer1",
                                "local-as": {
                                    "as-number": "64561",
                                    "no-prepend-global-as": [None],
                                },
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        local_as = result.ir["configuration"]["protocols"]["bgp"]["group"][0]["local-as"]
        assert local_as["as-number"] != "64561"
        assert local_as["as-number"].isdigit()

    def test_as_number_with_descriptions_and_ips(self) -> None:
        """AS number rule coexists with description and IP rules."""
        cfg = AnonymizeConfig(
            as_numbers=[64496],
            descriptions=True,
            ips=True,
            salt="test",
        )
        ir = {
            "configuration": {
                "protocols": {
                    "bgp": {
                        "group": [
                            {
                                "name": "peers",
                                "description": "Transit provider",
                                "peer-as": "64496",
                                "neighbor": [{"name": "10.0.0.1"}],
                            },
                        ],
                    },
                },
            },
        }
        result = anonymize(ir, cfg)
        group = result.ir["configuration"]["protocols"]["bgp"]["group"][0]
        assert group["peer-as"] != "64496"
        assert group["description"].startswith("descr_")
        assert group["neighbor"][0]["name"] != "10.0.0.1"
