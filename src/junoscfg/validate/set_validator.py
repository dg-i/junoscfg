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
from typing import Any

from lark import Lark
from lark.exceptions import UnexpectedEOF, UnexpectedInput

from junoscfg.display import (
    build_from_artifact,
    load_schema_tree,
    meta_target,
    statement_children,
    statement_key,
)
from junoscfg.input import (
    find_unsupported_set_brackets,
    find_unsupported_set_commands,
    iter_visible_set_lines,
    set_tokens,
)
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
            self._parser = build_from_artifact(grammar_path, _compile)
        except Exception as e:
            raise SchemaLoadError(f"Failed to load Lark grammar: {e}") from e
        self._directory = Path(grammar_path).parent
        self._tree: dict[str, Any] | None = None

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
            # prints `deactivate ... max-hello-size` (synthetic captures), and
            # must name a statement the device can tag (`_names_a_statement`).
            line = visible_line.strip()
            verb, _, path = line.partition(" ")
            err = self._validate_line(f"set {path}", line, lineno, partial=verb != "set")
            if err is None and verb != "set" and not self._names_a_statement(path):
                err = ValidationError(message=f"Invalid syntax: {line}", line=lineno)
            elif err is not None and verb == "set" and self._holds_several_statements(path):
                err = ValidationError(
                    message=f"Unsupported in set input, one statement a line: {line}",
                    line=lineno,
                )
            if err:
                errors.append(err)

        if errors:
            return ValidationResult(valid=False, errors=tuple(errors))
        return ValidationResult(valid=True)

    def _validate_line(
        self, command: str, line: str, lineno: int, *, partial: bool = False
    ) -> ValidationError | None:
        """Validate one statement as the `set` *command*; an error quotes the whole *line*.

        With *partial*, a command may stop where one value would follow -- a
        leaf's value: `deactivate ... max-hello-size`. It is valid when the
        grammar takes it with one value more, and so never when it stops
        inside an entry's key, before a keyword the key still needs
        (`route-filter 10.0.0.0/8` without its match type).
        """
        try:
            self._parser.parse(command)
            return None
        except UnexpectedEOF:
            if partial and self._parses(f"{command} {_ANY_VALUE}"):
                return None
        except UnexpectedInput:
            pass
        return ValidationError(message=f"Invalid syntax: {line}", line=lineno)

    def _names_a_statement(self, path: str) -> bool:
        """Whether a verb line's *path* names a statement the device can tag.

        The walk the set reader places the tag by (`junoscfg.display.meta_target`)
        reads the path through the structure tree beside the grammar, which
        tells a list's name from a leaf's value where the grammar cannot. The
        keyword of a list the XSD does not mark `homogeneous` without its
        entry's name (the QFX5120 25.2R2-S1.5 refuses `protect policy-options
        policy-statement`, probe D5; it deactivates a homogeneous one whole,
        deactivate6.txt), a leaf's value (`deactivate ... community 64496:2`,
        probe A2) and a stop inside an entry's key are none; a path the tree
        does not place is left to the grammar, as the reader keeps it whole.
        """
        tree = self._structure_tree()
        assert tree is not None
        target = meta_target(set_tokens(path), tree)
        return target.kind not in ("list", "value", "partial-key")

    def _holds_several_statements(self, path: str) -> bool:
        """Whether a `set` line the grammar refuses gives a leaf its value and
        goes on with another statement of the same level: `hold-time up 0
        down 0`. The device takes this typed form, but `show configuration |
        display set` writes one statement a line, and set input is read as a
        device exports it (ARCHITECTURE.md section 8), so it is named
        unsupported rather than invalid; conversion reads it. Without a
        structure tree the line stays invalid."""
        tree = self._structure_tree(required=False)
        if tree is None:
            return False
        tokens = set_tokens(path)
        target = meta_target(tokens, tree)
        if target.kind != "value" or target.at + 1 >= len(tokens):
            return False
        siblings = statement_children(target.node or {})
        if statement_key(siblings, tokens[target.at + 1]) not in siblings:
            return False
        # Each statement must stand on a line of its own: the first, and the
        # rest at the same level, itself several or one.
        level, rest = tokens[: target.at - 1], tokens[target.at + 1 :]
        return self._parses("set " + " ".join(tokens[: target.at + 1])) and (
            self._parses("set " + " ".join(level + rest))
            or self._holds_several_statements(" ".join(level + rest))
        )

    def _parses(self, command: str) -> bool:
        """Whether the grammar takes *command* whole."""
        try:
            self._parser.parse(command)
        except UnexpectedInput:
            return False
        return True

    def _structure_tree(self, *, required: bool = True) -> dict[str, Any] | None:
        """The structure tree beside the grammar, loaded the first time a line
        needs it; a verb line cannot be judged without one."""
        if self._tree is None:
            try:
                tree = load_schema_tree(self._directory)
            except ValueError as e:
                if not required:
                    return None
                raise SchemaLoadError(f"{e}: a verb line is judged by the structure tree") from e
            if tree is None:
                if not required:
                    return None
                raise SchemaLoadError(
                    "No junos-structure-tree.json beside the grammar: "
                    "a verb line is judged by the structure tree"
                )
            self._tree = tree
        return self._tree


#: A value no keyword of the grammar spells: what a leaf takes where a verb's
#: path stops before the value.
_ANY_VALUE = "junoscfg-any-value"


def _compile(grammar_text: str) -> Lark:
    """The parser for a grammar; one per grammar file and process, through the cache."""
    return Lark(grammar_text, parser="earley", propagate_positions=True)
