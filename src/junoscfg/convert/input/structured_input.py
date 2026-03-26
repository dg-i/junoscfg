"""Convert structured (curly-brace) configuration to the JSON dict IR.

Uses the existing SetConverter to get set commands, then feeds them
through set_to_dict for schema-guided dict construction.
"""

from __future__ import annotations

from typing import Any

from junoscfg.convert.input.set_input import set_to_dict
from junoscfg.display.set_converter import SetConverter


def structured_to_dict(source: str) -> dict[str, Any]:
    """Parse structured configuration into the IR dict."""
    set_commands = SetConverter(source).to_set()
    return set_to_dict(set_commands)
