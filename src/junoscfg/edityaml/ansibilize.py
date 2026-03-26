"""Ansibilize: extract leaf values into Ansible host_vars and templatize group_vars."""

from __future__ import annotations

import copy
import fnmatch
import ipaddress
import re

import yaml

from junoscfg.edityaml.path_walker import _parse_path, resolve_path_with_context

# MAC address regex patterns
_MAC_COLON_RE = re.compile(r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")
_MAC_DASH_RE = re.compile(r"^([0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2}$")
_MAC_DOT_RE = re.compile(r"^[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4}$")

# Trailing numeric pattern
_TRAILING_NUMERIC_RE = re.compile(r"^(.*?)(\d+)$")


def detect_value_type(value: str) -> str:
    """Detect the type of value for offset expression generation.

    Returns one of: ``'ip'``, ``'mac'``, ``'trailing_numeric'``.
    Raises :class:`ValueError` if none match.
    """
    # 1. IP address — split off /mask, validate with ipaddress module
    addr_part = value.split("/")[0]
    try:
        ipaddress.ip_address(addr_part)
        return "ip"
    except ValueError:
        pass

    # 2. MAC address
    if _MAC_COLON_RE.match(value) or _MAC_DASH_RE.match(value) or _MAC_DOT_RE.match(value):
        return "mac"

    # 3. Trailing numeric
    if _TRAILING_NUMERIC_RE.match(value):
        return "trailing_numeric"

    raise ValueError(f"cannot detect value type for offset expression: {value!r}")


def make_offset_expression(value: str, offset_var: str) -> str:
    """Generate Jinja2 offset expression based on detected value type."""
    vtype = detect_value_type(value)

    if vtype == "ip":
        parts = value.split("/", 1)
        addr_part = parts[0]
        expr = "{{ '" + addr_part + "' | ansible.utils.ipmath(" + offset_var + ") }}"
        if len(parts) == 2:
            expr += "/" + parts[1]
        return expr

    if vtype == "mac":
        if ":" in value:
            sep = ":"
            prefix = value.rsplit(":", 1)[0]
            last_group = value.rsplit(":", 1)[1]
        elif "-" in value:
            sep = "-"
            prefix = value.rsplit("-", 1)[0]
            last_group = value.rsplit("-", 1)[1]
        else:
            # Cisco dot format: AABB.CCDD.EEFF — last 2 hex chars of last group
            last_dot_group = value.rsplit(".", 1)[1]  # e.g. "EE55"
            prefix_part = value.rsplit(".", 1)[0] + "." + last_dot_group[:2]  # "AABB.CCDD.EE"
            last_hex = last_dot_group[2:]  # "55"
            decimal = int(last_hex, 16)
            return prefix_part + "{{ '%02x' % (" + str(decimal) + " + " + offset_var + ") }}"

        decimal = int(last_group, 16)
        return prefix + sep + "{{ '%02x' % (" + str(decimal) + " + " + offset_var + ") }}"

    # trailing_numeric
    m = _TRAILING_NUMERIC_RE.match(value)
    assert m is not None
    prefix_str = m.group(1)
    num_str = m.group(2)
    num_val = int(num_str)
    if len(num_str) > 1 and num_str[0] == "0":
        # Zero-padded
        width = len(num_str)
        return (
            prefix_str
            + "{{ '%0"
            + str(width)
            + "d' % ("
            + str(num_val)
            + " + "
            + offset_var
            + ") }}"
        )
    else:
        return prefix_str + "{{ " + str(num_val) + " + " + offset_var + " }}"


def split_leaf_from_path(path: str) -> tuple[str, str]:
    """Split the last key segment off *path* as the leaf.

    Returns ``(parent_path, leaf_key)``.  Raises :class:`ValueError` if the
    last segment is a wildcard (``[*]``, ``*``, glob) instead of a plain key.
    """
    segments = _parse_path(path)
    if not segments:
        raise ValueError("empty path — cannot determine leaf")
    last_key, last_kind = segments[-1]
    if last_kind != "key":
        raise ValueError(
            f"path must end with a plain key as the leaf, not a wildcard or match ({path!r})"
        )
    # Reconstruct the parent path from the original dot-separated string
    # We can't just rejoin parsed segments because bracket syntax gets parsed.
    # Instead, rsplit on the last dot.
    dot_idx = path.rfind(".")
    if dot_idx == -1:
        return "", last_key
    return path[:dot_idx], last_key


def sanitize_var_component(s: str) -> str:
    """Clean a string for use as part of an Ansible variable name."""
    result = re.sub(r"[^a-z0-9]", "_", s.lower())
    result = re.sub(r"_+", "_", result)
    return result.strip("_")


def generate_var_name(prefix: str, discriminators: list[str]) -> str:
    """Join prefix with sanitized discriminator components."""
    if not discriminators:
        return prefix
    parts = [sanitize_var_component(d) for d in discriminators]
    return prefix + "_" + "_".join(parts)


def ansibilize_multi(
    data: dict,
    pairs: list[tuple[str, str]],
    root_keys: list[str] | None = None,
) -> tuple[dict, dict]:
    """Extract leaf values for multiple prefix:path pairs in one pass.

    Each element of *pairs* is ``(prefix, path)``.  A single deep copy of
    *data* is made and all replacements are applied to it.

    *root_keys* controls which top-level keys to auto-descend into:

    - ``None`` (default): if there is exactly one top-level key and the
      path doesn't start with it, auto-descend into that key.
    - A list of shell glob patterns: descend into each top-level key
      matching any pattern and resolve paths inside each.

    Returns ``(merged_host_vars, group_vars)`` where *merged_host_vars*
    contains variables from all pairs and *group_vars* is the single deep
    copy with all leaves replaced by ``{{ variable_name }}`` strings.
    """
    group_vars = copy.deepcopy(data)
    host_vars: dict[str, object] = {}

    top_keys = list(group_vars.keys())

    for prefix, path in pairs:
        parent_path, leaf_key = split_leaf_from_path(path)

        if root_keys is not None:
            # Explicit root_keys mode: descend into each matching top-level key
            walk_roots = []
            for tk in top_keys:
                if any(fnmatch.fnmatch(tk, pat) for pat in root_keys):
                    walk_roots.append(group_vars[tk])
            if not walk_roots:
                # No keys matched — try against the top-level dict itself
                walk_roots = [group_vars]
        elif len(top_keys) == 1 and isinstance(group_vars[top_keys[0]], dict):
            # Auto-descend: single top-level key whose value is a dict
            single_key = top_keys[0]
            starts_with_single = path == single_key or path.startswith(single_key + ".")
            walk_roots = [group_vars] if starts_with_single else [group_vars[single_key]]
        else:
            walk_roots = [group_vars]

        for walk_root in walk_roots:
            walk_path = parent_path if parent_path else None
            if walk_path:
                matches = resolve_path_with_context(walk_root, walk_path, leaf_key)
            else:
                matches = [(walk_root, [])]
            for node, discriminators in matches:
                if leaf_key not in node:
                    continue
                var_name = generate_var_name(prefix, discriminators)
                host_vars[var_name] = node[leaf_key]
                node[leaf_key] = "{{ " + var_name + " }}"

    return host_vars, group_vars


def ansibilize(data: dict, path: str, prefix: str) -> tuple[dict, dict]:
    """Extract leaf values into host_vars and replace with Jinja2 references.

    The last segment of *path* is the leaf key to extract.  For example,
    ``"items[*].name"`` navigates to each item in ``items`` and extracts
    the ``name`` value.

    Returns ``(host_vars, group_vars)`` where *host_vars* maps variable names
    to original values and *group_vars* is a deep copy of *data* with those
    values replaced by ``{{ variable_name }}`` strings.

    The Jinja2 references are stored as plain strings. When serialized to YAML
    by :func:`format_output`, PyYAML automatically quotes them (e.g.
    ``"{{ var }}"``) which is required for valid Ansible YAML — see
    `Ansible YAML Syntax <https://docs.ansible.com/ansible/latest/reference_appendices/YAMLSyntax.html>`_.
    """
    return ansibilize_multi(data, [(prefix, path)])


def ansibilize_with_offset(
    data: dict,
    literal_pairs: list[tuple[str, str]],
    offset_pairs: list[tuple[str, str]],
    root_keys: list[str] | None = None,
    offset_var: str = "base_address_offset",
) -> tuple[dict, dict, dict]:
    """Extract leaf values with offset expressions for multi-router deployments.

    Returns ``(host_vars, offset_address_vars, group_vars_template)``.

    *literal_pairs* are processed exactly like :func:`ansibilize_multi` — values
    go into host_vars as literals.

    *offset_pairs* detect value types (IP/MAC/trailing numeric) and generate
    Jinja2 offset expressions into *offset_address_vars*.

    *host_vars* includes ``{offset_var: 0}`` for per-host override.
    """
    template = copy.deepcopy(data)
    host_vars: dict[str, object] = {}
    offset_vars: dict[str, str] = {}

    top_keys = list(template.keys())

    def _resolve_walk_roots(path: str) -> list[dict]:
        if root_keys is not None:
            walk_roots = []
            for tk in top_keys:
                if any(fnmatch.fnmatch(tk, pat) for pat in root_keys):
                    walk_roots.append(template[tk])
            if not walk_roots:
                walk_roots = [template]
            return walk_roots
        elif len(top_keys) == 1 and isinstance(template[top_keys[0]], dict):
            single_key = top_keys[0]
            starts_with_single = path == single_key or path.startswith(single_key + ".")
            return [template] if starts_with_single else [template[single_key]]
        else:
            return [template]

    # Process literal pairs — same as ansibilize_multi
    for prefix, path in literal_pairs:
        parent_path, leaf_key = split_leaf_from_path(path)
        for walk_root in _resolve_walk_roots(path):
            walk_path = parent_path if parent_path else None
            if walk_path:
                matches = resolve_path_with_context(walk_root, walk_path, leaf_key)
            else:
                matches = [(walk_root, [])]
            for node, discriminators in matches:
                if leaf_key not in node:
                    continue
                var_name = generate_var_name(prefix, discriminators)
                host_vars[var_name] = node[leaf_key]
                node[leaf_key] = "{{ " + var_name + " }}"

    # Process offset pairs — generate offset expressions
    for prefix, path in offset_pairs:
        parent_path, leaf_key = split_leaf_from_path(path)
        for walk_root in _resolve_walk_roots(path):
            walk_path = parent_path if parent_path else None
            if walk_path:
                matches = resolve_path_with_context(walk_root, walk_path, leaf_key)
            else:
                matches = [(walk_root, [])]
            for node, discriminators in matches:
                if leaf_key not in node:
                    continue
                var_name = generate_var_name(prefix, discriminators)
                value = str(node[leaf_key])
                offset_vars[var_name] = make_offset_expression(value, offset_var)
                node[leaf_key] = "{{ " + var_name + " }}"

    host_vars[offset_var] = 0
    return host_vars, offset_vars, template


def format_output(host_vars: dict, group_vars: dict) -> str:
    """Format host_vars and group_vars as two YAML documents separated by ``---``.

    Jinja2 references are quoted (e.g. ``"{{ var }}"``), which is required
    by Ansible. Values starting with ``{`` must be quoted in YAML or the
    YAML parser interprets them as flow mappings.
    """
    host_doc = yaml.dump(host_vars, default_flow_style=False)
    group_doc = yaml.dump(group_vars, default_flow_style=False)
    return host_doc + "---\n" + group_doc


def format_output_with_offset(host_vars: dict, offset_vars: dict, template: dict) -> str:
    """Format three YAML documents: host_vars, offset_vars, template.

    Separated by ``---`` lines, suitable for Ansible group_vars/host_vars split.
    """
    _kw: dict = {"default_flow_style": False, "width": 10000}
    host_doc = yaml.dump(host_vars, **_kw)
    offset_doc = yaml.dump(offset_vars, **_kw)
    template_doc = yaml.dump(template, **_kw)
    return host_doc + "---\n" + offset_doc + "---\n" + template_doc
