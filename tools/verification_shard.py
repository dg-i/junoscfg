"""Deterministic process sharding; parent checks exact node and report union."""

import json
import os
from pathlib import Path

_rows = []


def assign(all_ids, count, costs):
    """Place every live test exactly once, retaining module fixture locality."""
    if not 1 <= count <= 10 or len(set(all_ids)) != len(all_ids):
        raise ValueError("invalid worker count or duplicate live test")
    product_count = min(3, count)
    groups = {}
    for nodeid in all_ids:
        if count < 6 or not nodeid.startswith("tests/tooling/"):
            groups.setdefault(nodeid.split("::")[0], []).append(nodeid)
    owners = {}
    loads = [0.0] * count
    for module in sorted(groups, key=lambda m: (-costs.get("modules", {}).get(m, 1.0), m)):
        worker = min(range(product_count if count >= 6 else count), key=lambda w: (loads[w], w))
        loads[worker] += costs.get("modules", {}).get(module, 1.0)
        owners.update((nodeid, worker) for nodeid in groups[module])
    cases = [nodeid for nodeid in all_ids if nodeid not in owners]
    for nodeid in sorted(cases, key=lambda n: (-costs.get("tooling", {}).get(n, 1.0), n)):
        worker = min(range(product_count, count), key=lambda w: (loads[w], w))
        loads[worker] += costs.get("tooling", {}).get(nodeid, 1.0)
        owners[nodeid] = worker
    return owners


def pytest_collection_modifyitems(config, items):
    """Persist live collection and assign using placement-only cost hints."""
    index = int(os.environ["VERIFICATION_SHARD_INDEX"])
    count = int(os.environ["VERIFICATION_SHARDS"])
    all_ids = [item.nodeid for item in items]
    costs_path = Path("tools/verification-costs.json")
    costs = json.loads(costs_path.read_text()) if costs_path.is_file() else {}
    owners = assign(all_ids, count, costs)
    chosen = [item for item in items if owners[item.nodeid] == index]
    chosen_ids = {id(item) for item in chosen}
    deselected = [item for item in items if id(item) not in chosen_ids]
    config.hook.pytest_deselected(items=deselected)
    items[:] = chosen
    Path(os.environ["VERIFICATION_SHARD_RESULT"] + ".collection").write_text(
        json.dumps({"all": all_ids, "selected": [item.nodeid for item in chosen]})
    )


def pytest_runtest_logreport(report):
    """Retain every actual setup, call and teardown result."""
    _rows.append(
        {
            "nodeid": report.nodeid,
            "when": report.when,
            "outcome": report.outcome,
            "wasxfail": getattr(report, "wasxfail", None),
            "duration": report.duration,
        }
    )


def pytest_sessionfinish(exitstatus):
    """Publish reports with the actual worker exit status."""
    Path(os.environ["VERIFICATION_SHARD_RESULT"]).write_text(
        json.dumps({"exit": int(exitstatus), "reports": _rows})
    )
