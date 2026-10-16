"""Set command validation via Lark parser.

Validates Junos set commands against generated Lark grammar.

The four `apply-*` meta-statements -- `apply-groups`, `apply-groups-except`,
`apply-flags` and `apply-macro` -- are valid at every hierarchy level and
appear in no NETCONF XSD. `xsd_fixes._fix_apply_statements` declares them on
the root with the `universal` flag and `grammar_generator` splices them into
every rule, so the shipped grammar takes them wherever Junos does. Until the
artifacts were regenerated in 0.8.0 this module cut them off the line before
parsing; that bridge is gone, and
`TestTheShippedArtifactsModelTheApplyStatements` pins what replaced it.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from lark import Lark
from lark.exceptions import UnexpectedEOF, UnexpectedInput

from junoscfg.display import build_from_artifact
from junoscfg.input import (
    find_unsupported_set_brackets,
    find_unsupported_set_commands,
    iter_visible_set_lines,
)
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
            self._parser = build_from_artifact(grammar_path, _compile)
        except Exception as e:
            raise SchemaLoadError(f"Failed to load Lark grammar: {e}") from e

    def validate(self, source: str) -> ValidationResult:
        """Validate set commands.

        Args:
            source: Set commands as a string (one per line).

        Returns:
            ValidationResult with per-line errors.
        """
        errors: list[ValidationError] = []
        bracket_errors = dict(find_unsupported_set_brackets(source))
        command_errors = dict(find_unsupported_set_commands(source))

        for lineno, _original_line, visible_line in iter_visible_set_lines(source):
            if message := bracket_errors.get(lineno):
                errors.append(ValidationError(message=message, line=lineno))
                continue

            if message := command_errors.get(lineno):
                errors.append(ValidationError(message=message, line=lineno))
                continue

            # Every verb the set reader reads (`find_unsupported_set_commands`
            # reported any other line above) names a statement path, judged as
            # `set` judges it: `protect groups GR-PROTECTED`. Only `set` gives a
            # leaf its value; the others may stop before it, as the device
            # prints `deactivate ... max-hello-size` (synthetic captures).
            line = visible_line.strip()
            verb, _, path = line.partition(" ")
            err = self._validate_line(f"set {path}", line, lineno, partial=verb != "set")
            if err:
                errors.append(err)

        if errors:
            return ValidationResult(valid=False, errors=tuple(errors))
        return ValidationResult(valid=True)

    def _validate_line(
        self, command: str, line: str, lineno: int, *, partial: bool = False
    ) -> ValidationError | None:
        """Validate one statement as the `set` *command*; an error quotes the whole *line*.

        With *partial*, a command that ends where the grammar wants more -- a
        leaf's value -- is a statement path, and valid.
        """
        try:
            self._parser.parse(command)
            return None
        except UnexpectedEOF:
            if partial:
                return None
        except UnexpectedInput:
            pass
        return ValidationError(message=f"Invalid syntax: {line}", line=lineno)


def _compile(grammar_text: str) -> Lark:
    """The parser for a grammar; one per grammar file and process, through the cache."""
    return Lark(grammar_text, parser="earley", propagate_positions=True)
