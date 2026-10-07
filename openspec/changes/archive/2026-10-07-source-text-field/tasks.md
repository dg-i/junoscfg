## 1. Tests

- [x] 1.1 Rewrite `TestNetworksAutoNoOpsThroughThePythonApi` as
  `TestNetworksAutoNeedsSourceText`: auto without the text raises naming the
  field; auto with it anonymizes; `source_text` is a declared dataclass field
  and `_source_text` is not.

## 2. Implementation

- [x] 2.1 Declare `source_text: str | None = None` on `AnonymizeConfig`.
- [x] 2.2 Raise in `IpRule._build_network_registry` when `auto` is asked for
  without it.
- [x] 2.3 Assign the declared field in `cli.py` and drop the `type: ignore`.
- [x] 2.4 Append the field rather than inserting it, so no positional
  parameter moves; confirmed by `agent-ready stage griffe`.
- [x] 2.5 Document the new exception in `anonymize()`'s docstring, which
  renders through mkdocstrings.

## 3. Coverage the review found missing

- [x] 3.1 Strengthen `test_auto_with_source_text_*` to assert host-bit
  preservation. It previously asserted only that the address changed, which
  plain IP anonymization satisfies, so a silent failure of auto-detection kept
  it green. Mutation-tested: `load_from_text("")` now fails it.
- [x] 3.2 Add `TestAnonymizeNetworksAuto` to `tests/test_cli.py`. There was no
  automated test for `--anonymize-networks auto` at all, so deleting the two
  lines in `cli.py` that supply the text would have broken it silently.
