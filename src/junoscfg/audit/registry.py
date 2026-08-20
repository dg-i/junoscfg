"""Type registry for the unused-config-object audit.

The registry is a curated YAML file describing each auditable object
type: where objects of the type are defined and where their names may
legitimately appear as references. Patterns are relative (tail-anchored)
so they also match inside ``groups``, ``logical-systems`` and
``routing-instances`` without special-casing.
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from junoscfg.audit.model import AuditLoadError


class RegistryError(AuditLoadError):
    """Raised when the type-registry file is missing, malformed, or invalid."""


_ALLOWED_TYPE_KEYS = frozenset({"source", "definition", "references", "implicit", "report"})
_ALLOWED_REFERENCE_KEYS = frozenset({"paths", "schema-types"})
_SOURCES = frozenset({"curated", "generated"})
_SUPPORTED_VERSION = 1


@dataclass(frozen=True, slots=True)
class TypeEntry:
    """One auditable object type from the registry.

    Attributes:
        name: Registry key, e.g. ``policy-statement``.
        source: ``curated`` or ``generated`` (merge point for the planned
            YANG-derived registry generator).
        definition: Path patterns (split into segments) where objects of
            this type are defined.
        reference_paths: Path patterns where a name of this type may
            legitimately appear as a value.
        reference_schema_types: Schema type-reference names (``tr``) that
            mark reference positions for this type.
        implicit: Name globs that are implicitly used and never reported.
        report: False marks a namespace-only entry that anchors collision
            classification but never produces findings itself.
    """

    name: str
    source: str
    definition: tuple[tuple[str, ...], ...]
    reference_paths: tuple[tuple[str, ...], ...] = ()
    reference_schema_types: frozenset[str] = frozenset()
    implicit: tuple[str, ...] = ()
    report: bool = True


@dataclass(frozen=True, slots=True)
class Registry:
    """The loaded type registry (insertion order defines output order)."""

    types: dict[str, TypeEntry]

    def reportable(self) -> list[str]:
        """Names of the types that produce findings (``report: true``)."""
        return [name for name, entry in self.types.items() if entry.report]


def default_registry_path() -> Path:
    """Path of the bundled registry file."""
    return Path(__file__).resolve().parent / "data" / "unused-types.yaml"


def tail_match(schema_path: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    """Check whether *schema_path* ends with *pattern* (segment-wise fnmatch).

    Tail-anchoring is what makes registry patterns relative: the pattern
    ``policy-options policy-statement`` matches the same definition inside
    ``groups group ...`` or ``logical-systems ...`` as well.
    """
    if not pattern or len(pattern) > len(schema_path):
        return False
    tail = schema_path[len(schema_path) - len(pattern) :]
    return all(fnmatch(segment, pat) for segment, pat in zip(tail, pattern, strict=True))


def load_registry(path: str | Path | None = None) -> Registry:
    """Load and validate a type-registry YAML file.

    Args:
        path: Registry file path; None loads the bundled default.

    Returns:
        The validated registry.

    Raises:
        RegistryError: If the file is missing, malformed, or invalid.
    """
    import yaml

    registry_path = Path(path) if path is not None else default_registry_path()
    try:
        with open(registry_path) as f:
            raw = yaml.safe_load(f)
    except OSError as e:
        raise RegistryError(f"registry {registry_path}: cannot read file: {e}") from e
    except yaml.YAMLError as e:
        raise RegistryError(f"registry {registry_path}: invalid YAML: {e}") from e

    if not isinstance(raw, dict):
        raise RegistryError(f"registry {registry_path}: top level must be a mapping")
    if raw.get("version") != _SUPPORTED_VERSION:
        raise RegistryError(
            f"registry {registry_path}: unsupported or missing 'version'"
            f" (expected {_SUPPORTED_VERSION}, got {raw.get('version')!r})"
        )
    types_raw = raw.get("types")
    if not isinstance(types_raw, dict) or not types_raw:
        raise RegistryError(f"registry {registry_path}: 'types' must be a non-empty mapping")

    types: dict[str, TypeEntry] = {}
    for name, spec in types_raw.items():
        types[str(name)] = _parse_type(registry_path, str(name), spec)
    return Registry(types=types)


def _parse_type(registry_path: Path, name: str, spec: Any) -> TypeEntry:
    """Validate and convert one registry type entry."""

    def fail(problem: str) -> RegistryError:
        return RegistryError(f"registry {registry_path}: type '{name}': {problem}")

    if not isinstance(spec, dict):
        raise fail("entry must be a mapping")
    unknown = set(spec) - _ALLOWED_TYPE_KEYS
    if unknown:
        raise fail(f"unknown key(s): {', '.join(sorted(unknown))}")

    source = spec.get("source")
    if source not in _SOURCES:
        raise fail(f"'source' must be one of {sorted(_SOURCES)}, got {source!r}")

    definition = _parse_patterns(fail, "definition", spec.get("definition"), required=True)

    references = spec.get("references", {})
    if references is None:
        references = {}
    if not isinstance(references, dict):
        raise fail("'references' must be a mapping")
    unknown = set(references) - _ALLOWED_REFERENCE_KEYS
    if unknown:
        raise fail(f"'references' has unknown key(s): {', '.join(sorted(unknown))}")
    reference_paths = _parse_patterns(fail, "references.paths", references.get("paths"))
    schema_types = _parse_strings(fail, "references.schema-types", references.get("schema-types"))
    implicit = _parse_strings(fail, "implicit", spec.get("implicit"))

    report = spec.get("report", True)
    if not isinstance(report, bool):
        raise fail("'report' must be a boolean")
    if report and not reference_paths and not schema_types:
        raise fail(
            "a reportable type must declare at least one reference path or schema-type"
            " (otherwise every object of the type would be reported as unused)"
        )

    return TypeEntry(
        name=name,
        source=source,
        definition=definition,
        reference_paths=reference_paths,
        reference_schema_types=frozenset(schema_types),
        implicit=implicit,
        report=report,
    )


def _parse_patterns(
    fail: Any, field_name: str, value: Any, *, required: bool = False
) -> tuple[tuple[str, ...], ...]:
    """Validate a list of path-pattern strings and split them into segments."""
    if value is None:
        if required:
            raise fail(f"'{field_name}' is required and must be a non-empty list")
        return ()
    patterns = _parse_strings(fail, field_name, value)
    if required and not patterns:
        raise fail(f"'{field_name}' is required and must be a non-empty list")
    split = []
    for pattern in patterns:
        segments = tuple(pattern.split())
        if not segments:
            raise fail(f"'{field_name}' contains an empty pattern")
        split.append(segments)
    return tuple(split)


def _parse_strings(fail: Any, field_name: str, value: Any) -> tuple[str, ...]:
    """Validate an optional list of non-empty strings."""
    if value is None:
        return ()
    if not isinstance(value, list):
        raise fail(f"'{field_name}' must be a list of strings")
    result = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise fail(f"'{field_name}' must contain only non-empty strings, got {item!r}")
        result.append(item)
    return tuple(result)
