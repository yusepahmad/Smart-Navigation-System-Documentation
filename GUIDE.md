# GUIDE — Smart Navigation System

## 1. Setup Python

```bash
pip install -r requirements.txt
```

Jika memakai virtualenv:

```bash
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

---

## 2. Menjalankan Python CLI

```bash
python main.py
```

---

## 3. Menjalankan Streamlit UI

```bash
streamlit run streamlit_app.py
```

Streamlit membuka browser otomatis. Semua fitur CLI tersedia di panel kiri,
visualisasi graph interaktif di panel kanan.

---

## 4. Setup & Menjalankan C++ CLI

### 4.1 Inisialisasi environment MSVC

Jalankan sekali per sesi terminal PowerShell:

```powershell
.\init.ps1
```

Script ini mengimpor variabel environment dari `vcvarsall.bat x64` ke sesi
PowerShell yang sedang berjalan, sehingga `cl` dan `link` tersedia langsung.

### 4.2 Compile

```powershell
cl /std:c++17 /EHsc /O2 /Fe:cli_app.exe cli_app.cpp
```

### 4.3 Jalankan

```powershell
.\cli_app.exe
```

Program mendeteksi otomatis apakah folder `data/` ada di direktori saat ini
atau di subdirektori `Smart-Navigation-System-Documentation/`, sehingga bisa
dijalankan dari `CODE\` maupun dari dalam folder repo.

---

## 5. Menu CLI (Python & C++ identik)

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
| `krl/nodes.csv belum ada di folder data/` | Jalankan program dari direktori yang mengandung folder `data/`, atau gunakan menu 7 dan ketik path relatif yang benar |
| `cl: command not found` | Jalankan `.\init.ps1` terlebih dahulu untuk inisialisasi MSVC |
| Node/path tidak ditemukan di menu 4 | Pastikan graph sudah dimuat (menu 7) atau node sudah ditambahkan (menu 1) |
| Batch query hasil kosong | Cek `data/query.csv` — node start/end harus ada di graph yang sudah dimuat |
| `fatal error C1034: algorithm: no include path set` | Jalankan `.\init.ps1` sebelum compile |

---

## 10. Testing

```bash
python -m unittest discover -s tests -v
```
