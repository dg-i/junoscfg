"""Audit Junos configurations for unused config objects.

Finds objects (policy-statements, prefix-lists, firewall filters, config
groups, ...) that are defined but never referenced, based on the parsed
IR and a curated type registry — not on text matching.

Example:
    from junoscfg.audit import find_unused
    from junoscfg.convert import to_dict

    ir = to_dict(source, "set")
    result = find_unused(ir)
    for finding in result.findings:
        print(finding.confidence, " ".join(finding.path))
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from junoscfg.audit.engine import run_audit
from junoscfg.audit.model import (
    AuditLoadError,
    AuditResult,
    Finding,
    Occurrence,
)
from junoscfg.audit.registry import Registry, RegistryError, load_registry

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "AuditLoadError",
    "AuditResult",
    "Finding",
    "Occurrence",
    "Registry",
    "RegistryError",
    "find_unused",
    "load_registry",
]


def find_unused(
    ir: dict[str, Any],
    *,
    types: Sequence[str] | None = None,
    match: str | None = None,
    registry: Registry | None = None,
) -> AuditResult:
    """Find config objects that are defined but never referenced.

    Args:
        ir: The configuration IR (wrapped or unwrapped), as produced by
            :func:`junoscfg.convert.to_dict`.
        types: Registry type keys to audit; None audits all reportable types.
        match: Regex filtering which definitions are checked (searched
            against the object name); the reference corpus is always the
            whole configuration.
        registry: A custom type registry; None loads the bundled default.

    Returns:
        The audit result with findings classified by confidence.

    Raises:
        AuditLoadError: If the registry or schema artifacts cannot be loaded.
        ValueError: On unknown type names or an invalid regex.
    """
    from junoscfg.convert.ir import find_configuration

    config = find_configuration(ir)
    if config is None:
        config = ir
    if registry is None:
        registry = load_registry()
    return run_audit(config, registry, types=types, match=match)
