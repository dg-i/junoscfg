"""edityaml: post-process YAML output by adding derived keys via rules."""

from __future__ import annotations

import copy

from junoscfg.edityaml.ansibilize import (
    ansibilize,
    ansibilize_multi,
    ansibilize_with_offset,
    format_output,
    format_output_with_offset,
)
from junoscfg.edityaml.path_walker import resolve_path
from junoscfg.edityaml.rules import load_rules_file, merge_rulesets, parse_inline_rules
from junoscfg.edityaml.transforms import apply_transform

__all__ = [
    "ansibilize",
    "ansibilize_multi",
    "ansibilize_with_offset",
    "apply_rules",
    "apply_transform",
    "format_output",
    "format_output_with_offset",
    "load_rules_file",
    "merge_rulesets",
    "parse_inline_rules",
    "resolve_path",
]


def apply_rules(data: dict, ruleset: dict) -> dict:
    """Apply all rules in *ruleset* to *data*, returning a modified copy.

    Each rule specifies a ``path`` (dot-separated with ``[*]`` wildcards)
    and a list of ``transforms`` to apply to every matching dict node.
    """
    result = copy.deepcopy(data)
    for rule in ruleset.get("rules", []):
        nodes = resolve_path(result, rule["path"])
        for node in nodes:
            for transform in rule.get("transforms", []):
                apply_transform(node, transform)
    return result
