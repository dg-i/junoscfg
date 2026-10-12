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
