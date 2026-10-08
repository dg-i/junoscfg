"""Set command validation via Lark parser.

Validates Junos set commands against generated Lark grammar.

The four `apply-*` meta-statements -- `apply-groups`, `apply-groups-except`,
`apply-flags` and `apply-macro` -- are valid at every hierarchy level and
appear in no NETCONF XSD. `xsd_fixes._fix_apply_statements` declares them on
the root with the `universal` flag and `grammar_generator` splices them into
every rule, so the shipped grammar takes them wherever Junos does. Until the
artifacts were regenerated in 0.8.0 this module cut them off the line before
parsing; that bridge is gone, and
`TestTheShippedGrammarModelsTheApplyStatements` pins what replaced it.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from lark import Lark
from lark.exceptions import UnexpectedInput

from junoscfg.display import read_artifact_text
from junoscfg.validate import SchemaLoadError, ValidationError, ValidationResult

if TYPE_CHECKING:
    from pathlib import Path


class SetValidator:
    """Validates Junos set commands against a Lark grammar."""

    def __init__(self, grammar_path: str | Path) -> None:
        """Load the Lark grammar.

        Args:
            grammar_path: Path to the .lark grammar file.

        Raises:
            SchemaLoadError: If grammar cannot be loaded.
        """
        try:
            grammar_text = read_artifact_text(grammar_path)
            self._parser = Lark(grammar_text, parser="earley", propagate_positions=True)
        except Exception as e:
            raise SchemaLoadError(f"Failed to load Lark grammar: {e}") from e

    def validate(self, source: str) -> ValidationResult:
        """Validate set commands.

        Args:
            source: Set commands as a string (one per line).

        Returns:
            ValidationResult with per-line errors.
        """
        lines = source.strip().splitlines()
        errors: list[ValidationError] = []
        set_lines: list[str] = []

        for lineno, raw_line in enumerate(lines, 1):
            line = raw_line.strip()
            if not line or line.startswith("#") or line.startswith("/*"):
                continue

            if line.startswith("deactivate "):
                # Check that corresponding set path exists
                set_path = "set " + line[len("deactivate ") :]
                # Just check syntax - deactivate is valid if the path is valid
                err = self._validate_line(set_path, lineno)
                if err:
                    errors.append(err)
                continue

            if line.startswith("set "):
                set_lines.append(line)
                err = self._validate_line(line, lineno)
                if err:
                    errors.append(err)
            else:
                errors.append(
                    ValidationError(
                        message=f"Line does not start with 'set' or 'deactivate': {line[:80]}",
                        line=lineno,
                    )
                )

        if errors:
            return ValidationResult(valid=False, errors=tuple(errors))
        return ValidationResult(valid=True)

    def _validate_line(self, line: str, lineno: int) -> ValidationError | None:
        """Validate a single set command line."""
        try:
            self._parser.parse(line)
            return None
        except UnexpectedInput:
            return ValidationError(
                message=f"Invalid syntax: {line[:80]}",
                line=lineno,
            )
