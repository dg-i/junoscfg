"""Anonymization for Junos configuration IR dicts.

Public API::

    from junoscfg.anonymize import AnonymizeConfig, anonymize

    config = AnonymizeConfig(ips=True, salt="my-salt")
    result = anonymize(ir_dict, config)
    anonymized_ir = result.ir
    mapping = result.mapping
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from junoscfg.anonymize.config import AnonymizeConfig, build_config_from_cli
from junoscfg.anonymize.path_filter import PathFilter
from junoscfg.anonymize.revert import apply_revert, export_mapping, load_mapping
from junoscfg.anonymize.rules import Rule, build_rules
from junoscfg.anonymize.rules.as_number import AsNumberRule
from junoscfg.anonymize.rules.community import CommunityRule
from junoscfg.anonymize.rules.description import DescriptionRule
from junoscfg.anonymize.rules.group import GroupRule
from junoscfg.anonymize.rules.identity import IdentityRule
from junoscfg.anonymize.rules.ip import IpRule
from junoscfg.anonymize.rules.sensitive_word import SensitiveWordRule
from junoscfg.anonymize.rules.ssh_key import SshKeyRule
from junoscfg.anonymize.walker import walk

if TYPE_CHECKING:
    from junoscfg.anonymize.rules.password import PasswordRule


def __getattr__(name: str) -> Any:
    """Load `PasswordRule` on first use.

    Its module imports netutils, which costs more than the rest of the
    package together; `build_rules` imports it only when passwords are on.
    """
    if name == "PasswordRule":
        from junoscfg.anonymize.rules.password import PasswordRule

        return PasswordRule
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


@dataclass
class AnonymizeResult:
    """Result of anonymization."""

    ir: dict[str, Any]
    mapping: dict[str, dict[str, str]] = field(default_factory=dict)


def _count_kept_statements(node: Any) -> int:
    """How many entries the IR's records of statements kept whole hold."""
    from junoscfg.display import UNPLACED_STATEMENTS

    if isinstance(node, dict):
        return sum(
            (len(value) if isinstance(value, dict) else 1)
            if key == UNPLACED_STATEMENTS
            else _count_kept_statements(value)
            for key, value in node.items()
        )
    if isinstance(node, list):
        return sum(_count_kept_statements(item) for item in node)
    return 0


def anonymize(
    ir: dict[str, Any],
    config: AnonymizeConfig,
    *,
    diagnostic_sink: Callable[[str], None] | None = None,
) -> AnonymizeResult:
    """Anonymize an IR dict according to *config*.

    Args:
        ir: The full IR dict (``{"configuration": {...}}``).
        config: Anonymization configuration specifying which rules to apply.
        diagnostic_sink: Optional receiver for debug diagnostics.

    Returns:
        An :class:`AnonymizeResult` with the modified IR and the revert mapping.

    Raises:
        ValueError: If ``config.networks`` contains ``"auto"`` without
            ``config.source_text``. Auto-detection scans the configuration
            text for subnets, so it needs that text; asking for it without
            supplying the text used to do nothing at all.
        ValueError: If the IR keeps a statement whole (a non-empty
            `junoscfg.display.UNPLACED_STATEMENTS` record). The rules rewrite
            values the schema places, never a kept statement's text, so its
            addresses and names would leave unchanged. The message names no
            statement.
    """
    # Auto-generate a random salt when none is provided to prevent
    # trivially reversible HMAC outputs (empty-string key).
    if config.salt is None:
        config.salt = secrets.token_hex(16)

    rules = build_rules(config)
    if not rules:
        return AnonymizeResult(ir=ir)
    kept = _count_kept_statements(ir)
    if kept:
        raise ValueError(
            f"cannot anonymize: {kept} statement(s) kept whole, which no rule can see; "
            "fix or remove what the conversion reports as not placed in the schema"
        )

    walk(ir, rules, config, diagnostic_sink=diagnostic_sink)

    # Second pass: replace IPs embedded in larger strings (URLs, host+IP, etc.)
    if config.ips_in_strings:
        ip_rule = next((r for r in rules if isinstance(r, IpRule)), None)
        if ip_rule:
            _replace_ips_in_strings(ir, ip_rule)

    # Second pass: replace AS numbers embedded in larger strings
    if config.as_numbers_in_strings and config.as_numbers:
        as_rule = next((r for r in rules if isinstance(r, AsNumberRule)), None)
        if as_rule:
            _replace_as_in_strings(ir, as_rule)

    # Second pass: anonymize apply-groups / apply-groups-except values.
    # The schema walker cannot reach these because their schema nodes are
    # empty (``{}``), so we handle them with a brute-force IR walk.
    if config.groups:
        group_rule = next((r for r in rules if isinstance(r, GroupRule)), None)
        if group_rule:
            _replace_apply_groups(ir, group_rule)

    # Collect mappings from all rules, keyed by rule name
    mapping: dict[str, dict[str, str]] = {}
    for rule in rules:
        rule_map = rule.get_mapping()
        if rule_map:
            mapping[rule.name] = rule_map

    return AnonymizeResult(ir=ir, mapping=mapping)


_APPLY_GROUPS_KEYS = frozenset({"apply-groups", "apply-groups-except"})


def _replace_apply_groups(obj: Any, group_rule: GroupRule) -> None:
    """Walk the IR and anonymize values in apply-groups arrays."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in _APPLY_GROUPS_KEYS and isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        value[i] = group_rule.transform(item)
            elif isinstance(value, (dict, list)):
                _replace_apply_groups(value, group_rule)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                _replace_apply_groups(item, group_rule)


def _replace_ips_in_strings(obj: Any, ip_rule: IpRule) -> None:
    """Walk all string values and replace embedded IP addresses.

    Values that are already in the anonymizer's output mapping are skipped —
    those were already transformed by the schema walker and must not be
    re-anonymized (which would break network-registry host-bit locking).
    """
    already_done = set(ip_rule.get_mapping().values())

    def _walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    if value not in already_done:
                        replaced = ip_rule.replace_ips_in_string(value)
                        if replaced != value:
                            obj[key] = replaced
                elif isinstance(value, (dict, list)):
                    _walk(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    if item not in already_done:
                        replaced = ip_rule.replace_ips_in_string(item)
                        if replaced != item:
                            obj[i] = replaced
                elif isinstance(item, (dict, list)):
                    _walk(item)

    _walk(obj)


def _replace_as_in_strings(obj: Any, as_rule: AsNumberRule) -> None:
    """Walk all string values and replace embedded AS numbers."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                replaced = as_rule.replace_as_in_string(value)
                if replaced != value:
                    obj[key] = replaced
            elif isinstance(value, (dict, list)):
                _replace_as_in_strings(value, as_rule)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                replaced = as_rule.replace_as_in_string(item)
                if replaced != item:
                    obj[i] = replaced
            elif isinstance(item, (dict, list)):
                _replace_as_in_strings(item, as_rule)


__all__ = [
    "AnonymizeConfig",
    "AnonymizeResult",
    "AsNumberRule",
    "CommunityRule",
    "DescriptionRule",
    "GroupRule",
    "IdentityRule",
    "IpRule",
    "PasswordRule",
    "PathFilter",
    "Rule",
    "SensitiveWordRule",
    "SshKeyRule",
    "anonymize",
    "apply_revert",
    "build_config_from_cli",
    "build_rules",
    "export_mapping",
    "load_mapping",
    "walk",
]
