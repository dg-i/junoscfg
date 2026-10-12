# Shipped patterns validate without Python warnings
Add one focused sweep of the shipped structure tree's complete pattern table.
Preserved behaviour: validate_ir applies POSIX translation and compiles each pattern without emitting Python warnings; accepted/rejected values remain unchanged.
Verification: bundled_tree supplies the exact shipped table; synthetic indexed leaves traverse validate_ir under warnings capture, with a genuine FutureWarning sensitivity control.
Baseline: the prior bracket regression covers patterns 49/83's shape, not every shipped entry; no complete sweep was found by test search.
Risk: test-only conversion coverage; no source, shared fixtures, public API, dependencies, generated artifacts or device claims change.
Changelog: none, because this adds internal coverage of existing behavior.
Review: fresh lightweight maintenance Reviewer required; Root owns later gates.
Authorization: unattended owner phase approval persists; Builder stops after targeted evidence.
Next: implement the new test and retain baseline/source-identity evidence; no pre-fix red is expected or claimed.
