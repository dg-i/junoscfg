## Reader and task

- Reader: a junoscfg user who validates set commands or converts annotated JSON/YAML, reading
  `docs/guide/validation.md` or `docs/guide/annotations.md`.
- Task: copy an example and have it load on a device; know what set validation catches, what it
  lets through, and where its known false rejections are recorded.

## Authoritative sources

| Claim | Source |
|---|---|
| `set system location dc-a` is malformed; the device takes keyworded children | `openspec/specs/validation/set-command-validation/spec.md` scenario "Lines the device rejected" (device probe, vMX 23.2R2-S7.5); `tests/corpus/test_set_corpus.py` `CORRECTLY_REJECTED`; `validate_set` returns invalid at the checked head |
| The device spelling `set system location building "B 2"`, and that it validates | `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.set.gz` (vMX, 23.2R2-S7.5) and `tests/data/device/synthetic/qfx5120-25.2R2-S1.5/junoscfg-oracle.set.gz` (QFX5120, 25.2R2-S1.5): `set groups GR-UNUSED system location building "B 2"`; `validate_set` valid at the checked head |
| Same-named nodes share one grammar rule; a line may pass with a child the model has only at another position of that name | `src/junoscfg/validate/grammar_generator.py` module docstring (step 1) and the union of `common_alts` in `generate_lark_grammar`; shipped grammar: both `labeled_unicast__v…` variants (inet, inet6) offer `"per-prefix-label"`; bundled tree: `per-prefix-label` under `family inet labeled-unicast` only; `validate_set("set protocols bgp group RR family inet6 labeled-unicast per-prefix-label")` valid; both captures above print that line; unchanged in live change #8's regenerated grammar (ef06855) |
| Every leaf accepts any token (kept) | existing text, unchanged; `QUOTED_OR_VALUE` slots in the shipped grammar |
| 8,713 distinct device lines; fewer than one in a hundred rejected; each recorded | `tests/data/device/grammar-corpus.json` `device_lines` 8,713, `rejected` 66 at master 13719d9 and 65 in live change #8 (ef06855); `tests/corpus/test_set_corpus.py::TestTheGrammarTakesWhatDevicesPrint::test_the_false_rejections_are_exactly_the_recorded_ones` |
| The test lists malformed input and intentional exclusions by hand | `tests/corpus/test_set_corpus.py` `CORRECTLY_REJECTED`, `INTENTIONALLY_UNSUPPORTED` |
| `domain-name example.net` is a plain leaf the devices print as written | bundled tree `system domain-name` (`l`); both captures above: `set groups GR-SYSTEM system domain-name example.net`, curly `domain-name example.net;`; `validate_set` valid |
| The JSON → YAML → curly and JSON → set outputs of the worked example | `junoscfg convert` run at the checked head on the page's own input (QA 2) |

## Affected documents

- `docs/guide/validation.md`: the "Set Commands" warning admonition; the user guide is where the
  limits of set validation are explained to users (reference-like guide page, already in nav).
- `docs/guide/annotations.md`: the container-annotation example and the worked `replace` example;
  their purpose is the annotation, so the leaf beside `host-name` only has to be valid Junos.

## Documentation QA

- Links and anchors: `uv run --locked --group docs mkdocs build --strict` exits 0 with no new
  warning; the two pages add no link.
- Commands and examples: run the worked example's three `junoscfg convert` commands and the
  container example (`-i json -e conf`) at the checked head; the page shows their exact stdout.
  Every set line the changed text names is run through `validate_set` and gives the stated result.
- Referenced paths: every path the changed text names exists (`ls`).
- Terminology: "over-rejects", "malformed", "structural" as the page and `test_set_corpus.py`
  use them; no remaining `dc-a` or bare `system location <value>` in tracked documents
  (`git grep`), the archived change folders and the main spec's rejected-lines scenario aside.
- Diátaxis placement: the change stays inside existing guide sections; no new page.
- Rendered output: markdownlint passes (pre-commit); the admonition renders as one block in the
  strict MkDocs build (indentation kept at four spaces).
