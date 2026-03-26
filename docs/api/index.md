# API Reference

The Junoscfg Python API is organized into three layers:

## Top-Level Functions

The [`junoscfg`](conversion.md) module provides convenience functions for all conversions
and validations. These are the primary entry points for most users.

```python
from junoscfg import convert_config, validate_json
```

## Convert Module

The [`junoscfg.convert`](internals/convert.md) module implements the unified conversion
pipeline. It provides `pipeline()`, `to_dict()`, `from_dict()`, and `validate_ir()` for
converting between any format pair through a JSON dict intermediate representation (IR).

The [`junoscfg.convert.field_validator`](internals/field_validator.md) submodule validates
leaf values against schema constraints (enums, patterns, IP addresses, integer bounds).

## Display Module

The [`junoscfg.display`](display.md) module contains shared conversion utilities
such as `is_display_set()` and `filter_set_by_path()`. The actual format
converters live in `junoscfg.convert.input/` and `junoscfg.convert.output/`,
accessed via `junoscfg.convert.pipeline()` or the top-level `convert_config()`.

## Validate Module

The [`junoscfg.validate`](validate.md) module contains validation data types and the
`JunosValidator` facade. Format-specific validators and schema pipeline components
are in submodules.

## Anonymize Module

The [`junoscfg.anonymize`](anonymize.md) module provides configuration anonymization —
replacing sensitive data with deterministic pseudonyms. It includes `anonymize()`,
`AnonymizeConfig`, `AnonymizeResult`, and revert dictionary utilities.

```python
from junoscfg.anonymize import anonymize, AnonymizeResult
from junoscfg.anonymize.config import AnonymizeConfig
```

## Internals

Internal modules are documented under Internals in the sidebar navigation for reference.
These implement the conversion and validation logic and are not part of the public API.
