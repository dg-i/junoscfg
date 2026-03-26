"""Transform implementations for edityaml rules."""

from __future__ import annotations

import re


def apply_transform(node: dict, rule: dict) -> None:
    """Apply a single transform rule to a dict node (mutates in-place).

    Missing source keys are silently skipped.
    """
    transform_type = rule["type"]

    if transform_type == "regex_extract":
        _apply_regex_extract(node, rule)
    elif transform_type == "static":
        node[rule["target"]] = rule["value"]
    elif transform_type == "copy":
        _apply_copy(node, rule)
    elif transform_type == "rename":
        _apply_rename(node, rule)
    elif transform_type == "template":
        _apply_template(node, rule)
    elif transform_type == "conditional":
        _apply_conditional(node, rule)
    else:
        msg = f"Unknown transform type: {transform_type}"
        raise ValueError(msg)


def _apply_regex_extract(node: dict, rule: dict) -> None:
    source = rule["source"]
    if source not in node:
        return
    value = node[source]
    if not isinstance(value, str):
        return
    match = re.search(rule["pattern"], value)
    if match:
        group = rule.get("group", 1)
        node[rule["target"]] = match.group(group)


def _apply_copy(node: dict, rule: dict) -> None:
    source = rule["source"]
    if source in node:
        node[rule["target"]] = node[source]


def _apply_rename(node: dict, rule: dict) -> None:
    source = rule["source"]
    if source in node:
        node[rule["target"]] = node.pop(source)


def _apply_template(node: dict, rule: dict) -> None:
    import contextlib

    with contextlib.suppress(KeyError):
        node[rule["target"]] = rule["template"].format_map(node)


def _apply_conditional(node: dict, rule: dict) -> None:
    when = rule["when"]
    key = when["key"]
    if key not in node:
        return

    value = node[key]

    if "matches" in when:
        if not isinstance(value, str) or not re.search(when["matches"], value):
            return
    elif "equals" in when and value != when["equals"]:
        return

    for sub_rule in rule.get("transforms", []):
        apply_transform(node, sub_rule)
