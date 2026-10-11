## Why

From XML, a leaf value with leading or trailing spaces loses them (DEV-17): the
device writes `<allow-commands>^show </allow-commands>` and displays
`allow-commands "^show "`, junoscfg writes `allow-commands "^show"`. That is
another configuration, written without a word. The XML walker strips every
element's text, a strip only pretty-printed flags and containers need.

## What Changes

- `junoscfg.display.xml_to_dict`, the one XML walker, reads an element's text
  as the value verbatim. Text that is only whitespace counts as a value only on
  a leaf the structure tree says takes one; a flag or container written across
  lines (`<passive>\n</passive>`) reads as before.
- Every output of XML input (set, structured, JSON, YAML) keeps the spaces.
- The four recorded lines of known-differences class `xml-value-whitespace-lost`
  (vMX and QFX5120 `junoscfg-oracle.xml`) go, with the class, through
  `tools/device_differences.py`: a serialized path, sequenced by the
  orchestrator after change 8 (`value-quoting-by-type`), which holds both files.

## Capabilities

### New Capabilities

- `conversion/xml-input`: an XML leaf's text is its value as written.

### Modified Capabilities

- None.

## Non-goals

- The empty element of a value leaf (DEV-16, spec `conversion/entry-keys`), already fixed in change 3.
- Quoting of values that hold spaces in set output (change 8).

## Impact

`src/junoscfg/display/to_yaml.py` (zone kernel), `tests/unit/display/test_to_yaml.py`, a changelog
fragment. Evidence: `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.{xml,set}.gz` and
the QFX5120 25.2R2-S1.5 pair; the four lines are in `tests/data/device/known-differences.json`, and
`uv run --locked pytest tests/corpus/test_device_renderings.py` reports them gone after the fix.
