"""Junoscfg validation: validate Junos configurations against the Junos XSD schema.

Provides data types for validation results and errors, used by all
format-specific validators and the unified ``JunosValidator`` facade.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # the heavy modules stay lazy; see __getattr__ below
    from junoscfg.validate.artifact_builder import ArtifactBuilder
    from junoscfg.validate.validator import JunosValidator

__all__ = [
    "ArtifactBuilder",
    "JunosValidator",
    "SchemaLoadError",
    "ValidationError",
    "ValidationResult",
]


@dataclass(frozen=True, slots=True)
class ValidationError:
    """A single validation error with optional location info.

    Attributes:
        message: Human-readable error description.
        line: Line number where the error was found, if available.
        path: Configuration path where the error was found, if available.
    """

    message: str
    line: int | None = None
    path: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of validating a configuration.

    Attributes:
        valid: ``True`` if the configuration passed validation.
        errors: Tuple of validation errors found.
        warnings: Tuple of non-fatal validation warnings.
    """

    valid: bool
    errors: tuple[ValidationError, ...] = ()
    warnings: tuple[ValidationError, ...] = ()


class SchemaLoadError(Exception):
    """Raised when validation artifacts cannot be loaded.

    This typically occurs when the artifacts directory does not exist
    or is missing required files (XSD, JSON Schema, Lark grammar).
    """


def __getattr__(name: str) -> object:
    """Resolve the heavy re-exports on first use.

    ``artifact_builder`` and ``validator`` pull in lxml and the schema
    artifacts; importing them eagerly would make ``junoscfg.validate`` costly
    for callers that only want ``ValidationResult``.
    """
    if name == "ArtifactBuilder":
        from junoscfg.validate.artifact_builder import ArtifactBuilder

        return ArtifactBuilder
    if name == "JunosValidator":
        from junoscfg.validate.validator import JunosValidator

        return JunosValidator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
