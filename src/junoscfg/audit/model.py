"""Data model for the unused-config-object audit."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

OccurrenceKind = Literal[
    "entry-key",
    "leaf",
    "algebra",
    "apply-groups",
    "apply-groups-except",
    "unknown",
]

Confidence = Literal["unused", "probably-unused"]


class AuditLoadError(Exception):
    """Raised when audit prerequisites (registry, schema artifacts) cannot be loaded."""


@dataclass(frozen=True, slots=True)
class Occurrence:
    """A single occurrence of a name-like string value in the configuration.

    Attributes:
        value: The string value as it appears in the IR.
        path: Full hierarchy path in CLI tokens, including instance names
            and excluding transparent wrapper keys (suitable for emitting
            Junos commands).
        schema_path: Hierarchy path in schema keys, including transparent
            wrapper keys and excluding instance names (used for registry
            pattern matching).
        kind: How the value occurs in the tree.
        schema_types: Schema type references (``tr``) attached to the
            position (the leaf's own type and, for leaves, the enclosing
            container's type).
    """

    value: str
    path: tuple[str, ...]
    schema_path: tuple[str, ...]
    kind: OccurrenceKind
    schema_types: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Finding:
    """One defined-but-unreferenced configuration object.

    Attributes:
        type_name: Registry type key (e.g. ``policy-statement``).
        name: The object's name.
        path: Full definition path in CLI tokens, ending with the name.
        confidence: ``unused`` (no potential reference at all) or
            ``probably-unused`` (occurrences at unknown positions exist).
        duplicate_definition: True when a same-named object of the same
            type is defined at another path.
        unresolved: Occurrences at unknown positions that prevented a
            strict ``unused`` verdict (empty for strict findings).
    """

    type_name: str
    name: str
    path: tuple[str, ...]
    confidence: Confidence
    duplicate_definition: bool = False
    unresolved: tuple[Occurrence, ...] = ()


@dataclass(frozen=True, slots=True)
class AuditResult:
    """Result of an unused-config-object audit.

    Attributes:
        findings: All findings, ordered by registry declaration order,
            then object name, then definition path.
        definitions_checked: Number of definitions that were examined
            (after ``types``/``match``/implicit filtering).
        types_audited: Registry type keys that were audited.
    """

    findings: tuple[Finding, ...] = ()
    definitions_checked: int = 0
    types_audited: tuple[str, ...] = field(default=())

    @property
    def n_unused(self) -> int:
        """Number of strict ``unused`` findings."""
        return sum(1 for f in self.findings if f.confidence == "unused")

    @property
    def n_probably_unused(self) -> int:
        """Number of ``probably-unused`` findings."""
        return sum(1 for f in self.findings if f.confidence == "probably-unused")
