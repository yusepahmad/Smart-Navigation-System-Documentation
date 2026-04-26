# 📘 Smart Navigation System Documentation (Python Version)

**Explorer + Shortest Path + History – Python Implementation**

---

## 1. 📌 Overview

Smart Navigation System adalah sistem simulasi navigasi berbasis **graph** yang menyediakan:

* 🔍 Pencarian jalur tercepat (**BFS**)
* 🌐 Eksplorasi seluruh node (**DFS**)
* 🧾 Penyimpanan riwayat perjalanan (**Stack / History**)
* 📂 Dukungan input/output berbasis **CSV**

---

## 2. 🧠 Arsitektur Sistem

### 2.1 Representasi Graph

Graph direpresentasikan menggunakan:

* **Adjacency List (dictionary)**
* Node berupa string (`A, B, C, ...`)

Contoh:

```
A -- B -- C
|    |
D -- E
```

---

### 2.2 Struktur Data

#### Graph

```python
class Graph:
    def __init__(self):
        self.adj = {}
```

#### Queue (BFS)

```python
from collections import deque
queue = deque()
```

#### Stack (DFS & History)

```python
stack = []
```

---

## 3. ⚙️ Fitur Sistem

| No | Fitur           | Deskripsi                       |
| -- | --------------- | ------------------------------- |
| 1  | Tambah Node     | Menambahkan lokasi              |
| 2  | Tambah Edge     | Menambahkan koneksi antar node  |
| 3  | Tampilkan Graph | Melihat adjacency list          |
| 4  | BFS             | Mencari jalur tercepat          |
| 5  | DFS             | Eksplorasi graph                |
| 6  | History         | Riwayat path yang pernah dicari |
| 7  | CSV Support     | Load & save data                |

---

## 4. 🔄 Algoritma

---

### 4.1 BFS (Shortest Path)

Digunakan untuk mencari jalur tercepat berdasarkan jumlah edge.

#### Flow:

1. Masukkan start node ke queue
2. Tandai visited
3. Simpan parent
4. Stop saat tujuan ditemukan
5. Rekonstruksi path

#### Implementasi:

```python
from collections import deque

def bfs_shortest_path(graph, start, end):
    visited = set()
    queue = deque()
    parent = {}

    queue.append(start)
    visited.add(start)
    parent[start] = None

    while queue:
        current = queue.popleft()

        if current == end:
            break

        for neighbor in graph.adj[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = current
                queue.append(neighbor)

    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)

    path.reverse()

    return path if path and path[0] == start else []
```

---

### 4.2 DFS (Exploration)

Digunakan untuk eksplorasi seluruh graph.

#### Flow:

1. Push node ke stack
2. Pop node
3. Tandai visited
4. Push neighbors

#### Implementasi:

```python
def dfs(graph, start):
    visited = set()
    stack = [start]
    result = []

    while stack:
        node = stack.pop()

        if node not in visited:
            visited.add(node)
            result.append(node)

            for neighbor in reversed(graph.adj[node]):
                if neighbor not in visited:
                    stack.append(neighbor)

    return result
```

---

### 4.3 History (Stack)

Digunakan untuk menyimpan riwayat path.

```python
class History:
    def __init__(self):
        self.stack = []

    def push(self, path):
        self.stack.append(path)

    def show(self):
        for i, p in enumerate(self.stack, 1):
            print(f"{i}. {'-'.join(p)}")
```

---

## 5. 💻 Implementasi Graph

```python
class Graph:
    def __init__(self):
        self.adj = {}

    def add_node(self, node):
        if node not in self.adj:
            self.adj[node] = []

    def add_edge(self, u, v):
        self.add_node(u)
        self.add_node(v)
        self.adj[u].append(v)
        self.adj[v].append(u)

    def show(self):
        for node in self.adj:
            print(node, "->", self.adj[node])
```

---

## 6. 📊 Format Data (Excel & CSV)

---

### 6.1 Nodes

| id | name |
| -- | ---- |
| 0  | A    |
| 1  | B    |
| 2  | C    |
| 3  | D    |
| 4  | E    |

```csv
id,name
0,A
1,B
2,C
3,D
4,E
```

---

### 6.2 Edges

| from | to |
| ---- | -- |
| A    | B  |
| A    | D  |
| B    | C  |
| B    | E  |
| D    | E  |

```csv
from,to
A,B
A,D
B,C
B,E
D,E
```

---

### 6.3 Query

| start | end |
| ----- | --- |
| A     | E   |
| C     | D   |

```csv
start,end
A,E
C,D
```

---

### 6.4 Result

| start | end | path    | distance |
| ----- | --- | ------- | -------- |
| A     | E   | A-B-E   | 2        |
| C     | D   | C-B-A-D | 3        |

---

### 6.5 History

| no | path    |
| -- | ------- |
| 1  | A-B-E   |
| 2  | C-B-A-D |

---

## 7. 📂 Load Data dari CSV

```python
import csv

def load_graph(nodes_file, edges_file):
    g = Graph()

    with open(nodes_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.add_node(row['name'])

    with open(edges_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.add_edge(row['from'], row['to'])

    return g
```

---

## 8. 📤 Export Result ke CSV

```python
def save_result(filename, data):
    import csv

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['start', 'end', 'path', 'distance'])

        for row in data:
            writer.writerow([
                row['start'],
                row['end'],
                '-'.join(row['path']),
                len(row['path']) - 1
            ])
```

---

## 9. ▶️ Contoh Output Program

```
Shortest Path A → E:
A → B → E

DFS Exploration:
A → D → E → B → C

History:
1. A-B-E
2. C-B-A-D
```

---

## 10. 📦 Struktur Project

```
project/
│
├── main.py
├── graph.py
├── algorithms.py
├── history.py
│
├── data/
│   ├── nodes.csv
│   ├── edges.csv
│   └── query.csv
│
└── output/
    ├── result.csv
    └── history.csv
```

---

## 11. 🚀 Improvement (Advanced)

### 🔥 Pengembangan lanjut:

* ✅ Weighted Graph → Dijkstra (`heapq`)
* ✅ API → FastAPI (cocok dengan stack kamu)
* ✅ Visualisasi → networkx + matplotlib
* ✅ Streaming data → SSE
* ✅ Integrasi crawling graph (social media network)

---

## 12. 🧠 Insight Penting

Kenapa BFS untuk shortest path?

> Karena BFS mengeksplorasi graph per level, sehingga jalur pertama yang ditemukan adalah jalur dengan jumlah edge paling sedikit.

---

## 13. 📌 Perbandingan C vs Python

| Aspek           | C            | Python          |
| --------------- | ------------ | --------------- |
| Struktur data   | Array manual | dict + list     |
| Queue           | Manual       | deque           |
| Stack           | Manual       | list            |
| Complexity code | Tinggi       | Lebih sederhana |
| Scalability     | Rendah       | Tinggi          |

---

## 14. 📌 Kesimpulan

Sistem ini menggabungkan:

* Graph → representasi relasi
* BFS → pencarian jalur tercepat
* DFS → eksplorasi
* Stack → penyimpanan history