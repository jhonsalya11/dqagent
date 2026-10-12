# dqagent

Rule-based data quality checker for messy public CSV datasets (open
government data, NGO exports, research data dumps). Finds the usual
suspects — missing values, duplicate rows, ambiguous dates, inconsistent
units, mixed casing, outliers — and gives you an explainable report you
review before changing anything. **It never auto-deletes or auto-edits
your data.**

## Why

Open datasets from government portals and small organizations are
routinely messy: inconsistent date formats, blank cells written five
different ways, duplicate rows, typos in region names. Enterprise
data-quality tools (Informatica, Alation, Great Expectations) are built
for big teams with infrastructure budgets. `dqagent` is a small, free,
single-file-output tool for the person who just has a CSV and needs to
know what's wrong with it before publishing or analyzing it.

## Install

```bash
pip install dqagent   # once published to PyPI
# or, from source:
git clone https://github.com/jhonsalya11/dqagent.git
cd dqagent
pip install -e .
```

## Usage

```bash
# Quick console summary
dqagent mydata.csv

# Full issue list as JSON
dqagent mydata.csv --json report.json

# Interactive HTML review (open in any browser, no server needed)
dqagent mydata.csv --html review.html

# Flag rows missing a value in specific required columns
dqagent mydata.csv --required name,date_of_birth
```

## What it checks (10 rules)

| # | Rule | What it catches |
|---|------|------------------|
| 1 | Date format | Ambiguous dates (`03/04/2026` — March 4 or April 3?) |
| 2 | Missing values | Blank cells, and inconsistent "empty" tokens (`N/A`, `-`, `null`...) |
| 3 | Duplicate rows | Exact-match duplicates |
| 4 | Type consistency | A mostly-numeric column with stray text values |
| 5 | Encoding | Mojibake / replacement-character artifacts |
| 6 | Whitespace & casing | Trailing spaces, inconsistent capitalization |
| 7 | Outliers | Numeric values far outside the normal range (IQR method) |
| 8 | Region name typos | Fuzzy-match variants in province/city/region columns |
| 9 | Required fields | Opt-in: flags blanks in columns YOU declare required |
| 10 | Unit consistency | Mixed units in one column (e.g. "kg" vs "gram") |

## How the HTML review works

`--html` generates one self-contained `.html` file: a table of every
issue found, with filter buttons per rule and Accept/Reject buttons per
row. Your decisions are saved in the browser's `localStorage` (keyed by
filename) — **nothing is sent to a server**, there's no backend. An
export button lets you download your decisions as JSON. Good for one
person reviewing one dataset at a time; not (yet) built for multi-user
review of the same file.

## Known limitations (we'd rather you know than find out)

- Outlier and unit-consistency checks use simple heuristics — good at
  catching obvious problems, not a substitute for domain-specific rules
- Region-typo detection is a cheap fuzzy match, not an official
  administrative code database (e.g. not validated against Indonesia's
  official BPS region codes)
- Required-field checking never guesses on its own — you must pass
  `--required` explicitly
- No semantic/LLM-based checks — purely rule-based, which also means: no
  API calls, no cost, works fully offline

## Tested against real data

Validated against a real NYC Dept. of Buildings permit dataset (500 rows,
95 columns) during development — found and fixed 3 real false-positive
bugs in the process (see commit history). Issue count on that same
dataset dropped from 16,454 (before fixes) to 3,842 (after), with no loss
of genuine detections.

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

18 tests, covering all 10 rules plus the HTML report generator.

## License

MIT — see [LICENSE](LICENSE).
