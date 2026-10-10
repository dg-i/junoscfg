"""Tests for the sensitive word and pattern substring replacement rule.

What every rule keeps -- determinism, the salt, consistency, the mapping and
revert -- is `tests/contract/test_every_rule.py`; this file keeps what is the
sensitive word rule's own: which leaves it takes and the form of its replacements.
"""

from __future__ import annotations

import re

import pytest

from junoscfg.anonymize import AnonymizeConfig, SensitiveWordRule, anonymize


class TestSensitiveWordRuleMatches:
    def _make_rule(self, words: list[str] | None = None) -> SensitiveWordRule:
        return SensitiveWordRule(
            AnonymizeConfig(sensitive_words=words or ["acmecorp", "newyork"], salt="test")
        )

    def test_matches_exact_word(self) -> None:
        rule = self._make_rule()
        path = ["system", "host-name"]
        assert rule.matches("acmecorp-router1", {"l": True}, path)

    def test_matches_case_insensitive(self) -> None:
        rule = self._make_rule()
        path = ["system", "host-name"]
        assert rule.matches("AcmeCorp-Router1", {"l": True}, path)

    def test_matches_second_word(self) -> None:
        rule = self._make_rule()
        path = ["interfaces", "interface", "description"]
        assert rule.matches("Link to NewYork office", {"l": True}, path)

    def test_no_match_when_absent(self) -> None:
        rule = self._make_rule()
        path = ["system", "host-name"]
        assert not rule.matches("router1-chicago", {"l": True}, path)

    def test_no_match_when_empty_list(self) -> None:
        rule = SensitiveWordRule(AnonymizeConfig(sensitive_words=[], salt="test"))
        path = ["system", "host-name"]
        assert not rule.matches("acmecorp", {"l": True}, path)

    def test_no_match_on_non_string(self) -> None:
        rule = self._make_rule()
        path = ["some", "path"]
        assert not rule.matches(42, {"l": True}, path)


class TestSensitiveWordRuleTransform:
    def _make_rule(
        self, words: list[str] | None = None, salt: str = "test-salt"
    ) -> SensitiveWordRule:
        return SensitiveWordRule(
            AnonymizeConfig(sensitive_words=words or ["acmecorp", "newyork"], salt=salt)
        )

    def test_replaces_word(self) -> None:
        rule = self._make_rule()
        result = rule.transform("acmecorp-router1")
        assert "acmecorp" not in result.lower()
        assert "router1" in result

    def test_replaces_with_word_prefix(self) -> None:
        rule = self._make_rule()
        result = rule.transform("acmecorp")
        assert result.startswith("word_")

    def test_case_insensitive_replacement(self) -> None:
        rule = self._make_rule()
        result = rule.transform("AcmeCorp-Router1")
        assert "acmecorp" not in result.lower()
        assert "Router1" in result

    def test_preserves_surrounding_text(self) -> None:
        rule = self._make_rule()
        result = rule.transform("Link to newyork office")
        assert "newyork" not in result.lower()
        assert "Link to " in result
        assert " office" in result

    def test_multiple_words_replaced(self) -> None:
        rule = self._make_rule()
        result = rule.transform("acmecorp-newyork-router")
        assert "acmecorp" not in result.lower()
        assert "newyork" not in result.lower()
        assert "router" in result

    def test_same_word_same_replacement(self) -> None:
        """Same word in different contexts gets the same replacement."""
        rule = self._make_rule()
        r1 = rule.transform("acmecorp-router1")
        r2 = rule.transform("acmecorp-router2")
        # Extract the replacement for "acmecorp" — it should be the same
        # in both results (same word_ prefix hash)
        replacement = r1.replace("-router1", "")
        assert r2.startswith(replacement)


class TestSensitiveWordAnonymizeIntegration:
    """Test the full anonymize() function with sensitive word rule."""

    def test_hostname_word_replaced(self) -> None:
        cfg = AnonymizeConfig(sensitive_words=["acmecorp"], salt="test")
        ir = {
            "configuration": {
                "system": {
                    "host-name": "acmecorp-border-gw01",
                },
            },
        }
        result = anonymize(ir, cfg)
        hostname = result.ir["configuration"]["system"]["host-name"]
        assert "acmecorp" not in hostname.lower()
        assert "border-gw01" in hostname
        assert "sensitive_word" in result.mapping

    def test_description_word_replaced(self) -> None:
        cfg = AnonymizeConfig(sensitive_words=["newyork"], salt="test")
        ir = {
            "configuration": {
                "interfaces": {
                    "interface": [
                        {
                            "name": "ge-0/0/0",
                            "description": "Link to NewYork DC",
                        },
                    ],
                },
            },
        }
        result = anonymize(ir, cfg)
        desc = result.ir["configuration"]["interfaces"]["interface"][0]["description"]
        assert "newyork" not in desc.lower()
        assert "Link to " in desc
        assert " DC" in desc


class TestSensitivePatternMatches:
    def _make_rule(
        self,
        patterns: list[str] | None = None,
        words: list[str] | None = None,
        salt: str = "test",
    ) -> SensitiveWordRule:
        return SensitiveWordRule(
            AnonymizeConfig(
                sensitive_words=words or [],
                sensitive_patterns=patterns or [r"LAX\d+"],
                salt=salt,
            )
        )

    def test_pattern_matches_regex(self) -> None:
        rule = self._make_rule()
        path = ["system", "host-name"]
        assert rule.matches("LAX001-router", {"l": True}, path)

    def test_pattern_no_match(self) -> None:
        rule = self._make_rule()
        path = ["system", "host-name"]
        assert not rule.matches("SFO-router", {"l": True}, path)

    def test_pattern_case_insensitive(self) -> None:
        rule = self._make_rule(patterns=[r"corp-[a-z]+"])
        path = ["system", "host-name"]
        assert rule.matches("CORP-Office", {"l": True}, path)

    def test_pattern_invalid_regex_raises(self) -> None:
        with pytest.raises(re.error):
            self._make_rule(patterns=["[unclosed"])

    def test_pattern_different_matches_different_hashes(self) -> None:
        rule = self._make_rule()
        r1 = rule.transform("LAX001-router")
        r2 = rule.transform("LAX002-router")
        # Both should be anonymized but differently
        assert "LAX001" not in r1
        assert "LAX002" not in r2
        assert r1 != r2

    def test_pattern_and_words_combined(self) -> None:
        rule = self._make_rule(patterns=[r"LAX\d+"], words=["acmecorp"])
        result = rule.transform("acmecorp-LAX001-router")
        assert "acmecorp" not in result.lower()
        assert "LAX001" not in result
        assert "router" in result

    def test_pattern_integration(self) -> None:
        cfg = AnonymizeConfig(sensitive_patterns=[r"LAX\d+"], salt="test")
        ir = {
            "configuration": {
                "system": {
                    "host-name": "LAX001-border-gw01",
                },
            },
        }
        result = anonymize(ir, cfg)
        hostname = result.ir["configuration"]["system"]["host-name"]
        assert "LAX001" not in hostname
        assert "border-gw01" in hostname
        assert "sensitive_word" in result.mapping
