"""Tests for ConfigStore tree."""

from __future__ import annotations

from junoscfg.display.config_store import ConfigStore


class TestConfigStore:
    def test_empty_store(self) -> None:
        store = ConfigStore()
        assert store.empty()
        assert str(store) == ""

    def test_single_leaf(self) -> None:
        store = ConfigStore()
        store.push("system\nhost-name router1")
        result = str(store)
        # system has one terminal child → collapses to oneliner
        assert "system host-name router1;" in result

    def test_multiple_children(self) -> None:
        store = ConfigStore()
        store.push("system\nhost-name router1")
        store.push("system\ndomain-name example.com")
        result = str(store)
        assert "host-name router1;" in result
        assert "domain-name example.com;" in result

    def test_deep_nesting(self) -> None:
        store = ConfigStore()
        store.push("interfaces\nge-0/0/0\nunit 0\nfamily\ninet\naddress 10.0.0.1/24")
        result = str(store)
        assert "interfaces {" in result
        assert "ge-0/0/0 {" in result
        assert "unit 0 {" in result
        # family is a compound keyword → merges with inet
        assert "family inet {" in result
        assert "address 10.0.0.1/24;" in result

    def test_compound_keyword_family(self) -> None:
        store = ConfigStore()
        store.push("family\ninet\naddress 10.0.0.1/24")
        store.push("family\ninet6\naddress 2001:db8::1/64")
        result = str(store)
        # family merges with each child on the same line
        assert "family inet {" in result
        assert "family inet6 {" in result
        assert "address 10.0.0.1/24;" in result
        assert "address 2001:db8::1/64;" in result
        # No standalone "family {" block
        assert "family {" not in result

    def test_compound_keyword_single_child_collapses(self) -> None:
        store = ConfigStore()
        store.push("family\ninet\nunicast")
        result = str(store)
        # family + inet + single terminal child → "family inet unicast;"
        assert "family inet unicast;" in result

    def test_deactivate_container(self) -> None:
        store = ConfigStore()
        store.push("interfaces\nge-0/0/0\ndescription uplink")
        store.deactivate("interfaces ge-0/0/0")
        result = str(store)
        assert "inactive: ge-0/0/0 {" in result

    def test_deactivate_leaf(self) -> None:
        store = ConfigStore()
        store.push("interfaces\nge-0/0/0\ndescription uplink")
        store.deactivate("interfaces ge-0/0/0 description uplink")
        result = str(store)
        assert "inactive: description uplink;" in result

    def test_arg_wrapper(self) -> None:
        store = ConfigStore()
        store.push("system\narg(host-name) router1")
        result = str(store)
        # system has one terminal child → collapses to oneliner
        assert "system host-name router1;" in result

    def test_deactivate_nonexistent_path_no_crash(self) -> None:
        store = ConfigStore()
        store.push("system\nhost-name router1")
        store.deactivate("interfaces ge-0/0/0")
        result = str(store)
        assert "host-name router1;" in result

    def test_replace_container(self) -> None:
        store = ConfigStore()
        store.push("interfaces\nge-0/0/0\ndescription uplink")
        store.mark_replaced("interfaces ge-0/0/0")
        result = str(store)
        assert "replace: ge-0/0/0 {" in result

    def test_replace_leaf(self) -> None:
        store = ConfigStore()
        store.push("interfaces\nge-0/0/0\ndescription uplink")
        store.mark_replaced("interfaces ge-0/0/0 description uplink")
        result = str(store)
        assert "replace: description uplink;" in result

    def test_protect_container(self) -> None:
        store = ConfigStore()
        store.push("interfaces\nge-0/0/0\ndescription uplink")
        store.mark_protected("interfaces ge-0/0/0")
        result = str(store)
        assert "protect: ge-0/0/0 {" in result

    def test_protect_leaf(self) -> None:
        store = ConfigStore()
        store.push("interfaces\nge-0/0/0\ndescription uplink")
        store.mark_protected("interfaces ge-0/0/0 description uplink")
        result = str(store)
        assert "protect: description uplink;" in result

    def test_prefix_order_replace_protect_inactive(self) -> None:
        store = ConfigStore()
        store.push("interfaces\nge-0/0/0\ndescription uplink")
        store.mark_replaced("interfaces ge-0/0/0")
        store.mark_protected("interfaces ge-0/0/0")
        store.deactivate("interfaces ge-0/0/0")
        result = str(store)
        assert "replace: protect: inactive: ge-0/0/0 {" in result

    def test_replace_nonexistent_path_no_crash(self) -> None:
        store = ConfigStore()
        store.push("system\nhost-name router1")
        store.mark_replaced("interfaces ge-0/0/0")
        result = str(store)
        assert "host-name router1;" in result

    def test_indentation(self) -> None:
        store = ConfigStore()
        store.push("a\nb\nc")
        result = str(store)
        lines = result.strip().splitlines()
        # b has single terminal child c (plain keyword) → collapses
        assert lines[0] == "a {"
        assert lines[1] == "    b c;"
        assert lines[2] == "}"


class TestConfigStoreSubtree:
    """Tests for subtree extraction (path filtering for structured output)."""

    def test_subtree_single_level(self) -> None:
        store = ConfigStore()
        store.push("system\nhost-name router1")
        store.push("system\ndomain-name example.com")
        store.push("interfaces\nge-0/0/0\ndescription uplink")

        sub = store.subtree(["system"])
        result = str(sub)
        assert "host-name router1;" in result
        assert "domain-name example.com;" in result
        assert "interfaces" not in result

    def test_subtree_multi_level(self) -> None:
        store = ConfigStore()
        store.push("system\nsyslog\nfile messages\nany notice")
        store.push("system\nsyslog\nfile interactive\nany error")
        store.push("system\nhost-name router1")

        sub = store.subtree(["system", "syslog"])
        result = str(sub)
        assert "file messages" in result
        assert "file interactive" in result
        assert "host-name" not in result
        assert "system" not in result

    def test_subtree_absolute_wraps_in_path(self) -> None:
        """Without relative, subtree output wraps content in the full path."""
        store = ConfigStore()
        store.push("system\nsyslog\nfile messages\nany notice")

        sub = store.subtree(["system", "syslog"], relative=False)
        result = str(sub)
        assert "system {" in result
        assert "syslog {" in result
        assert "file messages" in result

    def test_subtree_relative_omits_path(self) -> None:
        """With relative=True, subtree output starts at the filtered level."""
        store = ConfigStore()
        store.push("system\nsyslog\nfile messages\nany notice")

        sub = store.subtree(["system", "syslog"], relative=True)
        result = str(sub)
        assert "system" not in result
        assert "syslog" not in result
        assert "file messages" in result

    def test_subtree_not_found_returns_empty(self) -> None:
        store = ConfigStore()
        store.push("system\nhost-name router1")

        sub = store.subtree(["interfaces"])
        assert str(sub) == ""

    def test_subtree_preserves_attributes(self) -> None:
        store = ConfigStore()
        store.push("system\nsyslog\nfile messages\nany notice")
        store.deactivate("system syslog file messages")

        sub = store.subtree(["system", "syslog"], relative=True)
        result = str(sub)
        assert "inactive:" in result

    def test_subtree_empty_path_returns_full_tree(self) -> None:
        store = ConfigStore()
        store.push("system\nhost-name router1")

        sub = store.subtree([])
        result = str(sub)
        assert "host-name router1;" in result
