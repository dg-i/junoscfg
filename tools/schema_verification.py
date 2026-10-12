"""Truthful per-dump schema execution for the existing verification wrapper."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from agent_ready_checks import lane, readiness, verification

from junoscfg.validate import ArtifactBuilder
from tests.support.schema_data import read_version
from tools.schema_dependencies import check_dependencies

POLICY = "tools/schema-verification/policy.json"
PRODUCTS = (
    "junos-json-schema.json.gz",
    "junos-yaml-schema.json.gz",
    "junos-structure-tree.json.gz",
    "junos-set.lark.gz",
)
META = "junos-schema-meta.json.gz"
NORMALIZED_META = "junos-schema-meta.normalized.json"


def _json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError(f"missing or invalid JSON input: {path.name}") from error


def _path(root, name):
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("declared paths must remain inside the candidate")
    result = root / relative
    for part in (result, *result.parents):
        if part.is_symlink():
            raise ValueError("symlink path is unsupported")
    return result


def _policy(root):
    value = _json(_path(root, POLICY))
    if not isinstance(value, dict) or not value.get("shards"):
        raise ValueError("schema shard policy is empty")
    return value


def _required(value):
    if not isinstance(value, dict) or set(value) != {"tests", "shards"}:
        raise ValueError("coverage requires exactly tests and shards")
    for key in ("tests", "shards"):
        ids = value[key]
        if (
            not isinstance(ids, list)
            or not ids
            or any(not isinstance(i, str) or not i for i in ids)
        ):
            raise ValueError("coverage IDs must be nonempty strings")
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate coverage IDs")


def completion(required, reports, exit_status, allowed_skips, *, collected):
    """Validate actual reports separately from collected obligations."""
    _required(required)
    expected = set(required["tests"])
    if exit_status or len(collected) != len(set(collected)) or set(collected) != expected:
        raise ValueError("execution or selected coverage failed")
    phases = {}
    for report in reports:
        node = report["nodeid"]
        when = report["when"]
        if node not in expected or when not in {"setup", "call", "teardown"}:
            raise ValueError("unexpected execution report")
        if when in phases.setdefault(node, {}):
            raise ValueError("duplicate execution report")
        phases[node][when] = report
    observed = {}
    passed = 0
    for node in required["tests"]:
        rows = phases.get(node, {})
        if set(rows) != {"setup", "call", "teardown"}:
            raise ValueError("incomplete executed phases")
        if any(rows[phase]["outcome"] != "passed" for phase in ("setup", "teardown")):
            raise ValueError("setup or teardown did not succeed")
        outcome = rows["call"]["outcome"]
        reason = rows["call"].get("reason", "")
        if outcome == "passed":
            passed += 1
        elif outcome != "skipped" or node not in allowed_skips or reason != allowed_skips[node]:
            raise ValueError("failed or unapproved skipped call")
        observed[node] = {"outcome": outcome, "reason": reason}
    if not passed:
        raise ValueError("all required calls skipped")
    return {"tests": list(required["tests"]), "shards": list(required["shards"])}, {
        "tests": observed
    }


def validate_input(path, expected_release):
    """Refuse unknown or nonphysical dumps before schema parsing."""
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError("symlink schema input is unsupported")
    if not path.is_file() or not path.stat().st_size:
        raise ValueError("schema input is missing or empty")
    version = read_version(path)
    if version == "unknown" or version != expected_release:
        raise ValueError("schema release is unknown or mismatched")


def observe_versions():
    """Bind observable runtime/library bytes without capturing environment secrets."""
    values = {
        "python": sys.version,
        "python-executable": hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
    }
    for distribution in sorted(
        importlib.metadata.distributions(), key=lambda d: d.metadata["Name"]
    ):
        name = distribution.metadata["Name"].lower()
        version = distribution.version
        if not version or version.lower() == "unknown" or distribution.files is None:
            raise ValueError("runtime package identity is unavailable")
        digest = hashlib.sha256()
        for relative in sorted(distribution.files, key=str):
            if relative.suffix == ".pyc" or "__pycache__" in relative.parts:
                continue
            path = distribution.locate_file(relative)
            if not path.is_file():
                raise ValueError("runtime package content is unavailable")
            digest.update(str(relative).encode())
            digest.update(path.read_bytes())
        values[f"version:{name}"] = version
        values[f"content:{name}"] = digest.hexdigest()
    from lxml import etree

    for key in ("LIBXML_VERSION", "LIBXML_COMPILED_VERSION", "LIBXSLT_VERSION"):
        version = getattr(etree, key, None)
        if not version:
            raise ValueError("native XML library version is unavailable")
        values[key] = ".".join(map(str, version))
    for needed in ("pytest", "lxml", "jsonschema", "lark"):
        if f"version:{needed}" not in values:
            raise ValueError("required schema runtime is unavailable")
    return values


def verify_versions(path):
    """Compare immutable prepared versions with current observable runtime bytes."""
    observed = _json(path)
    if observed != observe_versions():
        raise ValueError("prepared runtime identity is unknown or mismatched")


def _write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def prepare_runtime(root):
    """Prepare an ignored immutable version input before verification."""
    policy = _policy(root)
    _write(_path(root, policy["runtime"]), observe_versions())


def _repository_environment():
    # Git hooks export repository selectors; cwd must select our intended repository.
    controls = {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_PREFIX",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    }
    return {
        key: value
        for key, value in os.environ.items()
        if key not in controls and not key.startswith("GIT_CONFIG")
    }


@contextmanager
def _repository_context():
    """Scope installed-wrapper Git calls to the candidate, restoring caller context."""
    clean = _repository_environment()
    removed = {key: value for key, value in os.environ.items() if key not in clean}
    for key in removed:
        os.environ.pop(key)
    try:
        yield
    finally:
        os.environ.update(removed)


def _git(root, *arguments):
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        env=_repository_environment(),
    ).stdout


def _read_inputs(policy, recipe, extra=()):
    return {
        Path(name).as_posix()
        for name in (
            POLICY,
            policy["suite"],
            policy["runtime"],
            recipe["dump"],
            recipe["required"],
            recipe["stability"],
            *extra,
        )
    }


def _candidate_input(name, explicit):
    parts = Path(name).parts
    record = (
        len(parts) == 4
        and parts[:2] == ("openspec", "changes")
        and parts[-1] in verification.EVIDENCE_RECORDS
    )
    return name in explicit or not record


def _preflight(root, policy, shard, extra=()):
    check_dependencies(root)
    recipe = policy["shards"][shard]
    names = {Path(row["dump"]).name for row in policy["shards"].values()}
    directory = _path(root, recipe["dump"]).parent
    present = {path.name for path in directory.glob("*.xsd")}
    if present != names:
        raise ValueError("schema inventory is missing, staged or undeclared")
    validate_input(_path(root, recipe["dump"]), recipe["release"])
    verify_versions(_path(root, policy["runtime"]))
    dirty = _git(root, "status", "--porcelain", "--untracked-files=no", "--no-renames", "-z").split(
        "\0"
    )
    if any(
        record and _candidate_input(record[3:], _read_inputs(policy, recipe, extra))
        for record in dirty
    ):
        raise ValueError("schema verification requires a committed clean candidate")
    required = _json(_path(root, recipe["required"]))
    _required(required)
    if required["shards"] != [shard]:
        raise ValueError("required shard identity differs")
    stable = _json(_path(root, recipe["stability"]))
    expected = [f"{recipe['artifacts']}/{name}" for name in (*PRODUCTS, NORMALIZED_META)]
    if stable != expected:
        raise ValueError("stability manifest differs from protected products")
    return recipe, required


def _snapshot(root, policy, recipe, extra=()):
    explicit = _read_inputs(policy, recipe, extra)
    names = set(_git(root, "ls-files", "-z").split("\0")) | explicit
    return {
        name: hashlib.sha256(_path(root, name).read_bytes()).hexdigest()
        for name in sorted(names)
        if name and _candidate_input(name, explicit)
    }


def _normalized_metadata(directory):
    with gzip.open(directory / META, "rt") as handle:
        value = json.load(handle)
    value.pop("generated_at", None)
    return value


def _compare(generated, committed):
    for name in PRODUCTS:
        if (generated / name).read_bytes() != (committed / name).read_bytes():
            raise ValueError(f"protected generated artifact differs: {name}")
    if _normalized_metadata(generated) != _normalized_metadata(committed):
        raise ValueError("generated metadata differs beyond its timestamp")


def _clear_success(root, recipe):
    for key in ("result", "outcomes"):
        _path(root, recipe[key]).unlink(missing_ok=True)


def run_shard(root, shard):
    """Execute genuine pytest; no successful record survives failure or mutation."""
    policy = _policy(root)
    recipe = policy["shards"][shard]
    _clear_success(root, recipe)
    recipe, _ = _preflight(root, policy, shard)
    before = _snapshot(root, policy, recipe)
    command = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "-p",
        "tools.schema_verification",
        policy["suite"],
        "--schema",
        "--schema-evidence-shard",
        shard,
        "-q",
        "-o",
        "addopts=",
    ]
    status = subprocess.run(
        command, cwd=root, check=False, env=_repository_environment()
    ).returncode
    try:
        if _snapshot(root, policy, recipe) != before:
            raise ValueError("schema execution mutated candidate or input bytes")
        if status or not _path(root, recipe["result"]).is_file():
            raise ValueError("schema execution did not publish successful completion")
    except (OSError, ValueError):
        _clear_success(root, recipe)
        raise
    return status


def _export_products(source, output):
    output.mkdir(parents=True, exist_ok=True)
    for name in (*PRODUCTS, META):
        shutil.copyfile(source / name, _path(output, name))
    _write(_path(output, NORMALIZED_META), _normalized_metadata(source))


def generation_inputs(recipe):
    """Bind assertion completion and every consumed product to generation identity."""
    return [
        recipe["result"],
        *[f"{recipe['artifacts']}/{name}" for name in (*PRODUCTS, META, NORMALIZED_META)],
    ]


def run_generation(root, shard):
    """Perform one fresh build; the template owns the two-pass stability check."""
    policy = _policy(root)
    recipe = policy["shards"][shard]
    result = _path(root, recipe["generation-result"])
    outcomes = _path(root, recipe["generation-outcomes"])
    result.unlink(missing_ok=True)
    outcomes.unlink(missing_ok=True)
    try:
        inputs = generation_inputs(recipe) + [
            recipe["generation-required"],
            recipe["generation-stability"],
        ]
        recipe, required = _preflight(root, policy, shard, inputs)
        if _json(_path(root, recipe["result"])) != required:
            raise ValueError("successful assertion completion is required before generation")
        obligations = {
            "tests": ["public-build", "artifact-integrity"],
            "shards": [f"{shard}-generation"],
        }
        if _json(_path(root, recipe["generation-required"])) != obligations:
            raise ValueError("generation obligations differ")
        expected = [
            f"{recipe['generation-artifacts']}/{name}" for name in (*PRODUCTS, NORMALIZED_META)
        ]
        if _json(_path(root, recipe["generation-stability"])) != expected:
            raise ValueError("generation stability manifest differs")
        before = _snapshot(root, policy, recipe, inputs)
        assertion = _path(root, recipe["artifacts"])
        if _json(assertion / NORMALIZED_META) != _normalized_metadata(assertion):
            raise ValueError("assertion metadata export differs")
        with tempfile.TemporaryDirectory(prefix="schema-generation-") as directory:
            output = Path(directory)
            start = time.perf_counter()
            ArtifactBuilder().build(_path(root, recipe["dump"]), output)
            duration = time.perf_counter() - start
            _compare(output, assertion)
            if shard == policy["shipped"]:
                _compare(output, root / "src/junoscfg/validate/data")
            _export_products(output, _path(root, recipe["generation-artifacts"]))
        if _snapshot(root, policy, recipe, inputs) != before:
            raise ValueError("generation mutated candidate or input bytes")
        measured = {"durations": {"public-build": duration}}
        _write(outcomes, measured)
        _write(result, obligations)
        print("schema generation outcomes: " + json.dumps(measured, sort_keys=True))
    except BaseException:
        result.unlink(missing_ok=True)
        outcomes.unlink(missing_ok=True)
        raise
    return 0


def qualify(root, shard):
    """Explicit compatibility qualification through the installed evidence wrapper."""
    with _repository_context():
        return _qualify(root, shard)


def _qualify(root, shard):
    if readiness.config(root).get("enabled", False):
        snapshot = lane.snapshot_problem(root)
        problems = readiness.problems(root, lane.selected_change_for_base(root, None), None)
        if snapshot or problems:
            raise ValueError(
                "qualification not ready: " + "; ".join(([snapshot] if snapshot else []) + problems)
            )
    check_dependencies(root)
    policy = _policy(root)
    recipe = policy["shards"][shard]
    command = [sys.executable, "-B", "-m", "tools.schema_verification"]
    common = {"inputs": [recipe["dump"], policy["runtime"]], "version-files": [policy["runtime"]]}
    assertion = dict(
        common,
        name=shard,
        **{"required-manifest": recipe["required"], "result-manifest": recipe["result"]},
    )
    generation = dict(
        common,
        name=f"{shard}-generation",
        **{
            "inputs": common["inputs"] + generation_inputs(recipe),
            "required-manifest": recipe["generation-required"],
            "result-manifest": recipe["generation-result"],
            "stability-manifest": recipe["generation-stability"],
        },
    )
    with verification.capacity(root):
        status = verification.execute(root, command + ["run", shard], None, assertion, reuse=False)
        if status:
            return status
        return verification.execute(
            root, command + ["generation", shard], None, generation, reuse=False
        )


def run_sentinel(root):
    """Always perform fresh public generation without reading stable tier output."""
    policy = _policy(root)
    shard = policy["shipped"]
    recipe, _ = _preflight(root, policy, shard)
    before = _snapshot(root, policy, recipe)
    with tempfile.TemporaryDirectory(prefix="schema-sentinel-") as directory:
        output = Path(directory)
        ArtifactBuilder().build(_path(root, recipe["dump"]), output)
        _compare(output, root / "src/junoscfg/validate/data")
    if _snapshot(root, policy, recipe) != before:
        raise ValueError("sentinel mutated candidate or input bytes")
    return 0


class _Evidence:
    def __init__(self, root, shard):
        self.root = root
        self.shard = shard
        self.policy = _policy(root)
        self.recipe, self.required = _preflight(root, self.policy, shard)
        self.collected = []
        self.reports = []
        self.generated = False

    def export(self, path):
        if self.generated:
            return
        if self.shard == self.policy["shipped"]:
            _compare(path, self.root / "src/junoscfg/validate/data")
        output = _path(self.root, self.recipe["artifacts"])
        _export_products(path, output)
        self.generated = True

    def finish(self, exit_status):
        if not self.generated:
            raise ValueError("actual real_artifacts generation was not observed")
        actual, outcomes = completion(
            self.required,
            self.reports,
            exit_status,
            self.recipe["allowed-skips"],
            collected=self.collected,
        )
        outcomes["durations"] = {
            node: {row["when"]: row["duration"] for row in self.reports if row["nodeid"] == node}
            for node in self.required["tests"]
        }
        _write(_path(self.root, self.recipe["outcomes"]), outcomes)
        _write(_path(self.root, self.recipe["result"]), actual)
        print("schema executed outcomes: " + json.dumps(outcomes, sort_keys=True))


def pytest_addoption(parser):
    """Register only the application evidence shard selector."""
    parser.addoption("--schema-evidence-shard", default=None)


def pytest_configure(config):
    """Bind the selected shard after prerequisite validation."""
    shard = config.getoption("--schema-evidence-shard")
    if shard is not None:
        config._schema_evidence = _Evidence(Path(config.rootpath), shard)


def pytest_collection_modifyitems(config, items):
    """Select the declared dump and verify exact collected obligations."""
    evidence = getattr(config, "_schema_evidence", None)
    if evidence is None:
        return
    wanted = Path(evidence.recipe["dump"]).name
    chosen, deselected = [], []
    for item in items:
        callspec = getattr(item, "callspec", None)
        (
            chosen
            if callspec is not None and callspec.params.get("schema_dump") == wanted
            else deselected
        ).append(item)
    evidence.collected = [item.nodeid for item in chosen]
    if len(evidence.collected) != len(set(evidence.collected)) or (
        set(evidence.collected) != set(evidence.required["tests"])
    ):
        raise pytest.UsageError("selected schema tests differ from required obligations")
    items[:] = chosen
    config.hook.pytest_deselected(items=deselected)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item):
    """Capture actual executed phases and temporary generation products."""
    result = yield
    report = result.get_result()
    evidence = getattr(item.config, "_schema_evidence", None)
    if evidence is None:
        return
    reason = ""
    if report.skipped:
        reason = str(report.longrepr[2])
        if reason.startswith("Skipped: "):
            reason = reason.removeprefix("Skipped: ")
    evidence.reports.append(
        {
            "nodeid": report.nodeid,
            "when": report.when,
            "outcome": report.outcome,
            "reason": reason,
            "duration": report.duration,
        }
    )
    if report.when == "setup" and report.passed:
        artifacts = item.funcargs.get("real_artifacts")
        if artifacts is not None:
            evidence.export(Path(artifacts))


def pytest_sessionfinish(session, exitstatus):
    """Publish completion only after all required execution succeeds."""
    evidence = getattr(session.config, "_schema_evidence", None)
    if evidence is None:
        return
    try:
        evidence.finish(int(exitstatus))
    except (OSError, ValueError) as error:
        _clear_success(evidence.root, evidence.recipe)
        session.exitstatus = 1
        print(f"schema evidence refused: {error}", file=sys.stderr)


def main(argv=None):
    """Run preparation or immutable schema verification from the candidate root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "generation", "qualify", "sentinel"))
    parser.add_argument("shard", nargs="?")
    args = parser.parse_args(argv)
    root = Path.cwd()
    try:
        if args.action == "prepare":
            prepare_runtime(root)
        elif args.action == "run" and args.shard:
            return run_shard(root, args.shard)
        elif args.action == "generation" and args.shard:
            return run_generation(root, args.shard)
        elif args.action == "qualify" and args.shard:
            return qualify(root, args.shard)
        elif args.action == "sentinel":
            return run_sentinel(root)
        else:
            parser.error("run, generation and qualify require a shard")
    except (OSError, ValueError, KeyError) as error:
        print(f"schema evidence refused: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
