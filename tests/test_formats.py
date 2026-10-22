import json
import pathlib

import pytest

from dotless import cli, formats
from dotless.scanner import scan_paths

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def result():
    return scan_paths([str(FIXTURES)])


def test_text(result):
    out = formats.text(*result)
    assert "DL004" in out and "fix:" in out
    assert out.rstrip().endswith("files scanned")


def test_json(result):
    doc = json.loads(formats.as_json(*result))
    assert doc["files_scanned"] == 10
    assert len(doc["findings"]) == len(result[0])
    assert {"rule", "severity", "path", "line", "column", "fingerprint"} <= set(doc["findings"][0])
    assert len({f["fingerprint"] for f in doc["findings"]}) == len(doc["findings"])


def test_sarif(result):
    doc = json.loads(formats.sarif(*result))
    assert doc["version"] == "2.1.0"
    run = doc["runs"][0]
    rules = run["tool"]["driver"]["rules"]
    for res in run["results"]:
        assert rules[res["ruleIndex"]]["id"] == res["ruleId"]
        assert res["level"] in ("error", "warning")
        region = res["locations"][0]["physicalLocation"]["region"]
        assert region["startLine"] >= 1 and region["endColumn"] > region["startColumn"]
        assert not res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"].startswith("/")


def test_gitlab(result):
    items = json.loads(formats.gitlab(*result))
    assert items and all(i["severity"] in ("major", "minor") for i in items)
    assert all(set(i) >= {"description", "check_name", "fingerprint", "severity", "location"} for i in items)


def test_cli_min_severity_and_exit_code(capsys):
    assert cli.main(["scan", str(FIXTURES / "c" / "safe.c")]) == 0
    assert "0 findings" in capsys.readouterr().out
    assert cli.main(["scan", "--min-severity", "high", "-f", "json", str(FIXTURES / "c" / "bad.c")]) == 1
    doc = json.loads(capsys.readouterr().out)
    assert doc["findings"] and all(f["severity"] == "high" for f in doc["findings"])


def test_cli_exit_zero_and_output(tmp_path):
    out = tmp_path / "r.sarif"
    assert cli.main(["scan", "-f", "sarif", "-o", str(out), "--exit-zero", str(FIXTURES)]) == 0
    assert json.loads(out.read_text())["runs"][0]["results"]


def test_cli_exclude():
    assert cli.main(["scan", "--exclude", "bad.*", str(FIXTURES)]) == 0


def test_cli_missing_path():
    assert cli.main(["scan", "does-not-exist"]) == 2
