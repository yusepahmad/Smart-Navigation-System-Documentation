# Smart Navigation System

Smart Navigation System menyediakan dua antarmuka:
- CLI OOP (`python main.py`)
- Streamlit UI interaktif (`streamlit run streamlit_app.py`)

Saat ini fitur Streamlit sudah parity dengan fitur CLI, ditambah visualisasi graph interaktif.

## Fitur Utama di Streamlit

- Semua fitur CLI tersedia di tab **CLI Features in UI**:
  - Tambah node
  - Tambah edge
  - Tampilkan graph (adjacency list)
  - BFS shortest path manual
  - DFS exploration
  - Tampilkan history
  - Load graph dari CSV
  - Batch query + export result
  - Export history
- Tab **Graph Dashboard**:
  - Visualisasi graph interaktif (hover, zoom, drag)
  - Metrics cards (nodes, edges, avg degree, connected components)
  - Sidebar filter (`minimum degree`, node selector, highlight mode)
  - Node detail panel
  - Expandable data explorer (query/result/history)

## Struktur Project (Ringkas)

```text
project-akhir/
├── main.py
├── streamlit_app.py
├── requirements.txt
├── data/
├── output/
├── smart_navigation/
├── ui/
│   ├── graph_builder.py
│   └── components.py
└── tests/
```

## Setup

```bash
pip install -r requirements.txt
```

## Menjalankan Streamlit UI

```bash
streamlit run streamlit_app.py
```

## Menjalankan CLI

```bash
python main.py
```

## Menjalankan Test

```bash
python -m unittest discover -s tests -v
```

## Dokumentasi Detail

Lihat [GUIDE.md](GUIDE.md).
