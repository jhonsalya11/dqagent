# DQ Agent — AI Data-Quality Agent (MVP)

MVP rule-based validator untuk dataset CSV publik yang berantakan
(open-government/NGO/riset). Lihat `docs/research/2026-10-12-open-data-quality-deep-research.md`
untuk konteks lengkap persona, rule set, dan mockup UI.

Status: **10/10 rule dari deep research sudah diimplementasikan** (rule-based,
bukan LLM). Semantic/LLM-based check (deteksi makna duplikat yang lebih canggih)
tetap direncanakan untuk tahap selanjutnya SETELAH budget cap disetujui terpisah.

## Rule yang sudah diimplementasikan (10/10)

1. Format tanggal konsisten → normalisasi ke ISO-8601, flag yang ambigu
2. Missing value → deteksi sel kosong/variasi penulisan ("", "N/A", "-", "NULL")
3. Duplikat baris (exact match)
4. Tipe data tidak konsisten per kolom (angka ketulis sebagai teks)
5. Encoding/karakter aneh → deteksi mojibake / replacement character
6. Whitespace & casing tidak konsisten pada kolom teks
7. Validasi range/outlier → metode IQR (1.5x fence) untuk kolom numerik
8. Konsistensi kode wilayah → deteksi kemungkinan typo/variasi penulisan
   pada kolom provinsi/kabupaten/kota (fuzzy match sederhana)
9. Field wajib tidak kosong → **butuh schema eksplisit** dari pemanggil
   (`--required kolom1,kolom2` di CLI), tidak otomatis menebak sendiri
10. Konsistensi unit → deteksi campuran unit dalam 1 kolom (mis. "kg" vs "gram")

## Pakai

```bash
cd product
pip install -r requirements.txt
python -m dqagent.cli path/to/dataset.csv
python -m dqagent.cli path/to/dataset.csv --json laporan.json
python -m dqagent.cli path/to/dataset.csv --required nama,tanggal_lahir
```

Output: ringkasan console atau laporan JSON lengkap, TIDAK ada auto-delete —
sesuai prinsip "explainable, human review per-item" di mockup UI.

## Keterbatasan yang diketahui (jujur, biar nggak over-claim)

- Rule 7 (outlier) & 10 (unit) pakai heuristik sederhana, bisa false
  positive/negative pada dataset kecil (<4 baris numerik tidak dicek)
- Rule 8 (region) pakai fuzzy match karakter sederhana, bukan database
  resmi kode wilayah BPS — cocok buat nangkap typo kasar, bukan validasi
  administratif resmi
- Rule 9 (required field) sengaja tidak otomatis — "wajib" itu keputusan
  skema yang nggak bisa ditebak dari data saja
- Belum ada UI visual (masih CLI/JSON), belum ada LLM/semantic check

## Test

```bash
cd product
pytest tests/ -v
```

12 test, semua rule punya minimal 1 test dengan fixture dataset realistis.
