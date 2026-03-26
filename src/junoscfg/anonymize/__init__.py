"""Anonymization for Junos configuration IR dicts.

Public API::

    from junoscfg.anonymize import anonymize
    from junoscfg.anonymize.config import AnonymizeConfig

    config = AnonymizeConfig(ips=True, salt="my-salt")
    result = anonymize(ir_dict, config)
    anonymized_ir = result.ir
    mapping = result.mapping
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

from junoscfg.anonymize.config import AnonymizeConfig
from junoscfg.anonymize.rules import build_rules
from junoscfg.anonymize.rules.as_number import AsNumberRule
from junoscfg.anonymize.rules.group import GroupRule
from junoscfg.anonymize.rules.ip import IpRule
from junoscfg.anonymize.walker import walk


@dataclass
class AnonymizeResult:
    """Result of anonymization."""

    ir: dict[str, Any]
    mapping: dict[str, dict[str, str]] = field(default_factory=dict)


def anonymize(ir: dict[str, Any], config: AnonymizeConfig) -> AnonymizeResult:
    """Anonymize an IR dict according to *config*.

    Args:
        ir: The full IR dict (``{"configuration": {...}}``).
        config: Anonymization configuration specifying which rules to apply.

    Returns:
        An :class:`AnonymizeResult` with the modified IR and the revert mapping.
    """
    # Auto-generate a random salt when none is provided to prevent
    # trivially reversible HMAC outputs (empty-string key).
    if config.salt is None:
        config.salt = secrets.token_hex(16)

    rules = build_rules(config)
    if not rules:
        return AnonymizeResult(ir=ir)

    walk(ir, rules, config)

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
    """Walk all string values and replace embedded IP addresses."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                replaced = ip_rule.replace_ips_in_string(value)
                if replaced != value:
                    obj[key] = replaced
            elif isinstance(value, (dict, list)):
                _replace_ips_in_strings(value, ip_rule)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                replaced = ip_rule.replace_ips_in_string(item)
                if replaced != item:
                    obj[i] = replaced
            elif isinstance(item, (dict, list)):
                _replace_ips_in_strings(item, ip_rule)


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


__all__ = ["AnonymizeConfig", "AnonymizeResult", "anonymize"]
