"""Anonymization rule base class and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig


class Rule(ABC):
    """Base class for anonymization rules.

    Each rule handles one category of sensitive data. The walker calls
    :meth:`matches` to check whether the rule applies to a given leaf,
    then :meth:`transform` to produce the anonymized value.
    """

    #: Human-readable name for logging and revert-dictionary keys.
    name: str = ""

    #: Lower numbers run first. A leaf is processed by the first matching rule.
    priority: int = 100

    @abstractmethod
    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Return True if this rule should anonymize *value*."""

    @abstractmethod
    def transform(self, value: str) -> str:
        """Return the anonymized replacement for *value*."""

    def get_mapping(self) -> dict[str, str]:
        """Return the mapping of original -> anonymized values."""
        return {}


def build_rules(config: AnonymizeConfig) -> list[Rule]:
    """Build an ordered list of active rules from *config*.

    Only rules whose category is enabled in *config* are included.
    The list is sorted by :attr:`Rule.priority` (ascending).
    """
    rules: list[Rule] = []

    if config.passwords:
        from junoscfg.anonymize.rules.password import PasswordRule

        rules.append(PasswordRule(config))

    if config.ips:
        from junoscfg.anonymize.rules.ip import IpRule

        rules.append(IpRule(config))

    if config.communities:
        from junoscfg.anonymize.rules.community import CommunityRule

        rules.append(CommunityRule(config))

    if config.ssh_keys:
        from junoscfg.anonymize.rules.ssh_key import SshKeyRule

        rules.append(SshKeyRule(config))

    if config.identities:
        from junoscfg.anonymize.rules.identity import IdentityRule

        rules.append(IdentityRule(config))

    if config.groups:
        from junoscfg.anonymize.rules.group import GroupRule

        rules.append(GroupRule(config))

    if config.descriptions:
        from junoscfg.anonymize.rules.description import DescriptionRule

        rules.append(DescriptionRule(config))

    if config.as_numbers:
        from junoscfg.anonymize.rules.as_number import AsNumberRule

        rules.append(AsNumberRule(config))

    if config.sensitive_words or config.sensitive_patterns:
        from junoscfg.anonymize.rules.sensitive_word import SensitiveWordRule

        rules.append(SensitiveWordRule(config))

    rules.sort(key=lambda r: r.priority)
    return rules
