## 1. Verification (one per docs-plan QA item)

- [x] 1.1 Links and anchors: `uv run --locked --group docs mkdocs build --strict` exits 0; the only INFO notice is the pre-existing `how-to/hosting.md` not in nav (baseline at 5d464a8: exit 0, that notice only)
- [x] 1.2 Commands and examples: the worked example's `junoscfg convert -i json -e yaml`, `-i yaml -e conf`, `-i json -e set`, and the container example's `-i json -e conf`, run on the page's own input at the checked head, print exactly what the page shows; every set line the changed text names gives the stated `validate_set` result
- [x] 1.3 Referenced paths: every path the changed text names exists (`ls`)
- [x] 1.4 Terminology: `git grep -n -e dc-a -e "system location" -- '*.md' ':!openspec/changes/archive' ':!openspec/changes/docs-corrections' ':!openspec/specs'` lists only lines of the corrected validation paragraph (baseline at 5d464a8: six lines in `annotations.md`, one in `validation.md`)
- [x] 1.5 Placement: the edits stay inside the existing "Set Commands" admonition and the two annotation examples; no new page or section (inspection of the diff)
- [x] 1.6 Rendered output: markdownlint passes on both pages (pre-commit); the admonition keeps its four-space indentation and renders as one block in the strict build (inspection of `site/guide/validation/index.html`)
- [x] 1.7 One full checkpoint: `uv run --locked --group dev --with griffe --with tach --with towncrier --with vulture agent-ready check --set full` passes

## 2. Change

- [x] 2.1 `docs/guide/validation.md`: the "Set Commands" warning (merge of same-named rules, share of device lines, `system location dc-a` as malformed input with the device spelling)
- [x] 2.2 `docs/guide/annotations.md`: `location dc-a` becomes `domain-name example.net` in the container example and the worked `replace` example, outputs as rerun

## 3. Review and evidence

- [x] 3.1 Complete the risk-required fresh isolated review, or record why the assurance policy does not require it.
- [x] 3.2 Capture `metrics.md` and `metrics.json` for the immutable base and code head.
- [x] 3.3 Finalizer completes bounded spec application, evidence, and archive housekeeping without product edits. No delta to apply (`skip_specs: true`); evidence captured; the archive move and version bump are the orchestrator's merge step.

## Evidence

- 1.1 at a73827f: `mkdocs build --strict` exit 0; INFO only for the pre-existing `how-to/hosting.md` not in nav (same as the 5d464a8 baseline).
- 1.2 at a73827f (`private_test_data/makeover-work/docs-corrections/qa_examples.py`, untracked): the container example (`-i json -e conf`), the worked example's `-i json -e yaml`, `-i yaml -e conf` and `-i json -e set`, run on the page's own JSON, exit 0 with empty stderr and print byte for byte what the page shows; `validate_set` gives valid for `set protocols bgp group RR family inet6 labeled-unicast per-prefix-label`, `set system location building "B 2"`, `set system domain-name example.net`, invalid for `set system location dc-a`, as the text states. The schema claim checked over the whole bundled tree: `per-prefix-label` under 36 copies of `family inet labeled-unicast` and none of `family inet6 labeled-unicast` (it also sits under `transport`, which the text does not name); the shipped grammar's inet6 `labeled_unicast` variant offers it through the same-name union. The line holds in live change #8's regenerated grammar (ef06855).
- 1.3: `tests/data/device/`, `tests/data/device/grammar-corpus.json`, `tests/corpus/test_set_corpus.py` exist.
- 1.4: the grep lists only `docs/guide/validation.md:70` and `:72`, the corrected paragraph.
- 1.5: the diff stays inside the "Set Commands" admonition and the two annotation examples.
- 1.6: pre-commit markdownlint and document caps passed on a73827f; the built `guide/validation/index.html` holds one warning admonition containing the new text up to the bracket paragraph.
- 1.7: full checkpoint at a73827f failed only `stage towncrier` (no fragment on the branch); fragment `changelog.d/+docs-corrections.doc.md` added in fe0d979; rerun at fe0d979: "every check passed" (application tests skipped by the docs lane).
- 3.1: no review required; omission rationale in `review.md`.
- 3.2: `agent-ready metrics docs-corrections --base-sha 13719d9… --head-sha fe0d979…` (full IDs in `metrics.json`); 3 files, +19 −13 outside this folder.
