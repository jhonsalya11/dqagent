import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dqagent.report import generate_html_report  # noqa: E402
from dqagent.rules import run_all_rules  # noqa: E402
from fixtures import SAMPLE_COLUMNS, SAMPLE_ROWS  # noqa: E402


def test_generate_html_report_writes_valid_file(tmp_path):
    issues = run_all_rules(SAMPLE_ROWS, SAMPLE_COLUMNS)
    out = tmp_path / "report.html"
    generate_html_report(issues, "sample.csv", str(out))

    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "sample.csv" in content
    # embedded issues payload must be valid-looking JSON (spot check a rule name)
    assert "missing_value" in content


def test_generate_html_report_handles_zero_issues(tmp_path):
    out = tmp_path / "empty.html"
    generate_html_report([], "clean.csv", str(out))
    assert out.exists()
    assert "clean.csv" in out.read_text(encoding="utf-8")
