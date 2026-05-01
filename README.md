# Smart Navigation System

Sistem navigasi berbasis **weighted graph** dengan tiga antarmuka:

| Antarmuka | Command |
|---|---|
| Python CLI (OOP) | `./run.sh cli` |
| Streamlit UI interaktif | `./run.sh ui` |
| C CLI (Linux/Mac) | `./run.sh c-build` lalu `./run.sh c-run` |
| C CLI (Windows) | Lihat `docs/GUIDE.md` bagian 4.B |

---

## Quickstart

```bash
# 1. Clone repo
git clone https://github.com/yusepahmad/Smart-Navigation-System.git
cd Smart-Navigation-System

# 2. Install dependencies
./run.sh setup

# 3. Jalankan
./run.sh cli        # Python CLI
./run.sh ui         # Streamlit UI
./run.sh test       # Test suite
```

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
Smart-Navigation-System/
├── run.sh                   # Unified runner — semua command dari sini
├── pyproject.toml           # Dependensi Python (uv)
├── README.md
│
├── app/
│   ├── main.py              # Entry point Python CLI
│   └── streamlit_app.py     # Streamlit UI
│
├── docs/
│   ├── GUIDE.md             # Panduan lengkap setup & penggunaan
│   └── documentation.md    # Dokumentasi teknis algoritma
│
├── c/
│   ├── cli_app.c            # C CLI source
│   ├── cli_app.cpp          # C++ CLI source
│   ├── Makefile             # Build targets (Linux/Mac)
│   └── init.ps1             # Windows MSVC environment init
│
├── data/
│   ├── krl/
│   │   ├── nodes.csv        # Dataset stasiun KRL
│   │   └── edges.csv        # Koneksi antar stasiun
│   ├── nodes.csv
│   ├── edges.csv
│   └── query.csv
│
├── output/                  # Generated (result.csv, history.csv)
│
├── smart_navigation/        # Python package (core logic)
│   ├── cli/app.py
│   ├── core/graph.py
│   ├── core/history.py
│   ├── services/navigation_service.py
│   ├── io/csv_repository.py
│   └── models/query_result.py
│
└── tests/
```

---

## Setup

### Python (via uv)

```bash
./run.sh setup
```

Jika belum punya `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### C / C++ (Linux/Mac)

```bash
./run.sh c-build      # compile C
./run.sh c-run        # jalankan
```

Atau langsung via `make`:
```bash
make -C c/
./c/cli_app
```

### C / C++ (Windows)

Lihat [docs/GUIDE.md](docs/GUIDE.md) bagian 4.B.

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
./run.sh test
```

---

## Dokumentasi Detail

- [docs/GUIDE.md](docs/GUIDE.md) — panduan setup, menu CLI, format CSV, troubleshooting
- [docs/documentation.md](docs/documentation.md) — dokumentasi teknis algoritma & arsitektur
