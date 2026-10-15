"""Which implementation each format name selects.

This is the one place a format name meets its implementation. The readers
(`to_dict`), the writers (`from_dict`) and top-level validation dispatch on the
implementation id, never on the name, so renaming a format edits this table and
`junoscfg.Format` only (docs/decisions/2026-10-15-yaml-new-before-renaming-yaml.md).

Implementation ids:

- ``set``, ``structured``, ``xml``: the display-set, curly-brace and XML readers
  and writers (XML is input only).
- ``junos-json``: the Junos JSON object as JSON text.
- ``junos-yaml``: the same Junos JSON object as YAML text; it shares the JSON
  reader's and writer's object stages.
- ``ir-yaml``: the IR dumped as YAML, read with metadata cleanup and leaf-list
  promotion; planned to be named ``yaml-old``.
"""

from __future__ import annotations

#: Format name -> implementation id, in `junoscfg.Format` order. Read at each
#: call, never copied, so a test can rehearse the rename by patching it; callers
#: read it and do not change it.
FORMAT_IMPLEMENTATIONS: dict[str, str] = {
    "set": "set",
    "structured": "structured",
    "json": "junos-json",
    "yaml": "ir-yaml",
    "yaml-new": "junos-yaml",
    "xml": "xml",
}


def implementation(fmt: str, direction: str) -> str:
    """The implementation id *fmt* selects.

    Raises:
        ValueError: ``Unknown <direction> format: <fmt>`` for a name the table
            does not hold.
    """
    try:
        return FORMAT_IMPLEMENTATIONS[fmt]
    except KeyError:
        raise ValueError(f"Unknown {direction} format: {fmt}") from None
