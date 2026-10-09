"""Keep the committed CLI reference synchronized with Click declarations."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click
from tools.generate_cli_reference import render_cli_reference

from junoscfg.cli import main

if TYPE_CHECKING:
    from collections.abc import Iterator


def _walk_commands(
    command: click.Command, path: tuple[str, ...] = ("junoscfg",)
) -> Iterator[tuple[tuple[str, ...], click.Command]]:
    yield path, command
    if isinstance(command, click.Group):
        for name, child in sorted(command.commands.items()):
            yield from _walk_commands(child, (*path, name))


def test_generated_reference_is_current() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    committed = (repo_root / "docs/guide/cli-reference.md").read_text()
    assert committed == render_cli_reference()


def test_generated_reference_covers_every_command_and_declared_option() -> None:
    rendered = render_cli_reference()
    walked = list(_walk_commands(main))

    assert len(walked) > 1
    for path, command in walked:
        heading = f"## `{' '.join(path)}`"
        assert heading in rendered
        section = rendered.split(heading, 1)[1].split("\n## `", 1)[0]
        for param in command.params:
            if isinstance(param, click.Option):
                assert any(f"`{option}`" in section for option in param.opts)


def test_generated_reference_is_deterministic() -> None:
    assert render_cli_reference() == render_cli_reference()
