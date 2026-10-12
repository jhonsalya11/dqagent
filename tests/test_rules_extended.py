import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dqagent.rules import (  # noqa: E402
    check_encoding,
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
