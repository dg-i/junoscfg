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
import re
import secrets
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from junoscfg.anonymize.config import AnonymizeConfig, build_config_from_cli
from junoscfg.anonymize.path_filter import PathFilter
from junoscfg.anonymize.revert import apply_revert, export_mapping, load_mapping
from junoscfg.anonymize.rules import Rule, build_rules, wildcard_text
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
    anonymization/placed-values; specification challenges S1-S3).
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

    unplaced, report = walk_with_patterns(ir, rules, config, diagnostic_sink=diagnostic_sink)
    #: Wildcard names a strings pass could not rewrite, by `(id(entry), key)`.
    unvouched: set[tuple[int, str]] = set()

    # Second pass: replace IPs embedded in larger strings (URLs, host+IP, etc.)
    if config.ips_in_strings:
        ip_rule = next((r for r in rules if isinstance(r, IpRule)), None)
        if ip_rule:
            _replace_ips_in_strings(ir, ip_rule, unvouched)

    # Second pass: replace AS numbers embedded in larger strings
    if config.as_numbers_in_strings and config.as_numbers:
        as_rule = next((r for r in rules if isinstance(r, AsNumberRule)), None)
        if as_rule:
            _replace_as_in_strings(ir, as_rule, unvouched)

    # Read from the final values, after every pass (Reviewer R2).
    patterns = report(unvouched)

    # Collect mappings from all rules, keyed by rule name
    mapping: dict[str, dict[str, str]] = {}
    for rule in rules:
        rule_map = rule.get_mapping()
        if rule_map:
            mapping[rule.name] = rule_map

    return AnonymizeResult(ir=ir, mapping=mapping, unplaced=unplaced, patterns=patterns)


def _replace_ips_in_strings(obj: Any, ip_rule: IpRule, unvouched: set[tuple[int, str]]) -> None:
    """Walk all string values and replace embedded IP addresses.

    A replacement the walk already wrote -- a whole value, or an address
    inside one -- is left as it is: re-anonymized, it would break the network
    registry's host-bit locking and leave the mapping unable to revert it. A
    wildcard name's text is a pattern (`IpRule.pattern_in_string`); one it
    cannot rewrite is added to *unvouched*.
    """
    done = frozenset(ip_rule.get_mapping().values())

    def _walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                text = wildcard_text(value)
                if text is not None:
                    rewritten, vouched = ip_rule.pattern_in_string(text, done=done)
                    obj[key] = f"<{rewritten}>"
                    if not vouched:
                        unvouched.add((id(obj), key))
                elif isinstance(value, str):
                    if value not in done:
                        replaced = ip_rule.replace_ips_in_string(value, done=done)
                        if replaced != value:
                            obj[key] = replaced
                elif isinstance(value, (dict, list)):
                    _walk(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    if item not in done:
                        replaced = ip_rule.replace_ips_in_string(item, done=done)
                        if replaced != item:
                            obj[i] = replaced
                elif isinstance(item, (dict, list)):
                    _walk(item)

    _walk(obj)


def _replace_as_in_strings(
    obj: Any, as_rule: AsNumberRule, unvouched: set[tuple[int, str]]
) -> None:
    """Walk all string values and replace embedded AS numbers.

    A wildcard name whose digits a `?` or a class touches (`<AS6449?-*>`)
    may select an AS number the pass replaces where it cannot replace it: it
    is added to *unvouched* (Reviewer R3, specification challenge S3).
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                text = wildcard_text(value)
                if text is not None and _DIGITS_BESIDE_SYNTAX.search(text):
                    unvouched.add((id(obj), key))
                replaced = as_rule.replace_as_in_string(value)
                if replaced != value:
                    obj[key] = replaced
            elif isinstance(value, (dict, list)):
                _replace_as_in_strings(value, as_rule, unvouched)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                replaced = as_rule.replace_as_in_string(item)
                if replaced != item:
                    obj[i] = replaced
            elif isinstance(item, (dict, list)):
                _replace_as_in_strings(item, as_rule, unvouched)


#: Digits a `?` or a class stands beside, in a wildcard's text.
_DIGITS_BESIDE_SYNTAX = re.compile(r"\d[?\[]|[?\]]\d")


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
