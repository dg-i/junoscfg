# Test/Challenge: value-quoting-by-type (STOP-T)

Independent, context-isolated Test/Challenge role (phase 4), high risk floor.
Worktree `../junoscfg-wt/value-quoting-by-type`, branch `change/value-quoting-by-type`,
base `50b0a10`, head `34f7a48` (acceptance tests `e6efdb2`, no product code).
Synthetic values only. Scratch: `roles/probe/` (plugin `cx_plugin.py` swapping
`format_value` for named candidates; `src/` is a scratch copy of the package with
a spec-faithful `format_value`, node passed at `dict_walker.py` lines 145, 389
and 409, and the candidate `QUOTED` terminal; `run-unit.txt` and `run-matrix.txt`
are the base runs).

## What holds

- **277 failing nodes on base, mostly for the right reason.** 254 format-matrix nodes
  (wrong set lines such as `""( P-A )""` and `"uplink to sw1 "core""`, a read-back
  mismatch, or the curly reader refusing a bare inner quote) plus 23 others (grammar
  `Invalid syntax`, anonymize revert, round trip refused at `"[`). 254 + 23 = 277, as
  `metrics.md` says.
- **The tests can be satisfied.** A spec-faithful candidate (escape `"` only;
  `policy-algebra` text starting with `(`, or one `"(?:[^"\\]|\\.)*"` token, written as
  it is) passes all 22 `test_value_format.py` nodes, including the 2,379-value round
  trip. With the node passed in the scratch `dict_walker`, it also passes 411 selected
  matrix, unit and anonymize nodes (the reader-side quoted-name rows were left out,
  because the scratch copy has no reader change).
- **The tests check meaning, not layout.** They compare IR or declared set lines,
  which `test_format_matrix.py` defines as meaning. No oracle is weakened.
  Removing the strict xfail is correct: `TestKeyedEntriesSurvive` passes 26 of 26
  under the candidate.
- **The text-versus-type traps are caught.** A look-based quoted name on any leaf
  fails the round trip on `"a"`. Quoting an expression on a description fails
  `test_an_expression_on_another_leaf_is_quoted` and row `an-expression-in-a-description`.
  Escaping `\` fails the `\n` pin. Over-quoting `PS-1` fails the plain-name test.
  The reader rule "keep quotes only when the text starts with `(`" is tested from
  both sides: `a-quoted-policy-name-that-reads-as-an-expression` against
  `a-quoted-plain-policy-name` (pin). It is tied to the leaf type by the description row.
- **The device evidence was re-read gunzipped.** vMX and QFX `junoscfg-oracle.set.gz`
  lines 47 and 75, XML `<message>…\nAll…</message>`, JSON `"…only.\\nAll…"`.
  `synthetic-probes.xml.gz` 78-83 holds `<import>"( P-A &amp;&amp; P-B )"</import>`.
  No capture and no grammar-corpus line holds a trailing backslash, `\\` or `\"` after
  a backslash. The only backslashes anywhere are `\n` and `\"`.

## Findings, ranked

### 1. High: policy chains (the curly bracket path) are untested; a partial implementation passes

**Evidence.** All 7,730 `policy-algebra` nodes are leaf-lists (`ll`), so a chain such as
`import [ … ]` is the common case. `dict_walker.py:292` writes a structured leaf-list
of more than one value as `[ … ]`, calling `format_value(v)` with no node. Every new
row uses one-element lists, so that line is never reached.

- The scratch implementation leaves line 292 unchanged. It passes all 411 selected
  nodes and still writes JSON `["( P-A )","P-B"]` as `import [ "( P-A )" P-B ];`,
  which is DEV-4 in curly output.
- On base, `["\"( P-A && P-B )\"","P-C"]` is written `import [ ""( P-A && P-B )"" P-C ];`
  (DEV-6).
- Curly `import [ "( P-A && P-B )" P-C ];` reads to `["( P-A && P-B )","P-C"]` (DEV-5).
- Pre-existing problem: curly `import [ ( P-A && P-B ) P-C ];` reads as
  `["(","P-A","&&","P-B",")","P-C"]`. So once the bracket path is fixed, a one-term
  expression in a chain written to curly also stops reading back. See SC1.

**Proposed test.** Add a shapes row `a-policy-chain-holding-a-quoted-name` with set,
structured (`import [ "( P-A && P-B )" P-C ];`), JSON, YAML and XML sources and IR
`import: ['"( P-A && P-B )"', "P-C"]`, plus
`written={STRUCTURED: ('import [ "( P-A && P-B )" P-C ];',)}`. Add a unit-level
writer test for JSON `["( P-A )","P-B"]` to structured with
`never_written '"( P-A )"'`, until SC1 decides whether a chain may hold an expression.

### 2. High: escaping is not tested where no node is passed

**Evidence.** Candidate `w6_escape_only_with_node` escapes `"` only when a node is
given. It passes all 411 selected nodes. It still writes
`set policy-options policy-statement "P "x" 1" then accept`, which the set reader
refuses ("an unbalanced or inner quote"). The same no-node paths are entry names and
key fields (`dict_walker.py` 312, 315, 383, 575, 589), apply-macro data, `apply-groups`
in `structured_output.py`, and `audit/render.py::_format_path`, whose docstring promises
safety for "adversarial hand-crafted object names". `test_a_quote_inside_a_value_is_escaped`
always passes `_TEXT`, and the round trip only drives `description`.

**Proposed tests.**
- Parametrize the escape test over `node in (_TEXT, None)`.
- Extend the round trip to an entry name and to an apply-macro value: for example,
  apply-macro `M` with data `k` set to `'say "hi"'`.
- In `tests/unit/audit/test_render.py`, render a definition named `P "x" 1` and assert
  `policy-statement "P \"x\" 1"`.

### 3. Medium: the trailing-backslash claim is wrong, and junoscfg's own output stops validating

**Evidence.** The scratch grammar with `QUOTED: /"(?:[^"\\]|\\.)*"/` accepts
`set system host-name "abc\"` (it matches `VALUE: /\S+/`) and rejects only
`"a b\"`. The set reader reads both, as `abc\` and `a b\`, because its tokenizer takes
an unterminated quote to the end of the line. The writer writes value `a b\` as
`"a b\"`. That set output validated on base and is rejected after the change.

No device evidence exists either way, so C7's rejection is a guess. It is consistent
with the curly lexer, which refuses `"abc\";`, but not with the set reader. No test
covers the delta sentence "A quoted value ending in a lone backslash is no longer one
value", or the declared-break text "no longer accepts a quoted value that ends in a
lone backslash". See SC2.

**Proposed tests.**
- Pin the actual behaviour: `"a b\"` is rejected and `"abc\"` is accepted, with a note
  for P11.
- Add a negative case: `set system host-name "a\\" b"` is rejected (an escaped
  backslash, then the closing quote, then `b"`).
- Add an agreement property: over the alphabet `a ␠ " \`, the set reader refuses a line
  exactly when the grammar's `QUOTED` does not close it.

### 4. Medium: a quoted plain name in the IR does not survive a set round trip

**Evidence.** `test_a_policy_algebra_token_is_written_as_it_is[quoted-spaced-name]`
asserts that `"P 1"` is written as it is. With the candidate, JSON `["\"P 1\""]` goes
to set as `import "P 1"`, which reads back as `["P 1"]`. The same happens for
`"P-1"` → `P-1`. This breaks the binding law "each writer's output reads back as that
IR" for an IR that XML or JSON input can carry. See SC3.

**Proposed test.** Add a strict pin or xfail tied to P12: JSON `"\"P 1\""` → set →
JSON gives `"P 1"`. A P12 answer then flips it deliberately rather than by accident.

### 5. Medium: a policy-algebra value can be over-accepted

**Evidence.** These candidates pass every `test_value_format.py` node:
- `w1`: a quoted name is anything that starts and ends with `"`. It writes `"`, and
  `"a" "b"`, as they are.
- `w3`: it escapes quotes inside an expression, so `( "my pol" && ! P-B )` becomes
  `( \"my pol\" … )`.
- `w5`: anything starting with `(` or `"` is written bare.

On base, `import ( "my pol" && ! P-B )` reads and writes back unchanged through set
and curly. `tests/unit/audit` already uses that form.

**Proposed test.** Add parameters on `_ALGEBRA`:
- `'( "P 1" && ! P-B )'` is written as it is.
- `'"'` is written `'"\\""'`.
- `'"a" "b"'` is written `'"\\"a\\" \\"b\\""'`.
- `'"P-1'` is written `'"\\"P-1"'`.

Add a shapes row for an expression holding a quoted name.

### 6. Low: five base failures are TypeErrors only, and the records disagree

**Evidence.** 16 of 22 `test_value_format.py` base failures are
`TypeError: format_value() takes 1 positional argument`. Ignoring the node, base
behaviour already passes five of them: `plain`, `spaced`, `semicolon`, `two-terms`
and `nested`. `evidence-freeze.md` lists `test_a_plain_name_is_quoted_only_where_it_must_be`
as a pin ("base behaviour kept"). `metrics.md` does not, and the node fails on base.

**Proposed correction.** Record these five as signature-only failures, which are pins in
substance, in `metrics.md` and the freeze.

### 7. Low: the `$junos-` pin never passes a node

**Evidence.** Candidate `w4` writes `$junos-…` bare once a node is given, and it passes
the unit pin. Today only `test_only_the_recorded_lines_differ` would catch it, through
the record's `junos-variable-quoted` lines. That test is bidirectional, so it does catch it.

**Proposed test.** Parametrize `test_a_junos_variable_stays_quoted` over
`node in (None, _TEXT)`.

### 8. Low: the spec names an XML door that the escaped-quote and lexing rows lack

**Evidence.** The spec scenario reads "from set, structured, JSON, YAML or XML", but
`_quoting_row` has no XML source.

**Proposed test.** Add `XML: _xml("<interfaces><interface><name>ge-0/0/0</name><description>{xml-escaped value}</description></interface></interfaces>")`
to `_quoting_row`.

### 9. Low: the round trip leaves out the empty string and `\`

**Evidence.** The value sizes are 1 to 3, so `""` is never tried (it reads back on base).
`\` is excluded for P11. Under the candidate:

| Writer | Backslash values that fail | Base | Notes |
|---|---|---|---|
| set | 15 of 45 | 25 of 45 | no regression |
| curly | 31 of 45 | 34 of 45 | one accidental regression, `" \` |

**Proposed test.** Add size 0. Add a P11 strict xfail over the backslash values, so the
gap stays visible.

### 10. Info: audit output changes but the declared break does not mention it

**Evidence.** `audit/render.py` calls `format_value(token)` with no node. A definition
whose name looks like an expression, for example `( A && B )`, used to render bare and
will now render quoted. That is correct, but neither the freeze nor the declared break
mentions it, and no test covers it (see finding 2).

## Specification challenges (`review.md` format)

### SC1

- **Artifact:** `specs/conversion/value-quoting/spec.md`, "A policy-algebra value is written as the device's token" (writer scope); codemap call sites.
- **Counterexample:** JSON `import: ["( P-A )","P-B"]` is written to structured as `import [ "( P-A )" P-B ];`, a policy name. With the node passed it becomes `import [ ( P-A ) P-B ];`, and the curly reader splits that into `(`, `P-A`, `)`, `P-B`. That reading is already wrong on base for `( P-A && P-B )`.
- **User impact:** a curly policy chain holding an expression either changes meaning or does not read back. It is undetected because no row has a chain of two or more values.
- **Proposed correction:** name the bracket path in the requirement, and add the quoted-name chain row (finding 1). Raise a device probe: does the device accept an expression inside a chain, and how does it print one? Until it answers, either have the curly reader take a parenthesised group inside `[ ]` as one value, or record the gap as a non-goal with a strict xfail.
- **Decision:** pending (owner).

### SC2

- **Artifact:** `specs/validation/set-command-validation/spec.md`, "A quoted value takes an escaped quote", last sentence; `.openspec.yaml` declared-break `why` for consumer and cli.
- **Counterexample:** under the new terminal, `set system host-name "abc\"` is still valid (as `VALUE`) and `"a b\"` is rejected. The set reader accepts both. The writer emits `"a b\"` for value `a b\`, which validated on base and is rejected after the change.
- **User impact:** the break is described wrongly, and junoscfg rejects its own set output for a value ending in `\`.
- **Proposed correction:** reword the sentence to "a quoted value holding whitespace and ending in a lone backslash", or make the set reader refuse an unclosed quote as the curly lexer does. Pin whichever behaviour is chosen, and keep P11 open.
- **Decision:** pending (owner).

### SC3

- **Artifact:** `specs/conversion/value-quoting/spec.md`, writer requirement, "or a quoted name (`"( P-A )"`)", against the reader requirement's `(`-only rule (C4).
- **Counterexample:** IR `import: ['"P 1"']` from JSON or XML is written `import "P 1"`, which reads back as `['P 1']`.
- **User impact:** JSON and YAML output after a set or curly hop differs from the input IR for quoted plain names. The device configuration is probably the same (P12).
- **Proposed correction:** state that this case is outside "the output reads back as the same IR" until P12 answers, and pin it (finding 4).
- **Decision:** pending (owner).

## Verdict for STOP-T

The tests are sound for what they cover: they fail for the right reasons, they check
meaning, and a spec-faithful implementation can satisfy them. They are not yet enough
to stop a wrong implementation. Add the tests in findings 1, 2 and 5 before phase 5.
Findings 3 and 4 need the owner's ruling on SC2 and SC3; their interim pins are
reversible. Findings 6 to 10 are record and coverage tidy-ups.
