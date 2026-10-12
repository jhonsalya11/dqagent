# DQ Agent — AI Data-Quality Agent (MVP)

MVP rule-based validator untuk dataset CSV publik yang berantakan
(open-government/NGO/riset). Lihat `docs/research/2026-10-12-open-data-quality-deep-research.md`
untuk konteks lengkap persona, rule set, dan mockup UI.

Status: **MVP tahap 1** — implementasi rule-based (bukan LLM dulu), supaya
bisa jalan tanpa spend uang (budget cap masih 0). Semantic/LLM-based check
(mis. deteksi makna duplikat yang lebih canggih) direncanakan untuk tahap 2
SETELAH budget cap disetujui terpisah.

## Rule yang sudah diimplementasikan (5 dari 10 di deep research)

1. Format tanggal konsisten → normalisasi ke ISO-8601, flag yang ambigu
2. Missing value → deteksi sel kosong/variasi penulisan ("", "N/A", "-", "NULL")
3. Duplikat baris (exact match)
4. Whitespace & casing tidak konsisten pada kolom teks
5. Tipe data tidak konsisten per kolom (angka ketulis sebagai teks)

Rule 6–10 (outlier, kode wilayah, field wajib, unit, encoding) menyusul di
iterasi berikutnya — di luar scope MVP ini.

## Pakai

```bash
cd product
pip install -r requirements.txt
python -m dqagent.cli path/to/dataset.csv
```

Output: laporan JSON + ringkasan console, TIDAK ada auto-delete — sesuai
prinsip "explainable, human review per-item" di mockup UI.

## Test

```bash
cd product
pytest tests/ -v
```
