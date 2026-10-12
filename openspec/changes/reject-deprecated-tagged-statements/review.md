## Specification challenges

### SC1: Preserve correctness by refusing ambiguous terminal metadata

- Artifact: baseline/structured-input-spec.md requirement "The schema-free set writer of the lexer is deprecated": "It keeps its schema-free route, which places a one-line statement's tag on its last node"; baseline/display-CONTRACT.md "deprecated SetConverter.to_set() tags a last node"; four frozen passing legacy tests listed below.
- Counterexample: held synthetic device route `inactive: route 10.98.0.0/16 reject;` is emitted as `deactivate routing-options static route 10.98.0.0/16 reject`; current reread attaches inactive to @reject and loses route entry inactivity. Device .set marks the route path. Protected autonomous-system likewise targets its value. This is executed evidence from current 69f0726, with matching unchanged owning source on base 5187ac9; no device-loaded consequence claimed.
- User impact: deprecated callers receive changed metadata without a visible error (DeprecationWarning is normally hidden). The correction deliberately rejects a bounded accepted legacy shape; deprecation alone does not waive compatibility.
- Proposed correction: standard bug, declared consumer migration to supported convert_config / validate_structured, explicit path-free ValueError for terminal multiword emitted tags only. Freeze and independently assess all original fixtures and assertions. Keep positive content and correct metadata through supported conversion; separately assert deprecated refusal. No schema knowledge/table/parser is added. Finalizer updates main specs after review.
- Decision: Accepted by root on 2026-10-12 after independently executed Test/Challenge, report SHA256 `5f2c855f8535ba4b01935f4b9e720a4a5f6becc604fd150439e7b7bbfc9591c9`. Verbatim report in test-challenge.md; exact ruling in sc1-ruling.json. Implementation remains gated on root-preserved rebase after the preceding safety release.

| Frozen existing test | Retained positive set content | Proposed supported metadata assertion |
|---|---|---|
| TestSetConverter.test_groups_transform_to_set | Every foo/bar/baz location line | deactivate groups baz snmp location |
| TestSetConverter.test_inactive_apply_groups_to_set | Every root/snmp foo/bar apply-groups line | deactivate apply-groups and deactivate snmp apply-groups |
| TestSetConverter.test_protect_leaf_emits_command | set system host-name router1 | protect system host-name |
| TestSetConverterWritesADeletePrefix.test_delete_prefix_leaf | set system host-name router1 (strengthen original content coverage) | delete system host-name |

None of these tests may simply be deleted, marked xfail or changed to retain a compatibility promise superseded by SC1 without recording the admitted break. Retain correct block-opening tags, one-token flag tags, replace-only and untagged assertions unchanged. Existing device-meaning xfails remain failures under explicit refusal; any reason update requires accurate follow-up context, never relaxed meaning.

## Accepted compatibility qualification

The four original passing tests are valid assertions of the old explicit schema-free compatibility promise. Independent execution found their legacy and supported outputs reread to equal IR on the frozen runtime; they do not establish four additional instances of metadata loss. The held route independently establishes entry metadata loss. Their correction is justified by the admitted conservative toolkit boundary, not a claim that every refused Junos shape or command is invalid.

The complete original group fixture contains `location "foo";`. Supported conversion canonically writes `location foo`; root explicitly accepts that spelling change with unchanged value and IR. Preserve all original positive content meaning, strengthen root apply-groups bar and delete-host-name content coverage, assert exact owning-node metadata targets, and separately assert deprecated refusal on each unchanged full fixture. Frozen baseline bytes remain unchanged.

The accepted predicate is emitted operational tag inactive/protect/delete on stripped terminal lexer text containing ASCII space. It conservatively includes quoted-only text containing ASCII space; quoted-only text with a tab and no ASCII space stays outside. Block tags, one-word terminal flags, replace-only, untagged output and statements() remain unchanged. No schema boundary is guessed.

Implementation comments, docstring and warning must state this refusal truthfully instead of claiming these unsafe terminal cases still return last-node output. Retain the established warning category, replacement and existing valid warning assertions. The standing "next minor release" deprecation timeline remains a policy promise requiring an explicit owner decision when retirement occurs; advancing release versions does not authorize removing these doors in this bounded change.


## Fresh independent source review

# Independent fresh phase-6 source review

## Done

**SOURCE PASS** for `reject-deprecated-tagged-statements` at immutable source HEAD `a439b50c0f052621d9c4b4fb1fa24de3f79efa5f`, BASE `dd626c13bd0bdd3877d848072b31ba7b62df6699`. No source correctness finding or new specification challenge remains within the admitted SC1 promise.

This is a genuinely fresh isolated review. Inputs were the frozen proposal, deltas, evidence freeze, code map, original baselines, public SC1 and independent Test/Challenge report/root ruling, source diff, tests, contracts, and raw proof receipts. No Builder private reasoning or implementer report was received. `implementation-verification.md` was not read as evidence; its filename appears only in the verified post-check records diff.

Recommend root accept the source verdict and proceed with the separately bound reviewed main-spec application. This verdict does not affirm future main-spec edits, authorize merge/archive/versioning, or claim completion of the deferred batch-end checks.

## Evidence

- The guard in `src/junoscfg/display/set_converter.py:151` examines existing stripped terminal lexer text for ASCII space and existing emitted tags inactive/protect/delete, then raises a constant value-free ValueError naming supported conversion. It examines every terminal before calling the renderer. There is one lexer evaluation, no additional parser, schema-name table, schema load, higher-layer import, new public signature, environment override, dependency, or fallback. Stack tags remain outside this terminal predicate.
- Owning display CONTRACT agrees with that precise conservative boundary and retains the shared-kernel layering/lazy-import invariants. The change adds a changelog fragment and declares the consumer break with existing conversion/validation migration. Decision `2026-10-09-scope-compatibility-to-production-consumer` governs the surface; the explicit SC1 root admission remains the controlling conservative compatibility correction. Minor version 0.27 to 0.28 belongs to root at merge.
- Independent focused execution: **113 passed, four existing strict xfailed**, actual exit 0. It includes terminal refusal, original display/deletion behavior, deprecated validators, modern metadata placement, and the lazy XML import invariant. Strict device-meaning xfails retain their assertions and strictness: refusal changes the unsupported failure mode and does not complete the deprecated feature.
- Independent semantic/privacy probes: all **24** orderings of the four stacked tags refuse multiword terminals before any rendering or supplied set-validator call; six further quote-only/comment-tab cases refuse; three explicit quoted-tab, replace-only tagged-looking value, and multiword block preservation cases retain exact output. `statements()` remains unchanged and readable after refusal, including stream input. Synthetic source secrets never occur in refusal messages.
- AST comparison verifies the exact original source string in each of the four migrated methods and unchanged bodies of every other original method in the two files. Each unchanged full fixture preserves supported positive content, exact owning-node metadata, supported STRUCTURED-to-SET-to-JSON equivalence, public `validate_structured()` acceptance, and separate deprecated refusal. The original quoted foo fixture still contains its quotes; supported output canonically unquotes foo, as explicitly accepted by SC1. The four historical old legacy/modern IR equalities were established on 5187ac9; this review does not carry them forward through the preceding scalar-value metadata-reader refusal.
- Held synthetic device oracle count independently reproduces **3 refused terminals / 332 lexed terminals**. The supported route emits the device's route-parent deactivate command and roundtrips with entry inactivity. Device truth comes from `examples/junoscfg-oracle.conf:806` and `:814`, plus `examples/junoscfg-oracle.set:269` and `:273`. No device load, operational side effect, or claim that every conservatively rejected Junos shape is invalid follows.
- Independent integrity execution checks **all 1,313 current tracked files** against `phase5/handoff-tracked.json`, and **all 1,312 tracked files** in each ordinary/initial-fast/corrected-fast before-after pair against the immutable checked-head Git objects. The 1,313 count includes the subsequently added change record. All **46 phase5** and **28 independent-TC** manifest entries match SHA256 and declared sizes. Receipt log hashes, source hash, root ruling report hash, frozen original tests/contract/both main specs, and BASE source identity match. Both main specs are still unchanged. Only five change-record paths differ after the ordinary/fast checked head.
- Raw ordinary evidence is actual exit 0, **10,290 passed / 37 skipped / 20 existing strict xfailed**, **92.95% coverage**, unchanged **91.47% floor**. Raw corrected four-extra fast evidence is actual exit 0, `every check passed`, on that same checked head. The ordinary command has no schema/regen option; the log explicitly records 36 schema skips and one device-grammar skip. This is the owner's admitted substitute and is not called a canonical full/schema checkpoint.

### Required review prompts

1. **Trust-boundary input:** caller-controlled structured configuration crosses the deprecated writer/validator boundary. The new refusal is constant, path/key/value-free, and cannot partially render or feed the set validator; independent probes execute those properties. Existing lexer error behavior is outside this scoped new refusal and unchanged.
2. **Incompatible-but-valid input:** the four valid frozen schema-free fixtures and quoted-only ASCII-space edge are intentionally refused by the declared conservative boundary. They are admitted compatibility changes, not invalid tests. Supported conversion/validation preserves fixture meaning; no retired compatibility guarantee is restored.
3. **Shared blind spot:** schema-free last-node placement can look plausible while losing route entry inactivity. Independent device-parent evidence, supported IR equivalence, and exact modern metadata targets close that blind spot. No inference that every rejected case loses meaning is used.
4. **Second answer:** `_strip_prefixes`, the existing lexer, and existing renderer remain the only tag/lexical providers. Modern conversion consumes unchanged `statements()` and retains schema-owned placement. The only production `to_set()` caller is `StructuredValidator._validate`, whose existing catch converts refusal to invalid; `JunosValidator.validate_structured` delegates and public `junoscfg.validate_structured` remains schema-aware. No new second provider or override appears.
5. **Figures and non-goals:** the 3/332 oracle predicate, four exact fixtures, six substantive paths, snapshot/manifest counts and recorded test/coverage totals were rerun or verified directly from source/raw logs and hashes. The no-parser/schema/import/refactor claims are substantiated by the complete substantive diff, unchanged non-owned tracked paths and lazy-import test. No throughput or device-load claim is made.

## Changed paths

Reviewer wrote only:

- `/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements/independent-fresh-phase6/review.md`

No public review record, lifecycle checkbox, metrics, runtime, test, contract, fixture, main specification, or tracked file was changed by this reviewer. The six reviewed substantive change paths are in the integrity receipt below.

## Commands and exit status

All substantive reviewer commands ran offline with the existing interpreter. Focused execution disables pytest cache and Python bytecode writes; probes disable bytecode writes. No ordinary/full/fast/schema/network/build command was launched by this reviewer.

- Git identity/status/diff and bounded artifact/source/contract/log reads: successful after correcting read-only path lookups. Initial lookup used the main checkout for the worktree's change folder (exit 1); source follow-up used guessed `junos_validator.py` and `test_device_captures.py` paths and was corrected to `validator.py` and the existing corpus files. These were lookup diagnostics, not failed verification.
- Integrity Python heredoc below: actual exit 0.
- Focused pytest argv in receipt below: actual exit 0.
- Independent source/migration/privacy/preservation Python heredoc below: actual exit 0.

The receipts record actual UTC start/end, duration, argv/cwd, code identity, output hashes, and results. Runtime values are observed records, not estimates.

### Integrity receipt

```json
{
  "command": "integrity Python heredoc: git object, snapshot, receipt, manifest and freeze SHA256 verification",
  "cwd": "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
  "start_utc": "2026-10-12T11:38:03.956127+00:00",
  "end_utc": "2026-10-12T11:38:36.269611+00:00",
  "duration_s": 32.31343829201069,
  "exit_code": 0,
  "head": "a439b50c0f052621d9c4b4fb1fa24de3f79efa5f",
  "base": "dd626c13bd0bdd3877d848072b31ba7b62df6699",
  "tracked_current": 1313,
  "tracked_aggregate_sha256": "fb2dd60d68e8bab6e4a00ae1fb67eeae21ec27aba28dbd5c98e5a0cd403b5ae7",
  "manifest_verified": {
    "phase5": 46,
    "independent-tc": 28
  },
  "unchanged_receipt_snapshots": {
    "ordinary": 1312,
    "fast": 1312,
    "fast-after-mirror": 1312
  },
  "only_post_check_record_changes": [
    "openspec/changes/reject-deprecated-tagged-statements/checkpoint.md",
    "openspec/changes/reject-deprecated-tagged-statements/evidence-freeze.md",
    "openspec/changes/reject-deprecated-tagged-statements/implementation-verification.md",
    "openspec/changes/reject-deprecated-tagged-statements/metrics.md",
    "openspec/changes/reject-deprecated-tagged-statements/tasks.md"
  ],
  "frozen": {
    "tests/unit/display/test_set_converter.py": "3e4b3895926724e76c6d429ab27273757a96efed786116baf6a7815e26f7b955",
    "tests/unit/display/test_delete_lines.py": "cf0b782b09860a5959c1004fbc443d44be9cabf56189ae72996580897a59e7ed",
    "src/junoscfg/display/CONTRACT.md": "92b21f2606b131295cff0c510f8efe1bb44a13cebcd8d49f04a794a81c5e96c7",
    "openspec/specs/conversion/structured-input/spec.md": "9f584e71d64b0b52069bada9681c2c258af4370a06ab0c17b301d52c7eeab92c",
    "openspec/specs/validation/structured-validation/spec.md": "3f7c38892f40bca6b5eb02801f6acde770088d77fb3232ba2121a072b0715e21"
  },
  "base_source_sha256": "93d16c7ed47fb3cf261a4e91e4f02623ecaf1711c8812759a15bb77f6c3c2100",
  "source_sha256": "2c274c6aa590b4648eab28ec4e53fb216956f64235df76e94a655452ea4498d8",
  "substantive_paths": [
    "changelog.d/+reject-deprecated-tagged-statements.bugfix.md",
    "src/junoscfg/display/CONTRACT.md",
    "src/junoscfg/display/set_converter.py",
    "tests/unit/display/test_delete_lines.py",
    "tests/unit/display/test_set_converter.py",
    "tests/unit/display/test_terminal_tag_refusal.py"
  ],
  "receipts": {
    "ordinary": {
      "tracked_unchanged": true,
      "argv": [
        "uv",
        "run",
        "--locked",
        "--group",
        "dev",
        "pytest",
        "tests/",
        "-q",
        "--cov",
        "--cov-report=term:skip-covered"
      ],
      "cwd": "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
      "head": "7c1b5a3f31d4279f09d3cb4ab31914f102b2031a",
      "start_utc": "2026-10-12T11:24:51.857311+00:00",
      "end_utc": "2026-10-12T11:28:10.723651+00:00",
      "duration_s": 198.866376166,
      "exit_code": 0,
      "output_sha256": "44c3678138d92c2efbba231fe38e1251f606dc6adf670a675bf984d40b7afcc3"
    },
    "fast": {
      "tracked_unchanged": true,
      "argv": [
        "uv",
        "run",
        "--locked",
        "--group",
        "dev",
        "--with",
        "griffe",
        "--with",
        "tach",
        "--with",
        "towncrier",
        "--with",
        "vulture",
        "agent-ready",
        "check",
        "--set",
        "fast",
        "--base",
        "dd626c13bd0bdd3877d848072b31ba7b62df6699"
      ],
      "cwd": "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
      "head": "7c1b5a3f31d4279f09d3cb4ab31914f102b2031a",
      "start_utc": "2026-10-12T11:28:37.140319+00:00",
      "end_utc": "2026-10-12T11:29:37.501254+00:00",
      "duration_s": 60.360841167,
      "exit_code": 1,
      "output_sha256": "567ac50fedcb8409638afa59bbb774ab538dd03caff8aaf093784a8eeee565af"
    },
    "fast-after-mirror": {
      "tracked_unchanged": true,
      "argv": [
        "uv",
        "run",
        "--locked",
        "--group",
        "dev",
        "--with",
        "griffe",
        "--with",
        "tach",
        "--with",
        "towncrier",
        "--with",
        "vulture",
        "agent-ready",
        "check",
        "--set",
        "fast",
        "--base",
        "dd626c13bd0bdd3877d848072b31ba7b62df6699"
      ],
      "cwd": "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
      "head": "7c1b5a3f31d4279f09d3cb4ab31914f102b2031a",
      "start_utc": "2026-10-12T11:30:04.527420+00:00",
      "end_utc": "2026-10-12T11:31:04.028555+00:00",
      "duration_s": 59.501029875,
      "exit_code": 0,
      "output_sha256": "7a64f69a0d4c7b0a184b012434c313a19c9e09287132f9ca79346b8403b6a6f0"
    }
  }
}
```

Reproduction command:

```sh
python3 - <<'PY'
import pathlib,hashlib,json,subprocess,datetime,time
start=datetime.datetime.now(datetime.timezone.utc).isoformat(); mono=time.monotonic()
w=pathlib.Path('/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements'); p=pathlib.Path('/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements'); base='dd626c13bd0bdd3877d848072b31ba7b62df6699'; head='a439b50c0f052621d9c4b4fb1fa24de3f79efa5f'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=w)
assert git('rev-parse','HEAD').decode().strip()==head
assert git('status','--porcelain')==b''
files=git('ls-files','-z').decode().split('\0')[:-1]
current={f:sha((w/f).read_bytes()) for f in files}
assert current==json.loads((p/'phase5/handoff-tracked.json').read_text())
manifest_counts={}
for sub in ['phase5','independent-tc']:
 d=json.loads((p/sub/'evidence-manifest.json').read_text())
 for f,v in d.items():
  raw=(p/sub/f).read_bytes()
  expected=v['sha256'] if isinstance(v,dict) else v
  assert sha(raw)==expected,(sub,f)
  if isinstance(v,dict):assert len(raw)==v['bytes'],f
 manifest_counts[sub]=len(d)
identity=json.loads((p/'phase5/handoff-identity.json').read_text())
assert sha((p/'phase5/evidence-manifest.json').read_bytes())==identity['evidence_manifest_sha256']
receipts={}; pairs={}
for stem in ['ordinary','fast','fast-after-mirror']:
 d=json.loads((p/'phase5'/f'{stem}.json').read_text());raw=(p/'phase5'/f'{stem}.log').read_bytes()
 assert sha(raw)==d['output_sha256']
 before=json.loads((p/'phase5'/f'{stem}-tracked-before.json').read_text());after=json.loads((p/'phase5'/f'{stem}-tracked-after.json').read_text())
 assert before==after,(stem,'mutated')
 for f,h in before.items(): assert sha(git('show',d['head']+':'+f))==h,(stem,f)
 pairs[stem]=len(before);receipts[stem]=d
changes=git('diff','--name-only',identity['checked_head'],head).decode().splitlines()
assert all(f.startswith('openspec/changes/reject-deprecated-tagged-statements/') for f in changes)
frozen={}
old=json.loads((p/'independent-tc/identity.json').read_text())
change=w/'openspec/changes/reject-deprecated-tagged-statements'
mapfiles={'tests/unit/display/test_set_converter.py':'test_set_converter.py.txt','tests/unit/display/test_delete_lines.py':'test_delete_lines.py.txt','src/junoscfg/display/CONTRACT.md':'display-CONTRACT.md','openspec/specs/conversion/structured-input/spec.md':'structured-input-spec.md','openspec/specs/validation/structured-validation/spec.md':'structured-validation-spec.md'}
for path,f in mapfiles.items():
 raw=(change/'baseline'/f).read_bytes(); expected=old['frozen_baseline_checks'][path]['frozen_sha256']; assert sha(raw)==expected
 assert sha(git('show',old['base']+':'+path))==expected
 if path.startswith('openspec/specs/'):
  assert (w/path).read_bytes()==raw
  assert git('show',base+':'+path)==raw
 frozen[path]=expected
assert sha(git('show',base+':src/junoscfg/display/set_converter.py'))==old['source_frozen_sha256']
assert sha((p/'independent-tc/report.md').read_bytes())==json.loads((p/'root-sc1-tc-ruling.json').read_text())['report_sha256']
substantive=[f for f in git('diff','--name-only',base,head).decode().splitlines() if not f.startswith('openspec/changes/')]
assert len(substantive)==6,substantive
print(json.dumps({'command':'integrity Python heredoc: git object, snapshot, receipt, manifest and freeze SHA256 verification','cwd':str(w),'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'duration_s':time.monotonic()-mono,'exit_code':0,'head':head,'base':base,'tracked_current':len(current),'tracked_aggregate_sha256':sha(json.dumps(current,sort_keys=True).encode()),'manifest_verified':manifest_counts,'unchanged_receipt_snapshots':pairs,'only_post_check_record_changes':changes,'frozen':frozen,'base_source_sha256':old['source_frozen_sha256'],'source_sha256':current['src/junoscfg/display/set_converter.py'],'substantive_paths':substantive,'receipts':receipts},indent=2))
PY
```

### Focused receipt, including raw stdout

```json
{
  "argv": [
    ".venv/bin/python",
    "-m",
    "pytest",
    "tests/unit/display/test_terminal_tag_refusal.py",
    "tests/unit/display/test_set_converter.py",
    "tests/unit/display/test_delete_lines.py",
    "tests/unit/validate/test_structured_validator.py",
    "tests/unit/convert/test_meta_tags.py",
    "tests/unit/display/test_to_yaml.py::TestLazyXmlImport::test_importing_the_package_loads_no_lxml",
    "-q",
    "-p",
    "no:cacheprovider"
  ],
  "cwd": "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
  "start_utc": "2026-10-12T11:38:42.838190+00:00",
  "end_utc": "2026-10-12T11:38:44.227882+00:00",
  "duration_s": 1.389620334,
  "exit_code": 0,
  "output_sha256": "2ebc2aef095d11cc8db84fc3fa4e316d602f52d94f6e44957c1a9d9fde1b8d10",
  "raw_stdout": "......................x............xxx.................................. [ 61%]\n.............................................                            [100%]\n=========================== short test summary info ============================\nXFAIL tests/unit/display/test_set_converter.py::TestStructuredBracketLists::test_an_expression_in_a_bracket_list_is_one_value - EVIDENCE_BLOCKED: specification challenge SC1 (change value-quoting-by-type, owned by change 13 one-ir-at-reader-boundary): the lexer splits a parenthesised expression inside a bracket list into its words; executed P13 confirms the device writes the expression and P-C as two values; owning reader fix pending\nXFAIL tests/unit/display/test_set_converter.py::TestTheExampleConfigurationConvertsToSet::test_the_set_output_means_what_the_devices_set_means - PRODUCT DEFECT of a deprecated door, removed in the next minor release (follow-up of change structured-one-line-blocks): no known-differences class (the device law reads curly through SetConverter.statements, not to_set): to_set() refuses terminal metadata with ASCII space instead of guessing its node; the deprecated door still cannot produce the device-correct route/AS metadata (bounded refusal: reject-deprecated-tagged-statements)\nXFAIL tests/unit/display/test_set_converter.py::TestATagOnAOneLineStatementCoversTheStatement::test_the_tag_names_the_statement[an-inactive-entry-with-a-flag] - PRODUCT DEFECT of a deprecated door, removed in the next minor release (follow-up of change structured-one-line-blocks): no known-differences class: SetConverter.to_set() now refuses the ambiguous terminal rather than placing its tag; device-correct output remains unsupported (see TestTheExampleConfigurationConvertsToSet; reject-deprecated-tagged-statements)\nXFAIL tests/unit/display/test_set_converter.py::TestATagOnAOneLineStatementCoversTheStatement::test_the_tag_names_the_statement[a-protected-statement-with-a-value] - PRODUCT DEFECT of a deprecated door, removed in the next minor release (follow-up of change structured-one-line-blocks): no known-differences class: SetConverter.to_set() now refuses the ambiguous terminal rather than placing its tag; device-correct output remains unsupported (see TestTheExampleConfigurationConvertsToSet; reject-deprecated-tagged-statements)\n113 passed, 4 xfailed in 0.52s\n"
}
```

Reproduction command:

```sh
python3 - <<'PY'
import subprocess,datetime,time,hashlib,json,os
argv=['.venv/bin/python','-m','pytest','tests/unit/display/test_terminal_tag_refusal.py','tests/unit/display/test_set_converter.py','tests/unit/display/test_delete_lines.py','tests/unit/validate/test_structured_validator.py','tests/unit/convert/test_meta_tags.py','tests/unit/display/test_to_yaml.py::TestLazyXmlImport::test_importing_the_package_loads_no_lxml','-q','-p','no:cacheprovider']
cwd='/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements';env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic();r=subprocess.run(argv,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
print(json.dumps({'argv':argv,'cwd':cwd,'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'duration_s':time.monotonic()-t,'exit_code':r.returncode,'output_sha256':hashlib.sha256(r.stdout).hexdigest(),'raw_stdout':r.stdout.decode()},indent=2));raise SystemExit(r.returncode)
PY
```

### Independent probe receipt

```json
{
  "argv": [
    ".venv/bin/python",
    "-"
  ],
  "environment": {
    "PYTHONDONTWRITEBYTECODE": "1"
  },
  "cwd": "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
  "start_utc": "2026-10-12T11:40:02.300347+00:00",
  "end_utc": "2026-10-12T11:40:14.009788+00:00",
  "duration_s": 11.709350874996744,
  "exit_code": 0,
  "head": "a439b50c0f052621d9c4b4fb1fa24de3f79efa5f",
  "canonical_tracked_map_algorithm": "SHA256(json.dumps(path_to_sha256, sort_keys=True, separators=(comma,colon)).encode(UTF-8))",
  "tracked_count": 1313,
  "tracked_before_sha256": "7b62c7f4d7c62a7a9cea32cc2ee3fd514750ffacbb182060b784a68908e73c55",
  "tracked_after_sha256": "7b62c7f4d7c62a7a9cea32cc2ee3fd514750ffacbb182060b784a68908e73c55",
  "original_fixture_rows": [
    {
      "test": "test_groups_transform_to_set",
      "fixture_sha256": "aff05670763bad75bd9af9ed8f276f12eb8800703a25c9f03f43a9ed2e41c709",
      "modern_lines": [
        "set groups foo snmp location foo",
        "set groups bar snmp location bar",
        "set groups baz snmp location baz",
        "deactivate groups baz snmp location"
      ],
      "same_ir": true,
      "public_validation": true,
      "deprecated_refusal": true
    },
    {
      "test": "test_inactive_apply_groups_to_set",
      "fixture_sha256": "7e18a40bfefcf9a601b8bc430145e1964cb0ffe9ba883e93f9e4a876a63a2c14",
      "modern_lines": [
        "set apply-groups foo",
        "set apply-groups bar",
        "deactivate apply-groups",
        "set snmp apply-groups foo",
        "set snmp apply-groups bar",
        "deactivate snmp apply-groups"
      ],
      "same_ir": true,
      "public_validation": true,
      "deprecated_refusal": true
    },
    {
      "test": "test_protect_leaf_emits_command",
      "fixture_sha256": "f45eec138b57a00205711e5f61f225fe357c5542414997bff1b14ea89d951a98",
      "modern_lines": [
        "set system host-name router1",
        "protect system host-name"
      ],
      "same_ir": true,
      "public_validation": true,
      "deprecated_refusal": true
    },
    {
      "test": "test_delete_prefix_leaf",
      "fixture_sha256": "d988f7a55a4e2171c059756be7af10a753382bd7eb947ad9eaf063f1b66781f8",
      "modern_lines": [
        "set system host-name router1",
        "delete system host-name"
      ],
      "same_ir": true,
      "public_validation": true,
      "deprecated_refusal": true
    }
  ],
  "other_original_test_bodies_unchanged": true,
  "stacked_normalized_quote_only_refusals": 30,
  "no_render_or_validator_call": true,
  "preservation_controls": 3,
  "held_oracle": {
    "terminals": 332,
    "refused_terminals": 3
  },
  "supported_device_route_ir_validation": true
}
```

Reproduction command:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import ast,datetime,hashlib,io,itertools,json,pathlib,subprocess,time,warnings
start=datetime.datetime.now(datetime.timezone.utc).isoformat(); t=time.monotonic(); w=pathlib.Path.cwd()
def tracked_map():
 fs=subprocess.check_output(['git','ls-files','-z']).decode().split('\0')[:-1]
 return {f:hashlib.sha256((w/f).read_bytes()).hexdigest() for f in fs}
def digest(d): return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
before=tracked_map();warnings.simplefilter('ignore',DeprecationWarning)
from junoscfg import Format,convert_config,validate_structured
from junoscfg.display import SetConverter
from junoscfg.validate import StructuredValidator
rows=[]; change=w/'openspec/changes/reject-deprecated-tagged-statements'
wanted={'test_groups_transform_to_set','test_inactive_apply_groups_to_set','test_protect_leaf_emits_command','test_delete_prefix_leaf'}
expected_meta={'test_groups_transform_to_set':['deactivate groups baz snmp location'],'test_inactive_apply_groups_to_set':['deactivate apply-groups','deactivate snmp apply-groups'],'test_protect_leaf_emits_command':['protect system host-name'],'test_delete_prefix_leaf':['delete system host-name']}
for file in ['test_set_converter.py','test_delete_lines.py']:
 old=ast.parse((change/'baseline'/(file+'.txt')).read_text()); new=ast.parse((w/'tests/unit/display'/file).read_text())
 def methods(tree):
  return {(cls.name,fn.name):fn for cls in tree.body if isinstance(cls,ast.ClassDef) for fn in cls.body if isinstance(fn,ast.FunctionDef)}
 old_methods=methods(old);new_methods=methods(new)
 for key,fn in old_methods.items():
  fresh=new_methods[key];name=key[1]
  if name not in wanted:
   assert ast.dump(ast.Module(body=fn.body,type_ignores=[]))==ast.dump(ast.Module(body=fresh.body,type_ignores=[])),key
   continue
  def fixture(node):
   return next(s.value.value for s in node.body if isinstance(s,ast.Assign) and isinstance(s.value,ast.Constant) and isinstance(s.value.value,str))
  source=fixture(fn);assert source==fixture(fresh),key
  modern=convert_config(source,from_format=Format.STRUCTURED,to_format=Format.SET)
  assert [l for l in modern.splitlines() if l.startswith(('deactivate ','protect ','delete '))]==expected_meta[name]
  direct=json.loads(convert_config(source,from_format=Format.STRUCTURED,to_format=Format.JSON));reread=json.loads(convert_config(modern,from_format=Format.SET,to_format=Format.JSON));assert direct==reread
  assert validate_structured(source).valid
  converter=SetConverter(source);statements=converter.statements()
  try:converter.to_set()
  except ValueError: pass
  else:raise AssertionError('missing refusal: '+name)
  assert converter.statements()==statements
  rows.append({'test':name,'fixture_sha256':hashlib.sha256(source.encode()).hexdigest(),'modern_lines':modern.splitlines(),'same_ir':True,'public_validation':True,'deprecated_refusal':True})
assert len(rows)==4
class NoRendering(SetConverter):
 def _transform_line(self,*args):raise AssertionError('Rendering began before terminal safety scan completed')
class MustNotValidate:
 def validate(self,*args):raise AssertionError('Refused source reached set validation')
refused=0
for tags in itertools.permutations(['replace','protect','inactive','delete']):
 source='system { host-name router1; '+''.join(tag+': ' for tag in tags)+'domain-name secret-sentinel; services { ssh; } }'
 c=NoRendering(io.StringIO(source));original=c.statements()
 try:c.to_set()
 except ValueError as e:
  assert 'convert_config' in str(e);assert all(v not in str(e) for v in ['router1','secret-sentinel','domain-name','system'])
 else:raise AssertionError('Stacked tags did not refuse')
 assert c.statements()==original
 result=StructuredValidator(MustNotValidate()).validate(source);assert not result.valid;assert 'secret-sentinel' not in result.errors[0].message
 refused+=1
for tag in ['inactive','protect','delete']:
 for source in [f'system {{ {tag}: "a b"; }}',f'system {{ {tag}: /* comment */ host-name\trouter1; }}']:
  try:SetConverter(source).to_set()
  except ValueError:refused+=1
  else:raise AssertionError('Normalized/quote-only source did not refuse')
legacy=[('system { protect: "a\tb"; }','set system "a\tb"\nprotect system "a\tb"\n'),('system { replace: host-name "protect: secret-sentinel"; }','set system host-name "protect: secret-sentinel"\n'),('routing-options { replace: protect: inactive: delete: static { route 198.51.100.0/24 { reject; } } }','set routing-options static route 198.51.100.0/24 reject\nprotect routing-options static\ndeactivate routing-options static\ndelete routing-options static\n')]
for source,expected in legacy:
 c=SetConverter(source);original=c.statements();assert c.to_set()==expected;assert c.statements()==original
oracle=SetConverter((w/'examples/junoscfg-oracle.conf').read_text()).statements(); refused_oracle=[terminal for levels in oracle for terminal,tags in [levels[-1]] if ' ' in terminal and tags & {'inactive','protect','delete'}]
assert len(oracle)==332 and len(refused_oracle)==3
route='routing-options { static { inactive: route 10.98.0.0/16 reject; } }'; modern=convert_config(route,from_format=Format.STRUCTURED,to_format=Format.SET)
assert modern=='set routing-options static route 10.98.0.0/16 reject\ndeactivate routing-options static route 10.98.0.0/16\n';assert validate_structured(route).valid
assert json.loads(convert_config(route,from_format=Format.STRUCTURED,to_format=Format.JSON))==json.loads(convert_config(modern,from_format=Format.SET,to_format=Format.JSON))
after=tracked_map();assert before==after;assert subprocess.check_output(['git','status','--porcelain'])==b''
print(json.dumps({'argv':['.venv/bin/python','-'],'environment':{'PYTHONDONTWRITEBYTECODE':'1'},'cwd':str(w),'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'duration_s':time.monotonic()-t,'exit_code':0,'head':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'canonical_tracked_map_algorithm':'SHA256(json.dumps(path_to_sha256, sort_keys=True, separators=(comma,colon)).encode(UTF-8))','tracked_count':len(before),'tracked_before_sha256':digest(before),'tracked_after_sha256':digest(after),'original_fixture_rows':rows,'other_original_test_bodies_unchanged':True,'stacked_normalized_quote_only_refusals':refused,'no_render_or_validator_call':True,'preservation_controls':len(legacy),'held_oracle':{'terminals':len(oracle),'refused_terminals':len(refused_oracle)},'supported_device_route_ir_validation':True},indent=2))
PY
```

The canonical tracked-map algorithm is SHA256 of UTF-8 `json.dumps(path_to_file_SHA256, sort_keys=True, separators=(',', ':'))`. Before and after independent probes both contain 1,313 files and hash `7b62c7f4d7c62a7a9cea32cc2ee3fd514750ffacbb182060b784a68908e73c55`. The earlier integrity receipt uses Python's default JSON separators for its aggregate, explicitly shown in its reproduction command; it is a separate reproducible representation of the same unchanged map.

## Open questions for the owner

None for source correctness or admitted SC1 compatibility. Carry-forward work is bounded main-spec application plus a separate same-reviewer affirmation, root-controlled merge-time minor bump, and the owner-reserved entire-batch-end checks. Deprecated-door retirement stays an explicit policy decision outside this source repair.

## Deviations

- Higher-priority reviewer write rules permit `review.md` rather than arbitrary report/manifest/receipt filenames. Root accepted one private `independent-fresh-phase6/review.md` containing the complete verdict, commands, hashes and receipts. No separate new evidence files are claimed. The public lifecycle checkbox remains untouched for root to record after acceptance.
- The dispatched ruling path concatenated the independent-TC directory with the root ruling filename. The actual `root-sc1-tc-ruling.json` beside that directory was located, read, and its accepted report hash verified.
- The owner explicitly substitutes the native ordinary suite plus four-extra fast for the canonical full adapter at this checkpoint. This is documented in the frozen instruction-integrity/evidence records; no schema execution was repeated.
- Existing proof retains an initial fast exit 1 solely for the missing ignored skills mirror, native ignored repair, and subsequent fast exit 0 with identical tracked inputs. A separate prelaunch wrapper typo is recorded as exit 2 with UTC/duration unmeasured; it was not a launched fast check. Neither failure is hidden or counted as passing evidence.
- Main-spec affirmation is intentionally a later separately bound pass. SOURCE PASS is scoped to the present immutable source and accepted delta, with main specs still frozen.



## Fresh independent exact main-spec affirmation

# Same-reviewer main-spec affirmation

## Done

**MAIN SPEC AFFIRMATION PASS**, separately bound to the following exact proposed bytes:

| Main specification | Affirmed SHA256 |
|---|---|
| `openspec/specs/conversion/structured-input/spec.md` | `ecf73001af7000f5a17bd256e64d14ba2e120fc58c694c7eb1ef1c5c5c66c541` |
| `openspec/specs/validation/structured-validation/spec.md` | `612550612e0eb8283d96061e70a0a3448c6431041fdfe03ffcb249b90680fc5c` |

Affirmed generated diff SHA256: `0ec32793d140d3c1528415186fa298f93d0b49323a51d5b8dedabb1d82eda50f`.

Recommend root admit precisely those two generated main-spec files. No concrete finding or new specification challenge arises. This affirmation does not authorize any additional product, test, fixture, contract, policy, version, or archive change.

The existing SOURCE PASS stays bound to immutable `a439b50c0f052621d9c4b4fb1fa24de3f79efa5f`, BASE `dd626c13bd0bdd3877d848072b31ba7b62df6699`, and immutable original source-review SHA256 `47aef028f0398b4d0c8cfc914c45d5dfa07d06af02a1c0c5595262b14cd62881`.

## Evidence

- Read both complete generated main files and exact diff. Each replaces one existing deprecated-door requirement with the exact corresponding reviewed delta. Conversion retains five requirements; validation retains two. Prefix/purpose and all unrelated requirement bodies match the source byte content; no requirement is added or removed.
- The conversion requirement now states precisely the conservative ASCII-space predicate on stripped terminal text with inactive/protect/delete, value-free ValueError and supported replacement. It preserves the existing lexer, block-opening tags, one-token terminals, replace-only, untagged output, and `statements()`. The route scenario retains supported parent inactivity; leaf/list scenarios retain supported positive content and owning metadata. These claims are the ones independently exercised in the accepted source review.
- The validation requirement adds invalid/path-free refusal without reaching set validation through the two deprecated doors; public schema-aware `junoscfg.validate_structured()` remains the replacement. It preserves prior warning category/replacement/removal wording and the unaffected modern validation requirement.
- The proposed text is consistent with approved SC1's conservative compatibility correction. It does not misclassify the four frozen old assertions as invalid, claim four additional device-proven losses, infer device-loaded effects, remove deprecated doors, or widen the named operational-tag predicate. The existing next-minor wording is preserved; it supplies no automatic retirement action here.
- Independently verified base/source/delta/proposed SHA256 for both files, corresponding BASE and SOURCE Git objects, exact current delta bytes, generated disposable-checkout main bytes, command receipt hashes, and exact proposed diff bytes. Native pinned offline archive receipts record `+0, ~2, -0, →0`; strict native spec validation records **28 passed, zero failed**, actual exit 0.
- Every one of **1,313 live tracked files** still matches the admitted source map. Canonical before/after map SHA256 remains `7b62c7f4d7c62a7a9cea32cc2ee3fd514750ffacbb182060b784a68908e73c55`. In the disposable checkout, **1,291** unaffected tracked source paths match the reviewed source hashes, covering all runtime, tests, contracts, original baselines, and committed fixtures. Exclusions are exactly the change's archived record folder and the two generated main-spec paths. The original private source report was verified unchanged.
- No live main specification has been applied by this reviewer. No new implementation evidence was invalidated: the live runtime/tests/fixtures/source identity is unchanged, and this pass verifies the private proposed documentation of the already reviewed behavior.

## Changed paths

Reviewer wrote only:

- `/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements/main-spec-affirmation/review.md`

The original `independent-fresh-phase6/review.md` remains immutable. No public record, lifecycle checkbox, metrics, source, tests, fixtures, contracts, main specification, or live checkout path was changed.

## Commands and exit status

Bounded proposed-file/diff reads: exit 0.

Independent integrity/requirement/receipt-preservation Python command: exit 0 after correcting an interpreter-compatibility issue in the private verification command. The original invocation exited 1 because the system interpreter lacks `zip(..., strict=True)`; replacing it with an explicit equal-length assertion and ordinary zip retained the intended check. No specification or product byte was changed to obtain the passing result.

No native archive, live-write/check flags, full/schema/network/build command was launched by this reviewer. The finalizer's native offline generation and strict-spec validation receipts were verified directly; full stdout/stderr are preserved in the existing private finalizer evidence folder and their hashes are embedded below.

### Verified receipt and independent command result

```json
{
  "argv": [
    "python3",
    "-"
  ],
  "cwd": "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
  "start_utc": "2026-10-12T11:52:03.546910+00:00",
  "end_utc": "2026-10-12T11:52:03.834656+00:00",
  "duration_s": 0.287687375,
  "exit_code": 0,
  "source_head": "a439b50c0f052621d9c4b4fb1fa24de3f79efa5f",
  "base": "dd626c13bd0bdd3877d848072b31ba7b62df6699",
  "source_report_sha256": "47aef028f0398b4d0c8cfc914c45d5dfa07d06af02a1c0c5595262b14cd62881",
  "tracked_count": 1313,
  "canonical_tracked_before_sha256": "7b62c7f4d7c62a7a9cea32cc2ee3fd514750ffacbb182060b784a68908e73c55",
  "canonical_tracked_after_sha256": "7b62c7f4d7c62a7a9cea32cc2ee3fd514750ffacbb182060b784a68908e73c55",
  "disposable_unaffected_source_files_verified": 1291,
  "proposed_main_specs": [
    {
      "main_path": "openspec/specs/conversion/structured-input/spec.md",
      "delta_path": "openspec/changes/reject-deprecated-tagged-statements/specs/conversion/structured-input/spec.md",
      "source_sha256": "9f584e71d64b0b52069bada9681c2c258af4370a06ab0c17b301d52c7eeab92c",
      "delta_sha256": "83a5637d01e4cba01ae960a195db7b76f7f53f9fd6fa054311a7a88534fc2cf1",
      "base_sha256": "9f584e71d64b0b52069bada9681c2c258af4370a06ab0c17b301d52c7eeab92c",
      "proposed_sha256": "ecf73001af7000f5a17bd256e64d14ba2e120fc58c694c7eb1ef1c5c5c66c541",
      "requirement_count_before": 5,
      "requirement_count_after": 5,
      "only_modified_requirement": "The schema-free set writer of the lexer is deprecated",
      "modified_requirement_identical_to_reviewed_delta": true,
      "unaffected_requirements_identical": true
    },
    {
      "main_path": "openspec/specs/validation/structured-validation/spec.md",
      "delta_path": "openspec/changes/reject-deprecated-tagged-statements/specs/validation/structured-validation/spec.md",
      "source_sha256": "3f7c38892f40bca6b5eb02801f6acde770088d77fb3232ba2121a072b0715e21",
      "delta_sha256": "15db570f008703db2d3427460151e5bb2065c7d348b9003e2831c17b2a35745d",
      "base_sha256": "3f7c38892f40bca6b5eb02801f6acde770088d77fb3232ba2121a072b0715e21",
      "proposed_sha256": "612550612e0eb8283d96061e70a0a3448c6431041fdfe03ffcb249b90680fc5c",
      "requirement_count_before": 2,
      "requirement_count_after": 2,
      "only_modified_requirement": "The validate package's structured doors are deprecated",
      "modified_requirement_identical_to_reviewed_delta": true,
      "unaffected_requirements_identical": true
    }
  ],
  "proposed_diff_sha256": "0ec32793d140d3c1528415186fa298f93d0b49323a51d5b8dedabb1d82eda50f",
  "native_command_receipts": [
    {
      "argv": [
        "uv",
        "run",
        "--locked",
        "--group",
        "dev",
        "agent-ready",
        "caps"
      ],
      "cwd": "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
      "utc_start": "2026-10-12T11:49:42.833092+00:00",
      "duration_seconds": 0.4967664169962518,
      "exit": 0,
      "environment_overrides": {
        "npm_config_offline": "true",
        "OPENSPEC_TELEMETRY": "0",
        "UV_OFFLINE": "1"
      },
      "stdout_sha256": "84c5d06c18a3d0b4fcc5b53dd159b2706fae38788a78e38f4e6c876c5e67a691",
      "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "raw_stdout": ".agents/skills/openspec-bulk-archive-change/SKILL.md: cap 300 lines; current length 339 lines; counting rule: physical lines; blank lines count and a final newline does not add a line  (reported, not capped)\n.agents/skills/openspec-explore/SKILL.md: cap 300 lines; current length 343 lines; counting rule: physical lines; blank lines count and a final newline does not add a line  (reported, not capped)\n.agents/skills/openspec-onboard/SKILL.md: cap 300 lines; current length 561 lines; counting rule: physical lines; blank lines count and a final newline does not add a line  (reported, not capped)\n",
      "raw_stderr": ""
    },
    {
      "argv": [
        "git",
        "clone",
        "--shared",
        "--no-hardlinks",
        "--single-branch",
        "--branch",
        "codex/reject-deprecated-tagged-statements",
        "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
        "/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements/finalizer-main-spec/disposable-checkout"
      ],
      "cwd": "/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements",
      "utc_start": "2026-10-12T11:49:43.333963+00:00",
      "duration_seconds": 0.2300442919950001,
      "exit": 0,
      "environment_overrides": {
        "npm_config_offline": "true",
        "OPENSPEC_TELEMETRY": "0",
        "UV_OFFLINE": "1"
      },
      "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "stderr_sha256": "8ef7bd08a7785c15b5a619908a65b42f30d3105e99e766e27e986561986f7297",
      "raw_stdout": "",
      "raw_stderr": "Cloning into '/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements/finalizer-main-spec/disposable-checkout'...\ndone.\n"
    },
    {
      "argv": [
        "npx",
        "--yes",
        "@fission-ai/openspec@1.13.0",
        "archive",
        "reject-deprecated-tagged-statements",
        "--yes"
      ],
      "cwd": "/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements/finalizer-main-spec/disposable-checkout",
      "utc_start": "2026-10-12T11:49:43.590312+00:00",
      "duration_seconds": 0.6192579579656012,
      "exit": 0,
      "environment_overrides": {
        "npm_config_offline": "true",
        "OPENSPEC_TELEMETRY": "0",
        "UV_OFFLINE": "1"
      },
      "stdout_sha256": "84cf44dcf376d9909731ecb712ce2852a886fccd1b98b4fb335a1087e3459126",
      "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "raw_stdout": "Task status: 6/9 tasks\nWarning: 3 incomplete task(s) found. Continuing due to --yes flag.\n\nSpecs to update:\n  conversion/structured-input: update\n  validation/structured-validation: update\nApplying changes to openspec/specs/conversion/structured-input/spec.md:\n  ~ 1 modified\nApplying changes to openspec/specs/validation/structured-validation/spec.md:\n  ~ 1 modified\nTotals: + 0, ~ 2, - 0, → 0\nSpecs updated successfully.\nChange 'reject-deprecated-tagged-statements' archived as '2026-10-12-reject-deprecated-tagged-statements'.\n",
      "raw_stderr": ""
    },
    {
      "argv": [
        "npx",
        "--yes",
        "@fission-ai/openspec@1.13.0",
        "validate",
        "--specs",
        "--strict"
      ],
      "cwd": "/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements/finalizer-main-spec/disposable-checkout",
      "utc_start": "2026-10-12T11:49:44.210797+00:00",
      "duration_seconds": 0.5928490829537623,
      "exit": 0,
      "environment_overrides": {
        "npm_config_offline": "true",
        "OPENSPEC_TELEMETRY": "0",
        "UV_OFFLINE": "1"
      },
      "stdout_sha256": "1aa2e81c386be2ffc34ad0a06ccdbeaee569182b7256fd708a72fd997e79eea3",
      "stderr_sha256": "6f09da278d37cab013983b0ee4f60b3166a5adee337cc4b11779077e280e8a98",
      "raw_stdout": "✓ spec/anonymization/embedded-values\n✓ spec/anonymization/keyed-entries\n✓ spec/anonymization/placed-values\n✓ spec/anonymization/wildcard-names\n✓ spec/audit/keyed-references\n✓ spec/conversion/curly-meta-tags\n✓ spec/conversion/device-output-comparison\n✓ spec/conversion/diagnostics\n✓ spec/conversion/entry-keys\n✓ spec/conversion/format-detection\n✓ spec/conversion/hidden-list-names\n✓ spec/conversion/meta-tags\n✓ spec/conversion/path-filtering\n✓ spec/conversion/raw-set-input\n✓ spec/conversion/structured-input\n✓ spec/conversion/tag-acceptance\n✓ spec/conversion/value-quoting\n✓ spec/conversion/writers\n✓ spec/conversion/xml-input\n✓ spec/schema-pipeline/conversion-hints\n✓ spec/schema-pipeline/entry-key-fields\n✓ spec/schema-pipeline/hidden-list-hints\n✓ spec/schema-pipeline/universal-statements\n✓ spec/schema-pipeline/verification-evidence\n✓ spec/validation/keyed-entries\n✓ spec/validation/raw-set-input\n✓ spec/validation/set-command-validation\n✓ spec/validation/structured-validation\nTotals: 28 passed, 0 failed (28 items)\n",
      "raw_stderr_summary": "Verified complete raw stderr against its SHA256; contains informational long-requirement notices only."
    },
    {
      "argv": [
        "git",
        "diff",
        "--",
        "openspec/specs/conversion/structured-input/spec.md",
        "openspec/specs/validation/structured-validation/spec.md"
      ],
      "cwd": "/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements/finalizer-main-spec/disposable-checkout",
      "utc_start": "2026-10-12T11:49:44.803933+00:00",
      "duration_seconds": 0.010260874987579882,
      "exit": 0,
      "environment_overrides": {
        "npm_config_offline": "true",
        "OPENSPEC_TELEMETRY": "0",
        "UV_OFFLINE": "1"
      },
      "stdout_sha256": "0ec32793d140d3c1528415186fa298f93d0b49323a51d5b8dedabb1d82eda50f",
      "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "raw_stderr": "",
      "raw_stdout_summary": "Verified complete exact proposed-main-spec.diff bytes against stdout SHA256."
    }
  ]
}
```

### Independent reproduction command

```sh
python3 - <<'PY'
import datetime,hashlib,json,pathlib,re,subprocess,time
start=datetime.datetime.now(datetime.timezone.utc).isoformat();t=time.monotonic();w=pathlib.Path('/Users/manon-dev/src/junoscfg-wt/reject-deprecated-tagged-statements');root=pathlib.Path('/Users/manon-dev/src/junoscfg/private_test_data/makeover-work/reject-deprecated-tagged-statements');p=root/'finalizer-main-spec';m=json.loads((p/'manifest.json').read_text());source_head='a439b50c0f052621d9c4b4fb1fa24de3f79efa5f'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=w)
assert git('rev-parse','HEAD').decode().strip()==source_head;assert git('status','--porcelain')==b''
files=git('ls-files','-z').decode().split('\0')[:-1];before={f:sha((w/f).read_bytes()) for f in files};assert before==m['tracked_source_hashes'];assert len(before)==1313
canonical=sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode());assert canonical=='7b62c7f4d7c62a7a9cea32cc2ee3fd514750ffacbb182060b784a68908e73c55'
source_report=root/'independent-fresh-phase6/review.md';assert sha(source_report.read_bytes())=='47aef028f0398b4d0c8cfc914c45d5dfa07d06af02a1c0c5595262b14cd62881'
assert sha((p/'commands.json').read_bytes())==m['commands_sha256'];assert sha((p/'proposed-main-spec.diff').read_bytes())==m['diff_sha256']=='0ec32793d140d3c1528415186fa298f93d0b49323a51d5b8dedabb1d82eda50f'
commands=json.loads((p/'commands.json').read_text());names=['source-native-caps','clone','native-archive','strict-specs-validate','proposed-main-spec-diff'];receipts=[]
assert len(names)==len(commands)
for name,c in zip(names,commands):
 assert c['exit']==0
 out=(p/(name+'.stdout')).read_bytes();err=(p/(name+'.stderr')).read_bytes();assert sha(out)==c['stdout_sha256'];assert sha(err)==c['stderr_sha256']
 assert c['environment_overrides']=={'npm_config_offline':'true','OPENSPEC_TELEMETRY':'0','UV_OFFLINE':'1'}
 receipts.append({**c,'raw_stdout':out.decode(),'raw_stderr':err.decode()})
assert commands[2]['argv']==['npx','--yes','@fission-ai/openspec@1.13.0','archive','reject-deprecated-tagged-statements','--yes']
assert commands[3]['argv']==['npx','--yes','@fission-ai/openspec@1.13.0','validate','--specs','--strict']
assert '28 passed, 0 failed (28 items)' in receipts[3]['raw_stdout']
def requirements(text):
 parts=re.split(r'^### Requirement: ',text,flags=re.M)
 return parts[0],{part.split('\n',1)[0]:part.rstrip() for part in parts[1:]}
rows=[]
for f in m['files']:
 main=f['main_path'];delta=f['delta_path'];raws={k:(p/k/(delta if k=='delta' else main)).read_bytes() for k in ['base','source','delta','proposed']}
 for k,v in raws.items():assert sha(v)==f[k+'_sha256'],(main,k)
 assert raws['source']==(w/main).read_bytes()==git('show',source_head+':'+main)
 assert raws['base']==git('show',m['base']+':'+main)==raws['source'];assert raws['delta']==(w/delta).read_bytes()
 assert raws['proposed']==(pathlib.Path(m['checkout'])/main).read_bytes()
 prefix,old=requirements(raws['source'].decode());newprefix,new=requirements(raws['proposed'].decode());dprefix,mods=requirements(raws['delta'].decode())
 assert prefix==newprefix;assert old.keys()==new.keys();assert len(mods)==1
 assert dprefix.strip()=='## MODIFIED Requirements'
 target=next(iter(mods));assert new[target]==mods[target];assert old[target]!=new[target]
 assert all(old[k]==new[k] for k in old if k!=target)
 rows.append({**f,'requirement_count_before':len(old),'requirement_count_after':len(new),'only_modified_requirement':target,'modified_requirement_identical_to_reviewed_delta':True,'unaffected_requirements_identical':True})
clone=pathlib.Path(m['checkout']);preserved=[f for f in files if not f.startswith('openspec/changes/reject-deprecated-tagged-statements/') and f not in {r['main_path'] for r in rows}]
for f in preserved:assert sha((clone/f).read_bytes())==before[f],f
after={f:sha((w/f).read_bytes()) for f in files};assert before==after;assert git('status','--porcelain')==b''
print(json.dumps({'argv':['python3','-'],'cwd':str(w),'start_utc':start,'end_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'duration_s':time.monotonic()-t,'exit_code':0,'source_head':source_head,'base':m['base'],'source_report_sha256':sha(source_report.read_bytes()),'tracked_count':len(before),'canonical_tracked_before_sha256':canonical,'canonical_tracked_after_sha256':sha(json.dumps(after,sort_keys=True,separators=(',',':')).encode()),'disposable_unaffected_source_files_verified':len(preserved),'proposed_main_specs':rows,'proposed_diff_sha256':m['diff_sha256'],'native_command_receipts':receipts},indent=2))
PY
```

### Preserved initial verification diagnostic

Actual exit: 1.

```text
Traceback (most recent call last):
  File "<stdin>", line 11, in <module>
TypeError: zip() takes no keyword arguments
```

The initial command differs only by using `for name,c in zip(names,commands,strict=True):` where the passing command uses the explicit `assert len(names)==len(commands)` and `for name,c in zip(names,commands):`. This was a reviewer command compatibility correction, not counterevidence against the proposed specs.

## Open questions for the owner

None for these exact proposed main-spec bytes. Root controls exact-SHA live application and subsequent lifecycle/merge/version/archive work.

## Deviations

The independent pass writes one private `review.md` to comply with the review-role write boundary. All actual command receipts are embedded here; no separate new receipt, verdict or manifest file is claimed. One private interpreter-compatibility failure is retained above. The source-review report was not edited.

