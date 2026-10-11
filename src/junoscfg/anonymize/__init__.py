"""Anonymization for Junos configuration IR dicts.

Public API::

    from junoscfg.anonymize import AnonymizeConfig, anonymize

    config = AnonymizeConfig(ips=True, salt="my-salt")
    result = anonymize(ir_dict, config)
    anonymized_ir = result.ir
    mapping = result.mapping
"""

from __future__ import annotations

import copy
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
from junoscfg.anonymize.walker import walk, walk_with_patterns

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
    """Result of anonymization.

    ``unplaced`` names, by schema path (dot-joined schema names, ``""`` for the
    top level), each piece of content the walk could not place -- a key the
    schema does not name, a value of a shape its node does not take, a
    statement kept whole -- once per piece. Its addresses, password hashes and
    sensitive words are replaced by their shape; every other word is left as
    written, so a caller who must not publish one stops on a non-empty tuple.
    No path holds the unplaced key, an entry name or a value (owner answer 5).

    ``patterns`` names, by the entry's schema path, once per wildcard, each
    wildcard name (`<EBGP-*>` in a group) that selects other names once
    anonymized than it selected, among the names the configuration holds at
    its place, or whose text a rule could not rewrite as a pattern; such text
    is left as written. A wildcard of `*` alone passes every rule (spec
    anonymization/wildcard-names; specification challenges S1-S4).
    """

    ir: dict[str, Any]
    mapping: dict[str, dict[str, str]] = field(default_factory=dict)
    unplaced: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ()


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
        diagnostic_sink: Optional receiver for debug diagnostics. At
            ``config.log_level == "debug"`` each one pairs an original value
            with its replacement, by design, and ``ipanon`` writes its own
            warnings to stderr; at any other level it receives nothing.

    Returns:
        An :class:`AnonymizeResult` with the anonymized copy of *ir* and the
        revert mapping. *ir* itself is never changed: it is copied once on
        entry (`apply_revert` and `walk`, by contrast, rewrite the IR they are
        given, as they document). A generated salt is written back into
        *config*, so a reused config keeps one salt.

    Raises:
        ValueError: If ``config.networks`` contains ``"auto"`` without
            ``config.source_text``. Auto-detection scans the configuration
            text for subnets, so it needs that text; asking for it without
            supplying the text used to do nothing at all.

    Content the walk cannot place, a statement kept whole
    (`junoscfg.display.UNPLACED_STATEMENTS`) included, is not refused: its
    words are rewritten by their shape and its place named in
    ``AnonymizeResult.unplaced``.
    """
    # Auto-generate a random salt when none is provided to prevent
    # trivially reversible HMAC outputs (empty-string key).
    if config.salt is None:
        config.salt = secrets.token_hex(16)

    # The caller's IR is the caller's: a rewrite in place left it holding the
    # pseudonyms, its originals lost (NEW-R3).
    ir = copy.deepcopy(ir)
    rules = build_rules(config)
    if not rules:
        return AnonymizeResult(ir=ir)

    # One walk: the shapes inside a value -- an address, a URL's user or
    # password, an AS number under `as_numbers_in_strings` -- are rewritten
    # where the value stands; no pass after it (spec anonymization/embedded-values).
    unplaced, patterns = walk_with_patterns(ir, rules, config, diagnostic_sink=diagnostic_sink)

    # Collect mappings from all rules, keyed by rule name
    mapping: dict[str, dict[str, str]] = {}
    for rule in rules:
        rule_map = rule.get_mapping()
        if rule_map:
            mapping[rule.name] = rule_map

    return AnonymizeResult(ir=ir, mapping=mapping, unplaced=unplaced, patterns=patterns)


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
