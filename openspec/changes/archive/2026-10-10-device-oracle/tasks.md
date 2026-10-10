## 1. Verification

- [x] 1.1 Baseline: `ledger-before.txt` (6,069 node ids on master 23c696d). `check_ledger.py` accounts for every one: kept, mapped by `ledger/*.tsv`, or dropped with a reason.
- [x] 1.2 The oracle: `tests/corpus/test_device_renderings.py` holds junoscfg's set rendering of every capture's every rendering to the device's display set, less `known-differences.json`; the grammar corpus to every rule the device lines use.

## 2. Change

- [x] 2.1 Captures curated (owner: few, specific, no redundancy): measured that the EX and QFX renderings of the JVD configurations add no junoscfg difference; three JVD configurations and the probes on the vMX; `junoscfg-oracle` (one new synthetic source merging the constructs, switching and router1's routing material) on the vMX and the QFX5120.
- [x] 2.2 JVD licence, notice with the modifications statement, unmodified sources, manifest with origins, devices, load refusals; decision record.
- [x] 2.3 Tools: import, differences (classes as definitions, matched on keywords and shape), grammar corpus (greedy rule cover).
- [x] 2.4 `set_corpus.txt` retires; the grammar corpus replaces it; `--device-grammar` for every line by hand.
- [x] 2.5 The name-keyed byte pin retires (owner, 2026-10-10); delta for `conversion/entry-keys`.
- [x] 2.6 `examples/` is the vMX's rendering of `junoscfg-oracle`; tests that read `router1` read it.
- [x] 2.7 Documents: README of the device data, tests/CONTRACT.md, the developer guide, the validation guide, settle-a-schema-question.

## 3. Review and evidence

- [x] 3.1 Review: lightweight record (owner); device facts and a review of the layout and the oracle law from the junoscfg-d9 session.
- [x] 3.2 Final full check: `agent-ready check --set full` at 02ba0e1, every gate passed; 6,016 passed / 45 skipped / 19 xfailed (12 new strict xfails, each a product defect the device-verified example showed). Ledger: 6,069 baseline nodes, 6,017 kept, 50 mapped, 2 dropped (the retired byte pin and the stale-entry guard), 0 problems. The entry-keys delta is applied to the main spec in this change.
