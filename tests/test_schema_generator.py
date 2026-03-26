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
        # List nodes should have oneOf with array option
        assert "oneOf" in interfaces
        array_option = next(o for o in interfaces["oneOf"] if o.get("type") == "array")
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

    def test_json_no_pattern_properties(self):
        schema = generate_json_schema(_make_tree(), variant="json")
        config = schema["properties"]["configuration"]
        assert "patternProperties" not in config
