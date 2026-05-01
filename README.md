# Smart Navigation System

Sistem navigasi berbasis **weighted graph** dengan tiga antarmuka:

| Antarmuka | Cara Jalankan |
|---|---|
| Python CLI (OOP) | `python main.py` |
| Streamlit UI interaktif | `streamlit run streamlit_app.py` |
| C++ CLI | `.\cli_app.exe` (lihat bagian Setup C++) |

---

## Fitur Utama

| No | Fitur | Deskripsi |
|----|-------|-----------|
| 1 | Tambah Node | Menambahkan lokasi ke graph |
| 2 | Tambah Edge | Menambahkan koneksi dengan bobot distance & time |
| 3 | Tampilkan Graph | Adjacency list dengan bobot per edge |
| 4 | Find Optimal Path | **Dijkstra** — pilih optimasi by distance atau time |
| 5 | DFS Exploration | Eksplorasi seluruh graph (iteratif) |
| 6 | Tampilkan History | Riwayat path yang pernah ditemukan |
| 7 | Load Graph dari CSV | Muat nodes + edges dari file CSV |
| 8 | Batch Query + Export | Jalankan banyak query sekaligus, simpan ke result.csv |
| 9 | Export History | Simpan riwayat ke history.csv |

---

## Algoritma

- **Dijkstra** — mencari jalur optimal berdasarkan total bobot minimum (distance atau time)
- **DFS** — eksplorasi graph dengan stack (iteratif), urutan kunjungan konsisten

---

## Struktur Project

```text
Smart-Navigation-System-Documentation/
├── main.py                  # Entry point Python CLI
├── streamlit_app.py         # Streamlit UI
├── cli_app.cpp              # C++ CLI (source, copy dari CODE/)
├── requirements.txt
├── data/
│   ├── krl/
│   │   ├── nodes.csv        # Dataset stasiun KRL
│   │   └── edges.csv        # Koneksi antar stasiun (with distance & time)
│   ├── nodes.csv
│   ├── edges.csv
│   └── query.csv
├── output/
│   ├── result.csv
│   └── history.csv
├── smart_navigation/
│   ├── cli/app.py
│   ├── core/graph.py
│   ├── core/history.py
│   ├── services/navigation_service.py
│   ├── io/csv_repository.py
│   └── models/query_result.py
└── tests/
```

---

## Setup Python

```bash
pip install -r requirements.txt
```

## Menjalankan Python CLI

```bash
python main.py
```

## Menjalankan Streamlit UI

```bash
streamlit run streamlit_app.py
```

## Setup & Menjalankan C++ CLI

### 1. Inisialisasi environment MSVC (sekali per sesi terminal)

```powershell
.\init.ps1
```

### 2. Compile

```powershell
cl /std:c++17 /EHsc /O2 /Fe:cli_app.exe cli_app.cpp
```

### 3. Jalankan

```powershell
.\cli_app.exe
```

> Program otomatis mendeteksi folder `data/` dari direktori kerja saat ini.

---

## Format CSV

| File | Kolom wajib |
|------|------------|
| `data/nodes.csv` | `name` |
| `data/edges.csv` | `from`, `to`, `distance`, `time` |
| `data/query.csv` | `start`, `end` |
| `output/result.csv` | `start`, `end`, `path`, `distance`, `time` |
| `output/history.csv` | `no`, `path` |

---

## Menjalankan Test

```bash
python -m unittest discover -s tests -v
```

## Dokumentasi Detail

Lihat [GUIDE.md](GUIDE.md) dan [documention.md](documention.md).
