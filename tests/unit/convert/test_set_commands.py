"""Raw set commands must be read or refused, never silently discarded.

OPEN-7 rejection-only owner decision; edit feature support is deferred.
Synthetic inputs exercise public doors independently of grammar regeneration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner

from junoscfg import Format, convert_config, convert_config_result, validate_config, validate_set
from junoscfg.anonymize import AnonymizeConfig
from junoscfg.cli import main
from junoscfg.convert import pipeline, pipeline_result, to_dict
from junoscfg.input import InputError
from junoscfg.validate import SetValidator

if TYPE_CHECKING:
    from collections.abc import Callable

UNSUPPORTED = (
    'annotate system "a note"',
    "insert system ntp server 10.0.0.2 before server 10.0.0.1",
    "replace pattern router1 with router2",
    "replace system host-name router2",
    "rename system host-name router1 to router2",
    "copy system host-name router1 to router2",
    "edit system",
    "top",
    "up",
    "wildcard delete interfaces ge-*",
    "unprotect system",
    "load merge terminal",
    "commit",
    "status",
    "show system",
    "foo bar baz",
    "set",
    "deactivate",
    "protect",
    "delete",
    "activate",
    "setting system host-name router2",
    "set\tsystem host-name router2",
)
BASE = "set system host-name router1"


def refusal(line: int) -> str:
    """The shared lexical diagnostic includes only a physical line number."""
    return f"Unsupported command in set input on line {line}"


@pytest.mark.parametrize("command", UNSUPPORTED)
def test_unsupported_commands_are_refused(command: str) -> None:
    source = f"# ignored\n{BASE}\n\n/* ignored\n comment */ {command}\n"
    with pytest.raises(InputError) as caught:
        to_dict(source, "set")
    assert caught.value.lineno == 5
    assert str(caught.value) == refusal(5)


@pytest.mark.parametrize("door", (convert_config, convert_config_result, pipeline, pipeline_result))
@pytest.mark.parametrize("target", (Format.JSON, Format.YAML, Format.SET, Format.STRUCTURED))
@pytest.mark.parametrize("validate,strict", ((False, False), (True, False), (True, True)))
def test_conversion_doors_refuse_before_rendering(
    door: Callable[..., object], target: Format, validate: bool, strict: bool
) -> None:
    source = f'{BASE}\nannotate system "a note"'
    options = {"validate": validate, "strict": strict}
    if door in (convert_config, convert_config_result):
        options.update(from_format=Format.SET, to_format=target)
    else:
        options.update(from_format="set", to_format=target.value)
    with pytest.raises(InputError) as caught:
        door(source, **options)
    assert str(caught.value) == refusal(2)


def test_anonymized_refusal_withholds_source() -> None:
    source = f'{BASE}\nannotate system "203.0.114.9 secret-marker"'
    with pytest.raises(ValueError) as caught:
        convert_config(
            source,
            from_format=Format.SET,
            to_format=Format.JSON,
            validate=False,
            anon_config=AnonymizeConfig(ips=True, salt="s"),
        )
    assert "line 2" in str(caught.value)
    assert "203.0.114.9" not in str(caught.value)
    assert "secret-marker" not in str(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


@pytest.mark.parametrize("anonymize", (False, True))
def test_cli_refusal_has_no_partial_output(anonymize: bool) -> None:
    args = ["convert", "-i", "set", "-e", "json", "--no-field-validate"]
    if anonymize:
        args += ["--anonymize-ips", "--anonymize-salt", "s"]
    result = CliRunner().invoke(main, args, input=f'{BASE}\nannotate system "secret-marker"')
    assert result.exit_code == 2
    assert result.stdout == ""
    assert "line 2" in result.stderr
    assert "secret-marker" not in result.stderr
    if not anonymize:
        assert refusal(2) in result.stderr


def test_validation_doors_collect_value_free_command_errors(artifacts_dir: str) -> None:
    source = (
        f'{BASE}\n# ignored\nannotate system "secret-marker"\n\n'
        "/* ignored */ insert system ntp server 10.0.0.2 before server 10.0.0.1"
    )
    validator = SetValidator(f"{artifacts_dir}/junos-set.lark")
    results = (
        validator.validate(source),
        validate_set(source, artifacts_dir=artifacts_dir),
        validate_config(source, format=Format.SET, artifacts_dir=artifacts_dir),
    )
    for result in results:
        assert not result.valid
        assert [(error.line, error.message) for error in result.errors] == [
            (3, refusal(3)),
            (5, refusal(5)),
        ]


@pytest.mark.parametrize("anonymize", (False, True))
def test_cli_validation_refuses_without_conversion(artifacts_dir: str, anonymize: bool) -> None:
    args = ["convert", "-i", "set", "-v", "--artifacts", artifacts_dir]
    if anonymize:
        args += ["--anonymize-ips", "--anonymize-salt", "s"]
    result = CliRunner().invoke(main, args, input=f'{BASE}\nannotate system "secret-marker"')
    assert result.exit_code == 1
    assert "line 2" in result.stderr.lower()
    assert "secret-marker" not in result.stderr
    if not anonymize:
        assert refusal(2) in result.stderr


@pytest.mark.parametrize(
    "verb,metadata",
    (
        ("deactivate", {"inactive": True}),
        ("protect", {"protect": "protect"}),
        ("delete", {"operation": "delete"}),
        ("activate", {"active": "active"}),
    ),
)
def test_supported_commands_keep_their_metadata(verb: str, metadata: dict[str, object]) -> None:
    assert to_dict(f"{BASE}\n{verb} system host-name", "set") == {
        "system": {"host-name": "router1", "@host-name": metadata}
    }


def test_comments_and_command_words_in_values_remain_content() -> None:
    source = (
        "# annotate ignored\n\n/* insert\nreplace ignored */ set system host-name router1\n"
        'set interfaces ge-0/0/0 description "annotate insert replace pattern"'
    )
    assert to_dict(source, "set") == {
        "system": {"host-name": "router1"},
        "interfaces": {
            "interface": [{"name": "ge-0/0/0", "description": "annotate insert replace pattern"}]
        },
    }
    assert to_dict("# annotate ignored\n/* insert ignored */\n", "set") == {}


def test_bracket_refusal_keeps_precedence() -> None:
    source = "annotate system [ foo ]"
    with pytest.raises(InputError) as caught:
        to_dict(source, "set")
    assert caught.value.lineno == 1
    assert str(caught.value) == f"Unsupported bracket syntax in set input on line 1:\n{source}"


def test_audit_rejects_before_emitting_findings() -> None:
    source = (
        'set policy-options policy-statement pol-a then accept\nannotate system "secret-marker"'
    )
    result = CliRunner().invoke(main, ["audit", "unused", "-i", "set"], input=source)
    assert result.exit_code == 2
    assert result.stdout == ""
    assert refusal(2) in result.stderr
    assert "secret-marker" not in result.stderr
