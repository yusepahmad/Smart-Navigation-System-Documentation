# GUIDE - Streamlit UI (Parity dengan CLI)

## 1. Setup

```bash
pip install -r requirements.txt
```

Jika kamu pakai virtualenv lokal:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Jalankan Streamlit

```bash
streamlit run streamlit_app.py
```

## 3. Struktur Halaman Streamlit

- **Tab 1: CLI Features in UI**
  - Seluruh fitur yang ada di CLI.
- **Tab 2: Graph Dashboard**
  - Fokus visualisasi graph dan insight.

## 4. Mapping Fitur CLI ke Streamlit

1. Tambah Node
- Form `Tambah Node` di tab **CLI Features in UI**.

2. Tambah Edge
- Form `Tambah Edge` di tab **CLI Features in UI**.

3. Tampilkan Graph
- Section `Tampilkan Graph (Adjacency List)`.

4. BFS Shortest Path (Manual)
- Form `BFS Shortest Path (Manual)`.
- Hasil sukses otomatis masuk ke history dan result in-memory.

5. DFS Exploration
- Form `DFS Exploration`.

6. Tampilkan History
- Section `Tampilkan History` (dataframe).

7. Load Graph dari CSV
- Tombol sidebar `Load Graph dari CSV`.

8. Batch Query dari CSV + Export Result
- Tombol `Jalankan Batch Query`.
- Membaca `query.csv` dan langsung simpan ke `result.csv`.

9. Export History
- Tombol `Export History CSV`.

## 5. Fitur Visual Tambahan (UI-first)

- Graph interaktif menggunakan Pyvis:
  - hover, zoom, drag node
- Filter minimum degree
- Node selector untuk detail relasi
- Highlight mode:
  - `all edges`
  - `neighbors only`
  - `path from result.csv`

## 6. Format CSV

- `data/nodes.csv` kolom: `id,name`
- `data/edges.csv` kolom: `from,to`
- `data/query.csv` kolom: `start,end`
- `output/result.csv` kolom: `start,end,path,distance`
- `output/history.csv` kolom: `no,path`

## 7. Testing

```bash
python -m unittest discover -s tests -v
```

## 8. Troubleshooting

- Node/path tidak ditemukan:
  - Pastikan graph sudah dimuat atau node sudah ditambahkan.
- Batch query kosong:
  - Cek `data/query.csv` dan pastikan node start/end ada di graph.
- Highlight path tidak aktif:
  - Pastikan `result.csv` punya kolom `path` dengan format `A-B-C`.
