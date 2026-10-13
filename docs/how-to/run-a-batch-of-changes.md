# Run a batch of changes

This page is for the Orchestrator, Builders and Reviewers of a batch of junoscfg
changes. The process itself comes from the `agent-ready-change` skill and its
`batches.md`. This page adds what is specific to this repository: which paths
run one at a time, where each change works, how a change is checked against the
devices' own output (the **device-evidence checks**), and how it is versioned
and merged. Which tests a path selects, and the per-path extras beside them,
are in the developer guide's
[pre-review evidence table](../architecture/developer-guide.md#pre-review-evidence-by-the-paths-a-change-touches).
The reasons for dropping the JVD tier are in the
[decision record](../decisions/2026-10-11-retire-jvd-from-per-change-verification.md).

## Plan the batch

1. Keep one gitignored ledger, for example `private_test_data/makeover-ledger.md`.
   It holds the plan and one progress line per finding:
   `ID | status | commit | evidence | blocker`. Every defect any role finds is
   recorded under the change that owns it, even when another change found it.
2. Device questions go in one probe file, for example
   `private_test_data/makeover-probes.md`, with its answers in a matching
   `.out` file beside it. Read the `.out` before you mark an item
   EVIDENCE_BLOCKED.
3. Run no more than `max-builders` Builders at once (`pyproject.toml`
   `[tool.template.batch]`; 3 today), each on its own branch and worktree.
4. Changes that touch any of these paths run **one at a time**:
   - `src/junoscfg/validate/xsd_fixes.py`
   - `src/junoscfg/validate/grammar_generator.py`
   - `src/junoscfg/validate/data/`, which holds the generated grammar
     `junos-set.lark.gz` and the other generated files
   - `tests/data/device/known-differences.json`

   `pyproject.toml` `[tool.template.batch] serialized-paths` carries the same
   list. Two changes that edit the same file never overlap. A change that depends on
   another starts from `master` after that one has merged.

## Give each change a worktree

The main checkout stays on `master`. It is used only for merges, archive commits
and tags. Each change works in `../junoscfg-wt/<slug>`. Run this from the main
checkout:

```sh
slug=<slug>
git worktree add -b change/$slug ../junoscfg-wt/$slug master
for entry in private_test_data/*; do
  [ "${entry##*/}" = README.md ] || ln -s "$PWD/$entry" "../junoscfg-wt/$slug/$entry"
done
```

`private_test_data/` is a tracked directory: git tracks its `.gitignore` and
`README.md`. So you link each entry inside it, not the directory itself, and the
worktree stays clean.

`private_test_data/` is the only place for scratch work, for example
`private_test_data/makeover-work/<slug>/`. Anything created inside a linked
entry lands in the main checkout. A new top-level entry created later in the
worktree's `private_test_data/` stays local to that worktree.

A fresh worktree has no `.claude/skills` mirror (it is untracked), and the
full check's `skills` step fails without it. Write it once:
`uv run --locked --group dev agent-ready skills --regenerate`.

Run Python with `export PYTHONDONTWRITEBYTECODE=1`. Tracked files hold
synthetic values only (`AGENTS.md`, Test Data Conventions).

## Check the change against device evidence

Every change that touches the schema, the grammar, a reader, a writer or the
anonymizer runs these checks. That means paths under `src/junoscfg/validate/`,
`convert/`, `display/` or `anonymize/`, and `src/junoscfg/input.py`.

The evidence comes from one of two sources:

- **(a)** `tests/data/device/`: every capture in its `manifest.json`. This is
  the vMX and QFX5120 renderings of `junoscfg-oracle`, the vMX rendering of
  `synthetic-probes` and the device-rendered JVD configurations, in conf, set,
  JSON and XML. It is the default source.
- **(b)** `examples/junoscfg-oracle.*`: the vMX rendering only. It is faster,
  but it is a subset of (a).

Each check uses (a) where a committed test already reads it, and (b) where only
an example-based test exists:

| # | Check | Source | Committed test today | Missing, and its follow-up |
|---|---|---|---|---|
| 1 | Every rendering converts to every output format with no error and no new diagnostic | (a) | none | T1. Until it lands, use the before/after comparison below: no exception, and no diagnostic the base lacks |
| 2 | Device law: set output equals the device's display set, except the lines in `known-differences.json` | (a) | `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet` | nothing |
| 3 | Every format reads to one IR, and every (reader, writer) round trip keeps it | (a) | `test_device_renderings.py::TestEveryDoorReadsTheDevicesUniversalStatements` (universal statements only); `tests/contract/test_format_matrix.py` (shapes) | T2: the whole IR across the four renderings of a capture, and round trips over the captures |
| 4 | Schema and field validation are as clean as `UNPLACED_IN_THE_EXAMPLE` records, plus the JSON shapes the strict xfails name | (b) | `tests/contract/test_round_trip_validates.py::TestTheExampleRendersValid`, `tests/unit/convert/test_field_validator.py::TestTheExampleConfigurationValidates` | nothing |
| 5 | Anonymization law: every rule combination leaves no eligible original, revert is exact, references resolve | (a) | `tests/corpus/test_device_anonymization.py::TestEveryCaptureAnonymizes` (all rules at once; addresses only) | T3: each rule and combination, and every eligible value, not only addresses |
| 6 | A before/after comparison of every output from base and head, with every changed line explained | (a) | tools/compare_device_outputs.py; tests/tooling/test_compare_device_outputs.py checks the tool with synthetic inputs | Run the shared tool as below |

The follow-ups T1–T4 are test-only or tooling changes, listed in the ledger.

Checks 2 to 5 run in the default suite, so the full checkpoint runs them too.
While you edit, run them on their own (about 18 seconds):

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --locked pytest -q \
  tests/corpus/test_device_renderings.py \
  tests/corpus/test_device_anonymization.py \
  tests/contract/test_format_matrix.py \
  "tests/contract/test_round_trip_validates.py::TestTheExampleRendersValid" \
  "tests/unit/convert/test_field_validator.py::TestTheExampleConfigurationValidates"
```

A fix that removes a recorded difference, or adds one, changes the record. To
rebuild it, run `uv run --locked python tools/device_differences.py`. The tool
stops on any line no class claims. Commit the record with the fix: it is a
serialized path.

### The before/after comparison

Every claim that output is "unchanged except as intended", and every
blast-radius claim, rests on a comparison of base and head over the committed
device captures. The JVD corpus and the `--jvd` tier are retired: do not use
them.

The corpus is every rendering listed in `tests/data/device/manifest.json`:
`synthetic/<device>/*.{conf,set,json,xml}.gz` and
`jvd/<device>/*.{conf,set,json,xml}.gz`. Read them gunzipped, in memory, and
never write them back.

1. Use `tools/compare_device_outputs.py` from the change tree for both records
   and their diff. Keep the resulting JSON files in
   `private_test_data/makeover-work/<slug>/`.
2. Make a base worktree and run the script there:

   ```sh
   git worktree add --detach private_test_data/makeover-work/$slug/base-tree "$(git merge-base master HEAD)"
   ```

3. For each capture, input format and output format (set, structured, json,
   yaml), record what the public API `junoscfg.convert_config_result` gives:
   - the output text;
   - the diagnostics, as (source, severity, path);
   - the field-validation errors and warnings;
   - the class of any exception.

   When the change touches anonymization, repeat this with each anonymize rule
   on its own and with all rules on.
4. Run the same script on the head, then diff the two JSON results by key. The
   shared tool does both:

   ```sh
   w=$PWD/private_test_data/makeover-work/$slug   # from the change worktree
   tool=$PWD/tools/compare_device_outputs.py
   (cd "$w/base-tree" && PYTHONDONTWRITEBYTECODE=1 uv run --locked python "$tool" record "$w/base.json")
   PYTHONDONTWRITEBYTECODE=1 uv run --locked python "$tool" record "$w/head.json"
   PYTHONDONTWRITEBYTECODE=1 uv run --locked python "$tool" diff "$w/base.json" "$w/head.json"
   ```

   For a change that touches anonymization, add `--anonymize` after the
   output path in both `record` commands.

   The base takes about 3 seconds for 96 conversions, or about 40 seconds for 1,152
   with every rule.
5. Every difference is either intended, naming the ID it closes, or a
   regression. Record the counts, for example "N of M conversions differ, all
   explained", in the evidence freeze and in `metrics.md`.
6. Remove the base worktree in phase 7, with
   `git worktree remove private_test_data/makeover-work/$slug/base-tree`.

The device law (`tests/corpus/test_device_renderings.py`) and
`tools/device_differences.py` stay the accountability check. A known-differences
class disappears only through the tool.

Device captures are machine-formatted, so they never exercise hand-written
text. A change may touch text lexing: the curly lexer, the set tokenizer,
comments, quoting, templates such as `${NAME}`, or prose that is not
configuration. It may also touch the lexical scanning of free text: the
anonymizer's address, password and sensitive-word tokenizers. Such a change
adds synthetic adversarial rows to the owning test catalogue. It covers at
least:

- one-line blocks;
- statements that span lines;
- comments that hold `;`, `{`, `}` and quotes;
- templates;
- prose;
- address-form values inside words: `10.255.0.1:100`, `target:<ip>:<n>`,
  `host:<ip>`, `lo_<ip>`.

The evidence freeze names these rows as the substitute for corpus coverage.

After review fixes, run the checks and the comparison again only if runtime
code, tests or generated artifacts changed.

## Run the schema tier when the generators change

Two real-schema declarations in `[tool.template.batch].expensive-tiers` qualify the shipped
25.2 release: one assertion pass, followed by public generation executed twice
for stability. All 12 existing schema assertions remain, including direct-tree
and serialized-tree grammar paths. Generation compares its four raw artifacts
and metadata (excluding only `generated_at`) with the assertion exports and
committed shipped artifacts. The separately scheduled sentinel is removed.

Automatic selection covers XSD parsing/fixes, artifact generators, their shared
compression/key helpers and package door, shipped data,
the schema corpus, schema fixture definitions in `tests/conftest.py`, its
schema-specific support, and the checked dependency fingerprint. Recognized wrapper tests,
workflow documentation and bookkeeping can avoid real schemas only with valid
qualification context. Unknown configuration changes select qualification.
Consumer function-body changes are exempt only when import-time structure and
qualification inputs remain demonstrably compatible; uncertainty selects the
expensive checks. The full checkpoint still runs all ordinary tests, including
compatibility and consumer tests. See the [selection and proof rules](verification-evidence.md#conservative-schema-classification).

A first cheap tier, `schema-dependency-guard`, handles `uv.lock` and dependency
projection changes. The committed `tools/schema-verification/dependencies.json`
fingerprints the entire parsed lockfile except the version of the unique editable
root `junoscfg` package. With valid qualification context, a version-only release bump runs the cheap
guard without selecting real schema work. Missing or invalid context selects
qualification conservatively. All dependency versions, sources,
artifact hashes, Python constraints, development dependencies and other parsed
fields remain relevant. Formatting-only TOML edits do not alter parsed content.

After an actual lock-content change, refresh the projection deliberately:

```sh
uv run --locked --group dev python -B -m tools.schema_dependencies write
```

Commit the changed lock and projection together. The projection change selects
both real-schema tiers. A stale or missing projection fails the cheap guard even
for `check --set expensive`, fails ordinary tests, and blocks direct schema
adapters before costly work. Guard completion means only dependency consistency;
it never claims schema assertions ran. The guard does not need XSD dumps or the
prepared runtime file. Template evidence identity and cache rules are unchanged;
this reduction affects when qualification is selected, not which results it reuses.

Keep the three known dumps under `private_test_data/schemas/` as physical files,
not symlinks. Never use a staged `new.xsd` during immutable qualification.
Before the checkpoint, prepare the runtime identity in the same environment:

```sh
uv run --locked --group dev --inexact python -B -m tools.schema_verification prepare
```

When generator changes alter shipped products, regenerate them through the
existing `--regen-schema` workflow and commit settled products first. Qualification
never overwrites committed artifacts. Run the cheap parity controls and review
wrapper changes before real qualification:

```sh
uv run --locked --group dev pytest -q tests/tooling/test_schema_set_parity.py \
  tests/tooling/test_schema_qualification.py::test_bundled_conversion_preflight
```

For explicit qualification, including older-release compatibility or a measured
shipped run after a wrapper change, use one command (replace the release as needed):

```sh
uv run --locked --group dev --inexact python -B -m tools.schema_verification qualify schema-25.2
```

`schema-21.4` and `schema-23.2` remain declared in application policy and use the
same command. Their existing approved release-count skips retain exact identity
and reason. Explicit qualification checks readiness, takes the template capacity
lock, and forces one uncached assertion pass plus two uncached generation passes.
It stops before generation if assertions fail. Automatic tiers may reuse matching
native evidence; generation inputs bind assertion completion and exports, and
its output hashes are revalidated by the installed wrapper.

Executed outcome JSON contains per-test setup/call/teardown seconds. Shared
fixtures are attributed to the triggering setup, not falsely separated into
individual generator stages. Generation reports public-build seconds. Native
wrapper logs retain these measurements and total command time; local outcome
JSON is a convenience and does not replace hashed native evidence.

No new cache framework or generator API is introduced. Compared with two full
assertion passes and a sentinel, the qualification performs one full pass and
two standalone builds. The extra build preserves the installed template's
stability/output-validation contract; speedup must be measured, not assumed.

## Version and merge

The Orchestrator merges, in the main checkout:

1. Rebase the branch onto the current `master`. Then run the affected tests and
   the fast set again. If the rebase brought runtime changes into the branch,
   run the full checkpoint again. Resolve a conflict in a generated artifact
   (`src/junoscfg/validate/data/`, `known-differences.json`) only by
   regenerating it from its sources.
2. Take the version from `master` at merge time and bump it as `AGENTS.md`
   Version Management says. Builders do not bump, so two parallel branches
   never claim the same number. The branch carries its Towncrier fragment,
   `changelog.d/+<slug>.<type>.md`.
3. On the branch, make the archive commit: the archive move and the version
   bump in `pyproject.toml` and `src/junoscfg/__init__.py`. Then fast-forward
   `master` to it, tag it `v{version}` and remove the worktree. Committing on
   the branch keeps anything staged in the main checkout out of the archive
   commit.
4. Never push without the owner's authorization.

## Rules every change keeps

- **An anonymized run leaks nothing.** No original value and no pseudonym of
  the run may reach any message. That covers warnings, diagnostics,
  `ValidationError`, exception text, `__notes__`, chained exceptions, and CLI
  stdout or stderr. An unexpected failure is re-raised as a `RuntimeError`
  that carries no value.
- **A missing artifact raises `SchemaLoadError`** (CLI exit code 3). It never
  reports "invalid configuration".
- **An acceptance test that fails by design is committed with
  `SKIP=affected-tests git commit ...`**, so the hook does not block it.
- **A test-support exception or marker is keyed to the one file it is for**,
  never to a pattern that could match others.
- **A device claim cites the capture path, the device family and the
  release**, for example
  `tests/data/device/synthetic/vmx-23.2R2-S7.5/junoscfg-oracle.set.gz` (vMX,
  23.2R2-S7.5).

## Assurance

On 2026-10-11 the owner set this standing preference for review and testing:

- **The high-risk floor** for every high-risk change, as the
  `agent-ready-change` skill defines it: a red zone, security or
  trust-boundary work, a data migration, a declared break, a change to a named
  public surface (`consumer`, `cli`), or a cross-domain change. The floor means
  independent Test/Challenge work and a fresh Reviewer at least as capable as
  the Builder.
- **`economy`** for every change below that floor, such as a yellow-zone
  change with none of those traits.

Phase 0 of every change applies this preference: `pyproject.toml`
`[tool.template.assurance]` holds it and cites this section as its record.
