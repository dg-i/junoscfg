# Preparation evidence

Runtime base: 5187ac92734dce8c9ebd4e8404a98f76871fd399; product and existing tests unchanged.
Command: `UV_OFFLINE=1 UV_PYTHON=3.13.15 uv run --locked --group dev pytest -q tests/unit/display/test_terminal_tag_refusal.py --no-cov`.
Result: 11 failed, 10 passed in 0.22s. Eight failures are DID NOT RAISE after exact supported conversion assertions passed; three failures are the spy proving deprecated validator forwarded unsafe output to set validation. Ten legacy preservation controls pass. Exact private log: `/private/tmp/deprecated-terminal-tag-preparation-red.log`.

Private lexical proof: `/private/tmp/deprecated-terminal-tag-lexical-proof.txt`. Public `statements()` observations show tabs normalized between terminal words, quoted description space retained, bracket values expanded with normalized separators, quoted single flag without spaces retained and combined prefix tags stripped independently. Hypothetical quoted-only `inactive: "a b";` remains one quoted token with spaces; the proposed conservative text boundary refuses it. This is explicitly recorded, not described as two lexer tokens. Held valid Junos statements have the unquoted statement keyword preceding values; no additional token parser is proposed. Independent challenge must judge the conservative edge.

No existing assertions or contract source was edited. The new file is intentionally red until admission and implementation. Its own dedicated placement was explicitly required by root even though tests/CONTRACT normally groups one unit file per source module; owner precedence is recorded, not a tooling exemption.

Preparation hooks: the affected-tests hook would rerun this intentionally red file and prevent a test-first commit. Only that hook is skipped for the phase-4 RED checkpoint; ruff, test doors, dependency checks and record checks still run. This is no success claim or final verification exemption. Product implementation will run focused tests and all required checkpoints after READY admission.
