"""AS number anonymization rule.

Replaces user-specified autonomous system numbers with sequential
replacements from the RFC 5398 documentation range (64496-64511).

Supports two modes:

- **Auto-sequential**: each new target AS seen is assigned the next
  available documentation AS (64496, 64497, ...).
- **Explicit mapping**: the user provides ``original:replacement`` pairs
  via ``--anonymize-as-numbers 1234:65230,1235:65231``.

Warns at runtime if a replacement AS number collides with a target AS
(which would create ambiguous mappings).
"""

from __future__ import annotations

import re
import warnings
from typing import TYPE_CHECKING, Any

from junoscfg.anonymize.rules import Rule

if TYPE_CHECKING:
    from junoscfg.anonymize.config import AnonymizeConfig

# RFC 5398 documentation ASes — used as the default sequential pool.
_SEQUENTIAL_START = 64496
_SEQUENTIAL_END = 64511  # inclusive


class AsNumberRule(Rule):
    """Replace AS numbers with sequential or explicitly mapped replacements.

    Only AS numbers listed in
    :attr:`~junoscfg.anonymize.config.AnonymizeConfig.as_numbers` are
    anonymized.  Replacements come from the explicit map first, then
    from a sequential counter starting at 64496 (RFC 5398 documentation
    range).
    """

    name = "as_number"
    priority = 80  # After description (70)

    def __init__(self, config: AnonymizeConfig) -> None:
        self._target_set: frozenset[int] = frozenset(config.as_numbers)
        self._explicit_map: dict[int, int] = dict(config.as_number_map)
        self._mapping: dict[str, str] = {}
        self._next_sequential = _SEQUENTIAL_START
        self._used_replacements: set[int] = set(self._explicit_map.values())

        # Validate explicit mappings and pre-populate
        for orig, repl in self._explicit_map.items():
            if repl in self._target_set and repl != orig:
                warnings.warn(
                    f"AS number replacement {orig}→{repl} collides with "
                    f"target AS {repl} (which is also being anonymized)",
                    stacklevel=2,
                )
            self._mapping[str(orig)] = str(repl)

        # Build regex for AS-in-string replacement
        self._as_in_string_re: re.Pattern[str] | None = None
        if self._target_set:
            sorted_asns = sorted(self._target_set, key=lambda x: -len(str(x)))
            pattern = "|".join(re.escape(str(asn)) for asn in sorted_asns)
            self._as_in_string_re = re.compile(rf"(?<!\d)(?:{pattern})(?!\d)")

    def matches(
        self,
        value: Any,
        schema_node: dict[str, Any],
        path: list[str],
    ) -> bool:
        """Match if the value is a numeric string whose int is in the target set."""
        if not self._target_set:
            return False
        try:
            asn = int(value)
        except (ValueError, TypeError):
            return False
        return asn in self._target_set

    def transform(self, value: str) -> str:
        """Replace an AS number with a sequential or explicit replacement."""
        if value in self._mapping:
            return self._mapping[value]

        replaced = self._do_transform(value)
        self._mapping[value] = replaced
        return replaced

    def _do_transform(self, value: str) -> str:
        asn = int(value)

        # Check explicit map first
        if asn in self._explicit_map:
            return str(self._explicit_map[asn])

        # Sequential assignment — skip values that are targets or already used
        while (
            self._next_sequential in self._target_set
            or self._next_sequential in self._used_replacements
        ):
            self._next_sequential += 1

        replacement = self._next_sequential
        self._next_sequential += 1
        self._used_replacements.add(replacement)

        if replacement in self._target_set:
            warnings.warn(
                f"Sequential AS replacement {asn}→{replacement} collides with "
                f"target AS {replacement}",
                stacklevel=3,
            )

        if replacement > _SEQUENTIAL_END:
            warnings.warn(
                f"Sequential AS replacement {asn}→{replacement} exceeds "
                f"RFC 5398 documentation range (64496-64511)",
                stacklevel=3,
            )

        return str(replacement)

    def replace_as_in_string(self, value: str) -> str:
        """Replace all embedded target AS numbers in a string.

        Uses digit-boundary anchoring so ``64498`` matches in
        ``eBGP-AS64498-Rx`` but does NOT spuriously match inside
        ``649480``.
        """
        if self._as_in_string_re is None:
            return value

        def _replace(m: re.Match[str]) -> str:
            return self.transform(m.group(0))

        return self._as_in_string_re.sub(_replace, value)

    def get_mapping(self) -> dict[str, str]:
        """Return the original -> anonymized AS number mapping."""
        return dict(self._mapping)
