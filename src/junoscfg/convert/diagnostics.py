"""Structured diagnostics returned by conversion APIs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One conversion diagnostic whose rendering belongs to the caller."""

    source: str
    message: str
    severity: Literal["debug", "warning", "note"] = "warning"
    path: str | None = None

    def render(self) -> str:
        """Render the stable CLI text for this diagnostic."""
        if self.path:
            return f"{self.source}: {self.path}: {self.message}"
        if self.source == "anonymize":
            return f"anonymize: {self.message}"
        return self.message


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Converted output plus immutable diagnostics."""

    output: str
    diagnostics: tuple[Diagnostic, ...] = ()
