"""Write the IR as the Junos JSON object, in JSON text or in YAML text.

`junos_json_object` is the writer's object stage: the native Junos JSON
spellings applied to its own copy of the IR. The format ``json`` serializes the
object as JSON (`dict_to_json`), ``yaml-new`` as YAML (`dict_to_junos_yaml`);
neither reparses the other's text (spec conversion/junos-json-yaml).
"""

from __future__ import annotations

import copy
import json
from typing import Any

import yaml

from junoscfg.convert.ir import wrap_configuration
from junoscfg.display import load_schema_tree, schema_child
from junoscfg.input import find_non_json_value


def junos_json_object(config: Any, *, wrap: bool = True) -> Any:
    """The Junos JSON object for the IR *config*.

    When *wrap* is true, wraps the config in ``{"configuration": ...}``.
    Dict input receives native-format normalization so the output can be
    loaded on a Junos device. When *wrap* is false, *config* is a relative
    selection, the value under its path's last key (a mapping, a list, ``{}``,
    a flag or a scalar): its presence flags and entry key order are spelled as
    under that key in the absolute object (spec conversion/path-filtering).
    The normalization works on the writer's own copy: the caller's IR is
    never changed (spec conversion/writers).
    """
    config = copy.deepcopy(config)
    if isinstance(config, dict):
        config = _native_groups(config)
        _normalize_presence_flags(config)
        tree = load_schema_tree()
        _coerce_scalar_leaves(config, tree, tree)
    if not wrap:
        held = {"selection": config}
        _normalize_presence_flags(held)
        config = held["selection"]
    config = _ensure_name_first(config)
    return wrap_configuration(config) if wrap else config


def dict_to_json(config: Any, *, wrap: bool = True) -> str:
    """Render the IR as Junos JSON text: `junos_json_object` serialized as JSON."""
    return json.dumps(junos_json_object(config, wrap=wrap), indent=4, ensure_ascii=False) + "\n"


def _unshared(value: Any) -> Any:
    """*value* with every mapping and list its own object.

    JSON has no anchors or aliases, so the YAML spelling of a JSON object
    holds none either, even where a caller's selection shares one object twice
    (PyYAML anchors a mapping or list it meets again).
    """
    if isinstance(value, dict):
        return {key: _unshared(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_unshared(item) for item in value]
    return value


#: Line breaks YAML reads in a plain or single-quoted scalar but JSON keeps as
#: characters: NEL, LINE SEPARATOR, PARAGRAPH SEPARATOR.
_YAML_ONLY_BREAKS = ("\x85", "\u2028", "\u2029")


class _JunosYamlDumper(yaml.SafeDumper):
    """PyYAML's safe dumper, writing a string that holds a YAML-only line break
    double-quoted, where the break is escaped and reads back as written."""


def _represent_str(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    style = '"' if any(mark in value for mark in _YAML_ONLY_BREAKS) else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_JunosYamlDumper.add_representer(str, _represent_str)


def dict_to_junos_yaml(config: Any, *, wrap: bool = True) -> str:
    """Render the IR as yaml-new: `junos_json_object` serialized as YAML.

    Block style, keys in the object's order, Unicode as written: the layout
    of the ``yaml`` writer, with no anchors or aliases.

    Raises:
        ValueError: If the object holds a value no JSON document can hold (a
            date a ``yaml`` file gave unquoted, say), named by kind and path:
            yaml-new holds what JSON holds, and its reader would refuse it.
    """
    document = _unshared(junos_json_object(config, wrap=wrap))
    found = find_non_json_value(document)
    if found is not None:
        kind, path = found
        where = f"at {path}" if path else "at the top level"
        raise ValueError(
            f"Cannot write yaml-new: a {kind} {where} has no JSON spelling; quote it in the source"
        )
    return yaml.dump(
        document,
        Dumper=_JunosYamlDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )


def _coerce_scalar_leaves(
    obj: Any, schema_node: dict[str, Any] | None, root: dict[str, Any] | None
) -> None:
    """Walk the IR and coerce single-element arrays to scalars for single-leaf fields.

    YAML input may represent a single value as a one-element list
    (e.g. ``class: [super-user]``). When the schema marks the field as a
    plain leaf (``l``) rather than a leaf-list (``ll``), the Junos device
    expects a scalar — coerce it here so the output is loadable.

    Named-list arrays (``L``) and presence-flag arrays (``[null]``) are not
    coerced but are recursed into. ``@``-prefixed operational keys are skipped.
    """
    if not isinstance(obj, dict):
        return
    for key, value in obj.items():
        if key.startswith("@"):
            continue
        child = schema_child(schema_node, key, root)
        if isinstance(value, list):
            is_leaf = child and child.get("l") and not child.get("ll")
            if is_leaf and len(value) == 1 and value[0] is not None:
                obj[key] = value[0]
            else:
                # For transparent containers unwrapped in the IR (e.g. groups by
                # _native_groups), the schema has one extra level — navigate through it.
                item_schema = child
                if child is not None and "t" in child and "L" not in child and "l" not in child:
                    item_schema = child.get("c", {}).get(child["t"], child)
                for item in value:
                    if isinstance(item, dict):
                        _coerce_scalar_leaves(item, item_schema, root)
        elif isinstance(value, dict):
            _coerce_scalar_leaves(value, child, root)


def _ensure_name_first(obj: Any) -> Any:
    """Walk the IR and enforce Junos JSON key ordering in each dict.

    Two rules from the Junos JSON spec:
    1. ``"name"`` must be first in named-list array entries (non-``@`` keys).
    2. ``"@leaf-name"`` (leaf annotation) must appear directly after its
       corresponding ``"leaf-name"`` key.  Bare ``"@"`` (container annotation)
       is placed first and is unaffected by rule 2.
    """
    if isinstance(obj, list):
        return [_ensure_name_first(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _ensure_name_first(v) for k, v in _reorder_dict_keys(obj).items()}
    return obj


def _reorder_dict_keys(obj: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of *obj* with keys in Junos-compliant order.

    Order produced:
      1. Bare ``"@"`` container annotation (if present)
      2. ``"name"`` (if present) — must lead named-list entries
      3. All other non-``@`` keys, each immediately followed by its
         ``"@<key>"`` leaf annotation when one exists
      4. Any orphaned ``"@leaf-name"`` keys whose leaf is absent
    """
    bare_at = {"@": obj["@"]} if "@" in obj else {}
    leaf_ats: dict[str, Any] = {}
    non_at: dict[str, Any] = {}

    for k, v in obj.items():
        if k == "@":
            continue
        elif k.startswith("@"):
            leaf_ats[k] = v
        else:
            non_at[k] = v

    # name first among non-@ keys
    ordered_keys: list[str] = []
    if "name" in non_at:
        ordered_keys.append("name")
    ordered_keys.extend(k for k in non_at if k != "name")

    result: dict[str, Any] = {**bare_at}
    placed: set[str] = set()
    for k in ordered_keys:
        result[k] = non_at[k]
        at_k = f"@{k}"
        if at_k in leaf_ats:
            result[at_k] = leaf_ats[at_k]
            placed.add(at_k)

    for k, v in leaf_ats.items():
        if k not in placed:
            result[k] = v

    return result


def _native_groups(config: dict[str, Any]) -> dict[str, Any]:
    """Unwrap the ``groups`` transparent container for native Junos JSON.

    The set/structured parsers produce ``"groups": {"group": [...]}``,
    but native Junos JSON uses ``"groups": [...]`` directly.  All other
    transparent containers (interfaces, routing-instances, vlans, and
    ``uplink-failure-detection group``) keep their wrapper keys, as the XSD
    declares them: ``groups`` is the only exception, the one wrapper the XSD
    itself declares unbounded.
    """
    if "groups" in config and isinstance(config["groups"], dict):
        inner = config["groups"].get("group")
        if isinstance(inner, list):
            config = {**config, "groups": inner}
    return config


def _normalize_presence_flags(obj: Any) -> None:
    """Walk the IR and normalize presence flags to ``[null]``.

    Native Junos JSON uses ``[null]`` for presence flags.  Some input
    paths produce ``true`` or ``{}`` instead — normalize them.

    Keys starting with ``@`` are operational attributes (inactive,
    replace, etc.) and are skipped — their ``true`` values are
    legitimate booleans, not presence flags.
    """
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key.startswith("@"):
                continue
            value = obj[key]
            if value is True or (isinstance(value, dict) and not value):
                obj[key] = [None]
            elif isinstance(value, (dict, list)):
                _normalize_presence_flags(value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if item is True:
                obj[i] = [None]
            elif isinstance(item, dict):
                _normalize_presence_flags(item)
