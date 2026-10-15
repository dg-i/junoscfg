Fresh isolated Reviewer (separate agent, Claude Opus, no Builder reasoning), base 037e012,
heads e5cb8cb then c542bc0; read-only, probes in a scratch clone.

## Findings

First review at e5cb8cb, verdict Changes required:

1. **B1 (binding)** "does not work around PyYAML or another parser" went beyond the owner's
   ruling and contradicted kept code (`_JunosYamlDumper` quoting NEL/LS/PS) and backlog
   YAML-DATE-001, and pre-decided YAML-BREAKS-001. Corrected: the clause covers a parser's
   limits on hostile input only, in `ARCHITECTURE.md`, the decision record and the fragment.
2. **B2 (binding)** "messages keep withholding configuration values" is true only of an
   anonymized run (`tests/contract/test_every_message.py`). Corrected, with the source row.
3. **B3 (binding, records)** QA tasks unticked; docs plan lacked the commands and Diátaxis
   items and a reason per document. Corrected in `docs-plan.md` and `tasks.md`.
4. Advisories corrected: a dangling "in this session" reference, defences listed beside
   attacks, fixes listed among defects. Own crashes C5 (non-string key in legacy `yaml`
   input, `AttributeError`) and C6 (JSON about 1,500 deep, `RecursionError`) are named in the
   proposal's non-goals and reported to the owner.

Correction review at c542bc0: B1 and B2 resolved, B3 resolved once tasks are ticked with
evidence; advisory: run the lane gate against master 1afcd29, which carries the activation
inventory merged into the branch.

## Already provided

Nothing reused: documents only.

## Specification challenges

None.

## Verdict

Merge, conditional on the ticked QA evidence and a passing full checkpoint (`tasks.md`).
