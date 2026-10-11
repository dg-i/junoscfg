# Test/Challenge: json-writer-pure (ARCH-C11; ARCH-C15 INTENTIONAL)

Role: independent Test/Challenge (phase 4, `balanced`, behavioural change).
Head `a05f314`, base `d1e804e`. Read from committed artefacts only; nothing
tracked was edited. The probes are in this folder:

- `probe_coverage.py`: which features the catalogue's read IRs hold, and which of them the current JSON writer mutates.
- `probe_paths.py`: mutation paths on the current writer that no acceptance spelling exercises.
- `wrong_fixes.py`: a pytest plugin that swaps in candidate fixes (`JWP_VARIANT=<name>`).
- `probe_variant.py`: shows that a candidate which passes every test still mutates the IR.

Run them with `PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 uv run --locked --group dev ...`.

## Verdict on the tests as written

- **They fail for the right reason.** On head, before the fix, `TestNoWriterChangesTheIrItIsGiven` fails 8 cases: the four hand-built JSON parameters and four set/structured sources. The assertion diff is `{}` or `True` becoming `[None]`, and the message is "after json". The guard rows pass.
- **They assert meaning.** `repr` equality on the IR catches value, type and key-order changes, and the spec does require key order.
- **No oracle is weakened.** The diff only adds tests.
- **The candidate fixes divide as follows.** A shallow copy fails 8 cases, a three-level copy fails 4, and a copy that shares lists fails 3. A full `copy.deepcopy` passes all 331 cases and the 6315 unit and contract tests. **Three wrong fixes pass everything** (findings 1 to 3).

## Findings, ranked

### 1. The `wrap=False` door is not covered (high)

**Evidence.**
- The `copy-only-when-wrapped` variant deep-copies only when `wrap=True`. It passes the class and all of `tests/unit` and `tests/contract` (6315 passed).
- It still rewrites the caller's IR: `from_dict({"system":{"services":{"ssh":True}}}, "json", wrap=False)` leaves `ssh: [None]` in it.
- `pipeline_result` calls `from_dict(..., wrap=False)` for relative JSON and YAML output, so this is a real door.

**Proposed test.** Parametrize `test_a_hand_built_ir_is_left_unchanged` over `wrap` in `(True, False)`. For set and structured, `wrap` is ignored, so pass it only to the JSON and YAML writers:
```python
@pytest.mark.parametrize("wrap", [True, False], ids=["wrapped", "bare"])
...
from_dict(ir, writer.value, **({"wrap": wrap} if writer in (JSON, YAML) else {}))
```

### 2. The requirement's output half is not asserted (high)

**Evidence.**
- The spec says "the output is the same as when the writer was handed its own copy". Its scenarios require `"ssh": [null]` and `"class": "super-user"` in the output.
- Neither acceptance test reads the output. Both `drop-coercion` (copy, skip `_coerce_scalar_leaves`) and `drop-presence` (copy, skip `_normalize_presence_flags`) pass the class.
- Only unrelated tests catch them:
  - `drop-coercion` is caught by exactly one test, `test_convert_api.py::TestUserClassSingle::test_yaml_user_class_as_list_coerced`, on the YAML door at the top level.
  - `drop-presence` is caught incidentally by the `test_set_input.py` apply-groups and partial-key tests.
- A fix that skipped the passes would therefore be stopped by chance, not by the law.

**Proposed test.**
- Pin the JSON `configuration` for each hand-built spelling. For example, `a-presence-flag-as-true` gives `{"system":{"services":{"ssh":[None]}}}`, and `a-group-in-its-wrapper` gives `{"groups":[{"name":"G1","system":{"services":{"ssh":[None]}}}]}`, which is also ARCH-C15's native list.
- For every writer, assert that `from_dict(ir, w) == from_dict(copy.deepcopy(spelling), w)`.

### 3. Mutation paths no spelling reaches (medium)

The class covers less than its parameter count suggests. Of the 315 catalogue sources, only 4 are mutated on base, all through a `{}` presence flag:

| Catalogue sources with this feature | Count | Mutated on base |
|---|---|---|
| `groups` in its `{"group": [...]}` wrapper | 27 | none |
| `groups` as a list | 26 | none |
| `apply-groups` | 5 | none |
| `@` annotations | 116 | none |

Against this the class runs 331 parametrized cases: 16 hand-built and 315 read.

`probe_paths.py` confirms that the current writer mutates the IR through these hand-built spellings, none of which the class contains:

| Spelling | What the writer does to the caller's IR |
|---|---|
| `{"system":{"services":{"ssh":[True]}}}` | becomes `[[None]]`, through the list branch of `_normalize_presence_flags` |
| a group entry holding `login user [{"name":"admin","class":["super-user"]}]` | coerced in place, through the transparent-container branch of `_coerce_scalar_leaves` |
| `{"groups":[{"name":"G1","system":{"services":{"ssh":{}}}}]}` | normalized in place; this is the JSON/XML reader's group shape |
| `interfaces interface[ge-0/0/0] unit[0] family inet address[198.51.100.1/24] primary: True` | normalized in place, four list levels deep |
| `ssh: True` next to `"@ssh": {"inactive": True}` | normalized in place |

The `share-scalar-lists` variant copies mappings and any list holding containers, and shares lists of scalars. It passes all 6315 tests and still turns a caller's `[True]` into `[[None]]`.

**Proposed test.**
- Add the five spellings above to `_HAND_BUILT`.
- Add one negative guard row, `{"apply-groups":["G1"],"system":{"host-name":"router1"}}`. It is a leaf-list, which is never coerced and not mutated today, so it stops a fix from coercing it.

### 4. The freeze's counts do not match (low)

The delta log says "the other 338 pass". The class collects 331 cases: 8 fail and 323 pass. Correct the figure in `evidence-freeze.md`, and in `tasks.md` if it is repeated there.

## The Builder's conflicts

- **C4 (the law at the owning door): accept.**
  - `tests/CONTRACT.md` and `tools/check_test_doors.py` limit contract tests to `junoscfg` and `junoscfg.cli`.
  - The only caller of `from_dict` inside `src/` is `pipeline_result`, as its last step, on an IR it read itself. The named surfaces, the CLI and `convert_config` included, therefore never hand a writer an IR their caller holds.
  - The door check passes. No CLI or `convert_config` purity test is needed. Their output is pinned by the format matrix, which `correct` passes.
- **C5 (patch, "not a break"): accept.**
  - The decision record `2026-10-09-scope-compatibility-to-production-consumer.md` requires the minor bump only "where compatibility changes".
  - `__init__.py` changes only `__version__`. There is a precedent: `2026-10-10-test-architecture` declared a version-only change for 0.15.2 to 0.15.3.
  - The production collection imports only top-level names.
  - The migration text, `json.loads(from_dict(ir,"json"))["configuration"]`, is accurate.

## Not proposed

A snapshot-and-restore "fix" would pass. Only an exception during rendering would expose it, and there is no cheap way to raise one there. `copy.deepcopy` on entry (C6) is the right shape, so this does not warrant a test.
