# Junoscfg (Python)

Convert and validate Junos configurations between JSON, structured, YAML, and display set formats.

Originally inspired by the [Ruby Junoser gem](https://github.com/codeout/junoser), now a comprehensive Junos configuration toolkit.

## Installation

```bash
pip install junoscfg
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

# Transform YAML for Ansible (literal extraction)
junoscfg edityaml ansibilize -p "addr:interfaces.interface[*].name" config.yaml

# Offset mode for multi-router deployments (generates ipmath expressions)
junoscfg edityaml ansibilize -P "addr:interfaces.interface[*].unit[*].family.*.address[*].name" config.yaml

# Anonymize all sensitive data
junoscfg -i json -e set --anonymize-all config.json

# Anonymize with regex patterns (e.g. match site codes)
junoscfg -e set --anonymize-sensitive-patterns 'LAX\d+' config.json

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
from junoscfg.anonymize import anonymize
from junoscfg.anonymize.config import AnonymizeConfig

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
- **User Guide** — Conversion, validation, and CLI reference
- **API Reference** — Auto-generated Python API docs
- **Architecture** — Design decisions and schema internals
