"""Output rendering for audit results.

Five styles, each with a ``-verbose`` variant: ``pathname`` (bare paths),
``delete-script``, ``show-script`` (configuration mode), ``show-configuration-script``
(operational mode), and ``deactivate-script``. Non-verbose output contains
only command/path lines (pipe- and paste-clean); verbose adds per-finding
comments and a summary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from junoscfg.display.value_format import format_value

if TYPE_CHECKING:
    from junoscfg.audit.model import AuditResult, Finding

_PREFIXES = {
    "pathname": "",
    "delete-script": "delete ",
    "show-script": "show ",
    "show-configuration-script": "show configuration ",
    "deactivate-script": "deactivate ",
}

# Styles whose output makes changes when pasted into a router session.
# These include only strict `unused` findings unless explicitly opted in.
_DESTRUCTIVE = frozenset({"delete-script", "deactivate-script"})

STYLE_CHOICES: tuple[str, ...] = tuple(
    variant for base in _PREFIXES for variant in (base, f"{base}-verbose")
)


def render(result: AuditResult, style: str, *, include_probably_unused: bool = False) -> str:
    """Render an audit result in the given output style.

    Args:
        result: The audit result.
        style: One of :data:`STYLE_CHOICES`.
        include_probably_unused: Include probably-unused findings in
            delete/deactivate script output (they are always shown in the
            non-destructive styles).

    Returns:
        The rendered text (empty when there is nothing to print).

    Raises:
        ValueError: On an unknown style name.
    """
    verbose = style.endswith("-verbose")
    base = style[: -len("-verbose")] if verbose else style
    if base not in _PREFIXES:
        raise ValueError(f"unknown output style: {style!r}")
    prefix = _PREFIXES[base]
    destructive = base in _DESTRUCTIVE

    lines: list[str] = []
    omitted = 0
    for finding in result.findings:
        in_script = finding.confidence == "unused" or include_probably_unused or not destructive
        if not in_script:
            omitted += 1
        if verbose:
            if lines:
                lines.append("")
            lines.extend(_comment_block(finding))
            if in_script:
                lines.append(prefix + _format_path(finding.path))
        elif in_script:
            lines.append(prefix + _format_path(finding.path))

    if verbose:
        if lines:
            lines.append("")
        summary = (
            f"# summary: {result.definitions_checked} definitions checked,"
            f" {result.n_unused} unused, {result.n_probably_unused} probably-unused"
        )
        if omitted:
            summary += f", {omitted} finding(s) omitted from script output"
        lines.append(summary)

    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _comment_block(finding: Finding) -> list[str]:
    """Build the verbose comment lines for one finding."""
    note = f"# {finding.confidence}: {finding.type_name} {finding.name}"
    if finding.duplicate_definition:
        note += " (duplicate definition)"
    block = [note]
    for occ in finding.unresolved:
        block.append(f'#   unresolved: {" ".join(occ.path)} = "{occ.value}"')
    return block


def _format_path(path: tuple[str, ...]) -> str:
    """Join path tokens into a command argument, quoting where needed.

    Embedded newlines are escaped so a single finding can never render as
    two physical lines — this keeps non-verbose output strictly one command
    per finding, even for adversarial hand-crafted object names.
    """
    return " ".join(format_value(token).replace("\n", "\\n").replace("\r", "\\r") for token in path)
