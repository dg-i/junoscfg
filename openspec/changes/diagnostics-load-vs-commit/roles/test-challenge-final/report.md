# Independent final-source controls — diagnostics-load-vs-commit

Verdict: **PASS; no concrete correctness challenge found.** This completes correction-dependent Test/Challenge preservation controls; it does not replace fast/ordinary verification or genuinely fresh review.

Exact candidate `0118eaf3a6060f845d3a05759f784e457febeba3`, current base `0e65a5f8a4a7fc2d2199e0f2398aceb5f822690d`. Scoped product diff and owning contract inspected independently of Builder reasoning: diagnostics now extend independently of validation validity; strict still raises only when errors invalidate the result; mandatory warning suffix is exactly owner-approved. Warning producer, schema/group evaluation and validation door boundaries are otherwise unchanged.

Original 14 acceptance identities match retained RED identities and pass: actual pytest exit 0, 14 passed, 0 failures/errors/skips. Offline locked exact-node command and raw/XML retained as `green.out`/`green.xml` in this directory. No acceptance or criteria mutation.

The existing eight public-door preservation combinations were rerun on this exact implementation: error beside warning on/off, strict on/off, anonymization on/off. Every returning result carries exactly one mandatory warning at `access.radius-server.secret` with severity `warning` and exact approved qualified text. Both result doors agree, library stderr is empty, strict errors still raise `FieldValidationError`, and anonymized messages contain neither original nor resulting pseudonym. Warning-only controls now test emitted warnings, completing the previously deferred confirmation.

Independently compared exact key sets of the 96 plain and 1,152 anonymizer base/head records: outputs and exception classes match in every case. Old nonmandatory messages remain; old mandatory messages gain only the approved suffix; all additional messages are qualified mandatory warnings; added diagnostic tuples have source `field-validate` and severity `warning`. This is direct examination of retained executed records, not a newly executed full corpus run. Retained implementation comparison and focused/device XML hashes match their declared bindings.

Historical baseline identity remains `13b2cc73fd42fb44d1c69121b73d9b9fa61677cd`. Independently checked actual old/new Git input trees/blobs listed in operator-only-rebase proof: source/tests/captures/lock/config/tools/skills are equal, supporting applicability of those retained baselines to current base. No historical fast result was relabeled.

Before/after HEAD/source/capture identities and clean working status remained unchanged throughout independent execution. Current criteria/test SHA-256 hashes and runtime executable/version are bound in `evidence.json`; all artifacts in this directory are bound by `bindings.json`. Existing pre-implementation evidence was retained unchanged.

No WT report mutation/commit, source/test/criteria edits, real schema/canonical full, network, device contact, push, publication or Claude control. Owning execution window released to root immediately after controls. Next work: current fast/ordinary checks and genuinely fresh isolated Reviewer. Usage/efficiency: UNMEASURED.

Direct retained implementation XML observed counts: `{"implementation-device.xml": {"errors": 0, "failures": 0, "skipped": 5, "tests": 4461}, "implementation-focused.xml": {"errors": 0, "failures": 0, "skipped": 1, "tests": 178}}`. Skips here correspond to the retained existing strict xfails; independent exact14 has no skips.
