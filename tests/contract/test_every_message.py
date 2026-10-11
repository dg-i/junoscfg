"""No message of an anonymized run quotes the configuration, through any door.

An anonymized run is one whose `anon_config` enables a rule: `convert_config`,
`convert_config_result` (the `pipeline` behind them) and `junoscfg convert
--anonymize-*`. Each door below is a place a message leaves such a run: the
conversion's diagnostics, `FieldValidationError`, a refusal to read the input,
the structured writer's notes, the `anonymize:` warnings, the read notes, and
on the command line `-v` (with `-e` and validate-only), `--strict` and the
error lines. Each row drives one door with a configuration whose words a
reader would recognise (an address, its pseudonym, an entry name, a word no
rule replaces) and asserts that none of them appears in an anonymized run, and
that the same run without anonymization still prints the door's own message.

Lesson #1 of the makeover run ("no original value may reach a diagnostic, a
warning, stderr or a ValidationError in an anonymized run"), NEW-R1, NEW-R4,
NEW-R9, NEW-R10; spec anonymization/placed-values. A word no rule replaced is
an original value too (change anonymize-every-placed-value, C12), and a
pseudonym in a message ties the output back to its place: neither is quoted.
`log_level="debug"` pairs each original with its replacement by design.

Synthetic values only, as AGENTS.md names them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING

import pytest
import yaml
from click.testing import CliRunner
from ipanon import PassThroughCollisionError

from junoscfg import FieldValidationError, Format, convert_config, convert_config_result
from junoscfg.anonymize import AnonymizeConfig
from junoscfg.cli import main

if TYPE_CHECKING:
    from collections.abc import Callable

ADDRESS = "203.0.114.9"
SALT = "s"


def _config(**options: object) -> AnonymizeConfig:
    return AnonymizeConfig(ips=True, salt=SALT, **options)  # type: ignore[arg-type]


@cache
def _pseudonym() -> str:
    """The address's replacement under the run's salt."""
    out = convert_config(
        f"set system name-server {ADDRESS}\n",
        from_format=Format.SET,
        to_format=Format.SET,
        anon_config=_config(),
    )
    return out.split()[-1]


@dataclass(frozen=True)
class Door:
    """One way a message leaves a run, and the words of the input it must not quote.

    ``run(anonymized)`` returns the exit code (``None`` for the library) and
    every message text the door produced. ``kept`` is a fragment of the door's
    own message that a run without anonymization still prints; ``None`` for a
    door only an anonymized run opens.
    """

    run: Callable[[bool], tuple[int | None, str]]
    words: tuple[str, ...]
    kept: str | None


def _library(
    source: str, fmt: Format, to: Format = Format.SET, **options: object
) -> Callable[[bool], tuple[int | None, str]]:
    def run(anonymized: bool) -> tuple[int | None, str]:
        anon = _config(**options) if anonymized else None
        try:
            result = convert_config_result(source, from_format=fmt, to_format=to, anon_config=anon)
        except FieldValidationError as error:
            details = [f"{e.path} {e.message} {e.value}" for e in error.result.errors]
            return None, "\n".join([str(error), *details])
        except (ValueError, yaml.YAMLError, PassThroughCollisionError) as error:
            return None, f"{type(error).__name__}: {error}"
        return None, "\n".join(d.render() for d in result.diagnostics)

    return run


def _strict(source: str, fmt: Format) -> Callable[[bool], tuple[int | None, str]]:
    def run(anonymized: bool) -> tuple[int | None, str]:
        with pytest.raises(FieldValidationError) as raised:
            convert_config_result(
                source,
                from_format=fmt,
                to_format=Format.SET,
                strict=True,
                anon_config=_config() if anonymized else None,
            )
        details = [f"{e.path} {e.message} {e.value}" for e in raised.value.result.errors]
        return None, "\n".join([str(raised.value), *details])

    return run


def _cli(source: str, args: list[str], *options: str) -> Callable[[bool], tuple[int | None, str]]:
    def run(anonymized: bool) -> tuple[int | None, str]:
        flags = ["--anonymize-ips", "--anonymize-salt", SALT, *options] if anonymized else []
        result = CliRunner().invoke(main, ["convert", *args, *flags], input=source)
        text = result.stderr  # stdout is the output, which carries the configuration
        if result.exception is not None and not isinstance(result.exception, SystemExit):
            text += f"\n{type(result.exception).__name__}: {result.exception}"
        return result.exit_code, text

    return run


_BRACKET = f"set system name-server [ {ADDRESS} ]\n"
_NO_SEMICOLON = f"system {{\n    host-name {ADDRESS}\n}}\n"
_BROKEN_YAML = f"configuration:\n  system: [{ADDRESS}\n"
_BROKEN_XML = f"<configuration><system><host-name>{ADDRESS}</host-name></sys-acme></configuration>"
_ENUM_WORD = "set system services ssh protocol-version v9-acme\n"
_ENUM_ADDRESS = f"set system services ssh protocol-version {ADDRESS}\n"
_UNKNOWN_KEY = json.dumps({"configuration": {"system": {f"bogus-knob {ADDRESS}": None}}})
_FAMILY_TAG = json.dumps(
    {
        "configuration": {
            "protocols": {
                "bgp": {
                    "group": [
                        {
                            "name": "G-PEERS",
                            "neighbor": [
                                {
                                    "name": ADDRESS,
                                    "family": {
                                        "@": {"inactive": True},
                                        "inet": {"unicast": {}},
                                    },
                                }
                            ],
                        }
                    ]
                }
            }
        }
    }
)
_EMPTY_BLOCK = "interfaces {\n    ge-0/0/9 {\n    }\n}\n"

#: door id -> the door. Words of the input are checked as written; the
#: address's pseudonym is checked on every door (`_pseudonym`).
DOORS: dict[str, Door] = {
    # -- the library: ConversionResult.diagnostics, raised errors -------------
    "field-validation-word": Door(_library(_ENUM_WORD, Format.SET), ("v9-acme",), "v9-acme"),
    "field-validation-address": Door(_library(_ENUM_ADDRESS, Format.SET), (ADDRESS,), ADDRESS),
    "field-validation-strict": Door(_strict(_ENUM_WORD, Format.SET), ("v9-acme",), "v9-acme"),
    "field-validation-unplaced": Door(
        _library(_UNKNOWN_KEY, Format.JSON), ("bogus-knob", ADDRESS), "bogus-knob"
    ),
    "unplaced-strict": Door(_strict(_UNKNOWN_KEY, Format.JSON), ("bogus-knob", ADDRESS), "bogus"),
    "read-set-bracket": Door(_library(_BRACKET, Format.SET), (ADDRESS,), ADDRESS),
    "read-structured": Door(_library(_NO_SEMICOLON, Format.STRUCTURED), (ADDRESS,), ADDRESS),
    "read-yaml": Door(_library(_BROKEN_YAML, Format.YAML), (ADDRESS,), ADDRESS),
    "read-xml": Door(_library(_BROKEN_XML, Format.XML), ("sys-acme",), "sys-acme"),
    "read-json": Door(
        _library(f'{{"configuration": [{ADDRESS}', Format.JSON), (ADDRESS,), "Expecting"
    ),
    "read-note": Door(_library(_EMPTY_BLOCK, Format.STRUCTURED), ("ge-0/0/9",), "ge-0/0/9"),
    "structured-writer-note": Door(
        _library(_FAMILY_TAG, Format.JSON, Format.STRUCTURED),
        ("G-PEERS", ADDRESS),
        "G-PEERS",
    ),
    "pass-through-collision": Door(
        lambda anonymized: _library(
            f"set system name-server {ADDRESS}\n",
            Format.SET,
            preserve_prefixes=[f"{_pseudonym()}/32"],
        )(anonymized),
        (ADDRESS,),
        None,
    ),
    # -- the command line: stderr and stdout, exit codes ------------------------
    "cli-validate-set": Door(
        _cli(f"set system bogus-statement {ADDRESS}\n", ["-i", "set", "-v", "-e", "set"]),
        ("bogus-statement", ADDRESS),
        "bogus-statement",
    ),
    "cli-validate-only-set": Door(
        _cli(f"set system bogus-statement {ADDRESS}\n", ["-i", "set", "-v"]),
        ("bogus-statement", ADDRESS),
        "bogus-statement",
    ),
    "cli-validate-only-bracket": Door(_cli(_BRACKET, ["-i", "set", "-v"]), (ADDRESS,), ADDRESS),
    "cli-validate-only-line": Door(
        _cli(f"bogus-command {ADDRESS}\n", ["-i", "set", "-v"]),
        ("bogus-command", ADDRESS),
        "bogus-command",
    ),
    "cli-validate-only-structured": Door(
        _cli(f"system {{\n    bogus-knob {ADDRESS};\n}}\n", ["-i", "structured", "-v"]),
        ("bogus-knob", ADDRESS),
        "bogus-knob",
    ),
    "cli-validate-only-structured-refusal": Door(
        _cli(_NO_SEMICOLON, ["-i", "structured", "-v"]), (ADDRESS,), ADDRESS
    ),
    "cli-validate-only-json": Door(
        _cli(_UNKNOWN_KEY, ["-i", "json", "-v"]), ("bogus-knob", ADDRESS), "bogus-knob"
    ),
    "cli-validate-only-yaml": Door(
        _cli("configuration:\n  system:\n    bogus-knob: x\n", ["-i", "yaml", "-v"]),
        ("bogus-knob",),
        "bogus-knob",
    ),
    "cli-validate-only-yaml-parse": Door(
        _cli(_BROKEN_YAML, ["-i", "yaml", "-v"]), (ADDRESS,), ADDRESS
    ),
    "cli-validate-only-schema-load": Door(
        _cli(
            f"<configuration><system><host-name>{ADDRESS}</host-name></system></configuration>",
            ["-i", "xml", "-v"],
        ),
        (ADDRESS,),
        "XSD",
    ),
    "cli-validate-warning": Door(
        _cli(_EMPTY_BLOCK, ["-i", "structured", "-v"]), ("ge-0/0/9",), "ge-0/0/9"
    ),
    "cli-field-validation": Door(
        _cli(_ENUM_WORD, ["-i", "set", "-e", "set"]), ("v9-acme",), "v9-acme"
    ),
    "cli-strict": Door(
        _cli(_ENUM_WORD, ["-i", "set", "-e", "set", "--strict"]), ("v9-acme",), "v9-acme"
    ),
    "cli-read-bracket": Door(_cli(_BRACKET, ["-i", "set", "-e", "json"]), (ADDRESS,), ADDRESS),
    "cli-read-structured": Door(
        _cli(_NO_SEMICOLON, ["-i", "structured", "-e", "set"]), (ADDRESS,), ADDRESS
    ),
    "cli-read-yaml": Door(_cli(_BROKEN_YAML, ["-i", "yaml", "-e", "set"]), (ADDRESS,), ADDRESS),
    "cli-read-xml": Door(_cli(_BROKEN_XML, ["-i", "xml", "-e", "set"]), ("sys-acme",), "sys-acme"),
    "cli-structured-writer-note": Door(
        _cli(_FAMILY_TAG, ["-i", "json", "-e", "structured"]), ("G-PEERS", ADDRESS), "G-PEERS"
    ),
    "cli-anonymize-warning": Door(
        _cli(_UNKNOWN_KEY, ["-i", "json", "-e", "set"]), ("bogus-knob",), "bogus-knob"
    ),
}

_KEPT = {name: door for name, door in DOORS.items() if door.kept is not None}


class TestAnAnonymizedRunQuotesNothingOfTheConfiguration:
    """Every door of an anonymized run names places by schema path, count and
    line, never by a word of the configuration, original or replaced."""

    @pytest.mark.parametrize("name", list(DOORS))
    def test_no_message_holds_a_word_of_it(self, name: str) -> None:
        door = DOORS[name]
        code, text = door.run(True)
        assert text.strip(), f"{name}: the door printed nothing, so nothing was scanned"
        for word in (*door.words, _pseudonym()):
            assert word not in text, f"{name}: {word!r} in {text!r}"
        if door.kept is not None:
            plain_code, _ = door.run(False)
            assert code == plain_code, f"{name}: anonymizing changed the exit code"


class TestARunThatDoesNotAnonymizeKeepsItsMessages:
    """Without anonymization every door prints its own message, the words included."""

    @pytest.mark.parametrize("name", list(_KEPT))
    def test_the_message_quotes_the_configuration(self, name: str) -> None:
        door = _KEPT[name]
        _, text = door.run(False)
        assert door.kept is not None
        assert door.kept in text, f"{name}: {door.kept!r} not in {text!r}"


class TestOnlyTheDebugLevelPrintsOriginals:
    """`log_level="debug"` pairs each original with its replacement, by design
    and documented (CLI help, `AnonymizeConfig.log_level`, the CLI guide); no
    other level prints one."""

    def test_debug_pairs_each_original_with_its_replacement(self) -> None:
        result = convert_config_result(
            f"set system name-server {ADDRESS}\n",
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=_config(log_level="debug"),
        )
        debug = [d.render() for d in result.diagnostics if d.severity == "debug"]
        assert any(ADDRESS in line and _pseudonym() in line for line in debug), debug

    @pytest.mark.parametrize("level", ["quiet", "normal"])
    def test_no_other_level_does(self, level: str) -> None:
        result = convert_config_result(
            f"set system name-server {ADDRESS}\n",
            from_format=Format.SET,
            to_format=Format.SET,
            anon_config=_config(log_level=level),
        )
        assert result.output.strip(), "the run converted"
        assert not any(ADDRESS in d.render() for d in result.diagnostics)


class TestTheAuditHasNoAnonymizedRun:
    """`junoscfg audit` reads a configuration and never anonymizes it, so it
    opens no door of an anonymized run."""

    def test_it_takes_no_anonymize_option(self) -> None:
        result = CliRunner().invoke(
            main, ["audit", "unused", "--anonymize-ips"], input="set system host-name r1\n"
        )
        assert result.exit_code == 2
        assert "No such option" in result.output
