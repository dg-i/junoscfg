"""Tests for the include/exclude path filter."""

from __future__ import annotations

from junoscfg.anonymize.path_filter import PathFilter


class TestPathFilterNoFilters:
    def test_all_paths_match_when_empty(self) -> None:
        pf = PathFilter()
        assert pf.matches(["system", "host-name"])
        assert pf.matches(["interfaces", "ge-0/0/0"])
        assert pf.matches([])

    def test_no_filters_always_true(self) -> None:
        pf = PathFilter(include=[], exclude=[])
        assert pf.matches(["anything"])


class TestPathFilterInclude:
    def test_include_matches_exact_path(self) -> None:
        pf = PathFilter(include=["system"])
        assert pf.matches(["system", "host-name"])

    def test_include_rejects_non_matching_path(self) -> None:
        pf = PathFilter(include=["system"])
        assert not pf.matches(["interfaces", "ge-0/0/0"])

    def test_include_allows_prefix_for_container_walk(self) -> None:
        """A path that is a prefix of an included path should pass
        so the walker can reach deeper included leaves."""
        pf = PathFilter(include=["system.login"])
        # "system" is a prefix of "system.login" — should pass
        assert pf.matches(["system"])

    def test_include_matches_descendant(self) -> None:
        pf = PathFilter(include=["system"])
        assert pf.matches(["system", "login", "user"])

    def test_multiple_include_patterns(self) -> None:
        pf = PathFilter(include=["system", "protocols.bgp"])
        assert pf.matches(["system", "host-name"])
        assert pf.matches(["protocols", "bgp", "group"])
        assert not pf.matches(["interfaces", "ge-0/0/0"])

    def test_include_with_glob(self) -> None:
        pf = PathFilter(include=["protocols.*"])
        assert pf.matches(["protocols", "bgp"])
        assert pf.matches(["protocols", "ospf"])
        assert not pf.matches(["system", "host-name"])


class TestPathFilterExclude:
    def test_exclude_rejects_matching_path(self) -> None:
        pf = PathFilter(exclude=["system.ntp"])
        assert not pf.matches(["system", "ntp", "server"])

    def test_exclude_allows_non_matching_path(self) -> None:
        pf = PathFilter(exclude=["system.ntp"])
        assert pf.matches(["system", "host-name"])

    def test_exclude_exact_match(self) -> None:
        pf = PathFilter(exclude=["system.ntp"])
        assert not pf.matches(["system", "ntp"])


class TestPathFilterCombined:
    def test_exclude_overrides_include(self) -> None:
        pf = PathFilter(include=["system"], exclude=["system.ntp"])
        assert pf.matches(["system", "host-name"])
        assert not pf.matches(["system", "ntp", "server"])

    def test_include_and_exclude_both_applied(self) -> None:
        pf = PathFilter(include=["system", "interfaces"], exclude=["system.ntp"])
        assert pf.matches(["system", "host-name"])
        assert not pf.matches(["system", "ntp"])
        assert pf.matches(["interfaces", "ge-0/0/0"])
        assert not pf.matches(["protocols", "bgp"])
