"""Rule file loading and inline argument parsing for edityaml."""

from __future__ import annotations

import re

import yaml


def load_rules_file(path: str) -> dict:
    """Load and validate a YAML rules file.

    Raises ``FileNotFoundError`` if *path* does not exist,
    ``yaml.YAMLError`` on parse failure, or ``ValueError`` if the
    top-level ``rules`` key is missing.
    """
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "rules" not in data:
        msg = "Rules file must contain a top-level 'rules' key"
        raise ValueError(msg)
    return data


def parse_inline_rules(path: str, set_exprs: list[str]) -> dict:
    """Parse ``--set`` CLI expressions into a ruleset dict.

    Each expression has the form ``target=expr`` where expr is one of:
    - ``regex_extract(key, 'pattern')`` or ``regex_extract(key, 'pattern', N)``
    - ``static(value)`` or a bare value
    - ``copy(key)``
    - ``template('string with {key} refs')``
    """
    transforms: list[dict] = []
    for expr in set_exprs:
        target, _, rhs = expr.partition("=")
        target = target.strip()
        rhs = rhs.strip()
        transforms.append(_parse_set_expr(target, rhs))

    return {"rules": [{"path": path, "transforms": transforms}]}


def merge_rulesets(*rulesets: dict) -> dict:
    """Combine multiple rulesets into one."""
    merged: list[dict] = []
    for rs in rulesets:
        merged.extend(rs.get("rules", []))
    return {"rules": merged}


# ── Inline expression parser ─────────────────────────────────────────


_REGEX_EXTRACT_RE = re.compile(
    r"""regex_extract\(\s*(\w[\w\-]*)\s*,\s*'([^']*)'\s*(?:,\s*(\d+))?\s*\)""",
)
_STATIC_RE = re.compile(r"""static\((.+)\)""")
_COPY_RE = re.compile(r"""copy\((\w[\w\-]*)\)""")
_TEMPLATE_RE = re.compile(r"""template\('([^']*)'\)""")


def _parse_set_expr(target: str, rhs: str) -> dict:
    m = _REGEX_EXTRACT_RE.match(rhs)
    if m:
        rule: dict = {
            "type": "regex_extract",
            "source": m.group(1),
            "pattern": m.group(2),
            "target": target,
        }
        if m.group(3):
            rule["group"] = int(m.group(3))
        return rule

    m = _COPY_RE.match(rhs)
    if m:
        return {"type": "copy", "source": m.group(1), "target": target}

    m = _TEMPLATE_RE.match(rhs)
    if m:
        return {"type": "template", "template": m.group(1), "target": target}

    m = _STATIC_RE.match(rhs)
    if m:
        return {"type": "static", "target": target, "value": _parse_static_value(m.group(1))}

    # Bare value -> static string
    return {"type": "static", "target": target, "value": rhs}


def _parse_static_value(raw: str) -> str | int | float | bool:
    """Parse a static value literal."""
    raw = raw.strip()
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    # Strip surrounding quotes if present
    if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
        return raw[1:-1]
    return raw
