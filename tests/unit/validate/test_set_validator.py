"""`SetValidator`: a verdict per line of display-set input, against one grammar file.

Everything here runs on the minimal grammar of `tests/support/artifacts.py`,
with the structure tree that knows what it knows, or on the small grammar with
a list and a leaf-list below, so it tests the class, not a grammar. What the
shipped grammar accepts and rejects is evidence, in
`tests/corpus/test_shipped_artifacts.py`; that every validation door agrees on
it is `tests/contract/test_every_door.py`.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from junoscfg import Format, validate_config, validate_set
from junoscfg.validate import SchemaLoadError, SetValidator, ValidationError
from tests.support.artifacts import make_artifacts_dir, write_minimal_tree

if TYPE_CHECKING:
    from pathlib import Path

    from tests.support.artifacts import MinimalArtifacts


@pytest.fixture
def minimal(tmp_path: Path) -> MinimalArtifacts:
    return make_artifacts_dir(tmp_path)


@pytest.fixture
def validator(minimal: MinimalArtifacts) -> SetValidator:
    write_minimal_tree(minimal.directory)
    return SetValidator(minimal.grammar)


#: A grammar and its structure tree with a list keyed by name, a list inside
#: it, a leaf-list and a leaf: what a verb line may and may not name.
_LISTS_GRAMMAR = """\
start: SET configuration
configuration: "system" system? | "policy-options" policy_options?
system: "host-name" VALUE | "domain-search" VALUE | "services" services?
services: "ssh"
policy_options: "policy-statement" policy_statement__list
policy_statement__list: VALUE ("term" term__list)?
term__list: VALUE ("then" then?)?
then: "accept"

SET: "set"
VALUE: /\\S+/

%import common.WS
%ignore WS
"""
_NAME = {"l": True, "nk": True}
_LISTS_TREE = {
    "c": {
        "system": {
            "c": {
                "host-name": {"l": True},
                "domain-search": {"l": True, "ll": True},
                "services": {"c": {"ssh": {"p": True}}},
            }
        },
        "policy-options": {
            "c": {
                "policy-statement": {
                    "L": True,
                    "c": {
                        "name": _NAME,
                        "term": {
                            "L": True,
                            "c": {"name": _NAME, "then": {"c": {"accept": {"p": True}}}},
                        },
                    },
                }
            }
        },
    }
}


@pytest.fixture
def lists(tmp_path: Path) -> SetValidator:
    (tmp_path / "junos-set.lark").write_text(_LISTS_GRAMMAR, encoding="utf-8")
    (tmp_path / "junos-structure-tree.json").write_text(json.dumps(_LISTS_TREE), encoding="utf-8")
    return SetValidator(tmp_path / "junos-set.lark")


class TestSetValidator:
    def test_valid_set_command(self, validator: SetValidator) -> None:
        result = validator.validate("set system host-name router1")
        assert result.valid is True

    def test_valid_multiple_lines(self, validator: SetValidator) -> None:
        source = "set system host-name router1\nset interfaces description test\n"
        result = validator.validate(source)
        assert result.valid is True

    def test_invalid_set_command(self, validator: SetValidator) -> None:
        result = validator.validate("set bogus nonexistent")
        assert result.valid is False
        assert len(result.errors) > 0
        assert result.errors[0].line == 1

    def test_deactivate_line(self, validator: SetValidator) -> None:
        result = validator.validate("set system host-name router1\ndeactivate system host-name")
        assert result.valid is True

    def test_comment_lines_skipped(self, validator: SetValidator) -> None:
        source = "# This is a comment\nset system host-name router1\n"
        result = validator.validate(source)
        assert result.valid is True

    def test_empty_lines_skipped(self, validator: SetValidator) -> None:
        source = "\n\nset system host-name router1\n\n"
        result = validator.validate(source)
        assert result.valid is True

    def test_no_set_prefix_error(self, validator: SetValidator) -> None:
        result = validator.validate("system host-name router1")
        assert result.valid is False
        assert result.errors[0].message == "Unsupported command in set input on line 1"
        assert result.errors[0].line == 1

    def test_quoted_value(self, validator: SetValidator) -> None:
        result = validator.validate('set interfaces description "my interface"')
        assert result.valid is True

    def test_load_error(self) -> None:
        with pytest.raises(SchemaLoadError):
            SetValidator("/nonexistent/grammar.lark")


class TestEveryVerbIsValidated:
    """Every verb the set reader reads names a statement path the grammar judges.

    The device's display set prints `protect groups GR-PROTECTED` and, for a
    leaf, the path without its value: `deactivate groups GR-ISIS-TPL protocols
    isis interface <ge-*> max-hello-size` (vMX 23.2R2-S7.5 and QFX5120
    25.2R2-S1.5, `junoscfg-oracle.set.gz`). The validator took `set` and
    `deactivate` only and called every `protect` line no set command (change
    device-validation). Every door: `tests/contract/test_every_door.py`.
    """

    @pytest.mark.parametrize("verb", ["deactivate", "protect", "activate", "delete"])
    def test_a_verb_line_is_validated_as_its_path(self, validator: SetValidator, verb: str) -> None:
        source = (
            f"set system host-name router1\n{verb} system host-name\n{verb} system services ssh\n"
        )
        assert validator.validate(source).valid

    @pytest.mark.parametrize("verb", ["deactivate", "protect", "activate", "delete"])
    def test_an_invalid_path_after_a_verb_is_reported(
        self, validator: SetValidator, verb: str
    ) -> None:
        for line in (f"{verb} bogus nonexistent", f"{verb} system host-name a b"):
            result = validator.validate(line)
            assert not result.valid, line
            assert result.errors[0].message == f"Invalid syntax: {line}"

    @pytest.mark.parametrize("verb", ["deactivate", "protect", "activate", "delete"])
    @pytest.mark.parametrize(
        "path",
        ["system host-name router1", "system domain-search a.example"],
        ids=["a-leaf-value", "a-leaf-list-value"],
    )
    def test_a_verb_line_names_no_value(self, lists: SetValidator, verb: str, path: str) -> None:
        """A leaf's value, single or one of a leaf-list, is no statement: the
        QFX5120 25.2R2-S1.5 refuses `deactivate ... community 64496:2`
        ("syntax error, expecting ';', [Enter], or '|'"), and the set reader
        refuses both (probe A2, change device-probe-fixes)."""
        result = lists.validate(f"{verb} {path}")
        assert [e.message for e in result.errors] == [f"Invalid syntax: {verb} {path}"]
        assert lists.validate(f"set {path}").valid

    @pytest.mark.parametrize("verb", ["deactivate", "protect", "activate", "delete"])
    def test_a_verb_line_names_no_list_without_its_entry(
        self, lists: SetValidator, verb: str
    ) -> None:
        """A list's keyword without its entry's name is refused ("syntax error,
        expecting <identifier>", probe D5); the entry with its name, a list
        inside it with its own, a container and a leaf before its value are
        statements."""
        for path in ("policy-options policy-statement", "policy-options policy-statement P1 term"):
            result = lists.validate(f"{verb} {path}")
            assert [e.message for e in result.errors] == [f"Invalid syntax: {verb} {path}"]
        for path in (
            "policy-options policy-statement P1",
            "policy-options policy-statement P1 term T1",
            "policy-options policy-statement P1 term T1 then",
            "policy-options policy-statement P1 term T1 then accept",
            "policy-options",
            "system domain-search",
            "system host-name",
        ):
            assert lists.validate(f"{verb} {path}").valid, path

    def test_a_verb_line_without_a_structure_tree_is_a_load_error(
        self, minimal: MinimalArtifacts
    ) -> None:
        """What a verb line names is read from the structure tree beside the
        grammar; without one the validator cannot judge it, so it says which
        artifact is missing instead of a verdict. A `set` line needs no tree."""
        validator = SetValidator(minimal.grammar)
        assert validator.validate("set system host-name router1").valid
        with pytest.raises(SchemaLoadError, match="junos-structure-tree"):
            validator.validate("deactivate system host-name")

    def test_set_gives_a_leaf_its_value(self, validator: SetValidator) -> None:
        """Only the other verbs may stop before the value."""
        result = validator.validate("set system host-name")
        assert [e.message for e in result.errors] == ["Invalid syntax: set system host-name"]

    def test_another_verb_is_no_command(self, validator: SetValidator) -> None:
        result = validator.validate("show system host-name")
        assert [e.message for e in result.errors] == ["Unsupported command in set input on line 1"]

    def test_a_long_line_is_reported_whole(self, validator: SetValidator) -> None:
        """The owner's log showed `port 3276` for `port 32767`: the line was cut at 80."""
        line = "set interfaces description " + "x" * 70 + " trailing-word 32767"
        result = validator.validate(line)
        assert not result.valid
        assert result.errors[0].message == f"Invalid syntax: {line}"


def _bracket_error(line: str, lineno: int = 1) -> ValidationError:
    return ValidationError(
        message=f"Unsupported bracket syntax in set input on line {lineno}:\n{line}",
        line=lineno,
    )


class TestBracketShorthandIsALineError:
    """`[ a b ]` shorthand in raw set input is one line error, never an exception.

    Spec: validation/raw-set-input. The lexical check runs before the grammar,
    so the minimal grammar shows it as well as the shipped one does; the
    shipped artifacts through every door are in `tests/contract/test_every_door.py`.
    """

    COMMANDS = (
        "set system apply-groups [ foo bar ]",
        "delete system apply-groups [ foo bar ]",
        "deactivate system apply-groups [ foo bar ]",
        "activate system apply-groups [ foo bar ]",
        "protect system apply-groups [ foo bar ]",
        "replace system apply-groups [ foo bar ]",
    )

    def test_validation_doors_return_line_errors_without_throwing(
        self, validator: SetValidator, minimal: MinimalArtifacts
    ) -> None:
        line = self.COMMANDS[0]
        directory = str(minimal.directory)
        results = (
            validator.validate(line),
            validate_set(line, artifacts_dir=directory),
            validate_config(line, format=Format.SET, artifacts_dir=directory),
        )
        for result in results:
            assert result.valid is False
            assert result.errors == (_bracket_error(line),)

    @pytest.mark.parametrize("command", COMMANDS)
    def test_every_configuration_command_reports_it(
        self, validator: SetValidator, command: str
    ) -> None:
        assert validator.validate(command).errors == (_bracket_error(command),)

    def test_a_bracket_after_an_inline_comment_still_counts(self, validator: SetValidator) -> None:
        line = "/* ignored */ set system apply-groups [ foo bar ]"
        assert validator.validate(line).errors == (_bracket_error(line),)

    @pytest.mark.parametrize(
        "source",
        [
            '# ignored bracket [\nset interfaces description "64498:[2-6]....$"',
            "/* ignored\n[ still ignored ]\n*/\nset system host-name router1",
        ],
        ids=["in-a-comment-and-quotes", "in-a-block-comment"],
    )
    def test_a_bracket_the_line_does_not_show_is_none(
        self, validator: SetValidator, source: str
    ) -> None:
        assert validator.validate(source).valid is True

    def test_validation_collects_each_offending_line(self, validator: SetValidator) -> None:
        lines = [
            "# ignored bracket [",
            "set system apply-groups [ foo bar ]",
            "set system host-name router1",
            "delete system apply-groups ]",
        ]

        result = validator.validate("\n".join(lines))

        assert result.valid is False
        assert result.errors == (_bracket_error(lines[1], 2), _bracket_error(lines[3], 4))
