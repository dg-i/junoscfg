"""Tests for JSON Schema generation from SchemaNode tree."""

from __future__ import annotations

from junoscfg.validate.schema_generator import generate_json_schema
from junoscfg.validate.schema_node import SchemaNode


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

    def test_mandatory_in_required(self):
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
        assert "required" in config
        assert "required-field" in config["required"]


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
        generator names them from `UNIVERSAL_STATEMENTS` whether or not the
        tree declares the flag -- see `TestUniversalStatementsReachEveryContainer`.
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

    The names come from `UNIVERSAL_STATEMENTS` in the kernel, with any the tree
    declares through the `universal` flag added. The kernel list is the floor
    because a tree built before `_fix_apply_statements` carries no such node —
    the shipped one does not — and junoscfg emitted `apply-groups` and then
    rejected its own output for all three real device configurations.
    """

    @staticmethod
    def _tree() -> SchemaNode:
        tree = _make_tree()
        groups = SchemaNode(name="apply-groups", is_leaf=True, is_list=True)
        groups.flags.add("universal")
        tree.children["apply-groups"] = groups
        return tree

    # Every universal name the generator knows: the kernel's four, which the
    # tree's own `apply-groups` is already one of.
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
        assert set(system["patternProperties"]) == {self._PATTERN, "^_ansible_", "^_meta_"}

    def test_a_tree_without_the_flag_still_names_the_kernel_four(self) -> None:
        """The flag adds to the floor; it is not what puts the floor there.

        This asserted the opposite -- that a tree without the flag gains no
        pattern -- which pinned the state in which junoscfg's JSON output of
        any configuration carrying `apply-groups` failed its own validation.
        """
        schema = generate_json_schema(_make_tree())
        system = schema["properties"]["configuration"]["properties"]["system"]
        assert self._PATTERN in system["patternProperties"]
