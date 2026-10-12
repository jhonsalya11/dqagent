import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dqagent.rules import (  # noqa: E402
    check_date_format,
    check_duplicate_rows,
    check_missing_values,
    check_type_consistency,
    check_whitespace_casing,
    run_all_rules,
)
from fixtures import SAMPLE_COLUMNS, SAMPLE_ROWS  # noqa: E402


def test_missing_values_detects_empty_and_na_tokens():
    issues = check_missing_values(SAMPLE_ROWS, SAMPLE_COLUMNS)
    rows_flagged = {i.row for i in issues}
    assert 3 in rows_flagged  # empty tanggal_cair
    assert 6 in rows_flagged  # "N/A" nama_opd


def test_duplicate_rows_detects_exact_duplicate():
    issues = check_duplicate_rows(SAMPLE_ROWS, SAMPLE_COLUMNS)
    assert len(issues) == 1
    assert issues[0].row == 5
    assert "baris 4" in issues[0].message


def test_whitespace_casing_detects_trailing_space():
    issues = check_whitespace_casing(SAMPLE_ROWS, SAMPLE_COLUMNS)
    whitespace_issues = [i for i in issues if i.rule == "whitespace"]
    assert any(i.row == 2 and i.column == "nama_opd" for i in whitespace_issues)


def test_date_format_flags_ambiguous_date():
    issues = check_date_format(SAMPLE_ROWS, SAMPLE_COLUMNS)
    ambiguous = [i for i in issues if i.row == 2]
    unparseable = [i for i in issues if i.row == 6]
    assert ambiguous, "row 2 '03/04/2026' should be flagged as ambiguous"
    assert unparseable, "row 6 'not-a-date' should be flagged as unparseable"


def test_type_consistency_flags_non_numeric_in_numeric_column():
    issues = check_type_consistency(SAMPLE_ROWS, SAMPLE_COLUMNS)
    assert any(i.row == 3 and i.column == "jumlah" for i in issues)


def test_run_all_rules_returns_combined_issues():
    issues = run_all_rules(SAMPLE_ROWS, SAMPLE_COLUMNS)
    rules_found = {i.rule for i in issues}
    assert "missing_value" in rules_found
    assert "duplicate_row" in rules_found
    assert len(issues) > 0
