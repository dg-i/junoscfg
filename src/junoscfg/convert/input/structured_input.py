"""Convert structured (curly-brace) configuration to the JSON dict IR.

`SetConverter` lexes the braces into statements, each with the tags that
lead its levels, and the set reader's schema walk builds the dict: one walk
for set and structured input, so a tag lands where the schema says the
statement it leads starts.
"""

from __future__ import annotations

from typing import Any

from junoscfg.convert.input.set_input import statements_to_dict
from junoscfg.display import SetConverter


def structured_to_dict(source: str) -> dict[str, Any]:
    """Parse structured configuration into the IR dict."""
    return statements_to_dict(SetConverter(source).statements())
