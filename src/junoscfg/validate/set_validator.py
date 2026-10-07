"""Set command validation via Lark parser.

Validates Junos set commands against generated Lark grammar.
"""

from __future__ import annotations

from pathlib import Path

from lark import Lark
from lark.exceptions import UnexpectedInput

from junoscfg.validate import SchemaLoadError, ValidationError, ValidationResult


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
            grammar_text = Path(grammar_path).read_text()
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
                set_path = _strip_apply_groups(set_path)
                # Just check syntax - deactivate is valid if the path is valid
                err = self._validate_line(set_path, lineno)
                if err:
                    errors.append(err)
                continue

            if line.startswith("set "):
                line = _strip_apply_groups(line)
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
        if line.strip() in ("set", "deactivate"):
            # Nothing left after `_strip_apply_groups`, so the whole statement
            # was one: `set apply-groups global-vxlan` at the top level sets no
            # path of its own. There is nothing to check against the schema.
            return None
        try:
            self._parser.parse(line)
            return None
        except UnexpectedInput:
            return ValidationError(
                message=f"Invalid syntax: {line[:80]}",
                line=lineno,
            )


def _strip_apply_groups(line: str) -> str:
    """Strip a trailing apply-* meta-statement from a set command.

    `apply-groups`, `apply-groups-except`, `apply-flags` and `apply-macro` may
    be attached at any level and none of them appears in the schema, so the
    grammar has no rule for them. Only `apply-groups` was stripped, which left
    `set protocols bgp group overlay apply-flags replace` -- a line the
    downstream Ansible collection renders -- reported as invalid syntax.
    """
    # "set ... apply-groups foo"             → "set ..."
    # "set ... apply-groups-except [foo bar]" → "set ..."
    # "set ... apply-flags replace"          → "set ..."
    # "set ... apply-macro m1 key1 val1"     → "set ..."
    import re

    for pattern in (
        r"\s+apply-groups(-except)?\s+(\S+|\[.*?\])\s*$",
        r"\s+apply-flags\s+(\S+|\[.*?\])\s*$",
        r"\s+apply-macro\s+\S+(\s+\S+)*\s*$",
    ):
        match = re.search(pattern, line)
        if match and not _inside_quotes(line, match.start()):
            line = line[: match.start()]
    return line


def _inside_quotes(line: str, position: int) -> bool:
    """True when *position* falls inside a quoted value.

    `set interfaces ge-0/0/0 description "uplink to apply-groups foo"` is a
    description that happens to contain the words, and stripping there cut the
    closing quote off and left something that could never parse. An odd number
    of quotes before the match means it is inside one — which also keeps
    `apply-groups "foo"`, whose quote comes after, strippable.
    """
    return line.count('"', 0, position) % 2 == 1
