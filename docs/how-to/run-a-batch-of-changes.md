# Run a batch of changes

This page is for the Orchestrator, Builders and Reviewers of a batch of junoscfg
changes. The process itself comes from the `agent-ready-change` skill and its
`batches.md`. This page adds what is specific to this repository: which paths
run one at a time, where each change works, how a change is checked against the
devices' own output, and how it is versioned and merged. The reasons for
dropping the JVD tier are in the
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
3. Run no more than three Builders at once, each on its own branch and worktree.
4. Changes that touch any of these paths run **one at a time**:
   - `src/junoscfg/validate/xsd_fixes.py`
   - `src/junoscfg/validate/grammar_generator.py`
   - `src/junoscfg/validate/data/`, which holds the generated grammar
     `junos-set.lark.gz` and the other generated files
   - `tests/data/device/known-differences.json`

   Two changes that edit the same file never overlap. A change that depends on
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

`private_test_data/` is the only place for scratch work. Create the change's
scratch directory in the main checkout before you link, for example
`private_test_data/makeover-work/<slug>/`. A directory created later inside the
worktree stays local to that worktree.

Run Python with `export PYTHONDONTWRITEBYTECODE=1`. Tracked files hold
synthetic values only (`AGENTS.md`, Test Data Conventions).

## Check the change against device evidence

Every change that touches the schema, the grammar, a reader, a writer or the
anonymizer runs these checks. That means paths under `src/junoscfg/validate/`,
`convert/`, `display/` or `anonymize/`, and `src/junoscfg/input.py`.

The evidence comes from one of two sources:

- **(a)** `tests/data/device/`: every committed capture. This is the vMX and
  QFX5120 renderings of `junoscfg-oracle` and the device-rendered JVD
  configurations, each in conf, set, JSON and XML. It is the default source.
- **(b)** `examples/junoscfg-oracle.*`: the vMX rendering only. It is faster,
  but it is a subset of (a).

Each check uses (a) where a committed test already reads it, and (b) where only
an example-based test exists:

| # | Check | Source | Committed test today | Missing, and its follow-up |
|---|---|---|---|---|
| 1 | Every rendering converts to every output format with no error and no new diagnostic | (a) | none | T1. Until it lands, use the before/after comparison below: no exception, and no diagnostic the base lacks |
| 2 | Device law: set output equals the device's display set, except the lines in `known-differences.json` | (a) | `tests/corpus/test_device_renderings.py::TestJunoscfgWritesTheDevicesSet` | nothing |
| 3 | Every format reads to one IR, and every (reader, writer) round trip keeps it | (a) | `test_device_renderings.py::TestEveryDoorReadsTheDevicesUniversalStatements` (universal statements only); `tests/contract/test_format_matrix.py` (shapes) | T2: the whole IR across the four renderings of a capture, and round trips over the captures |
| 4 | Schema and field validation are as clean as `UNPLACED_IN_THE_EXAMPLE` records | (b) | `tests/contract/test_round_trip_validates.py::TestTheExampleRendersValid`, `tests/unit/convert/test_field_validator.py::TestTheExampleConfigurationValidates` | nothing |
| 5 | Anonymization law: every rule combination leaves no eligible original, revert is exact, references resolve | (a) | `tests/corpus/test_device_anonymization.py::TestEveryCaptureAnonymizes` (all rules at once; addresses only) | T3: each rule and combination, and every eligible value, not only addresses |
| 6 | A before/after comparison of every output from base and head, with every changed line explained | (a) | none: a per-change script | T4: commit the script as a shared tool. Until then, follow the steps below |

The follow-ups T1–T4 are test-only or tooling changes, listed in the ledger.

Checks 1 to 5 run in the default suite, so the full checkpoint runs them too.
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

1. Put the script in `private_test_data/makeover-work/<slug>/compare.py`.
   Until follow-up T4 commits a shared tool, start from
   `private_test_data/makeover-work/compare-template.py`.
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
   template does both:

   ```sh
   cd private_test_data/makeover-work/$slug/base-tree
   PYTHONDONTWRITEBYTECODE=1 uv run --locked python ../compare.py record ../base.json [--anonymize]
   cd -   # back to the change worktree
   PYTHONDONTWRITEBYTECODE=1 uv run --locked python private_test_data/makeover-work/$slug/compare.py record private_test_data/makeover-work/$slug/head.json [--anonymize]
   PYTHONDONTWRITEBYTECODE=1 uv run --locked python private_test_data/makeover-work/$slug/compare.py diff private_test_data/makeover-work/$slug/base.json private_test_data/makeover-work/$slug/head.json
   ```

   The base takes about 3 seconds for 96 conversions, or 37 seconds for 1,056
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

Run the schema tier only when a change touches `xsd_fixes.py`, the parser
(`xsd_extractor.py`, `xsd_parser.py`, `schema_node.py`) or the generators
(`artifact_builder.py`, `schema_generator.py`, `grammar_generator.py`). Run it
once, before review, never again for a review-fix round. It needs a dump under
`private_test_data/schemas/`:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --locked pytest tests/ -q --regen-schema   # regenerates (about 3 minutes), then runs the suite
PYTHONDONTWRITEBYTECODE=1 uv run --locked pytest tests/ -q --regen-schema   # a second run on the committed tree:
git diff --stat -- src/junoscfg/validate/data                               # must print nothing
PYTHONDONTWRITEBYTECODE=1 uv run --locked pytest --schema tests/corpus/test_schema_data.py -q
```

While the generator is still changing, regenerate in a scratch worktree. Do the
official regeneration once, at the end.

## Version and merge

The Orchestrator merges, in the main checkout:

1. Rebase the branch onto the current `master`. Then run the affected tests and
   the fast set again.
2. Take the version from `master` at merge time. Bump the patch for a bug, a
   fix or a docs change. Bump the minor for a break on `consumer` or `cli` that
   the change declares. Builders do not bump, so two parallel branches never
   claim the same number. The branch carries its Towncrier fragment,
   `changelog.d/+<slug>.<type>.md`.
3. Fast-forward `master` to the branch. Make the archive commit, which holds
   the archive move and the version bump in `pyproject.toml` and
   `src/junoscfg/__init__.py`. Tag that commit `v{version}`. Remove the
   worktree.
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

- **`economy`** for a yellow-zone change that declares no break, crosses no
  trust boundary and does no cross-domain work.
- **The high-risk floor** in every other case: a red zone, a declared break, a
  trust boundary or cross-domain work. The floor means independent
  Test/Challenge work and a fresh Reviewer at least as capable as the Builder.

Phase 0 of every change applies this preference.
