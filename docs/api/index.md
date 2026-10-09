# API Reference

The published Python API follows package doors. Import the documented names
from these modules, not from their implementation submodules.

## Top-Level Functions

The [`junoscfg`](conversion.md) module provides convenience functions for all conversions
and validations. These are the primary entry points for most users.

```python
from junoscfg import convert_config, validate_json
```

## Convert Module

The [`junoscfg.convert`](convert.md) module implements the unified conversion
pipeline. It provides `pipeline()`, `pipeline_result()`, `to_dict()`, `from_dict()`, and `validate_ir()` for
converting between any format pair through a JSON dict intermediate representation (IR).

## Display Module

The [`junoscfg.display`](display.md) module contains shared conversion utilities
such as `detect_format()`, `is_display_set()`, `xml_to_dict()`, and `filter_set_by_path()`. The actual format
converters live in `junoscfg.convert.input/` and `junoscfg.convert.output/`,
but those implementation modules are not published. Access conversion through
`junoscfg.convert.pipeline()` or the top-level `convert_config()`.

## Validate Module

The [`junoscfg.validate`](validate.md) module contains validation data types and the
`JunosValidator` facade. Format-specific validators and schema pipeline components
are in submodules.

## Anonymize Module

The [`junoscfg.anonymize`](anonymize.md) module provides configuration anonymization —
replacing sensitive data with deterministic pseudonyms. It includes `anonymize()`,
`AnonymizeConfig`, `AnonymizeResult`, and revert dictionary utilities.

```python
from junoscfg.anonymize import AnonymizeConfig, AnonymizeResult, anonymize
```
