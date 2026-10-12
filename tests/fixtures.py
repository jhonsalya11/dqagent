"""Sample messy dataset fixture + helper for tests."""
from __future__ import annotations

SAMPLE_ROWS = [
    {"nama_opd": "Dinas Pendidikan", "tanggal_cair": "2026-01-15", "jumlah": "1000000"},
    {"nama_opd": "Dinas pendidikaN ", "tanggal_cair": "03/04/2026", "jumlah": "2.500.000"},
    {"nama_opd": "Dinas Kesehatan", "tanggal_cair": "", "jumlah": "abc"},
    {"nama_opd": "Dinas Kesehatan", "tanggal_cair": "2026-02-01", "jumlah": "500000"},
    {"nama_opd": "Dinas Kesehatan", "tanggal_cair": "2026-02-01", "jumlah": "500000"},  # exact dup of row above
    {"nama_opd": "N/A", "tanggal_cair": "not-a-date", "jumlah": "750000"},
]
SAMPLE_COLUMNS = ["nama_opd", "tanggal_cair", "jumlah"]
