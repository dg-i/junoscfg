"""Shared before/after comparison evidence, using synthetic compressed captures.

T4 promotes the private comparison template. Expected matrices are computed
from the supplied captures and public format/rule names, never from that template.
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import runpy
import sys
from types import SimpleNamespace

import pytest

import junoscfg
from tests.support.paths import PROJECT_ROOT

TOOL = PROJECT_ROOT / "tools" / "compare_device_outputs.py"
FORMATS = {"conf": "STRUCTURED", "set": "SET", "json": "JSON", "xml": "XML"}
DESTINATIONS = ("SET", "STRUCTURED", "JSON", "YAML")
RULE_FIELDS = (
    "ips",
    "passwords",
    "communities",
    "ssh_keys",
    "identities",
    "groups",
    "descriptions",
    "as_numbers",
    "sensitive_words",
    "sensitive_patterns",
)


def comparison_tool():
    spec = importlib.util.spec_from_file_location("compare_device_outputs", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def captures(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    device = root / "tests/data/device/synthetic/sw1"
    device.mkdir(parents=True)
    entries = []
    keys = []
    for number in range(1, 7):
        name = f"router{number}"
        entries.append({"source": "synthetic", "device": "sw1", "name": name})
        for suffix in FORMATS:
            (device / f"{name}.{suffix}.gz").write_bytes(gzip.compress(name.encode(), mtime=0))
            keys.append(f"synthetic/sw1/{name}.{suffix}")
    entries.append({"source": "synthetic", "device": "sw1", "name": "absent"})
    (root / "tests/data/device/manifest.json").write_text(json.dumps({"captures": entries}))
    before = {path: path.read_bytes() for path in root.rglob("*") if path.is_file()}
    monkeypatch.chdir(root)
    return root, keys, before


@pytest.fixture
def conversions(monkeypatch):
    calls = []

    def convert(text, *, from_format, to_format, anon_config):
        calls.append((text, from_format.name, to_format.name, anon_config))
        if from_format.name == "XML" and to_format.name == "YAML":
            raise ValueError("synthetic failure text must not be recorded")
        warning = SimpleNamespace(
            source="field-validation", severity="warning", path=None, message="synthetic warning"
        )
        error = SimpleNamespace(
            source="field-validation", severity="error", path="system", message="synthetic error"
        )
        info = SimpleNamespace(
            source="reader", severity="info", path="system", message="not a field message"
        )
        return SimpleNamespace(
            output=f"{text}:{from_format.name}:{to_format.name}",
            diagnostics=[warning, error, info, warning],
        )

    monkeypatch.setattr(junoscfg, "convert_config_result", convert)
    return calls


def test_record_covers_the_matrix_and_preserves_result_evidence(
    captures, conversions, tmp_path, capsys
):
    root, keys, before = captures
    output = tmp_path / "plain.json"
    comparison_tool().record(output, False)
    data = json.loads(output.read_text())
    expected = {f"{key} -> {dst.lower()} [plain]" for key in keys for dst in DESTINATIONS}
    assert len(data) == len(conversions) == 96
    assert set(data) == expected
    assert list(data) == sorted(expected)
    assert all(anon is None for _, _, _, anon in conversions)
    assert {(src, dst) for _, src, dst, _ in conversions} == {
        (src, dst) for src in FORMATS.values() for dst in DESTINATIONS
    }
    for key in keys:
        src = FORMATS[key.rsplit(".", 1)[1]]
        name = key.rsplit("/", 1)[1].split(".")[0]
        for dst in DESTINATIONS:
            result = data[f"{key} -> {dst.lower()} [plain]"]
            if src == "XML" and dst == "YAML":
                assert result == {"exception": "ValueError"}
            else:
                assert result["output"] == f"{name}:{src}:{dst}"
                assert result["diagnostics"] == [
                    ["field-validation", "error", "system"],
                    ["field-validation", "warning", ""],
                    ["reader", "info", "system"],
                ]
                assert result["field_validation"] == [
                    "synthetic error",
                    "synthetic warning",
                    "synthetic warning",
                ]
    assert "synthetic failure text" not in output.read_text()
    assert all(path.read_bytes() == content for path, content in before.items())
    assert len([path for path in root.rglob("*") if path.is_file()]) == len(before)
    assert capsys.readouterr().out == f"96 conversions recorded in {output}\n"


def test_anonymized_record_covers_each_rule_and_plain(captures, conversions, tmp_path):
    _, keys, _ = captures
    output = tmp_path / "anon.json"
    comparison_tool().record(output, True)
    data = json.loads(output.read_text())
    modes = ("plain", *RULE_FIELDS, "all")
    assert len(data) == len(conversions) == 1152
    assert set(data) == {
        f"{key} -> {dst.lower()} [{mode}]" for key in keys for dst in DESTINATIONS for mode in modes
    }
    selections = {}
    for _, _, _, config in conversions:
        if config is None:
            mode = "plain"
        else:
            assert config.salt == "compare-salt"
            enabled = [field for field in RULE_FIELDS if getattr(config, field)]
            mode = "all" if len(enabled) == len(RULE_FIELDS) else enabled[0]
            assert len(enabled) == (10 if mode == "all" else 1)
            if config.as_numbers:
                assert config.as_numbers == [64496, 64497, 64498, 64499, 64511]
            if config.sensitive_words:
                assert config.sensitive_words == ["customer"]
            if config.sensitive_patterns:
                assert config.sensitive_patterns == [r"LAX\d+"]
        selections[mode] = selections.get(mode, 0) + 1
    assert selections == dict.fromkeys(modes, 96)


def test_diff_explains_outputs_diagnostics_exceptions_and_key_changes(tmp_path, capsys):
    base = tmp_path / "base.json"
    head = tmp_path / "head.json"
    stable = {"output": "stable"}
    base.write_text(
        json.dumps(
            {
                "unchanged": stable,
                "output": {"output": "keep\nold\n"},
                "diagnostics": {
                    "diagnostics": [["reader", "warning", ""]],
                    "field_validation": ["synthetic warning"],
                },
                "exception": {"exception": "ValueError"},
                "removed": {"output": "removed"},
            }
        )
    )
    head.write_text(
        json.dumps(
            {
                "unchanged": stable,
                "output": {"output": "keep\nnew\n"},
                "diagnostics": {"diagnostics": [], "field_validation": []},
                "exception": {"exception": "RuntimeError"},
                "added": {"output": "added"},
            }
        )
    )
    tool = comparison_tool()
    tool.diff(base, head)
    report = capsys.readouterr().out
    assert report.startswith("5 of 6 conversions differ\n")
    assert [line for line in report.splitlines() if line.startswith("=== ")] == [
        "=== added",
        "=== diagnostics",
        "=== exception",
        "=== output",
        "=== removed",
    ]
    assert "--- base\n+++ head\n@@ -2 +2 @@\n-old\n+new" in report
    assert "+added" in report and "-removed" in report
    assert "diagnostics: base [['reader', 'warning', '']]\ndiagnostics: head []" in report
    assert "field_validation: base ['synthetic warning']\nfield_validation: head []" in report
    assert "exception: base 'ValueError'\nexception: head 'RuntimeError'" in report
    assert "unchanged" not in report
    tool.diff(base, base)
    assert capsys.readouterr().out == "0 of 5 conversions differ\n"


def test_script_record_and_diff_commands(captures, conversions, tmp_path, monkeypatch, capsys):
    output = tmp_path / "record.json"
    monkeypatch.setattr(sys, "argv", [str(TOOL), "record", str(output), "--anonymize"])
    runpy.run_path(str(TOOL), run_name="__main__")
    assert len(json.loads(output.read_text())) == 1152
    assert capsys.readouterr().out == f"1152 conversions recorded in {output}\n"
    monkeypatch.setattr(sys, "argv", [str(TOOL), "diff", str(output), str(output)])
    runpy.run_path(str(TOOL), run_name="__main__")
    assert capsys.readouterr().out == "0 of 1152 conversions differ\n"
