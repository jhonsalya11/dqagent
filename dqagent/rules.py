"""DQ Agent — rule-based data quality checks for messy public CSV datasets.

Every rule returns a list of Issue objects. No rule ever mutates or deletes
data silently — issues are reported for human review (see mockup UI in
docs/research/2026-10-12-open-data-quality-deep-research.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([T ].*)?$")

try:
    from dateutil import parser as date_parser
except ImportError:  # pragma: no cover - exercised only if dependency missing
    date_parser = None

MISSING_TOKENS = {"", "n/a", "na", "null", "none", "-", "--", "?", "unknown"}


@dataclass
class Issue:
    row: int  # 1-indexed data row (header excluded), -1 for dataset-level issues
    column: str
    rule: str
    message: str
    value: Any = None
    suggestion: str | None = None

    def to_dict(self) -> dict:
        return {
            "row": self.row,
            "column": self.column,
            "rule": self.rule,
            "message": self.message,
            "value": self.value,
            "suggestion": self.suggestion,
        }


def _looks_like_date_column(column_name: str) -> bool:
    name = column_name.lower()
    return any(tok in name for tok in ("date", "tanggal", "tgl", "time", "waktu"))


def check_date_format(rows: list[dict], columns: list[str]) -> list[Issue]:
    """Rule 1: flag inconsistent / ambiguous date formats in date-like columns."""
    issues: list[Issue] = []
    if date_parser is None:
        return issues

    for col in columns:
        if not _looks_like_date_column(col):
            continue
        seen_formats: set[str] = set()
        for i, row in enumerate(rows, start=1):
            raw = (row.get(col) or "").strip()
            if not raw or raw.lower() in MISSING_TOKENS:
                continue
            if _ISO_DATE_RE.match(raw):
                # Already unambiguous (YYYY-MM-DD) — nothing to flag.
                continue
            try:
                parsed = date_parser.parse(raw, dayfirst=False, fuzzy=False)
                parsed_dayfirst = date_parser.parse(raw, dayfirst=True, fuzzy=False)
            except (ValueError, OverflowError):
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="date_format",
                        message=f"Nilai '{raw}' tidak bisa diparse sebagai tanggal",
                        value=raw,
                    )
                )
                continue

            if parsed.date() != parsed_dayfirst.date():
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="date_format",
                        message=(
                            f"Tanggal ambigu: '{raw}' bisa dibaca "
                            f"{parsed.date().isoformat()} (MM/DD) atau "
                            f"{parsed_dayfirst.date().isoformat()} (DD/MM)"
                        ),
                        value=raw,
                        suggestion=parsed_dayfirst.date().isoformat(),
                    )
                )
            else:
                seen_formats.add(parsed.date().isoformat()[:4])  # just to touch a format marker
    return issues


def check_missing_values(rows: list[dict], columns: list[str]) -> list[Issue]:
    """Rule 2: flag missing/empty values, including inconsistent 'missing' tokens."""
    issues: list[Issue] = []
    for col in columns:
        for i, row in enumerate(rows, start=1):
            raw = row.get(col)
            normalized = (raw or "").strip().lower()
            if normalized in MISSING_TOKENS:
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="missing_value",
                        message=f"Nilai kosong/missing ('{raw}')",
                        value=raw,
                    )
                )
    return issues


def check_duplicate_rows(rows: list[dict], columns: list[str]) -> list[Issue]:
    """Rule 3: exact-match duplicate row detection."""
    issues: list[Issue] = []
    seen: dict[tuple, int] = {}
    for i, row in enumerate(rows, start=1):
        key = tuple((row.get(c) or "").strip().lower() for c in columns)
        if key in seen:
            issues.append(
                Issue(
                    row=i,
                    column="*",
                    rule="duplicate_row",
                    message=f"Duplikat exact dari baris {seen[key]}",
                    suggestion=f"Bandingkan dengan baris {seen[key]}",
                )
            )
        else:
            seen[key] = i
    return issues


def check_whitespace_casing(rows: list[dict], columns: list[str]) -> list[Issue]:
    """Rule 4: inconsistent whitespace/casing in text columns."""
    issues: list[Issue] = []
    for col in columns:
        canonical_by_lower: dict[str, str] = {}
        for i, row in enumerate(rows, start=1):
            raw = row.get(col)
            if raw is None:
                continue
            stripped = raw.strip()
            if not stripped or stripped.lower() in MISSING_TOKENS:
                continue
            if raw != stripped:
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="whitespace",
                        message="Ada whitespace di awal/akhir nilai",
                        value=raw,
                        suggestion=stripped,
                    )
                )
            lower_key = stripped.lower()
            if lower_key in canonical_by_lower and canonical_by_lower[lower_key] != stripped:
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="casing",
                        message=(
                            f"Casing tidak konsisten: '{stripped}' vs "
                            f"'{canonical_by_lower[lower_key]}' (baris lain)"
                        ),
                        value=stripped,
                        suggestion=canonical_by_lower[lower_key],
                    )
                )
            else:
                canonical_by_lower.setdefault(lower_key, stripped)
    return issues


def check_type_consistency(rows: list[dict], columns: list[str]) -> list[Issue]:
    """Rule 5: flag numeric-looking columns where some values aren't numeric."""
    issues: list[Issue] = []

    def is_number(val: str) -> bool:
        try:
            float(val.replace(",", "").replace(".", "", val.count(".") - 1) if val.count(".") > 1 else val.replace(",", ""))
            return True
        except ValueError:
            return False

    for col in columns:
        values = [(i, (row.get(col) or "").strip()) for i, row in enumerate(rows, start=1)]
        non_empty = [(i, v) for i, v in values if v and v.lower() not in MISSING_TOKENS]
        if not non_empty:
            continue
        numeric_flags = [is_number(v) for _, v in non_empty]
        numeric_ratio = sum(numeric_flags) / len(numeric_flags)
        # Only flag columns that are "mostly numeric" (>70%) but have exceptions —
        # avoids false positives on genuinely text columns.
        if 0.7 <= numeric_ratio < 1.0:
            for (i, v), is_num in zip(non_empty, numeric_flags):
                if not is_num:
                    issues.append(
                        Issue(
                            row=i,
                            column=col,
                            rule="type_consistency",
                            message=(
                                f"Kolom '{col}' mayoritas numerik tapi nilai ini bukan: '{v}'"
                            ),
                            value=v,
                        )
                    )
    return issues


def _to_float(val: str) -> float | None:
    cleaned = val.replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


_MOJIBAKE_MARKERS = ("Ã", "Â", "â€", "\ufffd")


def check_encoding(rows: list[dict], columns: list[str]) -> list[Issue]:
    """Rule 5: flag mojibake / replacement-character artifacts from bad encoding."""
    issues: list[Issue] = []
    for col in columns:
        for i, row in enumerate(rows, start=1):
            raw = row.get(col)
            if not raw:
                continue
            if "\ufffd" in raw or any(marker in raw for marker in _MOJIBAKE_MARKERS):
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="encoding",
                        message="Nilai mengandung karakter mencurigakan (kemungkinan salah encoding/mojibake)",
                        value=raw,
                    )
                )
    return issues


def check_outliers(rows: list[dict], columns: list[str]) -> list[Issue]:
    """Rule 7: flag numeric outliers using the IQR method (1.5x fence)."""
    issues: list[Issue] = []
    for col in columns:
        parsed = [(i, _to_float((row.get(col) or "").strip())) for i, row in enumerate(rows, start=1)]
        values = sorted(v for _, v in parsed if v is not None)
        if len(values) < 4:
            continue  # not enough data to compute a meaningful IQR
        q1 = values[len(values) // 4]
        q3 = values[(len(values) * 3) // 4]
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        for i, v in parsed:
            if v is not None and (v < lower or v > upper):
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="outlier",
                        message=f"Nilai {v:g} di luar rentang wajar ({lower:.1f} s/d {upper:.1f})",
                        value=v,
                    )
                )
    return issues


def _region_like(column_name: str) -> bool:
    name = column_name.lower()
    return any(tok in name for tok in ("provinsi", "kabupaten", "kota", "wilayah", "daerah", "region"))


def _similar(a: str, b: str) -> bool:
    """Cheap near-duplicate check: same length-ish and most characters shared."""
    if a == b:
        return False  # identical isn't a typo issue
    if abs(len(a) - len(b)) > 2:
        return False
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    matches = sum(1 for ch in shorter if ch in longer)
    return matches / max(len(shorter), 1) >= 0.8


def check_region_consistency(rows: list[dict], columns: list[str]) -> list[Issue]:
    """Rule 8: flag likely typos/variants in region-name columns (e.g. 'Jakata' vs 'Jakarta')."""
    issues: list[Issue] = []
    for col in columns:
        if not _region_like(col):
            continue
        canonical_seen: list[str] = []
        for i, row in enumerate(rows, start=1):
            raw = (row.get(col) or "").strip()
            if not raw or raw.lower() in MISSING_TOKENS:
                continue
            match = next((c for c in canonical_seen if _similar(raw.lower(), c.lower())), None)
            if match:
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="region_consistency",
                        message=f"Kemungkinan typo/variasi penulisan: '{raw}' vs '{match}'",
                        value=raw,
                        suggestion=match,
                    )
                )
            else:
                canonical_seen.append(raw)
    return issues


def check_required_fields(
    rows: list[dict], columns: list[str], required_columns: list[str] | None = None
) -> list[Issue]:
    """Rule 9: flag rows missing a value in an explicitly-declared required column.

    No-op (returns no issues) unless the caller passes `required_columns` —
    "required" is a schema decision this tool can't infer on its own.
    """
    issues: list[Issue] = []
    if not required_columns:
        return issues
    for col in required_columns:
        if col not in columns:
            continue
        for i, row in enumerate(rows, start=1):
            raw = (row.get(col) or "").strip()
            if not raw or raw.lower() in MISSING_TOKENS:
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="required_field",
                        message=f"Kolom wajib '{col}' kosong",
                        value=raw,
                    )
                )
    return issues


_UNIT_SUFFIX_RE = re.compile(r"[\d.,]+\s*([a-zA-Z%]+)$")
_UNIT_PREFIX_RE = re.compile(r"^([a-zA-Z]+)\s*[\d.,]+")


def _extract_unit(value: str) -> str | None:
    m = _UNIT_SUFFIX_RE.match(value) or _UNIT_PREFIX_RE.match(value)
    return m.group(1).lower() if m else None


def check_unit_consistency(rows: list[dict], columns: list[str]) -> list[Issue]:
    """Rule 10: flag columns that mix different unit suffixes/prefixes (e.g. 'kg' vs 'gram')."""
    issues: list[Issue] = []
    for col in columns:
        units_seen: dict[str, int] = {}
        per_row_unit: list[tuple[int, str | None]] = []
        for i, row in enumerate(rows, start=1):
            raw = (row.get(col) or "").strip()
            if not raw or raw.lower() in MISSING_TOKENS:
                per_row_unit.append((i, None))
                continue
            unit = _extract_unit(raw)
            per_row_unit.append((i, unit))
            if unit:
                units_seen[unit] = units_seen.get(unit, 0) + 1

        distinct_units = set(units_seen)
        if len(distinct_units) < 2:
            continue  # nothing to compare

        majority_unit = max(units_seen, key=units_seen.get)
        for i, unit in per_row_unit:
            if unit and unit != majority_unit:
                issues.append(
                    Issue(
                        row=i,
                        column=col,
                        rule="unit_consistency",
                        message=(
                            f"Unit '{unit}' tidak konsisten dengan mayoritas kolom ('{majority_unit}')"
                        ),
                        value=unit,
                        suggestion=majority_unit,
                    )
                )
    return issues


ALL_RULES = [
    check_date_format,
    check_missing_values,
    check_duplicate_rows,
    check_whitespace_casing,
    check_type_consistency,
    check_encoding,
    check_outliers,
    check_region_consistency,
    check_unit_consistency,
    # check_required_fields deliberately excluded from ALL_RULES — it needs
    # an explicit `required_columns` schema from the caller, so it only runs
    # when invoked directly (see cli.py --required flag).
]


def run_all_rules(rows: list[dict], columns: list[str]) -> list[Issue]:
    issues: list[Issue] = []
    for rule_fn in ALL_RULES:
        issues.extend(rule_fn(rows, columns))
    return issues
