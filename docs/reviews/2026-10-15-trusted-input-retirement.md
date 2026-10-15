# Review: what the trusted-input rule retires

Date: 2026-10-15. Base: `master` at `adb6fb7` (v0.28.18). Analysis only; nothing in the
repository was changed.

## Scope and method

The rule: configuration input is trusted in every format. junoscfg adds no protection
against hostile input (alias bombs, memory exhaustion) and does not work around PyYAML.
Bugs in junoscfg's own code still get fixed: wrong output, silently dropped statements,
or a crash in its own processing. Rulings that apply it: the size bound goes, the
64-level depth ceiling and the cycle refusal stay, the PyYAML behaviour is left alone,
legacy `yaml` gets only its crash fix, and the relative `--path` leftovers get fixed.

Method: one `graphify query` (the graph dates from 2026-10-14 and doesn't contain the
yaml-new code merged on 2026-10-15, so it only helped for older code), then a grep sweep
over `src/`, `tests/`, `docs/`, `openspec/specs/`, `ARCHITECTURE.md` and `changelog.d/`
for size, depth, recursion, alias, bomb, untrusted, timeout and parser-hardening
patterns, followed by reading each hit.

Overlap: worktree `/private/tmp/junoscfg-yaml-depth-ceiling` (branch
`change/yaml-depth-ceiling`) has been started for these rulings. At the time of this
analysis it holds only `openspec/changes/yaml-depth-ceiling/.openspec.yaml`. Use this
report as that change's checklist.

**Main result:** all the hostile-input protection in the product is in one place: the
alias-expansion bounds in `junoscfg.input.find_non_json_value` and the records and tests
around them. No other format has hardening. The XML, set, structured, JSON and anonymizer
paths have no size, timeout or entity limits. Every other guard the sweep found protects
correctness or guards a crash in junoscfg's own processing, so it stays.

## Summary

| # | Item | Verdict |
|---|---|---|
| R1 | Size bound in `find_non_json_value` (`_TOO_LARGE`, budget, `_as_parsed` count) | **Delete** |
| R2 | Relative depth bound ("deeper than it is written") | **Replace** with the fixed 64-level ceiling |
| R3 | Copy tracking used only by the bounds (`seen`, `again`, `inside_copy`, `_BOUNDS`, outermost-alias path rewrite) | **Delete** |
| R4 | `_as_parsed` | **Delete** (it only exists to size the bounds) |
| R5 | Kind `alias` in `NonJsonValue` | **Delete or rename** (no refusal is about an alias any more) |
| R6 | Bomb tests, `alias_bomb_yaml` / `alias_bomb` rows, `within()` timer, `alias_chain_yaml` padding, `NESTED_ONCE` / bound-arithmetic tests | **Delete or rewrite** (with R1 gone they hang) |
| R7 | Records: ARCHITECTURE "untrusted input", decision record, spec requirement, contracts, API page, guides, changelog fragment | **Rewrite / supersede** |
| R8 | Dead `# noqa: S320` in `display/to_yaml.py:32` | **Delete** (ruff `S` is not selected) |
| K1–K7 | Cycle refusal, `unshared`, `_refuse_malformed_records`, iterative renderer, schema-generator depth cutoffs, `safe_load`, non-JSON-type refusal | **Keep** (correctness or own-crash guards) |
| B1 | Backlog YAML-BREAKS-001 | **Owner question**: possibly a PyYAML behaviour → drop |
| B2 | Backlog YAML-DATE-001 | **Keep** (a silent drop by junoscfg's set writer) |

## Product code

### R1–R4: `src/junoscfg/input.py` — `find_non_json_value`

Current shape (`input.py:41-176`, about 110 lines of logic):

- `_TOO_LARGE`, `_TOO_DEEP`, `_BOUNDS` (`:46-50`): two bound reasons.
- `find_non_json_value` (`:68-98`): runs `_as_parsed` first, then walks with a budget of
  the parsed size.
- `_as_parsed` (`:101-120`): an iterative pre-pass counting values and the deepest
  level. It exists only to size the two bounds.
- `_Walk` (`:123-173`): `left` (the budget), `deepest`, `seen` (containers already met),
  `open` (the containers on the current path, for cycles), `inside_copy` / `again`
  (charge only copies), and the rewrite at `:154-156` that moves a bound refusal's path
  to the outermost alias.

Under the rule:

| Part | Fate | Why |
|---|---|---|
| `left` budget, `_TOO_LARGE`, the `left < 0` branch | delete | the size bound is pure DoS protection (ruling) |
| `deepest` from `_as_parsed`, `_TOO_DEEP` "deeper than it is written" | replace with a constant `64` | the ruling keeps a fixed ceiling, not a relative one. The relative bound wrongly refuses harmless documents: `{"a": X, "b": [X]}` is refused today (`test_input.py` `test_a_block_aliased_deeper_than_anything_written_is_refused`) |
| `_as_parsed` | delete | with neither bound relative to the parsed document, nothing needs a pre-pass |
| `seen`, `again`, `inside_copy`, `_BOUNDS`, path rewrite `:154-156` | delete | they only decide which visits are copies and which alias gets blamed. A fixed ceiling refuses at the place where the depth is passed, whether or not an alias is involved |
| `open` (cycle detection) | keep | without it the walk, `unshared` and `junos_json_object` recurse forever (own crash, ruling) |
| non-JSON type and key checks, `_kind` | keep | correctness: yaml-new is the JSON object |

What's left is one recursive visit carrying `(depth, open)`: refuse a non-JSON
value or key, refuse a container already in `open` (cycle), refuse when `depth > 64`.
That's roughly 30 lines instead of about 110, with no pre-pass and no copy accounting.
The docstring's paragraphs about the bounds (`:81-93`) shrink to one sentence.

Accepted consequence (by the rule): a billion-laughs document is walked and then
materialized by `unshared` at full size, so the process hangs or runs out of memory.
That's the caller's problem now.

### R5: `NonJsonValue.kind == "alias"`

`alias` is only produced by the two bounds. With a fixed ceiling the refusal is about
depth, not an alias, and it can happen in an alias-free document too. Options:

- a kind such as `depth` with a reason like `nests deeper than 64 levels`, or
- fold it into the existing reasons.

The message is visible on both named surfaces (CLI stderr, `ValueError` text,
`ValidationError.message`): `json_input.py:70`, `json_output.py:89`,
`json_yaml_validator.py:119`. Removing the size refusal only accepts more (additive).
Renaming the depth refusal's kind and reason changes message text, so the change's
`.openspec.yaml` should say whether that counts as a surface change.

### Callers: simplification only, logic unchanged

- `convert/input/json_input.py:51-71`, `convert/output/json_output.py:75-89`,
  `validate/json_yaml_validator.py:94-121`: the docstrings mention "an alias whose
  copies pass the bounds"; that clause goes. The call stays (cycle, ceiling and
  non-JSON checks).
- `convert/ir.py:35-47` `unshared`: keep the function (correctness: the IR holds no
  object twice). Its docstring "its copies are bounded" becomes false; say "holds no
  cycle and nests at most 64 levels".

### Legacy `yaml` (ruling: only the own crash)

`convert/input/yaml_input.py:28-49`: `_strip_meta_keys` recurses, so a cycle crashes it
with `RecursionError`, and so does a document deeper than the recursion limit (decision
record C5). It already writes shared blocks out, so an alias bomb is simply expanded,
which is accepted now. The fix needs only the cycle refusal and the 64 ceiling, without
the JSON-type check (legacy `yaml` admits dates, see B2).

**Simplification opportunity:** split today's walk into a structural guard (cycle +
ceiling) and the JSON-type check. yaml-new uses both, legacy `yaml` uses only the guard.
That gives one rule instead of two independent crash fixes. Optional: plain `json` input
(`json.loads`, `json_input.py:45`) goes through no guard. A JSON document nested more
than about 1,000 levels crashes `_refuse_malformed_records` (`convert/input/__init__.py:73`)
just as a deep YAML document would. If the owner wants the ceiling to be a rule rather
than a yaml-new special case, the shared door after loading (`convert/input/__init__.py`)
is the place. That's an owner call; it adds a check, it doesn't remove one.

### R8: dead suppression

`src/junoscfg/display/to_yaml.py:32` has `# noqa: S320` (bandit "lxml is unsafe on
untrusted XML"). `pyproject.toml:88-90` doesn't select `S`, so the suppression does
nothing, and under the rule the warning wouldn't apply anyway. Delete it.

## Tests (R6)

With the size bound gone, every test that feeds a real bomb no longer gets a refusal: it
expands 10⁹ or 2⁶⁴ values and hangs until `within()` fails it. These tests have to be
deleted or turned into ceiling tests.

| File | Test / row | Fate |
|---|---|---|
| `tests/unit/input/test_input.py:168-197` | `test_an_alias_bomb_is_refused_in_linear_time`: rows `billion-laughs`, `two-to-the-16` | delete (pure size bound) |
| same | rows `two-to-the-64`, `two-to-the-200`, `a-deep-chain` | rewrite as ceiling refusals (depth > 64 is met on the first branch, so they're fast). New path and reason |
| `:199-207` | `test_a_block_aliased_deeper_than_anything_written_is_refused` | invert: now **accepted** |
| `:209-222` | `test_a_block_reached_three_times_through_nested_anchors_is_refused` (`NESTED_ONCE`, `once`) | invert: now accepted and written out |
| `:224-233` | `test_the_bound_is_twice_the_parsed_document` | delete |
| `:235-256` | `test_the_refusal_names_an_alias_when_the_copies_end_early` (+ `_hosts_sharing_contents` `:24`) | delete |
| `:258-263` | `test_one_value_past_twice_is_refused` | delete |
| `:265-270` | `test_scalars_count_toward_the_bound` | delete |
| `:21`, `:33` | `_TOO_LARGE`, `_TOO_DEEP` constants | delete / replace |
| new | ceiling at exactly 64 accepted, 65 refused; an alias-free 65-deep document refused | add (the boundary is otherwise unpinned) |
| `tests/unit/convert/test_convert_api.py:513-531` | `test_a_yaml_new_shared_block_and_alias_bomb` (validate): bomb half | delete the bomb half, keep the shared-block half |
| `:1142-1170` | `test_a_cycle_or_an_alias_bomb_is_refused`: `billion-laughs` row | delete; `two-to-the-200`, `a-deep-chain` → ceiling messages |
| `:1327-1349` | `test_a_cycle_or_an_alias_bomb_is_refused_on_write`: `two-to-the-16` | delete; `two-to-the-64` and `two-to-the-200` → ceiling |
| `tests/unit/validate/test_json_yaml_validator.py:141-152` | `test_an_alias_bomb_is_invalid` | keep only the deep-chain half, as a ceiling |
| `tests/unit/cli/test_cli.py:205-228` | `test_a_yaml_new_alias_bomb_exits_two`: `billion-laughs` row | delete; `a-cycle` stays, `a-deep-chain` → ceiling |
| `tests/unit/cli/test_cli_validate.py:56-65` | `test_a_yaml_new_alias_bomb_exits_one` | delete |
| `:67-76` | `test_a_yaml_new_deep_alias_chain_exits_one` | keep, ceiling message |
| `tests/unit/cli/test_audit_command.py:74-82` | bomb half of `test_a_yaml_new_shared_block_and_alias_bomb` | delete the bomb half |
| `tests/contract/test_every_message.py:246, 310, 402` | `_YAML_BOMB`, doors `read-yaml-new-alias-bomb`, `cli-read-yaml-new-alias-bomb` | replace with a deep-document door (the "message withholds the path" contract still needs a refusal with a path) |
| `tests/support/aliases.py` | `alias_bomb_yaml` | keep only if a ceiling row uses `(200, 2)`, otherwise delete |
| | `alias_bomb` (IR) | keep for the writer ceiling rows or delete |
| | `alias_chain_yaml` `pad` parameter | delete (it only existed to stay under the size bound) |
| | `NESTED_ONCE` | keep as an *accepted* case |
| | `within()` (SIGALRM timer) | delete once no test can hang. A missing ceiling turns `alias_chain_yaml` into a `RecursionError`, not a hang. Keep it only if a `2**200` row stays |
| | module docstring "or explode" | update |
| | `SHARED_BLOCK`, `CYCLE`, `shared_containers` | keep (correctness) |

The memory rule "tests stay comprehensive" is respected: what goes is the coverage of
a removed behaviour. The ceiling gets its boundary tests instead.

## Records (R7)

| Record | Change |
|---|---|
| `ARCHITECTURE.md:153-156` "yaml-new text is untrusted input: … refuses … an alias past twice the parsed size or deeper than the parsed depth" | contradicts the new rule outright. Replace it with a pointer to the project-wide trust rule plus the cycle and 64 ceiling |
| `docs/decisions/2026-10-15-yaml-new-expands-aliases-within-a-bound.md` (+ `index.md:18`) | supersede: "denial-of-service protection stays" (`:19`) is reversed. New record or status `superseded`, pointing to the trust rule. The "legacy yaml … a separate decision" sentence (`:46-47`) is now decided |
| `openspec/specs/conversion/junos-json-yaml/spec.md:101-143` requirement "… a cycle and an alias bomb are refused" | rewrite: shared blocks written out, cycle refused, ceiling 64. Scenario "Billion laughs" (`:135-138`) deleted; "deeper than the recursion limit" → ceiling. The list of test IDs at `:123` loses about 9 entries. Also `:17`, `:59-60` ("past the bound") |
| `openspec/specs/validation/junos-json-yaml/spec.md` | same wording (lists the bomb tests) |
| `src/junoscfg/input.CONTRACT.md:11-13, 23-26` | the invariant "an alias bomb … is refused, never expanded" is false after the change. Replace it with a cycle-and-ceiling invariant enforced by the new ceiling test |
| `docs/api/input.md:15-23` | drop "twice its parsed values", "linear in the loaded object" |
| `docs/guide/validation.md:59` | "an alias past the …" → ceiling |
| `docs/architecture/developer-guide.md:200` | check the yaml-new sentence for bound wording |
| `changelog.d/+yaml-new-alias-cycles.feature.md:4-8` | "so alias bombs stay harmless" is false after the change. If the fragment hasn't been rendered yet, edit it, otherwise add a new fragment saying the size bound was removed |
| `docs/VERIFICATION.md:263-264` | the timer-guarded bomb rows are gone. Update or note it |
| `openspec/changes/archive/*` | leave as is (history). The new change record points to the rule |

## Kept: looks like hardening, isn't

| Code | Why it stays |
|---|---|
| K1 cycle refusal (`_Walk.open`) | without it the walk, `unshared` and the object stage recurse forever (ruling) |
| K2 `convert/ir.py` `unshared` | correctness: the IR holds no object twice, so an in-place edit on one copy can't change another |
| K3 `convert/input/__init__.py:73` `_refuse_malformed_records` | correctness: an unplaced-statement record with a line break or a brace would make the writer print lines the input never held (wrong output), whoever wrote it |
| K4 `display/config_store.py:219` iterative renderer "to avoid recursion limits" | an own-crash guard on deep trees, and it costs nothing |
| K5 `validate/schema_generator.py:26` `_MAX_DEPTH = 12`, `xsd_parser.py:175`, `grammar_generator.py:339` | about the schema and generator, not configuration input |
| K6 `yaml.safe_load` everywhere | not hardening: it defines what YAML means here (no Python object tags). Switching to the full loader would change behaviour |
| K7 non-JSON-type refusal in yaml-new | correctness: yaml-new is the JSON object |
| Anonymizer "details withheld" | privacy, not input trust |
| lxml parsing (`to_yaml.py:32`, `xml_validator.py:48`) | already uses library defaults with no extra hardening, so nothing to remove |

## Backlog (rule: "PyYAML behaviour … not put on the backlog")

- **B1 YAML-BREAKS-001** (`docs/BACKLOG.md:191`): PyYAML's emitter writes NEL, LS and
  PS raw in a single-quoted scalar, and PyYAML's own reader then reads NEL as a line
  break. That's a PyYAML round-trip trait, which the rule says to leave alone. But it
  shows up as wrong output from junoscfg's `yaml` writer, and the fix (reusing the
  yaml-new representer) is a few lines in junoscfg. **Owner question:** drop it from the
  backlog as a PyYAML trait, or keep it as wrong output. Either way it disappears with
  the `yaml` → `yaml-old` retirement.
- **B2 YAML-DATE-001** (`docs/BACKLOG.md:171`): PyYAML reading a date as a date is
  PyYAML's trait. But junoscfg's **set writer silently drops** the statement, and its
  JSON writer crashes with `TypeError`. Both are junoscfg's own defects, which the rule
  explicitly keeps. **Keep**, and the entry could cite the rule.
- **SC-B** (scalar aliases and merge keys expanded by PyYAML): the rule settles it, no
  backlog entry. Delete the "(SC-B)" sentence from the spec and the decision record.

## Owner questions

1. Kind and reason of the ceiling refusal: new kind `depth`, or fold it in? And does the
   changed message text count as a named-surface change (`.openspec.yaml` migration
   note)?
2. Should the ceiling apply only to yaml-new and legacy `yaml`, or at the shared
   `convert.input` door for every mapping-based format, including `json`?
3. YAML-BREAKS-001: drop it as a PyYAML trait, or keep it?

## Rough size

Product: about 80 lines removed from `input.py`, 4 docstrings shortened, 1 noqa
removed. Tests: about 10 test functions or rows deleted, about 8 rewritten as ceiling
cases, 2 contract doors replaced, 2 or 3 helpers retired. Records: 10 files touched,
and 1 decision record superseded.
