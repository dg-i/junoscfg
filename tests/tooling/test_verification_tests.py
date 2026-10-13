"""Complete ordinary verification must prove execution, not just collection."""

from __future__ import annotations

import copy
import importlib

import pytest


def adapter():
    return importlib.import_module("tools.verification_tests")


def complete_records():
    nodes = ["tests/test_a.py::test_one", "tests/test_b.py::test_two"]
    collections = [{"all": list(nodes), "selected": [node]} for node in nodes]
    reports = [
        {
            "exit": 0,
            "reports": [
                {
                    "nodeid": node,
                    "when": phase,
                    "outcome": "passed",
                    "wasxfail": None,
                    "duration": 0.01,
                }
                for phase in ("setup", "call", "teardown")
            ],
        }
        for node in nodes
    ]
    return collections, reports


def test_complete_disjoint_execution():
    collections, reports = complete_records()
    adapter().validate_collections(collections)
    assert adapter().validate_reports(collections, reports) == {"passed": 2}


@pytest.mark.parametrize(
    "fault",
    [
        "no-workers",
        "empty",
        "duplicate-collection",
        "mismatch",
        "omission",
        "duplicate-assignment",
        "unknown-assignment",
        "missing-worker",
        "extra-worker",
        "worker-error",
        "missing-report",
        "unknown-report",
        "duplicate-report",
        "missing-setup",
        "missing-call",
        "missing-teardown",
        "setup-failed",
        "call-failed",
        "teardown-failed",
        "strict-xpass",
        "invalid-phase",
        "invalid-outcome",
        "skipped-teardown",
    ],
)
def test_incomplete_or_failed_execution_refuses(fault):
    collections, reports = copy.deepcopy(complete_records())
    if fault == "no-workers":
        collections, reports = [], []
    elif fault == "empty":
        collections, reports = [{"all": [], "selected": []}], [{"exit": 0, "reports": []}]
    elif fault == "duplicate-collection":
        for row in collections:
            row["all"].append(row["all"][0])
    elif fault == "mismatch":
        collections[1]["all"] = collections[1]["all"][:1]
    elif fault == "omission":
        collections[0]["selected"] = []
    elif fault == "duplicate-assignment":
        collections[1]["selected"] = collections[0]["selected"]
    elif fault == "unknown-assignment":
        collections[0]["selected"] = ["tests/test_new.py::test_unknown"]
    elif fault == "missing-worker":
        reports.pop()
    elif fault == "extra-worker":
        reports.append({"exit": 0, "reports": []})
    elif fault == "worker-error":
        reports[0]["exit"] = 3
    elif fault == "missing-report":
        reports[0]["reports"] = []
    elif fault == "unknown-report":
        reports[0]["reports"][0]["nodeid"] = "tests/test_new.py::test_unknown"
    elif fault == "duplicate-report":
        reports[0]["reports"].append(dict(reports[0]["reports"][0]))
    elif fault.startswith("missing-"):
        phase = fault.removeprefix("missing-")
        reports[0]["reports"] = [r for r in reports[0]["reports"] if r["when"] != phase]
    elif fault.endswith("-failed"):
        phase = fault.removesuffix("-failed")
        next(r for r in reports[0]["reports"] if r["when"] == phase)["outcome"] = "failed"
    elif fault == "strict-xpass":
        reports[0]["reports"][1].update(outcome="failed", wasxfail="strict XPASS")
    elif fault == "invalid-phase":
        reports[0]["reports"].append(dict(reports[0]["reports"][0], when="collect"))
    elif fault == "invalid-outcome":
        reports[0]["reports"][1]["outcome"] = "unknown"
    elif fault == "skipped-teardown":
        reports[0]["reports"][2]["outcome"] = "skipped"
    module = adapter()
    with pytest.raises(ValueError):
        module.validate_collections(collections)
        module.validate_reports(collections, reports)


@pytest.mark.parametrize("during_setup", [False, True])
@pytest.mark.parametrize("xfail", [False, True])
def test_ordinary_skips_and_expected_failures_keep_their_actual_outcome(during_setup, xfail):
    collections, reports = complete_records()
    reports[0]["reports"][0 if during_setup else 1].update(
        outcome="skipped", wasxfail="known follow-up" if xfail else None
    )
    if during_setup:
        reports[0]["reports"].pop(1)
    assert adapter().validate_reports(collections, reports) == {
        "passed": 1,
        "xfailed" if xfail else "skipped": 1,
    }


@pytest.mark.parametrize("workers", [1, 2, 4, 8])
def test_scheduler_covers_unknown_tests(workers):
    module = importlib.import_module("tools.verification_shard")
    nodes = [
        "tests/unit/new/test_unknown.py::test_added",
        "tests/unit/new/test_unknown.py::test_parameter[a]",
        "tests/tooling/test_new.py::test_unmeasured",
        "tests/corpus/test_existing.py::test_case",
    ]
    assignments = module.assign(nodes, workers, {"modules": {}, "tooling": {}})
    assert set(assignments) == set(nodes)
    assert all(type(index) is int and 0 <= index < workers for index in assignments.values())
    assert assignments[nodes[0]] == assignments[nodes[1]]


@pytest.mark.parametrize(
    "fault",
    [
        "none",
        "call",
        "setup",
        "teardown",
        "strict-xpass",
        "collection",
        "coverage",
        "combine-command",
        "coverage-command",
    ],
)
def test_real_workers_and_combined_coverage_propagate_failure(tmp_path, monkeypatch, fault):
    import shutil
    import sys
    from pathlib import Path

    from tests.support.paths import PROJECT_ROOT

    module = adapter()
    root = tmp_path / "repo"
    root.mkdir()
    (root / "tools").mkdir()
    (root / "tools/__init__.py").write_text("")
    for name in ("verification_tests.py", "verification_shard.py"):
        shutil.copyfile(PROJECT_ROOT / "tools" / name, root / "tools" / name)
    (root / "tests").mkdir()
    (root / ".venv/bin").mkdir(parents=True)
    (root / ".venv/bin/python").symlink_to(Path(sys.executable).absolute())
    (root / "sample.py").write_text("def covered():\n    return 1\n\ndef missed():\n    return 2\n")
    (root / "pyproject.toml").write_text(
        "[tool.pytest.ini_options]\nxfail_strict = true\n"
        '[tool.coverage.run]\nbranch = true\nsource = ["sample"]\n'
        "[tool.coverage.report]\nfail_under = 100\n"
    )
    body = (
        "import sample\n\ndef test_one():\n"
        "    assert sample.covered() == 1\n    assert sample.missed() == 2\n"
    )
    if fault == "call":
        body += "    assert False\n"
    elif fault == "setup":
        body = "def setup_function():\n    raise RuntimeError('setup')\n\n" + body
    elif fault == "teardown":
        body += "\ndef teardown_function():\n    raise RuntimeError('teardown')\n"
    elif fault == "strict-xpass":
        body = "import pytest\n" + body.replace(
            "def test_one", "@pytest.mark.xfail(strict=True)\ndef test_one"
        )
    elif fault == "collection":
        body = "raise RuntimeError('collection')\n" + body
    elif fault == "coverage":
        body = body.replace("    assert sample.missed() == 2\n", "")
    (root / "tests/test_sample.py").write_text(body)
    # Two modules ensure both worker sessions receive real obligations.
    (root / "tests/test_other.py").write_text("def test_other():\n    assert True\n")
    if fault in {"combine-command", "coverage-command"}:
        import subprocess

        original = subprocess.run
        observed = []

        def failing_coverage(command, *args, **kwargs):
            target = "combine" if fault == "combine-command" else "json"
            if "coverage" in command and target in command:
                observed.append(target)
                return subprocess.CompletedProcess(command, 2)
            return original(command, *args, **kwargs)

        monkeypatch.setattr(subprocess, "run", failing_coverage)
    result = module.run_suite(root, 2)
    if fault in {"combine-command", "coverage-command"}:
        assert observed
    assert (result == 0) is (fault == "none")
