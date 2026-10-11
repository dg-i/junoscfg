# Test/Challenge: anonymized-run-messages (STOP-T)

Role: independent Test/Challenge, phase 4. Read in place on `change/anonymized-run-messages`
at `bd17a78` (product code identical to merge base `b8e6fc1`). Nothing tracked was edited.
Probes (synthetic values only) are in this folder:

| Probe | What it shows |
|---|---|
| `tc_probe_doors.py` | candidate doors, exception chains, exception attributes |
| `tc_probe_tag.py` | the structured reader's "tag inside a key or value" refusal |
| `tc_probe_crash.py` | malformed inputs that crash an anonymized CLI run with a traceback |
| `tc_probe_ptc_cli.py` | the pass-through collision through `junoscfg convert` |
| `tc_probe_xsd.py` | `-v -i xml --artifacts <dir>` with a user-supplied XSD |
| `tc_counterexamples.py` | wrong implementations that the door law accepts (W1-W4) |

## Baseline: the tests fail for the right reason

`pytest` on the new tests: 36 failed and 45 passed. The door law fails 25 of 32 anonymized doors,
and the unit tests fail 11 of 16, as the freeze records. Every failure is the property itself: an
address, a word or a pseudonym appears in a message, the IR is mutated, a warning pairs an
original with its replacement, or the wording is wrong. None fails on setup. The non-anonymized
half and the named pins pass on the base, as the freeze declares.

## Findings, ranked

### F1 (high): three message doors that quote originals are missing from the table

These were executed on the base:

1. **`-v -i xml --artifacts <dir>`** (`tc_probe_xsd.py`). With a user-supplied
   `junos-validated.xsd`, an anonymized run prints `Element 'host-name': [facet 'pattern'] The
   value 'sw1-acme 203.0.114.9' is not accepted ... at /configuration/system/host-name`. The
   freeze lists XML `-v` only as `SchemaLoadError` ("no"). That holds only without artifacts.
2. **Pass-through collision on the CLI** (`tc_probe_ptc_cli.py`). `PassThroughCollisionError`
   derives from `Exception`, not `ValueError`, so `convert` re-raises it. The result is exit 1
   with an uncaught traceback that holds the original address. The door law has a library row
   only.
3. **Structured reader, "tag inside a key or value"** (`set_input.py:143`, `tc_probe_tag.py`).
   `host-name { inactive: sw1-acme; }` gives `Invalid structured input: a tag inside a key or
   value in system host-name sw1-acme`. The route form quotes `203.0.114.0/24`. No test in the
   repository reaches this raise. It is raised before the `;` refusal is reached, so a fix made
   per message would miss it.

Two doors are reached only at the rule level. The AS-number warnings (`warnings.warn`, which
reaches stderr on the CLI) have no CLI or pipeline row. `test_no_other_level_does` does not
capture ipanon's own stderr.

Sources searched for more doors: logging (none in `src/`), `print` (audit only), and
`DeprecationWarning` (value-free). The other raises in `convert/input`, `display` and
`dict_walker` carry no values or name schema words only. `FieldError.path` is a schema path
with no entry names (`tc_probe_doors.py` J2), and `ConversionResult.__repr__` adds only the output.

**Proposed rows for `DOORS`:**

- `cli-validate-only-xml-xsd`: a `tmp_path` XSD as in `tc_probe_xsd.py`, passed with `--artifacts`.
- `cli-pass-through-collision`: `--anonymize-preserve-prefixes <pseudonym>/32`. It needs no exception other than `SystemExit`, and a non-zero exit.
- `read-structured-tag` and `cli-read-structured-tag`.
- `read-structured-quote`: `host-name "sw1-acme ...;`.
- `cli-as-number-warning`: `--anonymize-as-numbers 64496,...` with an overflow.

### F2 (high): the C12 crash exclusion is not acceptable as written

F1.2 is not a defect crash. It is a documented refusal that leaks through the traceback path. In
a real crash, Python prints every message in the exception chain. That includes `__context__`,
which a re-raise inside `except` sets without being asked. Malformed JSON or YAML crashes an
anonymized run today: `{"configuration": [..]}` gives an `AttributeError`, and a YAML
self-anchor gives a `RecursionError` (`tc_probe_crash.py`). These two happen to carry no value,
but nothing guarantees that.

**Proposed rule:** in a run that anonymizes, `junoscfg convert` catches every exception left
after its specific handlers. It prints `Error: the conversion failed (<ExceptionClass>); details
withheld: the run anonymizes` and exits 1 (or 3). Only the class name is printed, and no
traceback. A run that does not anonymize keeps the traceback. `_run_validation` gets the same
rule. No override and no environment read are added.

**Proposed test:** monkeypatch `junoscfg.convert_config_result` to raise `RuntimeError("x")`
chained from `KeyError("203.0.114.9")`.

- Anonymized: `result.exception` is a `SystemExit`, and stderr holds neither the address nor
  `KeyError`.
- Not anonymized: `result.exception` is the `RuntimeError`.

### F3 (high): a wrong implementation passes, as executed in `tc_counterexamples.py`

- **W1, an IPv4 scrubber on every message.** It passes 18 of 32 doors. That is 11 more than the
  base, because those rows check only `ADDRESS` and its pseudonym. With the scrubber,
  `set system host-name [ sw1-acme ]` still prints the whole line.
  - Fix: give every refusal row a non-address word, such as `sw1-acme`.
- **W2, text withheld but the error re-raised inside `except`.** The door predicate passes, yet
  `traceback.format_exception` holds the address through the implicit `__context__`. The XML
  reader already raises `from exc`. `TestAPassThroughCollision` has the same hole.
  - Fix: `_library` and the unit test scan `"".join(traceback.format_exception(error))`.
- **W3, `-v` error lines sent to stdout.** `cli-validate-only-set` passes, because `_cli` reads
  only stderr.
  - Fix: scan `result.stdout` too whenever the exit code is non-zero or the run is validate-only.
  - Fix: add the traceback of a non-`SystemExit` exception, not only `str()`.
- **W4, the door's own message dropped.** The scan is non-empty only because another source
  printed. `field-validation-unplaced` passes on the `anonymize:` warning alone. More broadly,
  printing `error (withheld)` everywhere passes every row. Nothing asserts the meaning the spec
  keeps: path, reason, expected value, line and count.
  - Fix: add a field to `Door` that holds the fragment the anonymized run must print, for
    example `system.services.ssh.protocol-version` with `must be one of [v2]`, `line 1`,
    `1 tag(s)`, `collides`, or `Validation: FAILED (1 error(s))` with `line 1`.

### F4 (medium): how the test matches words

The match is a case-sensitive substring test on chosen words. The words are distinctive, such as
`v9-acme`, `G-PEERS` and `ge-0/0/9`, so short words and keywords cause no false failures. The
short `kept="bogus"` appears only in the positive direction. False passes come from three things:

- Only the chosen words are checked (W1).
- The match is case-sensitive.
- A partial quote, such as `203.0.114.`, slips through.

**Proposal:**

- Make every non-schema word of every row carry the marker `acme` (it is already in `v9-acme`,
  `sys-acme` and `bogus-knob`'s neighbours).
- Assert that `"acme" not in text.casefold()`.
- Assert that no dotted quad matches `\b\d{1,3}(\.\d{1,3}){3}\b`. Schema messages never contain
  one.

### F5 (low)

- `JSONDecodeError.doc` and `MarkedYAMLError.problem_mark.buffer` hold the whole source. They
  are object attributes rather than message text, and they show up in a chained traceback. The
  spec allows `yaml.YAMLError`. Prefer a fresh exception raised `from None`.
- The AS unit test allows the replacement in a warning ("may name a replacement"). The door law
  forbids pseudonyms ("original or replaced"). Settle which one wins in `review.md`.
- NEW-R3 tests (`TestAnonymizeLeavesItsInputAlone`) are sound. Identity-based sharing catches a
  shallow copy. The `no-rule` row requires a copy even when nothing is rewritten.
