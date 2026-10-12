# Targeted evidence freeze

Base: 6d5c152d6880b264c0f18ac86729ee7bdc986377.
Scope: only tests/unit/convert/test_shipped_pattern_warnings.py outside this folder.
Maintenance intent: one preserved warning-free-validation promise, no runtime edit.

## Executed evidence

The public bundled_tree fixture supplies all 263 shipped patterns.
Every entry has its own minimal synthetic leaf with its pattern index; router1 is
a concrete nonempty value, with no enum/type/presence shortcut. The actual public
validate_ir call follows current field validation into POSIX translation and
regex compilation. Python warning capture uses always and public re.purge so the
stdlib cache cannot hide first-compilation warnings. No private import/attribute,
new public API, patched translator, mocked warning or test-door exception is used.
The companion validation test genuinely emits FutureWarning for ^[a&&b]$ and
asserts both its valid current result and the set-intersection warning.

Existing test_field_validator.py::TestPatternValidation::test_a_literal_bracket_in_a_posix_bracket_expression
covers the shape of shipped patterns 49/83 only; repository test search found no
complete shipped-table warning sweep. The missing test already passes against
unchanged baseline source; this is preservation coverage, not a pre-fix red.

Focused pytest: 2 passed, 0 skipped, 0 xfailed, exit 0. Public-door check, Ruff
check and Ruff format --check each exit 0. Retained native argv, exits and hashes:
private_test_data/makeover-work/pattern-sweep-no-warning/targeted-commands.json.
- uv run --locked --group dev pytest -q tests/unit/convert/test_shipped_pattern_warnings.py: exit 0; log SHA256 1b69ecbb245749d5bb66cf7dace2b87f71d7a2b122b0823e25f5dcc67983132f.
- uv run --locked --group dev python tools/check_test_doors.py: exit 0; log SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.
- uv run --locked --group dev ruff check tests/unit/convert/test_shipped_pattern_warnings.py: exit 0; log SHA256 82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18.
- uv run --locked --group dev ruff format --check tests/unit/convert/test_shipped_pattern_warnings.py: exit 0; log SHA256 fd2299c9f1c6dc869070883e281051bfe93aacf66c1a3b0069f45b4aa410ca50.

## Identity and limits

All 83 files under src/ are identical before and after focused execution; manifests
source-before.json and source-after.json are identical. Structure-tree gzip SHA256:
bfef7e7f57e729b6c4ba01a2eb65216ebee2f9d41210f041d1d3468633c9f6a8.
The fixture/table remains read-only; temporary synthetic artifacts use using_tree.
No source, generated product, shared fixture, existing test, contract, activation,
framework, fragment or template changed. No XSD parse/generation/schema/full or
ordinary/fast verification was run. No warning was suppressed and no assertion
was skipped or weakened. Different Python releases may emit different warnings;
the complete sweep intentionally fails if a shipped pattern emits any warning.
Warning freedom does not prove that every regex accepts the correct Junos language
or that invalid-regex fallback never occurs; those are outside this bounded promise.

## Checkpoint

Parked. Targeted test material complete. Next: Root's base renewal and READY
admission, then fresh lightweight maintenance Reviewer and later checks under
owner-authorized scheduling. No review verdict, full-check completion, integration,
archive, version or tag is claimed by this Builder.

## Renewed review candidate

Root's operator-only rebases preserve all owned test/artifact bytes and all 83
source files. Current base: a6ea0c6362ab1a8586a6f9bea9a5d9945bbcdf69;
pre-admission HEAD: 70fb78db200d757abadaebabe887b0fe7bc44613. Original parked
checkpoint b75af5a2bdcc4f6524f2d831f1640ff5a7381fa9 remains preserved by named
ref and verified bundle. Root's retained root-preserved-operator-rebase.json and
root-ready-rebase.json record both renewals, identity comparisons and activation.
Own metadata now declares ready with the same exact sole planned test path;
Root's base/admission task is completed. Readiness is a permission precheck only.
The native readiness and two-test rerun on the resulting commit will be retained
with exact base/HEAD and complete tracked-file before/after manifests in
private_test_data/makeover-work/pattern-sweep-no-warning/immutable-review-checkpoint.json.
Fresh review, ordinary/fast/full-substitute evidence and finalization remain
pending. Historical parked text above describes the original bounded checkpoint.

## Qualified ordinary and fast substitute evidence

Fresh lightweight review remains bound to 5955ae353870fe5114664e86fd9eb5c878cae29f.
Native readiness precheck and the ordinary suite ran on clean proof HEAD
7828979f9990fc9f67b64136cd5ff45364f47265 against base
a6ea0c6362ab1a8586a6f9bea9a5d9945bbcdf69, with UV_OFFLINE=1 and
PYTHONDONTWRITEBYTECODE=1. Ordinary exact argv: uv run --locked pytest tests/ -q
--cov --cov-report=term:skip-covered. Exit 0: 9826 passed, 37 existing skips,
20 existing xfails, 187.95s pytest; 196.818454583s wrapper. Coverage 93.00%
meets unchanged 91.47% floor. Log SHA256
ccf34d8823443ea78f1bad20abe92467ae173926ae45c146edf539d8567efa8f.
All 1232 tracked before/after files match at that proof HEAD (manifest SHA256
2de045c6b46195e1b006f213a7ec2b3c65b9a4ab0d596acf48b0a2167d099a64).

The first sequential fast attempt exited 1 for missing ignored skill mirror,
standard-only removes metadata, and required news fragment; all actual failures
are preserved in substitute-fast.out, SHA256
84d88950f54b17cb40c9a1ff2b730be9d94410b0552d9673b69cffdea839df47.
Public skills --regenerate exited 0. Root approved record/news correction only:
remove removes, add changelog.d/+pattern-sweep-no-warning.misc.md and declare its
exact planned path/changelog. Ordinary was not rerun: all 83 original source
files and owning test remain byte-identical across the correction.

Native readiness precheck, focused 2-test rerun and exact fast retry then ran
sequentially on clean proof HEAD 8cbb125f9500641a3b746bb3b519fa64eb519f83,
with the same base/environment. Each exit 0; focused 2 passed in 0.18s.
Fast exact argv: uv run --locked --group dev --with griffe --with tach --with
towncrier --with vulture agent-ready check --set fast --base
a6ea0c6362ab1a8586a6f9bea9a5d9945bbcdf69. Fast wrapper: 11.164481458s;
log SHA256 3ebdd05bdbf210b37d7f00b25d4b4f558ec75a5a12a5e40dff54e581a7cc679b.
All 1233 tracked before/after files match at this fast proof HEAD (manifest
SHA256 e546caff87506ae6854b9213b3b3fa94d61867957c584e6a6a82d262a4a0d9ac).
Root's requested fresh bounded metadata/news affirmation remains pending.

These are distinct qualified ordinary and fast proof heads, not a canonical
full or physical-schema PASS. Native argv, environment, UTC timings, raw exits,
logs and identities are retained in substitute-native-commands.json,
substitute-retry-native-commands.json and their checkpoints in the canonical
ignored evidence directory. This final record commit changes no runtime/test
bytes. Integration, finalization, metrics, archive, version and tag remain open.

## Economical finalization records and gates

Root accepted the independent metadata/news affirmation of records HEAD
 e3fbb077113d63c754ced890ca9d6879a2a82fe1, base a6ea0c6362ab1a8586a6f9bea9a5d9945bbcdf69.
The affirmation is appended verbatim after the unchanged original review;
its standalone SHA256 is 84d5cc2f9fdc67d6b71045d726e9fd8d474a6f47a061ecffbdf66809168b70bd.
Native metrics capture uses the immutable base/e3fbb pair. Both files were
inspected: 55 added lines over two product paths, six declared runtime
 dependencies at both ends, and 63 root-lock packages at both ends. Session,
workflow and human telemetry remain UNMEASURED because none was supplied.
Measured ordinary/fast proof rows preserve their actual distinct commits/results.
Metrics are records of maintenance preservation, not a claimed performance gain.

On clean records candidate 6de8c57f16e0e7cbe2463041f5c98ad37adcd59a, native
fields, caps, lane, reconcile and strict OpenSpec change validation each exited 0.
All 1235 tracked before/after files match. Their exact argv/environment/head/base,
raw outputs, timings and hashes are retained as finalizer-native-gates.json and
finalizer-gate-*.out in the canonical ignored evidence directory. All lifecycle
checkboxes describe completed preparation/verification only. Actual merge,
archive, version/tag and cleanup remain pending Root action. Maintenance
skip_specs means no main-spec edit; canonical full/physical schema remain not run.
The final record-only task/evidence commit is rechecked with the same native gates
and retained as the clean finalizer checkpoint; it changes no source/test/news
meaning and does not change either reviewed verdict.
