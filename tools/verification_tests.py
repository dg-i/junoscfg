"""Run the entire default suite in processes and enforce aggregate coverage."""

import argparse
import collections
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path


def validate_collections(collections):
    """Require identical complete collections and a disjoint exhaustive assignment."""
    if not collections:
        raise ValueError("no worker collections")
    expected = collections[0]["all"]
    if len(expected) != len(set(expected)) or not expected:
        raise ValueError("empty or duplicate collection")
    if any(c["all"] != expected for c in collections):
        raise ValueError("worker collections differ")
    assigned = [node for c in collections for node in c["selected"]]
    if collections_counter(assigned) != collections_counter(expected):
        raise ValueError("missing or duplicate test assignment")


def collections_counter(items):
    """Count identities without losing duplicate assignments."""
    return collections.Counter(items)


def validate_reports(collected, reports):
    """Require actual unique successful phases and retain skip/xfail outcomes."""
    validate_collections(collected)
    if len(collected) != len(reports):
        raise ValueError("worker report count differs")
    counts = collections.Counter()
    for collection, record in zip(collected, reports, strict=True):
        if type(record["exit"]) is not int or record["exit"]:
            raise ValueError("worker result failed")
        grouped = collections.defaultdict(list)
        for row in record["reports"]:
            if row["when"] not in {"setup", "call", "teardown"} or row["outcome"] not in {
                "passed",
                "failed",
                "skipped",
            }:
                raise ValueError("unknown execution outcome")
            grouped[row["nodeid"]].append(row)
        if set(grouped) != set(collection["selected"]):
            raise ValueError("missing test reports")
        for rows in grouped.values():
            phases = [row["when"] for row in rows]
            if len(phases) != len(set(phases)) or not {"setup", "teardown"} <= set(phases):
                raise ValueError("incomplete phases")
            if any(row["outcome"] == "failed" for row in rows):
                raise ValueError("failed test")
            teardown = next(row for row in rows if row["when"] == "teardown")
            if teardown["outcome"] != "passed":
                raise ValueError("teardown did not succeed")
            setup = next(row for row in rows if row["when"] == "setup")
            if setup["outcome"] == "passed" and "call" not in phases:
                raise ValueError("missing call")
            if setup["outcome"] == "skipped" and "call" in phases:
                raise ValueError("call after skipped setup")
            call = next((row for row in rows if row["when"] == "call"), setup)
            counts["xfailed" if call["wasxfail"] else call["outcome"]] += 1
    if not counts["passed"]:
        raise ValueError("no successful ordinary test calls")
    return counts


def run_suite(root, count):
    """Run all assertions in isolated processes, then enforce aggregate coverage."""
    if not 1 <= count <= 10:
        raise ValueError("workers must be between 1 and 10")
    if os.environ.get("PYTEST_ADDOPTS") or os.environ.get("COVERAGE_RCFILE"):
        raise ValueError("inherited test/coverage overrides are not allowed for full verification")
    folder = root / "private_test_data/verification-runs" / ("suite-" + uuid.uuid4().hex)
    folder.mkdir(parents=True)
    python = sys.executable
    workers = []
    started = time.perf_counter()
    try:
        for index in range(count):
            result = folder / f"worker-{index}.json"
            env = dict(
                os.environ,
                VERIFICATION_SHARD_INDEX=str(index),
                VERIFICATION_SHARDS=str(count),
                VERIFICATION_SHARD_RESULT=str(result),
            )
            env.pop("COVERAGE_FILE", None)
            log = (folder / f"worker-{index}.log").open("w")
            command = [
                python,
                "-m",
                "coverage",
                "run",
                f"--data-file={folder}/.coverage.{index}",
                "-m",
                "pytest",
                "tests/",
                "-q",
                "-p",
                "tools.verification_shard",
                "--durations=10",
                "-o",
                f"cache_dir={folder}/cache-{index}",
            ]
            workers.append(
                (
                    subprocess.Popen(
                        command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT
                    ),
                    result,
                    log,
                )
            )
        statuses = [p.wait() for p, _, _ in workers]
    except BaseException:
        for process, _, _ in workers:
            if process.poll() is None:
                process.terminate()
        for process, _, _ in workers:
            process.wait()
        raise
    finally:
        for _, _, log in workers:
            log.close()
    if any(statuses):
        print("worker failures", statuses, "logs", folder, flush=True)
        return 1
    collected = [
        json.loads(Path(str(result) + ".collection").read_text()) for _, result, _ in workers
    ]
    validate_collections(collected)
    reports = [json.loads(result.read_text()) for _, result, _ in workers]
    counts = validate_reports(collected, reports)
    combine = [python, "-m", "coverage", "combine", "--keep", str(folder)]
    result = subprocess.run(combine, cwd=root)
    if result.returncode:
        return result.returncode
    # JSON applies the same configured fail_under threshold as report; avoid
    # computing the same complete coverage analysis twice.
    result = subprocess.run(
        [python, "-m", "coverage", "json", "-o", str(folder / "coverage.json")], cwd=root
    )
    if result.returncode:
        return result.returncode
    print(
        "VERIFICATION_COVERAGE",
        json.dumps(json.loads((folder / "coverage.json").read_text())["totals"]),
        flush=True,
    )
    print(
        "VERIFICATION_SUITE",
        json.dumps(
            {
                "seconds": time.perf_counter() - started,
                "workers": count,
                "counts": dict(counts),
                "collected": len(collected[0]["all"]),
                "folder": str(folder),
            }
        ),
        flush=True,
    )
    return result.returncode


def main():
    """Execute the complete committed suite under the native full checkpoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()
    return run_suite(Path.cwd(), args.workers)


if __name__ == "__main__":
    raise SystemExit(main())
