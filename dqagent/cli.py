"""CLI entrypoint: python -m dqagent.cli path/to/file.csv"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter

from .report import generate_html_report
from .rules import check_required_fields, run_all_rules


def load_csv(path: str) -> tuple[list[dict], list[str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)
    return rows, columns


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(
            "Usage: python -m dqagent.cli path/to/dataset.csv "
            "[--json out.json] [--html out.html] [--required col1,col2]"
        )
        return 1

    path = argv[0]
    json_out = None
    if "--json" in argv:
        json_out = argv[argv.index("--json") + 1]
    html_out = None
    if "--html" in argv:
        html_out = argv[argv.index("--html") + 1]
    required_columns = None
    if "--required" in argv:
        required_columns = argv[argv.index("--required") + 1].split(",")

    rows, columns = load_csv(path)
    issues = run_all_rules(rows, columns)
    if required_columns:
        issues += check_required_fields(rows, columns, required_columns)

    print(f"Dataset: {path}")
    print(f"Baris data: {len(rows)}  |  Kolom: {len(columns)}")
    print(f"Isu ditemukan: {len(issues)}")

    by_rule = Counter(issue.rule for issue in issues)
    for rule, count in sorted(by_rule.items(), key=lambda kv: -kv[1]):
        print(f"  - {rule}: {count}")

    if html_out:
        generate_html_report(issues, os.path.basename(path), html_out)
        print(f"Review UI (buka di browser): {html_out}")

    if json_out:
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump([issue.to_dict() for issue in issues], f, indent=2, ensure_ascii=False)
        print(f"Laporan lengkap: {json_out}")
    elif not html_out:
        for issue in issues[:20]:
            print(f"  [row {issue.row}] {issue.column}: {issue.message}")
        if len(issues) > 20:
            print(f"  ... dan {len(issues) - 20} isu lainnya (pakai --json untuk laporan lengkap)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
