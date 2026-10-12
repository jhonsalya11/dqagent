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

# Fixture for rules 5-10 (encoding, outlier, region, required field, unit)
EXTENDED_ROWS = [
    {"kabupaten": "Bandung", "berat": "10kg", "catatan": "normal", "skor": "85"},
    {"kabupaten": "Bandung", "berat": "12kg", "catatan": "normal", "skor": "88"},
    {"kabupaten": "Bandng", "berat": "11kg", "catatan": "normal", "skor": "90"},       # typo of Bandung
    {"kabupaten": "Surabaya", "berat": "9kg", "catatan": "normal", "skor": "82"},
    {"kabupaten": "Surabaya", "berat": "500gram", "catatan": "normal", "skor": "87"},  # mixed unit
    {"kabupaten": "Surabaya", "berat": "10kg", "catatan": "Data rusak: Ã©Ã¨ encoding error", "skor": "91"},
    {"kabupaten": "Surabaya", "berat": "9999", "catatan": "normal", "skor": "9999"},     # numeric outlier
]
EXTENDED_COLUMNS = ["kabupaten", "berat", "catatan", "skor"]
