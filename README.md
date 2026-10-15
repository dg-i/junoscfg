# Junoscfg (Python)

Convert and validate Junos configurations between JSON, structured, YAML, and display set formats.
Two YAML formats exist side by side: `yaml` (junoscfg's IR as YAML) and `yaml-new`
(exactly the Junos JSON object as YAML). `yaml-new` is planned to take over the
name `yaml`; see [Two YAML formats](docs/guide/conversion.md#two-yaml-formats-yaml-and-yaml-new).

**XML input and output: BUGGY; XML work is deferred.** XML input remains
available but is not qualified by the current makeover. XML output is not
implemented and raises `NotImplementedError`. See the
[XML work TODO](docs/roadmaps/xml-work-todo.md).

Originally inspired by the [Ruby Junoser gem](https://github.com/codeout/junoser), now a comprehensive Junos configuration toolkit.

## Installation

From PyPI:

```bash
pip install junoscfg
```

From a checked-out repository, run this in the repository root:

```bash
pip install .
```

## Usage

### CLI

```bash
# Convert structured config to set commands
junoscfg -i structured -e set config.conf

# Convert JSON to set commands
junoscfg -i json -e set config.json

# Convert to structured format
junoscfg -e structured config.set

# Read from stdin
echo '{"configuration":{"system":{"host-name":"test"}}}' | junoscfg -i json -e set

# Move a YAML file to yaml-new, the Junos JSON object in YAML
junoscfg -i yaml -e yaml-new old.yaml

# Transform YAML for Ansible (literal extraction)
junoscfg edityaml ansibilize -p "addr:interfaces.interface[*].name" config.yaml

# Offset mode for multi-router deployments (generates ipmath expressions)
junoscfg edityaml ansibilize -P "addr:interfaces.interface[*].unit[*].family.*.address[*].name" config.yaml

# Anonymize all sensitive data
junoscfg -i json -e set --anonymize-all config.json

# Anonymize with regex patterns (e.g. match site codes)
junoscfg -e set --anonymize-sensitive-patterns 'LAX\d+' config.json

# Find config objects that are defined but never referenced
junoscfg audit unused config.conf

# Generate a delete script for unused objects, with review comments
junoscfg audit unused -o delete-script-verbose config.conf

# Retrieve XSD dump and generate schema artifacts
echo "<rpc> <get-xnm-information> <type>xml-schema</type> <namespace>junos-configuration</namespace> </get-xnm-information> </rpc>" | ssh -Csp 830 router.example.com netconf > netconf.xml
junoscfg schema generate netconf.xml -o ./artifacts/
```

### Python API

```python
from junoscfg import convert_config, Format, validate_json

# Convert between any format pair
result = convert_config(
    '{"configuration":{"system":{"host-name":"test"}}}',
    from_format=Format.JSON, to_format=Format.SET,
)

# Validate a JSON config
result = validate_json('{"configuration":{"system":{"host-name":"test"}}}')
print(result.valid)  # True

# Convert with strict field-level validation (raises on invalid enum/pattern/IP values)
result = convert_config(source, from_format=Format.JSON, to_format=Format.SET, strict=True)

# Anonymize a configuration
from junoscfg.anonymize import AnonymizeConfig, anonymize

config = AnonymizeConfig(ips=True, passwords=True, salt="my-salt")
config.expand_all()
ir = {"configuration": {"system": {"host-name": "router1", "name-server": [{"name": "8.8.8.8"}]}}}
result = anonymize(ir, config)
```

## Documentation

For full documentation, install the docs dependencies and run:

```bash
uv sync --group docs
uv run mkdocs serve
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

Key sections:

- **Getting Started** — Installation and usage examples
- **User Guide** — Conversion, operational attributes (`@` annotations), validation, audit, and CLI reference
- **API Reference** — Auto-generated Python API docs
- **Architecture** — Design decisions and schema internals
