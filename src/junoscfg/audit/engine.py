"""Classification engine for the unused-config-object audit.

Implements the namespace-aware classification of name occurrences:

a) matches a reference position of the object's own type -> used;
b) position unambiguously owned by other types only -> collision;
c) definition of a same-named object at another path -> duplicate;
d) unknown position -> conservatively a potential reference.

Rule (d) is the safety property: an incomplete registry may reduce
precision but never produce a confident delete suggestion for an object
that is actually referenced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from fnmatch import fnmatch
from typing import TYPE_CHECKING, Any

from junoscfg.audit.model import AuditLoadError, AuditResult, Finding, Occurrence
from junoscfg.audit.registry import Registry, TypeEntry, tail_match
from junoscfg.audit.walker import collect_occurrences

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True, slots=True)
class _Definition:
    """One object definition found in the configuration."""

    type_entry: TypeEntry
    name: str
    path: tuple[str, ...]


def run_audit(
    config: dict[str, Any],
    registry: Registry,
    *,
    types: Sequence[str] | None = None,
    match: str | None = None,
) -> AuditResult:
    """Audit the configuration for unused objects.

    Args:
        config: Unwrapped configuration content dict (the IR).
        registry: The loaded type registry.
        types: Registry type keys to audit; None audits all reportable types.
        match: Regex filtering which definitions are checked (searched
            against the object name); the reference corpus is always the
            whole configuration.

    Returns:
        The audit result.

    Raises:
        AuditLoadError: If the bundled schema tree cannot be loaded.
        ValueError: On unknown type names or an invalid regex.
    """
    from junoscfg.display.constants import load_schema_tree

    schema = load_schema_tree()
    if schema is None:
        raise AuditLoadError("schema tree artifact missing or unreadable")
    schema_root = schema.get("c", {}).get("configuration", schema)

    audit_types = _validate_types(registry, types)
    match_re = _compile_match(match)

    occurrences = collect_occurrences(config, schema_root)

    # Precompute per occurrence which types own it as definition/reference.
    entries = list(registry.types.values())
    def_owners: list[frozenset[str]] = []
    ref_owners: list[frozenset[str]] = []
    for occ in occurrences:
        def_owners.append(_definition_owners(occ, entries))
        ref_owners.append(_reference_owners(occ, entries))

    by_value: dict[str, list[int]] = {}
    definitions: list[tuple[_Definition, int]] = []
    for idx, occ in enumerate(occurrences):
        by_value.setdefault(occ.value, []).append(idx)
        for type_name in def_owners[idx]:
            definitions.append((_Definition(registry.types[type_name], occ.value, occ.path), idx))

    findings: list[Finding] = []
    checked = 0
    type_order = {name: i for i, name in enumerate(registry.types)}

    for definition, def_idx in definitions:
        entry = definition.type_entry
        if not entry.report or entry.name not in audit_types:
            continue
        if match_re is not None and not match_re.search(definition.name):
            continue
        if any(fnmatch(definition.name, glob) for glob in entry.implicit):
            continue
        checked += 1

        finding = _classify(definition, def_idx, occurrences, by_value, def_owners, ref_owners)
        if finding is not None:
            findings.append(finding)

    findings.sort(key=lambda f: (type_order[f.type_name], f.name, f.path))
    return AuditResult(
        findings=tuple(findings),
        definitions_checked=checked,
        types_audited=tuple(audit_types),
    )


def _classify(
    definition: _Definition,
    def_idx: int,
    occurrences: list[Occurrence],
    by_value: dict[str, list[int]],
    def_owners: list[frozenset[str]],
    ref_owners: list[frozenset[str]],
) -> Finding | None:
    """Classify all external occurrences of a definition's name.

    Returns None when the object is used, else the finding.
    """
    type_name = definition.type_entry.name
    duplicate = False
    unresolved: list[Occurrence] = []

    for idx in by_value.get(definition.name, ()):
        if idx == def_idx:
            continue
        occ = occurrences[idx]
        # Occurrences inside the definition's own subtree (including the
        # definition itself) are self-references and never count as use.
        if occ.path[: len(definition.path)] == definition.path:
            continue

        if type_name in ref_owners[idx]:
            return None  # (a) real reference — object is used
        if type_name in def_owners[idx]:
            duplicate = True  # (c) duplicate definition, not a reference
            continue
        if def_owners[idx] or ref_owners[idx]:
            continue  # (b) position owned by other namespaces — collision
        unresolved.append(occ)  # (d) unknown position — potential reference

    return Finding(
        type_name=type_name,
        name=definition.name,
        path=definition.path,
        confidence="probably-unused" if unresolved else "unused",
        duplicate_definition=duplicate,
        unresolved=tuple(unresolved),
    )


def _definition_owners(occ: Occurrence, entries: list[TypeEntry]) -> frozenset[str]:
    """Types whose definition patterns own this occurrence's position."""
    if occ.kind != "entry-key":
        return frozenset()
    return frozenset(
        entry.name
        for entry in entries
        if any(tail_match(occ.schema_path, pattern) for pattern in entry.definition)
    )


def _reference_owners(occ: Occurrence, entries: list[TypeEntry]) -> frozenset[str]:
    """Types whose reference patterns or schema-types own this position."""
    owners = set()
    for entry in entries:
        if any(tr in entry.reference_schema_types for tr in occ.schema_types) or any(
            tail_match(occ.schema_path, pattern) for pattern in entry.reference_paths
        ):
            owners.add(entry.name)
    return frozenset(owners)


def _validate_types(registry: Registry, types: Sequence[str] | None) -> list[str]:
    """Resolve the requested type selection against the registry."""
    reportable = registry.reportable()
    if types is None:
        return reportable
    unknown = [t for t in types if t not in reportable]
    if unknown:
        raise ValueError(
            f"unknown audit type(s): {', '.join(unknown)}; valid types: {', '.join(reportable)}"
        )
    return list(types)


def _compile_match(match: str | None) -> re.Pattern[str] | None:
    """Compile the --match regex, mapping errors to ValueError."""
    if match is None:
        return None
    try:
        return re.compile(match)
    except re.error as e:
        raise ValueError(f"invalid match regex {match!r}: {e}") from e
