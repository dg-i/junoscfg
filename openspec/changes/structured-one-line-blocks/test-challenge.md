# Test/Challenge: structured-one-line-blocks (STOP-T)

Independent role, phase 4. Read the committed artefacts on `change/structured-one-line-blocks`
(head `c9f760f`, merge base `a19e978`). Nothing tracked was edited. `src/` on the branch is
byte-identical to the merge base (the diff touches only `openspec/` and `tests/`), so every probe
below ran against merge-base product code. Probes and counterexamples are in this folder
(`tc_probe1.py`, `tc_probe2.py`, `tc_probe3.py`, `tc_counter_lexer.py`, `tc_counter_c5.py`,
`tc_crash_plugin.py`). They use synthetic values only.

## 1. Do the new tests fail on the base for the right reason?

Run: the four new test groups plus the rest of `test_set_converter.py` gave
`47 failed, 51 passed, 5 xfailed`. The whole `test_every_door.py` gave `18 failed, 438 passed,
7 xfailed`, which is the 5 OPEN-13 strict xfails already there plus the 2 new ones.

| Group | Base failure | Right reason? |
|---|---|---|
| `TestTheLexerReadsTokensNotLines` (6) | "the one-line text read as nothing", or statements differ | yes |
| `TestACommentIsNeverPartOfAStatement` | `hash`, `block` and `between-tokens` fail on the value; `over-two-lines` and `after-an-opening-brace` pass on base | yes. The two passes are the guards the freeze names |
| `TestMalformedTextIsRefused` (lexer, 7) | 5 "DID NOT RAISE". `a-statement-without-a-semicolon` and `an-open-bracket-list` already raise `ValueError` on base (`Unknown statement`, `Unclosed bracket`) and fail on the message | yes: the message has to name the fault and its line |
| `TestWhatYieldsNoStatementIsReported` (lexer) | output not empty / no `notes()` | yes |
| `TestToSetIsDeprecated` | DID NOT WARN | yes |
| convert `TestABlockOnOneLine` | `to_dict` gives `{}` | yes |
| convert `TestMalformedTextIsRefused` | DID NOT RAISE | yes |
| convert `TestWhatYieldsNoStatementIsReported` | `TypeError: diagnostic_sink` | API shape only: nothing behavioural is checked on base. Acceptable, because every assertion runs after the change |
| convert `TestTheSetLinesOfAStatement` (4) | `ImportError` | API shape only, and that includes the two guard cases |
| contract `TestStructuredTextValidatesAsConversionReadsIt` | the hold-time, protect, one-line-block, brace and placeholder rows fail on the structured doors for the documented reasons (`Invalid syntax: ... hold-time up 2000 down 0`, `Line does not start with 'set'...: protect ...`, `Validation: OK`, `set groups GR-OMIT system { /* OMITTED */ }`) | yes |
| `TestTheStructuredDoorsAreDeprecated` | DID NOT WARN | yes |

The freeze's accounting is slightly off. "Every new test id fails on base except the guard
parameters (...)" leaves out the 35 set, json and yaml door parameters of the new contract rows.
They pass on base by construction because they are the reference verdicts. See F11.

## 2. The four Builder decisions

**C4: curly validation composed at the surface; the validate package's doors are deprecated.**
The design is sound under `tach.toml`: no new edge, and `validate_config` (given or detected)
already funnels into `junoscfg.validate_structured`, so a single composition point covers the
library and the CLI. There are two weaknesses. (a) The deprecated doors do *not* "give the verdict
they gave before". The contract expects `JunosValidator.validate_structured` to change its verdict
on three rows: `a-block-on-one-line` goes from valid on base to invalid, `a-brace-too-many` from
valid to invalid, and `the-omitted-placeholder` from invalid to valid. They share the new lexer.
The spec wording is false (F6). (b) No test guards against the recommended doors still routing
through the deprecated `StructuredValidator`/`to_set()` and leaking a `DeprecationWarning` to
users (F8).

**C5: validate the input's own tokens, split where the walk starts a sibling.** This is better
than the IR→writer route, and the two guard rows prove it: `an-unquoted-multi-word-value` and
`a-keyword-leaf-the-writer-drops` pass on base on every door and must stay passing. But the split
carries the set validator's leniency into curly validation, and it creates a **new false
acceptance** (F1, executed).

**`Row.xfail_on` and `_deprecated`.** Neither weakens an existing oracle. Pre-existing rows have
`xfail_on=()`, so they behave as before (5 strict xfails before, the same 5 plus 2 new now).
`pyproject.toml` sets no `filterwarnings = error`, so `_deprecated` only silences noise and cannot
change a verdict. The mechanism is still looser than it needs to be. A strict xfail accepts *any*
exception, so a crashing deprecated door counts as an expected failure (F5, executed).

**Malformed curly raises `ValueError`.** This matches the existing convention.
`convert_config_result` already raises `JSONDecodeError`, a `ValueError`, for malformed JSON. The
base lexer already raises `ValueError` for `Unknown statement` and `Unclosed bracket`. The CLI maps
`ValueError` to exit 2. The gaps are in coverage: the `audit unused` door, `};` after an ordinary
block, `;;` and a lone `;` (F10). The refusal is also a behaviour change on the `consumer` surface
(`convert_config` used to accept `system {...} }`), and C7's `declared-break` entry must name it.

## 3. Findings, ranked

### F1 (high): the sibling split creates a false acceptance, `hold-time up 2000 down;`

Evidence (`tc_probe3.py`, `tc_counter_c5.py`): the walk reads `hold-time up 2000 down` as
`{'up': '2000', 'down': None}` without any diagnostic. `validate_set` accepts the split lines
`set interfaces ge-0/0/0 hold-time up 2000` + `set interfaces ge-0/0/0 hold-time down` (valid=True).
On base, `validate_structured` of the curly rejects it (valid=False). A spec-faithful
implementation therefore flips a rejection into an acceptance. `down` takes an unsignedInt, so the
device must reject a missing value. That is inferred, not captured. Name it as a device probe.
`validate_set("set system host-name")` is rejected, so the leniency is specific to how the set
grammar treats `hold-time down`.
Proposed test: add a contract row `a-sibling-without-its-value` (valid False, structured only,
`_curly_interface("hold-time up 2000 down")`), and a `structured_set_lines` case pinning the lines.
Proposed spec correction (review.md challenge): a statement the walk cannot complete (a sibling
read without its value) is invalid in curly validation whatever the set grammar says. Otherwise
record the set-grammar leniency as a defect with its own strict xfail, so the curly door does not
inherit it silently.

### F2 (high): "an empty block is never written" is device-unverified and contradicts `x;`

Evidence (`tc_probe1.py`, base): `protocols { lldp; }` gives `set protocols lldp`, and
`protocols { lldp { } }` gives nothing. `system { services; }` gives `set system services`, and
`services { }` gives nothing. Both set lines validate. If the device loads `lldp { }` as `lldp;`,
which is likely because the device prints an existing empty container as `lldp;`, then the
change's tests (`an-empty-block` in `tests/unit/display/test_set_converter.py` and
`tests/unit/convert/test_structured_input.py`) freeze a wrong configuration. `set protocols lldp`
enables LLDP. `inactive: services { }` also drops the tag. AGENTS.md says to ask for a device
artefact before inferring.
Proposed: a device probe (named path only: load `protocols { lldp { } }` and `system { services { } }`,
then `show configuration protocols lldp | display set` and the same for `system services`). Until
it is answered, drop the `an-empty-block` parameters from the "never written" tests, keep the
OMITTED placeholder, and add a pinning test that `services { }` and `services;` read to the same
IR, or record the requirement as EVIDENCE_BLOCKED.

### F3 (medium-high): auto-detection reads one-line tagged curly as YAML

Evidence (`tc_probe2.py`): `detect_format` on `system { inactive: host-name router1; }`,
`routing-options { protect: autonomous-system 64496; }` and
`routing-options { static { inactive: route 10.98.0.0/16 reject; } }` returns `yaml`. The
untagged one-liner and the laid-out text return `structured`. `printf 'system { inactive:
host-name router1; }' | junoscfg -e set` exits 2 with "No 'configuration' key found in YAML
input". Every new test passes `-i structured` or `from_format`, so a correct lexer passes the
tests while `junoscfg convert` and `junoscfg audit unused` without `-i` still fail on one-line
tagged text. `validate_config` is unaffected because it only decides set versus structured.
Proposed tests: a `detect_format` unit case for each of the three strings (expect `structured`),
and in `TestABlockOnOneLine` the CLI without `-i` on a tagged one-liner.

### F4 (medium): the audit door is not tested for one-line blocks

Evidence: `junoscfg audit unused -i structured` on `policy-options { prefix-list PL-A { 198.51.100.0/24; } }`
prints nothing and exits 0, a false all-clear. The laid-out text reports
`policy-options prefix-list PL-A`. The ledger lists audit as a door of OPEN-1, but
`TestABlockOnOneLine` drives convert only.
Proposed: add `audit unused -i structured` to `TestABlockOnOneLine` with that input, expecting the
same stdout as the laid-out text.

### F5 (medium): `xfail_on` strict xfails accept any exception

Evidence (`tc_crash_plugin.py`): with `JunosValidator.validate_structured` patched to raise
`RuntimeError`, both new rows still report `XFAIL`. A broken deprecated door would go unnoticed.
Proposed correction in `cases()`: `pytest.mark.xfail(strict=True, raises=AssertionError, reason=...)`
when `xfail_on` is set (the verdict assertions in `_check` raise `AssertionError`). Optionally add
a collection-time assertion that every name in `xfail_on` is a `DOORS` name.

### F6 (medium): the spec says the deprecated doors keep their verdict and output; they do not

Evidence: §2 C4. Three contract rows change the deprecated facade's verdict. `to_set()` output
for one-line text changes too, from empty to lines.
Proposed spec correction: "keeps its schema-free route (the lexer is the new one)". In
`TestTheStructuredDoorsAreDeprecated`, add a verdict that changes (`system { bogus-statement 1; }`
→ invalid) so the change is explicit rather than incidental.

### F7 (medium): a relative-only lexer oracle lets a wrong lexer pass

Evidence (`tc_counter_lexer.py`): a lexer that ignores quotes and drops every tag passes
`test_one_line_text_reads_as_its_lines[a-tagged-entry]` and `[delimiters-inside-quotes]`. Both
layouts are read by the same wrong lexer, so they are equal and non-empty. The comment tests have
no case where a comment holds a quote, although the spec names one and the device prints
`## Warning: missing mandatory statement(s): 'secret'` and `## '( P-A && P-B )' is not defined`.
`/* */` inside quotes is covered only by the device law (vMX line
`description "a;b {c} #d /* e */"`).
Proposed: absolute expected `statements()` for the tagged and quoted cases (for example
`('route 10.98.0.0/16 reject', frozenset({'inactive'}))`). Add comment cases
`host-name router1; ## say "hi` and `## Warning: ... 'secret'`, and a quoted value holding `/* e */`.

### F8 (medium-low): warnings are asserted on one validation door; deprecation leaks are not asserted at all

Evidence: `the-omitted-placeholder` checks only `valid is True`, because `Verdict` drops warnings.
A door that silently swallows the placeholder passes on `validate_config-structured` and
`cli-structured`. Only `validate_structured` asserts the warning. No test asserts that
`validate_structured`, `validate_config`, `convert_config_result` and the CLI emit no
`DeprecationWarning`.
Proposed: give `Row` a `warnings` field checked on every structured door, and add a test that runs
the recommended doors under `warnings.simplefilter("error", DeprecationWarning)`.

### F9 (low): a stale class can survive in the device record

`TestTheRecordExplainsItself` checks `labels <= classes`. A leftover `omitted-block-emitted`
definition with no lines would pass, although the spec says the class is gone. On base no defined
class is unused (checked).
Proposed: assert `labels == classes`.

### F10 (low): malformed-text coverage gaps

Evidence (`tc_probe1.py`, base): `system {...};` writes `set system }`. `host-name router1;;`
gives `host-name "router1;"`. Neither is pinned. The convert-level refusal test omits
`audit unused`. Whether the device refuses a missing `;` before `}` has no device evidence (base
already refuses it).
Proposed: parameters for `};` after an ordinary block, `;;` and a lone `;`, each either refused or
read as the same statements, as the owner decides. Add `audit unused` to
`test_every_door_refuses_it`.

### F11 (low): freeze wording and the `artifacts_dir` scope

Correct the freeze's list of parameters that pass on base (§1). Optionally, add a spy test that
`validate_structured(text, artifacts_dir=X)` resolves only `X` for both the walk and the set
validation.

## Summary

All 47 new failures fail for the right reason. The passes on base are the named guards plus 35
reference parameters (set, JSON and YAML doors) that the freeze does not list. No existing oracle
is weakened.

Findings, ranked, each with a proposed test:

1. **F1 (high):** splitting at sibling boundaries makes `hold-time up 2000 down;` valid. It was
   invalid on base, and `validate_set` accepts `hold-time down` (executed).
   - Add a negative contract row and a `structured_set_lines` case.
   - Raise a spec challenge.
2. **F2 (high):** the tests freeze "an empty block is never written", but `lldp { }` drops what
   `lldp;` writes, and no device evidence backs the rule.
   - Ask for a device probe.
   - Hold back the `an-empty-block` parameters until it answers.
3. **F3 (medium-high):** auto-detection reads one-line text with a tag as YAML, so the CLI and
   audit fail without `-i`.
   - Add `detect_format` and CLI cases.
4. **F4 (medium):** `audit unused` gives a false all-clear on one-line blocks.
   - Add audit to `TestABlockOnOneLine`.
5. **F5 (medium):** `xfail_on` absorbs crashes (executed).
   - Add `raises=AssertionError`.
6. **F6 (medium):** the spec says the deprecated doors keep their verdicts, but three contract rows
   change them.
   - Reword the spec.
   - Pin one changed verdict.
7. **F7 (medium):** a quote-blind lexer that drops tags passes the relative lexer tests (executed).
   - Use absolute expectations.
   - Add cases where a comment holds a quote.
8. **F8 (medium-low):** only `validate_structured` asserts warnings, and nothing guards against a
   deprecation leak.
   - Add a `warnings` field to `Row`.
   - Add a test with DeprecationWarning set to error.
9. **F9 (low):** the device record allows a stale class.
   - Assert `labels == classes`.
10. **F10 (low):** `};`, `;;` and a lone `;` are unpinned, and the malformed test has no audit
    door.
    - Add those parameters.
11. **F11 (low):** the freeze's guard list needs correcting.
    - Add an `artifacts_dir` spy test.
