"""Tests for the audit output rendering."""

from __future__ import annotations

import pytest

from junoscfg.audit.model import AuditResult, Finding, Occurrence
from junoscfg.audit.render import STYLE_CHOICES, render

UNUSED = Finding(
    type_name="policy-statement",
    name="dead-pol",
    path=("policy-options", "policy-statement", "dead-pol"),
    confidence="unused",
)

PROBABLY = Finding(
    type_name="policy-statement",
    name="half-pol",
    path=("policy-options", "policy-statement", "half-pol"),
    confidence="probably-unused",
    unresolved=(
        Occurrence(
            value="half-pol",
            path=("interfaces", "ge-0/0/0", "description", "half-pol"),
            schema_path=("interfaces", "interface", "description"),
            kind="leaf",
        ),
    ),
)

RESULT = AuditResult(
    findings=(UNUSED, PROBABLY),
    definitions_checked=3,
    types_audited=("policy-statement",),
)

EMPTY = AuditResult(findings=(), definitions_checked=2, types_audited=("policy-statement",))

PREFIX_CASES = [
    ("pathname", ""),
    ("delete-script", "delete "),
    ("show-script", "show "),
    ("show-configuration-script", "show configuration "),
    ("deactivate-script", "deactivate "),
]


class TestStyles:
    def test_style_choices_complete(self) -> None:
        assert len(STYLE_CHOICES) == 10
        assert "pathname" in STYLE_CHOICES
        assert "delete-script-verbose" in STYLE_CHOICES

    @pytest.mark.parametrize(("style", "prefix"), PREFIX_CASES)
    def test_command_prefix(self, style: str, prefix: str) -> None:
        output = render(RESULT, style)
        assert f"{prefix}policy-options policy-statement dead-pol\n" in output

    def test_unknown_style(self) -> None:
        with pytest.raises(ValueError, match="unknown output style"):
            render(RESULT, "csv")

    def test_empty_result_non_verbose(self) -> None:
        assert render(EMPTY, "pathname") == ""

    def test_empty_result_verbose_has_summary(self) -> None:
        output = render(EMPTY, "pathname-verbose")
        assert output == "# summary: 2 definitions checked, 0 unused, 0 probably-unused\n"


class TestNonVerbosePurity:
    @pytest.mark.parametrize("style", [case[0] for case in PREFIX_CASES])
    def test_only_command_lines(self, style: str) -> None:
        output = render(RESULT, style, include_probably_unused=True)
        lines = output.splitlines()
        assert lines
        assert all(line and not line.startswith("#") for line in lines)

    def test_pathname_exact(self) -> None:
        assert render(RESULT, "pathname") == (
            "policy-options policy-statement dead-pol\npolicy-options policy-statement half-pol\n"
        )


class TestDestructiveStyles:
    @pytest.mark.parametrize("style", ["delete-script", "deactivate-script"])
    def test_probably_unused_excluded_by_default(self, style: str) -> None:
        output = render(RESULT, style)
        assert "dead-pol" in output
        assert "half-pol" not in output

    @pytest.mark.parametrize("style", ["delete-script", "deactivate-script"])
    def test_include_probably_unused_flag(self, style: str) -> None:
        output = render(RESULT, style, include_probably_unused=True)
        assert "dead-pol" in output
        assert "half-pol" in output

    @pytest.mark.parametrize("style", ["pathname", "show-script", "show-configuration-script"])
    def test_non_destructive_styles_always_include_all(self, style: str) -> None:
        output = render(RESULT, style)
        assert "dead-pol" in output
        assert "half-pol" in output


class TestVerbose:
    def test_comment_blocks(self) -> None:
        output = render(RESULT, "pathname-verbose")
        assert "# unused: policy-statement dead-pol\n" in output
        assert "# probably-unused: policy-statement half-pol\n" in output
        assert '#   unresolved: interfaces ge-0/0/0 description half-pol = "half-pol"\n' in output

    def test_blank_line_before_every_comment_block(self) -> None:
        lines = render(RESULT, "pathname-verbose").splitlines()
        assert lines[0].startswith("#")  # no leading blank line
        for i, line in enumerate(lines):
            if line.startswith("# ") and i > 0:
                assert lines[i - 1] == "" or lines[i - 1].startswith("#")

    def test_summary_line(self) -> None:
        output = render(RESULT, "pathname-verbose")
        assert output.rstrip().endswith(
            "# summary: 3 definitions checked, 1 unused, 1 probably-unused"
        )

    def test_summary_reports_omitted_findings(self) -> None:
        output = render(RESULT, "delete-script-verbose")
        assert output.rstrip().endswith(
            "# summary: 3 definitions checked, 1 unused, 1 probably-unused,"
            " 1 finding(s) omitted from script output"
        )

    def test_omitted_finding_keeps_comment_but_no_command(self) -> None:
        output = render(RESULT, "delete-script-verbose")
        assert "# probably-unused: policy-statement half-pol" in output
        assert "delete policy-options policy-statement half-pol" not in output

    def test_duplicate_definition_hint(self) -> None:
        finding = Finding(
            type_name="policy-statement",
            name="twice",
            path=("policy-options", "policy-statement", "twice"),
            confidence="unused",
            duplicate_definition=True,
        )
        result = AuditResult(findings=(finding,), definitions_checked=1, types_audited=())
        output = render(result, "pathname-verbose")
        assert "# unused: policy-statement twice (duplicate definition)\n" in output


class TestQuoting:
    def test_token_with_space_is_quoted(self) -> None:
        finding = Finding(
            type_name="policy-statement",
            name="my policy",
            path=("policy-options", "policy-statement", "my policy"),
            confidence="unused",
        )
        result = AuditResult(findings=(finding,), definitions_checked=1, types_audited=())
        output = render(result, "delete-script")
        assert output == 'delete policy-options policy-statement "my policy"\n'
