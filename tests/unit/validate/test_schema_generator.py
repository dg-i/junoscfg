"""Tests for JSON Schema generation from SchemaNode tree."""

from __future__ import annotations

import pytest

from junoscfg.validate import SchemaNode, generate_json_schema, parse_xsd
from tests.support.paths import TEST_DATA


def _make_tree() -> SchemaNode:
    """Build a test tree."""
    return SchemaNode(
        name="configuration",
        children={
            "system": SchemaNode(
                name="system",
                children={
                    "host-name": SchemaNode(name="host-name", is_leaf=True),
                    "services": SchemaNode(
                        name="services",
                        children={
                            "ssh": SchemaNode(name="ssh", is_presence=True),
                        },
                    ),
                },
            ),
            "interfaces": SchemaNode(
                name="interfaces",
                children={
                    "name": SchemaNode(name="name", is_leaf=True, is_key=True),
                    "unit": SchemaNode(
                        name="unit",
                        children={
                            "name": SchemaNode(name="name", is_leaf=True, is_key=True),
                        },
                        is_list=True,
                    ),
                },
                is_list=True,
            ),
        },
    )


class TestGenerateJsonSchema:
    def test_produces_draft7(self):
        schema = generate_json_schema(_make_tree())
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_has_configuration_property(self):
        schema = generate_json_schema(_make_tree())
        assert "configuration" in schema["properties"]

    def test_leaf_accepts_anything(self):
        schema = generate_json_schema(_make_tree())
        config = schema["properties"]["configuration"]
        system = config["properties"]["system"]
        hostname = system["properties"]["host-name"]
        assert hostname == {}  # Accept any value

    def test_presence_allows_null(self):
        schema = generate_json_schema(_make_tree())
        config = schema["properties"]["configuration"]
        system = config["properties"]["system"]
        services = system["properties"]["services"]
        ssh = services["properties"]["ssh"]
        assert "oneOf" in ssh
        types = [opt.get("type") for opt in ssh["oneOf"]]
        assert "null" in types

    def test_list_has_array(self):
        schema = generate_json_schema(_make_tree())
        config = schema["properties"]["configuration"]
        interfaces = config["properties"]["interfaces"]
        # `anyOf`, not `oneOf`: a container also accepts the bare-statement
        # renderings, so an array satisfies both branches and `oneOf` -- which
        # demands exactly one -- rejected every list junoscfg produced.
        assert "anyOf" in interfaces
        array_option = next(o for o in interfaces["anyOf"] if o.get("type") == "array")
        assert "items" in array_option

    def test_additional_properties_false(self):
        schema = generate_json_schema(_make_tree())
        assert schema["additionalProperties"] is False

    def test_mandatory_is_a_warning_not_a_schema_requirement(self):
        """`required` leaves the schema; mandatory stays a field-validator warning.

        This asserted the opposite. The 8,782 `required` arrays were inert
        behind the array escape; the moment entries were checked they rejected
        every fragment -- `set system login user admin uid 2000` for want of
        `class` -- which is what broke the first attempt at closing it.
        """
        root = SchemaNode(
            name="configuration",
            children={
                "required-field": SchemaNode(
                    name="required-field", is_leaf=True, is_mandatory=True
                ),
            },
        )
        schema = generate_json_schema(root)
        config = schema["properties"]["configuration"]
        assert "required" not in config

    def test_a_container_array_form_carries_an_items_constraint(self):
        """The array form is for `[null]` and leaf-list strings, never objects.

        `properties` and `additionalProperties` bind only objects, so a type
        union admitting `array` with no `items` let every list entry go
        unchecked: `{"configuration": "garbage"}` validated against the
        shipped schema. A bare string is not a container rendering either.
        """
        schema = generate_json_schema(_make_tree())
        system = schema["properties"]["configuration"]["properties"]["system"]
        assert "items" in system
        assert set(system["items"]["type"]) == {"null", "string"}
        assert "string" not in system["type"]

    def test_a_transparent_container_array_takes_its_child_entries(self):
        """`groups` holds `group` entries directly, so its array form carries
        objects -- bounded by that child's schema, not by nothing."""
        group = SchemaNode(
            name="group",
            is_list=True,
            children={"host-name": SchemaNode(name="host-name", is_leaf=True)},
        )
        groups = SchemaNode(name="groups", children={"group": group})
        groups.flags.add("transparent:group")
        root = SchemaNode(name="configuration", children={"groups": groups})
        schema = generate_json_schema(root)
        groups_schema = schema["properties"]["configuration"]["properties"]["groups"]
        alternatives = groups_schema["items"]["anyOf"]
        assert {"type": ["null", "string"]} in alternatives
        assert groups_schema["properties"]["group"] in alternatives

    def test_a_set_transparent_container_keeps_the_scalar_array_form(self):
        """`interfaces` is transparent in a set command, not in JSON.

        187 nodes carry a `transparent:` flag and only `groups` drops its
        wrapper when rendered as JSON; the others keep it --
        `{"interfaces": {"interface": [...]}}`. Giving every one of them the
        child-entry array form let `{"interfaces": [{...}]}` validate, a shape
        no device and no converter emits.
        """
        interface = SchemaNode(
            name="interface",
            is_list=True,
            children={"mtu": SchemaNode(name="mtu", is_leaf=True)},
        )
        interfaces = SchemaNode(name="interfaces", children={"interface": interface})
        interfaces.flags.add("transparent:interface")
        root = SchemaNode(name="configuration", children={"interfaces": interfaces})
        schema = generate_json_schema(root)
        node = schema["properties"]["configuration"]["properties"]["interfaces"]
        assert node["items"] == {"type": ["null", "string"]}

    def test_device_attribute_keys_are_named(self):
        """`@` carries what `| display json` puts on an element and junoscfg
        round-trips; `field_validator` skips the prefix, so the schema has to
        name it or it rejects junoscfg's own output."""
        schema = generate_json_schema(_make_tree())
        config = schema["properties"]["configuration"]
        assert "^@" in config["patternProperties"]


class TestYamlVariant:
    def test_yaml_allows_ansible_keys(self):
        schema = generate_json_schema(_make_tree(), variant="yaml")
        config = schema["properties"]["configuration"]
        assert "patternProperties" in config
        assert "^_ansible_" in config["patternProperties"]
        assert "^_meta_" in config["patternProperties"]

    def test_json_has_no_ansible_patterns(self):
        """The JSON variant carries the universal statements and nothing else.

        It used to carry no `patternProperties` at all. The four `apply-*`
        statements are legal at every level and junoscfg emits them, so the
        generator names the ones the tree declares, or the kernel's floor for a
        tree that declares none -- see `TestUniversalStatementsReachEveryContainer`.
        """
        schema = generate_json_schema(_make_tree(), variant="json")
        config = schema["properties"]["configuration"]
        assert "^_ansible_" not in config.get("patternProperties", {})
        assert "^_meta_" not in config.get("patternProperties", {})


class TestUniversalStatementsReachEveryContainer:
    """`apply-groups` and its siblings are legal at every hierarchy level.

    JSON and YAML validation rejected them at every level, including the top,
    because no NETCONF XSD models them and every container carries
    `additionalProperties: false`. This generator names them as one
    `patternProperties` entry per container — 123,769 containers, so a property
    per container would be four copies of each name in each of them.

    The names are the ones the tree declares through the `universal` flag, read
    through `junoscfg.display.universal_statements`: the tree is authoritative.
    A tree that declares none -- built before `_fix_apply_statements`, as the
    shipped one was until 0.8.0 -- gets the kernel's floor, because junoscfg
    emitted `apply-groups` and then rejected its own output for all three real
    device configurations. Until universal-statements-from-tree the generator
    unioned the floor with the tree's flags, so a tree could not leave one out.
    """

    @staticmethod
    def _tree(*names: str) -> SchemaNode:
        """The minimal tree with *names* (the four, by default) flagged universal."""
        tree = _make_tree()
        for name in names or ("apply-groups", "apply-groups-except", "apply-flags", "apply-macro"):
            node = SchemaNode(name=name, is_leaf=True, is_list=True)
            node.flags.add("universal")
            tree.children[name] = node
        return tree

    # The four universal names the fixed tree declares, and the floor names.
    _PATTERN = "^(apply\\-flags|apply\\-groups|apply\\-groups\\-except|apply\\-macro)$"

    def test_the_root_names_them(self) -> None:
        schema = generate_json_schema(self._tree())
        assert self._PATTERN in schema["properties"]["configuration"]["patternProperties"]

    def test_a_nested_container_names_them(self) -> None:
        schema = generate_json_schema(self._tree())
        system = schema["properties"]["configuration"]["properties"]["system"]
        assert self._PATTERN in system["patternProperties"]

    def test_the_yaml_variant_keeps_its_own_patterns(self) -> None:
        schema = generate_json_schema(self._tree(), variant="yaml")
        system = schema["properties"]["configuration"]["properties"]["system"]
        # `^@` is there in both variants: a device puts its attributes on an
        # element and junoscfg round-trips them.
        assert set(system["patternProperties"]) == {
            self._PATTERN,
            "^@",
            "^_ansible_",
            "^_meta_",
        }

    def test_the_tree_is_authoritative(self) -> None:
        """A tree that flags only `apply-groups` names only it (ARCH-C06)."""
        schema = generate_json_schema(self._tree("apply-groups"))
        system = schema["properties"]["configuration"]["properties"]["system"]
        assert "^(apply\\-groups)$" in system["patternProperties"]
        assert self._PATTERN not in system["patternProperties"]

    def test_a_tree_without_the_flag_still_names_the_kernel_four(self) -> None:
        """A tree that declares no universal statement gets the kernel's floor.

        This once asserted the opposite -- that a tree without the flag gains no
        pattern -- which pinned the state in which junoscfg's JSON output of
        any configuration carrying `apply-groups` failed its own validation.
        The floor retires with the trees that need it (spec
        schema-pipeline/universal-statements).
        """
        schema = generate_json_schema(_make_tree())
        system = schema["properties"]["configuration"]["properties"]["system"]
        assert self._PATTERN in system["patternProperties"]


# ── Entry keys: the schemas name a list's key fields ─────────────────
#
# Spec: openspec/changes/identifier-key-fields/specs/validation/keyed-entries,
# "The JSON and YAML schemas name the key fields". Generated from an XSD, so
# the keys reach the generator however the tree carries them.


def _keyed_schema(variant: str = "json") -> dict:
    from tests.support.keyed_entries import KEYED_XSD

    return generate_json_schema(parse_xsd(KEYED_XSD), variant=variant)


def _resolve(schema: dict, node: dict) -> dict:
    """Follow a `$ref`, then a list's array form to its entry schema."""
    while True:
        if "$ref" in node:
            node = schema["$defs"][node["$ref"].rsplit("/", 1)[-1]]
        elif "anyOf" in node and node["anyOf"][0].get("type") == "array":
            node = node["anyOf"][0]["items"]
        else:
            return node


def _entry(schema: dict, *path: str) -> dict:
    node = _resolve(schema, schema["properties"]["configuration"])
    for name in path:
        node = _resolve(schema, node["properties"][name])
    return node


def _walk(obj: object) -> list[dict]:
    found = []
    if isinstance(obj, dict):
        found.append(obj)
        for value in obj.values():
            found.extend(_walk(value))
    elif isinstance(obj, list):
        for value in obj:
            found.extend(_walk(value))
    return found


class TestEntryKeysAreTheTreesFields:
    @pytest.mark.parametrize("variant", ["json", "yaml"])
    def test_entry_properties_are_the_key_fields(self, variant: str) -> None:
        schema = _keyed_schema(variant)
        term = ("policy-options", "policy-statement", "term")
        expected = {
            (*term, "from", "as-path-neighbors"): {"list-type", "list-name"},
            (*term, "from", "route-filter"): {"address", "exact", "orlonger", "accept", "reject"},
            (*term, "then", "community"): {"add", "delete", "community-name"},
            ("system", "ntp", "server"): {"address", "version", "prefer"},
            ("event-options", "policy", "attributes-match"): {
                "from-event-attribute",
                "condition",
                "to-event-attribute-value",
            },
        }
        for path, keys in expected.items():
            entry = _entry(schema, *path)
            assert set(entry["properties"]) == keys, path
            assert entry["additionalProperties"] is False

    def test_name_keyed_lists_keep_name(self) -> None:
        """What 0.14.0 generated, compared as data, in both variants.

        `tests/data/name-keyed-schema-*.json` is the 0.14.0 output. Dict
        equality, not bytes (owner answer 4): `name` now arrives as the
        entry's first child rather than appended last. The one entry removed
        before comparing is `community-name` under `policy-options community`,
        a list keyed `name`: 0.14.0 added it by the retired
        `ENTRY_KEY_OVERRIDES` spelling, keyed on the node's name alone.
        """
        import json

        from tests.support.keyed_entries import NAME_KEYED_XSD

        data = TEST_DATA
        for variant in ("json", "yaml"):
            pinned = json.loads((data / f"name-keyed-schema-{variant}.json").read_text("utf-8"))
            for top in (pinned["properties"]["configuration"], pinned):
                community = top["properties"]["policy-options"]["properties"]["community"]
                for shape in (community["anyOf"][0]["items"], community["anyOf"][1]):
                    del shape["properties"]["community-name"]
            schema = generate_json_schema(parse_xsd(NAME_KEYED_XSD), variant=variant)
            assert "name" in _entry(schema, "policy-options", "policy-statement")["properties"]
            assert "name" in _entry(schema, "policy-options", "community")["properties"]
            assert json.loads(json.dumps(schema)) == pinned, variant

        keyed = _keyed_schema()
        for path in (("policy-options", "policy-statement"), ("event-options", "policy")):
            assert "name" in _entry(keyed, *path)["properties"], path

    def test_no_required_is_added(self) -> None:
        schema = _keyed_schema()
        nodes = _walk(schema)
        assert len(nodes) > 50
        assert [n for n in nodes if "required" in n] == []
        entry = _entry(schema, "policy-options", "policy-statement", "from", "as-path-neighbors")
        assert set(entry["properties"]) == {"list-type", "list-name"}
        assert "required" not in entry
