# Smart Navigation System — Dokumentasi Teknis

**Weighted Graph + Dijkstra + DFS + History**
Tersedia dalam dua bahasa: Python (CLI & Streamlit) dan C++ (CLI)

---

## 1. Overview

Smart Navigation System adalah sistem simulasi navigasi berbasis **weighted graph** yang menyediakan:

- Pencarian jalur optimal berdasarkan jarak atau waktu tempuh (**Dijkstra**)
- Eksplorasi seluruh node (**DFS iteratif**)
- Penyimpanan riwayat perjalanan (**Stack / History**)
- Input/output berbasis **CSV**
- Antarmuka **CLI** (Python & C++) dan **Streamlit UI** (Python)

---

## 2. Arsitektur Sistem

### 2.1 Representasi Graph

Graph direpresentasikan menggunakan **Adjacency List berbobot** (undirected / bidirectional).
Setiap edge menyimpan dua bobot: `distance` (km) dan `time` (menit).

```
Jakarta Kota --[d:1.5, t:3]--> Jayakarta --[d:1.0, t:2]--> Mangga Besar
                                    |
                              (bidirectional)
```

### 2.2 Struktur Data

| Struktur | Digunakan Untuk | Python | C++ |
|----------|----------------|--------|-----|
| Adjacency List | Representasi graph | `dict[str, dict[str, dict]]` | `std::map<string, map<string, EdgeData>>` |
| Min-Heap (Priority Queue) | Dijkstra | `heapq` | `std::priority_queue` (min) |
| Stack | DFS & History | `list` | `std::vector` |
| Parent Map | Rekonstruksi path | `dict` | `std::unordered_map` |

---

## 3. Fitur Sistem

| No | Fitur | Deskripsi |
|----|-------|-----------|
| 1 | Tambah Node | Menambahkan lokasi ke graph |
| 2 | Tambah Edge | Koneksi bidirectional dengan distance & time |
| 3 | Tampilkan Graph | Adjacency list terurut dengan bobot |
| 4 | Find Optimal Path | Dijkstra, pilih optimasi by distance atau time |
| 5 | DFS Exploration | Eksplorasi semua node dari titik awal |
| 6 | History | Riwayat semua path yang pernah ditemukan |
| 7 | Load CSV | Muat graph dari file nodes.csv + edges.csv |
| 8 | Batch Query | Proses banyak pasang (start, end) sekaligus |
| 9 | Export | Simpan result.csv dan history.csv |

---

## 4. Algoritma

### 4.1 Dijkstra (Find Optimal Path)

Mencari jalur dengan **total bobot minimum** dari node asal ke tujuan.
Bobot yang dioptimasi dipilih oleh user: `distance` atau `time`.

#### Flow

1. Masukkan `(0, start)` ke priority queue (min-heap)
2. Inisialisasi `min_weights[start] = 0`, semua lain = ∞
3. Simpan `parent[start] = None`
4. Loop — pop item dengan bobot terkecil:
   - Jika node == tujuan → stop
   - Skip jika bobot yang di-pop lebih besar dari `min_weights[node]` (stale entry)
   - Untuk setiap tetangga: hitung `new_weight = current + edge_weight`
   - Jika `new_weight < min_weights[neighbor]` → update dan push ke heap
5. Rekonstruksi path dari tujuan ke awal via `parent`, lalu reverse

#### Kompleksitas

| | Nilai |
|--|--|
| Waktu | O((V + E) log V) |
| Ruang | O(V) |

#### Implementasi Python

```python
import heapq

def find_optimal_path(graph, start, end, optimize_by="distance"):
    pq = [(0.0, start)]
    min_weights = {start: 0.0}
    parent = {start: None}   # start: None = sentinel

    while pq:
        current_weight, current = heapq.heappop(pq)

        if current == end:
            break
        if current_weight > min_weights.get(current, float('inf')):
            continue

        for neighbor in graph.neighbors(current):
            edge_data = graph.get_edge_data(current, neighbor)
            edge_weight = edge_data.get(optimize_by, 1.0)
            new_weight = current_weight + edge_weight

            if new_weight < min_weights.get(neighbor, float('inf')):
                min_weights[neighbor] = new_weight
                parent[neighbor] = (current,
                                    edge_data['distance'],
                                    edge_data['time'])
                heapq.heappush(pq, (new_weight, neighbor))

    if end not in parent:
        return [], 0.0, 0.0

    # Rekonstruksi path
    path, total_dist, total_time = [], 0.0, 0.0
    cur = end
    while cur is not None:
        path.append(cur)
        info = parent[cur]
        if info is not None:
            p_node, d, t = info
            total_dist += d
            total_time += t
            cur = p_node
        else:
            cur = None

    path.reverse()
    return path, round(total_dist, 1), round(total_time, 1)
```

#### Implementasi C++

```cpp
std::tuple<std::vector<std::string>, double, double>
find_optimal_path(const Graph& graph, const std::string& start,
                  const std::string& end,
                  const std::string& optimize_by = "distance") const
{
    using Item = std::pair<double, std::string>;
    std::priority_queue<Item, std::vector<Item>, std::greater<Item>> pq;

    std::unordered_map<std::string, double> min_w;
    struct ParentInfo { std::string node; double dist; double time; };
    std::unordered_map<std::string, ParentInfo> parent;

    min_w[start] = 0.0;
    parent[start] = {"", 0.0, 0.0};   // sentinel
    pq.push({0.0, start});

    while (!pq.empty()) {
        auto [w, cur] = pq.top(); pq.pop();
        if (cur == end) break;
        if (w > min_w[cur]) continue;

        for (const auto& nbr : graph.neighbors(cur)) {
            const EdgeData& ed = graph.get_edge_data(cur, nbr);
            double ew = (optimize_by == "time") ? ed.time_val : ed.distance;
            double nw = w + ew;
            if (!min_w.count(nbr) || nw < min_w[nbr]) {
                min_w[nbr] = nw;
                parent[nbr] = {cur, ed.distance, ed.time_val};
                pq.push({nw, nbr});
            }
        }
    }

    if (!parent.count(end)) return {{}, 0.0, 0.0};

    std::vector<std::string> path;
    double total_dist = 0.0, total_time = 0.0;
    std::string cur = end;
    while (true) {
        path.push_back(cur);
        const ParentInfo& pi = parent.at(cur);
        if (pi.node.empty()) break;
        total_dist += pi.dist;
        total_time += pi.time;
        cur = pi.node;
    }
    std::reverse(path.begin(), path.end());
    return {path, round1(total_dist), round1(total_time)};
}
```

---

### 4.2 DFS (Exploration)

Eksplorasi iteratif dari node awal menggunakan stack eksplisit.
Tetangga di-push dalam urutan terbalik agar urutan kunjungan konsisten (kiri ke kanan).

#### Flow

1. Push `start` ke stack
2. Pop node → skip jika sudah visited
3. Tandai visited, tambahkan ke result
4. Push semua tetangga yang belum visited (dalam urutan terbalik)
5. Ulangi sampai stack kosong

#### Implementasi Python

```python
def dfs_exploration(graph, start):
    if not graph.has_node(start):
        return []

    visited = set()
    stack = [start]
    result = []

    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        result.append(node)

        for neighbor in reversed(graph.neighbors(node)):
            if neighbor not in visited:
                stack.append(neighbor)

    return result
```

#### Implementasi C++

```cpp
std::vector<std::string> dfs_exploration(const Graph& graph,
                                          const std::string& start) const
{
    if (!graph.has_node(start)) return {};

    std::unordered_set<std::string> visited;
    std::vector<std::string> stack, result;
    stack.push_back(start);

    while (!stack.empty()) {
        std::string node = stack.back(); stack.pop_back();
        if (visited.count(node)) continue;
        visited.insert(node);
        result.push_back(node);

        auto nbrs = graph.neighbors(node);
        for (auto it = nbrs.rbegin(); it != nbrs.rend(); ++it)
            if (!visited.count(*it)) stack.push_back(*it);
    }
    return result;
}
```

---

### 4.3 History (Stack)

Menyimpan setiap path yang berhasil ditemukan secara berurutan (LIFO display).

#### Python

```python
class History:
    def __init__(self):
        self._stack = []

    def push(self, path):
        if path:
            self._stack.append(path)

    def to_display_string(self):
        return "\n".join(
            f"{i}. {'-'.join(p)}"
            for i, p in enumerate(self._stack, 1)
        ) or "(history kosong)"
```

#### C++

```cpp
class History {
public:
    std::vector<std::vector<std::string>> stack;

    void push(const std::vector<std::string>& path) {
        if (!path.empty()) stack.push_back(path);
    }

    void display() const {
        if (stack.empty()) { std::cout << "(history kosong)\n"; return; }
        for (size_t i = 0; i < stack.size(); ++i) {
            std::cout << (i + 1) << ". ";
            for (size_t j = 0; j < stack[i].size(); ++j) {
                if (j) std::cout << '-';
                std::cout << stack[i][j];
            }
            std::cout << '\n';
        }
    }
};
```

---

## 5. Implementasi Graph

### Python

```python
class Graph:
    def __init__(self):
        self.adj = {}   # dict[str, dict[str, dict[str, float]]]

    def add_node(self, node):
        node = node.strip()
        if node and node not in self.adj:
            self.adj[node] = {}

    def add_edge(self, source, target, distance=1.0, time=1.0):
        self.add_node(source)
        self.add_node(target)
        self.adj[source][target] = {"distance": distance, "time": time}
        self.adj[target][source] = {"distance": distance, "time": time}

    def has_node(self, node):
        return node in self.adj

    def neighbors(self, node):
        return list(self.adj.get(node, {}).keys())

    def get_edge_data(self, source, target):
        return self.adj.get(source, {}).get(target, {"distance": 1.0, "time": 1.0})
```

### C++

```cpp
struct EdgeData { double distance = 1.0; double time_val = 1.0; };

class Graph {
public:
    std::map<std::string, std::map<std::string, EdgeData>> adj;

    void add_node(const std::string& raw) {
        std::string node = trim(raw);
        if (!node.empty() && !adj.count(node)) adj[node] = {};
    }

    void add_edge(const std::string& src, const std::string& tgt,
                  double distance = 1.0, double time_val = 1.0) {
        add_node(src); add_node(tgt);
        adj[src][tgt] = {distance, time_val};
        adj[tgt][src] = {distance, time_val};   // bidirectional
    }

    bool has_node(const std::string& node) const { return adj.count(node) > 0; }
    EdgeData get_edge_data(const std::string& src, const std::string& tgt) const { ... }
};
```

---

## 6. Format Data CSV

### nodes.csv

| name |
|------|
| Jakarta Kota |
| Bogor |

```csv
name
Jakarta Kota
Bogor
```

### edges.csv

| from | to | distance | time |
|------|----|----------|------|
| Jakarta Kota | Jayakarta | 1.5 | 3 |
| Jayakarta | Mangga Besar | 1.0 | 2 |

```csv
from,to,distance,time
Jakarta Kota,Jayakarta,1.5,3
Jayakarta,Mangga Besar,1.0,2
```

Edge bersifat **bidirectional** — satu baris di CSV menciptakan dua arah.
Jika kolom `distance`/`time` tidak ada, default 1.0.

### query.csv

| start | end |
|-------|-----|
| Jakarta Kota | Bogor |

```csv
start,end
Jakarta Kota,Bogor
```

### result.csv (output)

| start | end | path | distance | time |
|-------|-----|------|----------|------|
| Jakarta Kota | Bogor | Jakarta Kota-Jayakarta-...-Bogor | 50.5 | 86.0 |

### history.csv (output)

| no | path |
|----|------|
| 1 | Jakarta Kota-Jayakarta-...-Bogor |

---

## 7. Load & Save CSV

### Load Graph (Python)

```python
class CsvRepository:
    def load_graph(self, nodes_file, edges_file):
        graph = Graph()
        with open(nodes_file, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                graph.add_node(row.get("name", ""))

        with open(edges_file, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dist = float(row.get("distance", 1.0))
                time = float(row.get("time", 1.0))
                graph.add_edge(row["from"], row["to"], dist, time)
        return graph
```

### Save Result (Python)

```python
def save_result(self, filename, data):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end", "path", "distance", "time"])
        for r in data:
            writer.writerow([r.start, r.end, "-".join(r.path),
                             r.total_distance, r.total_time])
```

---

## 8. Contoh Output Program

```
=== Smart Navigation System ===
Start node: Jakarta Kota
End node: Bogor
Optimize by (1) Distance or (2) Time [default: 1]: 1

Optimal path (distance):
Jakarta Kota --(1.5)--> Jayakarta --(1.0)--> Mangga Besar --(1.2)-->
... --(4.2)--> Bogor
Total Distance: 50.5
Total Time: 86.0
```

```
DFS exploration:
Jakarta Kota -> Jayakarta -> Mangga Besar -> Sawah Besar -> ...
```

```
History:
1. Jakarta Kota-Jayakarta-...-Bogor
```

---

## 9. Struktur Project

```
Smart-Navigation-System-Documentation/
├── main.py
├── streamlit_app.py
├── cli_app.cpp              # C++ CLI source
├── requirements.txt
├── data/
│   ├── krl/
│   │   ├── nodes.csv
│   │   └── edges.csv
│   ├── nodes.csv
│   ├── edges.csv
│   └── query.csv
├── output/
│   ├── result.csv
│   └── history.csv
├── smart_navigation/
│   ├── cli/app.py           # SmartNavigationCLI
│   ├── core/graph.py        # Graph class
│   ├── core/history.py      # History class
│   ├── services/navigation_service.py   # Dijkstra + DFS
│   ├── io/csv_repository.py # Load/save CSV
│   └── models/query_result.py
└── tests/
```

---

## 10. Compile & Jalankan C++ CLI

### Prasyarat (Windows)

Visual Studio Build Tools 2022 dengan komponen "Desktop development with C++".

### Inisialisasi environment (sekali per sesi terminal)

```powershell
.\init.ps1
```

### Compile

```powershell
cl /std:c++17 /EHsc /O2 /Fe:cli_app.exe cli_app.cpp
```

### Jalankan

```powershell
.\cli_app.exe
```

Program mendeteksi otomatis folder `data/` — bisa dijalankan dari `CODE\`
maupun dari dalam direktori repo.

---

## 11. Perbandingan Python vs C++

| Aspek | Python | C++ |
|-------|--------|-----|
| Struktur data graph | `dict` nested | `std::map` nested |
| Priority queue | `heapq` (min-heap) | `std::priority_queue` + `std::greater` |
| Stack DFS | `list` | `std::vector` |
| String handling | Native, dinamis | `std::string`, manual trim |
| CSV I/O | `csv.DictReader/Writer` | `std::ifstream` + manual split |
| Weighted edge | `dict` per edge | `struct EdgeData` |
| Path reconstruction | `dict` parent + backtrack | `unordered_map<string, ParentInfo>` |
| Eksekusi | Interpreter, lambat | Compiled, cepat |
| Kompleksitas kode | Lebih sederhana | Lebih verbose |
| Portabilitas build | `pip install` | Butuh compiler + env setup |

---

## 12. Kesimpulan

Sistem ini menggabungkan:

- **Graph berbobot** → representasi relasi antar lokasi dengan jarak dan waktu
- **Dijkstra** → pencarian jalur optimal berdasarkan total bobot minimum
- **DFS** → eksplorasi menyeluruh dari titik awal
- **Stack / History** → penyimpanan riwayat pencarian
- **CSV I/O** → persistensi data yang portabel
- **Tiga antarmuka** → Python CLI, Streamlit UI, dan C++ CLI dengan logika yang identik
