"""`SetValidator`: a verdict per line of display-set input, against one grammar file.

Everything here runs on the minimal grammar of `tests/support/artifacts.py`,
so it tests the class, not a grammar. What the shipped grammar accepts and
rejects is evidence, in `tests/corpus/test_shipped_artifacts.py`; that every
validation door agrees on it is `tests/contract/test_every_door.py`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from junoscfg import Format, validate_config, validate_set
from junoscfg.validate import SchemaLoadError, SetValidator, ValidationError
from tests.support.artifacts import make_artifacts_dir

if TYPE_CHECKING:
    from pathlib import Path

    from tests.support.artifacts import MinimalArtifacts


@pytest.fixture
def minimal(tmp_path: Path) -> MinimalArtifacts:
    return make_artifacts_dir(tmp_path)


@pytest.fixture
def validator(minimal: MinimalArtifacts) -> SetValidator:
    return SetValidator(minimal.grammar)


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
        result = validator.validate(
            "set system host-name router1\ndeactivate system host-name router1"
        )
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
        assert "does not start with" in result.errors[0].message

    def test_quoted_value(self, validator: SetValidator) -> None:
        result = validator.validate('set interfaces description "my interface"')
        assert result.valid is True

    def test_load_error(self) -> None:
        with pytest.raises(SchemaLoadError):
            SetValidator("/nonexistent/grammar.lark")


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
