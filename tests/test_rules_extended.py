import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dqagent.rules import (  # noqa: E402
    check_encoding,
    check_missing_values,
    check_outliers,
    check_region_consistency,
    check_required_fields,
    check_unit_consistency,
)
from fixtures import EXTENDED_COLUMNS, EXTENDED_ROWS  # noqa: E402


def test_check_encoding_flags_mojibake():
    issues = check_encoding(EXTENDED_ROWS, EXTENDED_COLUMNS)
    assert any(i.row == 6 and i.column == "catatan" for i in issues)


def test_check_outliers_flags_extreme_value():
    issues = check_outliers(EXTENDED_ROWS, EXTENDED_COLUMNS)
    # row 7 "skor"=9999 is far outside the ~82-91 range of the other rows
    assert any(i.row == 7 and i.column == "skor" for i in issues)


def test_check_region_consistency_flags_typo():
    issues = check_region_consistency(EXTENDED_ROWS, EXTENDED_COLUMNS)
    assert any(i.row == 3 and "Bandung" in (i.suggestion or "") for i in issues)


def test_check_unit_consistency_flags_mixed_unit():
    issues = check_unit_consistency(EXTENDED_ROWS, EXTENDED_COLUMNS)
    assert any(i.row == 5 and i.value == "gram" for i in issues)


def test_check_required_fields_is_noop_without_schema():
    issues = check_required_fields(EXTENDED_ROWS, EXTENDED_COLUMNS)
    assert issues == []


def test_check_required_fields_flags_missing_when_declared():
    rows = EXTENDED_ROWS + [{"kabupaten": "", "berat": "10kg", "catatan": "x"}]
    issues = check_required_fields(rows, EXTENDED_COLUMNS, required_columns=["kabupaten"])
    assert any(i.row == 8 and i.column == "kabupaten" for i in issues)


# --- Regression tests for bugs found during real-dataset testing ---
# See docs/research/2026-10-12-real-dataset-test-findings.md


def test_missing_values_summarizes_mostly_empty_column_as_single_issue():
    """A column empty in >80% of rows should be ONE dataset-level Issue,
    not one Issue per row (real bug: NYC DOB dataset had columns empty
    500/500 rows, producing 500 near-duplicate issues for 1 column)."""
    rows = [{"always_empty": "", "ok": "1"} for _ in range(20)]
    issues = check_missing_values(rows, ["always_empty", "ok"])
    always_empty_issues = [i for i in issues if i.column == "always_empty"]
    assert len(always_empty_issues) == 1
    assert always_empty_issues[0].row == -1


def test_missing_values_still_reports_per_row_below_threshold():
    """A column missing in a MINORITY of rows should still be reported
    per-row (not summarized) — this keeps the original MVP behavior."""
    rows = [{"col": "x"}] * 8 + [{"col": ""}] * 2  # 20% missing
    issues = check_missing_values(rows, ["col"])
    assert len(issues) == 2
    assert all(i.row != -1 for i in issues)


def test_outliers_skip_id_like_columns():
    """ID/number columns (job_id, zip, bin, etc.) must never be flagged as
    numeric outliers — an identifier has no 'statistically normal range'
    (real bug: job_s1_no flagged as outlier in NYC DOB dataset)."""
    rows = [{"job_s1_no": str(n)} for n in [100, 101, 102, 999999, 103]]
    issues = check_outliers(rows, ["job_s1_no"])
    assert issues == []


def test_unit_consistency_ignores_street_names():
    """Street addresses like '123 Main Street' must NOT be read as a unit
    'street' — only a whitelisted set of real measurement units counts
    (real bug found in NYC DOB dataset: 'street', 'road', 'flatlands' were
    being extracted as 'units')."""
    rows = [
        {"address": "123 Main Street"},
        {"address": "45 Flatlands Ave"},
        {"address": "10kg"},  # a genuine unit value for contrast
        {"address": "12kg"},
    ]
    issues = check_unit_consistency(rows, ["address"])
    assert not any(i.value in ("street", "flatlands", "ave") for i in issues)
