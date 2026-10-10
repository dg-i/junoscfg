"""Tests for input normalization."""

from __future__ import annotations

from junoscfg.input import normalize


class TestRemoveComments:
    def test_removes_hash_comment_lines(self) -> None:
        text = "# a comment\nset system host-name foo"
        assert "set system host-name foo" in normalize(text)
        assert "# a comment" not in normalize(text)

    def test_removes_block_comments(self) -> None:
        text = "/* a comment */\nset system host-name foo"
        result = normalize(text)
        assert "set system host-name foo" in result
        assert "a comment" not in result

    def test_removes_multiline_block_comments(self) -> None:
        text = "/*\n * a comment\n */\nset system host-name foo"
        result = normalize(text)
        assert "set system host-name foo" in result

    def test_preserves_inline_content(self) -> None:
        text = "set system host-name foo  /* a comment */\nset system domain-name bar  # a comment"
        result = normalize(text)
        assert "set system host-name foo" in result


class TestCarriageReturn:
    def test_normalizes_crlf(self) -> None:
        text = "set foo\r\nset bar"
        result = normalize(text)
        assert "\r" not in result
        assert "set foo" in result
        assert "set bar" in result

    def test_normalizes_cr(self) -> None:
        text = "set foo\rset bar"
        result = normalize(text)
        assert "\r" not in result


class TestSquareBrackets:
    def test_joins_split_brackets(self) -> None:
        text = "set apply-groups [\nfoo\nbar\n];"
        result = normalize(text)
        assert "set apply-groups [ foo bar ];" in result

    def test_preserves_single_line_brackets(self) -> None:
        text = "set apply-groups [ foo bar ];"
        result = normalize(text)
        assert "set apply-groups [ foo bar ];" in result

    def test_unbalanced_open_bracket_raises(self) -> None:
        import pytest

        text = "set foo [\nbar"
        with pytest.raises(ValueError, match="Unclosed bracket"):
            normalize(text)

    def test_brackets_inside_quotes_ignored(self) -> None:
        """Brackets inside quoted strings don't count as bracket nesting."""
        text = 'set community members "64498:[2-6]....$"'
        result = normalize(text)
        assert 'set community members "64498:[2-6]....$"' in result

    def test_empty_input_returns_empty(self) -> None:
        assert normalize("") == ""
