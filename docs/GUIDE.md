# GUIDE — Smart Navigation System

## 1. Setup Python

Pastikan `uv` sudah terinstall:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install dependensi:

```bash
./run.sh setup
# atau langsung: uv sync
```

Jika ingin menggunakan virtualenv manual:

```bash
uv venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows
uv sync
```

---

## 2. Menjalankan Python CLI

```bash
./run.sh cli
# atau: uv run python app/main.py
```

---

## 3. Menjalankan Streamlit UI

```bash
./run.sh ui
# atau: uv run streamlit run app/streamlit_app.py
```

Streamlit membuka browser otomatis. Semua fitur CLI tersedia di panel kiri,
visualisasi graph interaktif di panel kanan.

---

## 4. Setup & Menjalankan C CLI

### 4.A Linux / Mac (gcc)

#### 4.A.1 Pastikan gcc tersedia

```bash
gcc --version
```

Jika belum terinstall:

```bash
# Ubuntu / Debian / WSL
sudo apt install gcc

# Arch / Manjaro
sudo pacman -S gcc

# Mac (Homebrew)
brew install gcc
```

#### 4.A.2 Compile via run.sh

```bash
./run.sh c-build
```

Atau langsung via Makefile:

```bash
make -C c/
```

#### 4.A.3 Jalankan

```bash
./run.sh c-run
# atau: ./c/cli_app
```

---

### 4.B Windows (MSVC / PowerShell)

#### 4.B.1 Inisialisasi environment MSVC

Jalankan sekali per sesi terminal PowerShell:

```powershell
.\c\init.ps1
```

Script ini mengimpor variabel environment dari `vcvarsall.bat x64` ke sesi
PowerShell yang sedang berjalan, sehingga `cl` dan `link` tersedia langsung.

#### 4.B.2 Compile C++ (cl)

```powershell
cl /std:c++17 /EHsc /O2 /Fe:c\cli_app.exe c\cli_app.cpp
```

Atau compile versi C:

```powershell
cl /O2 /Fe:c\cli_app_c.exe c\cli_app.c
```

#### 4.B.3 Jalankan

```powershell
.\c\cli_app.exe
```

---

Program mendeteksi otomatis apakah folder `data/` ada di direktori saat ini
atau di subdirektori `Smart-Navigation-System-Documentation/`, sehingga bisa
dijalankan dari `CODE\` maupun dari dalam folder repo.

---

## 5. Menu CLI (Python & C identik)

| Pilihan | Fitur | Keterangan |
|---------|-------|------------|
| 1 | Tambah Node | Input nama lokasi |
| 2 | Tambah Edge | Input source, target, distance, time |
| 3 | Tampilkan Graph | Adjacency list dengan bobot tiap edge |
| 4 | Find Optimal Path | Dijkstra; pilih optimasi distance atau time |
| 5 | DFS Exploration | Eksplorasi dari node awal |
| 6 | Tampilkan History | Daftar path yang pernah dicari |
| 7 | Load Graph dari CSV | Muat `nodes.csv` + `edges.csv` |
| 8 | Batch Query + Export | Proses `query.csv`, simpan ke `result.csv` |
| 9 | Export History | Simpan ke `history.csv` |
| 0 | Keluar | — |

---

## 6. Mapping Fitur CLI ke Streamlit

| Fitur CLI | Lokasi di Streamlit |
|-----------|-------------------|
| Tambah Node | Panel kiri → *Graph Editing → Add Node* |
| Tambah Edge | Panel kiri → *Graph Editing → Add Directed Edge* |
| Tampilkan Graph | Panel kanan → *Data Snapshots → Edges Directed* |
| Find Optimal Path (Dijkstra) | Panel kiri → *Algorithms → Find Optimal Path* |
| DFS Exploration | Panel kiri → *Algorithms → Run DFS* |
| Tampilkan History | Panel kanan → *Data Snapshots → History* |
| Load Graph dari CSV | Panel kiri → *Data Source → Load CSV* |
| Batch Query + Export | Panel kiri → *Algorithms → Run Batch Query + Save Result* |
| Export History | Panel kiri → *Algorithms → Export History CSV* |

---

## 7. Format CSV

### nodes.csv

```csv
name
Jakarta Kota
Bogor
Depok
```

Kolom wajib: **`name`**

### edges.csv

```csv
from,to,distance,time
Jakarta Kota,Jayakarta,1.5,3
Jayakarta,Mangga Besar,1.0,2
```

Kolom wajib: **`from`**, **`to`**
Kolom opsional: `distance` (default 1.0), `time` (default 1.0)
Edge bersifat **bidirectional** — satu baris menciptakan dua arah.

### query.csv

```csv
start,end
Jakarta Kota,Bogor
Depok,Bekasi
```

Kolom wajib: **`start`**, **`end`**

### result.csv (output)

```csv
start,end,path,distance,time
Jakarta Kota,Bogor,Jakarta Kota-Jayakarta-...-Bogor,50.5,86.0
```

### history.csv (output)

```csv
no,path
1,Jakarta Kota-Jayakarta-...-Bogor
```

---

## 8. Fitur Visual Streamlit (tambahan dari CLI)

- Visualisasi graph interaktif (klik, zoom, drag node)
- Animasi step-by-step Dijkstra dan DFS
- Filter minimum degree
- Node detail panel (in/out degree, neighbors)
- Highlight mode: neighbors / path / custom selection
- Metrics: total nodes, edges, avg degree, weakly connected components

---

## 9. Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `krl/nodes.csv belum ada di folder data/` | Jalankan program dari direktori root project (yang mengandung folder `data/`) |
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `gcc: command not found` | Install gcc — lihat langkah 4.A.1 sesuai distro |
| `cl: command not found` | Windows: jalankan `.\c\init.ps1` untuk inisialisasi MSVC |
| Node/path tidak ditemukan di menu 4 | Pastikan graph sudah dimuat (menu 7) atau node sudah ditambahkan (menu 1) |
| Batch query hasil kosong | Cek `data/query.csv` — node start/end harus ada di graph yang sudah dimuat |
| `fatal error C1034: algorithm: no include path set` | Jalankan `.\c\init.ps1` sebelum compile |

---

## 10. Testing

```bash
./run.sh test
# atau: uv run python -m unittest discover -s tests -v
```
