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
- [x] 2.4 Verify the CLI path end to end: `--anonymize-networks auto` still
  preserves subnet structure.
