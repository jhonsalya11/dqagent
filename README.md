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

### Lewat `python -m` (tanpa install)
```bash
cd product
pip install -r requirements.txt
python -m dqagent.cli path/to/dataset.csv
python -m dqagent.cli path/to/dataset.csv --json laporan.json
python -m dqagent.cli path/to/dataset.csv --html review.html
python -m dqagent.cli path/to/dataset.csv --required nama,tanggal_lahir
```

### Sebagai command terinstall (`pip install -e .`)
```bash
cd product
pip install -e .
dqagent path/to/dataset.csv --html review.html
```
Terverifikasi jalan di virtualenv bersih — entry point `dqagent` terdaftar
lewat `pyproject.toml` (`[project.scripts]`).

Output: ringkasan console, laporan JSON lengkap, atau **UI review interaktif**
(`--html`) — file HTML statis, buka langsung di browser, tidak butuh server.
TIDAK ada auto-delete — sesuai prinsip "explainable, human review per-item"
di mockup UI.

### UI Review (`--html`)

Implementasi nyata dari mockup ASCII di deep research doc: tabel semua isu,
filter per rule, dan tombol **Terima / Tolak / Belum** per baris. Keputusan
disimpan di `localStorage` browser (per nama dataset) — **tidak ada server,
tidak ada data terkirim ke mana pun**, nol spend. Tombol "Export keputusan"
download hasil reviewnya sebagai JSON.

Keterbatasan: keputusan tersimpan di browser lokal reviewer, bukan di
database bersama — cocok buat 1 orang review 1 file, belum cocok untuk tim
yang perlu lihat keputusan satu sama lain (itu butuh backend, fase berikutnya
kalau diperlukan).

## Keterbatasan yang diketahui (jujur, biar nggak over-claim)

- Rule 7 (outlier) & 10 (unit) pakai heuristik sederhana, bisa false
  positive/negative pada dataset kecil (<4 baris numerik tidak dicek)
- Rule 8 (region) pakai fuzzy match karakter sederhana, bukan database
  resmi kode wilayah BPS — cocok buat nangkap typo kasar, bukan validasi
  administratif resmi
- Rule 9 (required field) sengaja tidak otomatis — "wajib" itu keputusan
  skema yang nggak bisa ditebak dari data saja. **Diverifikasi dengan
  dataset nyata** (lihat `docs/research/2026-10-12-required-field-verification.md`):
  0 false positive/negative pada 2 skenario uji
- UI review masih client-side only (localStorage), belum ada LLM/semantic check

## Test

```bash
cd product
pytest tests/ -v
```

18 test, semua rule + report generator punya minimal 1 test dengan fixture
dataset realistis, plus regression test untuk bug yang ditemukan dari
pengujian dataset nyata.
