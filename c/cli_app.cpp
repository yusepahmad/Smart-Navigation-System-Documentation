/*
 * Smart Navigation System - C++ CLI
 * Full port of the Python implementation (smart_navigation package).
 *
 * Graph  : undirected weighted adjacency list (distance + time per edge)
 * Algorithms : Dijkstra (optimal path) and iterative DFS (exploration)
 * Persistence: CSV load/save matching the Python CsvRepository format
 *
 * Compile (C++17):
 *   Windows : g++ -std=c++17 -O2 -o cli_app cli_app.cpp
 *   Linux   : g++ -std=c++17 -O2 -o cli_app cli_app.cpp
 *
 * Run from the Smart-Navigation-System-Documentation directory so that
 * the relative paths  data/  and  output/  resolve correctly.
 */

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <sstream>
#include <stdexcept>
#include <string>
#include <sys/stat.h>
#include <tuple>
#include <unordered_map>
#include <unordered_set>
#include <vector>

#ifdef _WIN32
#  include <direct.h>
#  define MAKE_DIR(p) _mkdir(p)
#else
#  include <sys/stat.h>
#  define MAKE_DIR(p) mkdir((p), 0755)
#endif

// ============================================================
// Utility
// ============================================================

static std::string trim(const std::string& s) {
    size_t a = 0, b = s.size();
    while (a < b && (unsigned char)s[a] <= ' ') ++a;
    while (b > a && (unsigned char)s[b - 1] <= ' ') --b;
    return s.substr(a, b - a);
}

static std::string format_double(double v) {
    char buf[32];
    std::snprintf(buf, sizeof(buf), "%.1f", v);
    return buf;
}

static double round1(double v) {
    return std::round(v * 10.0) / 10.0;
}

// Split a CSV line by commas (no quoted-field support needed for this dataset).
static std::vector<std::string> split_csv(const std::string& line) {
    std::vector<std::string> out;
    std::stringstream ss(line);
    std::string tok;
    while (std::getline(ss, tok, ','))
        out.push_back(trim(tok));
    return out;
}

static void ensure_dir(const std::string& path) {
    MAKE_DIR(path.c_str());
}

// ============================================================
// Graph
// ============================================================

struct EdgeData {
    double distance = 1.0;
    double time_val = 1.0;
};

class Graph {
public:
    // adj[node][neighbor] = EdgeData
    // std::map keeps keys in sorted order (used for deterministic display).
    std::map<std::string, std::map<std::string, EdgeData>> adj;

    void add_node(const std::string& raw) {
        std::string node = trim(raw);
        if (node.empty()) return;
        if (!adj.count(node)) adj[node] = {};
    }

    void add_edge(const std::string& raw_src, const std::string& raw_tgt,
                  double distance = 1.0, double time_val = 1.0) {
        std::string src = trim(raw_src);
        std::string tgt = trim(raw_tgt);
        if (src.empty() || tgt.empty()) return;

        add_node(src);
        add_node(tgt);

        adj[src][tgt] = {distance, time_val};
        adj[tgt][src] = {distance, time_val};   // undirected / bidirectional
    }

    bool has_node(const std::string& node) const {
        return adj.count(node) > 0;
    }

    // Returns neighbors in insertion/sorted order (matches map iteration).
    std::vector<std::string> neighbors(const std::string& node) const {
        auto it = adj.find(node);
        if (it == adj.end()) return {};
        std::vector<std::string> out;
        for (auto& kv : it->second) out.push_back(kv.first);
        return out;
    }

    EdgeData get_edge_data(const std::string& src, const std::string& tgt) const {
        auto si = adj.find(src);
        if (si == adj.end()) return {};
        auto ti = si->second.find(tgt);
        if (ti == si->second.end()) return {};
        return ti->second;
    }

    void display() const {
        if (adj.empty()) { std::cout << "(graph kosong)\n"; return; }
        for (auto& [node, nbrs] : adj) {
            std::cout << node << " -> [";
            bool first = true;
            for (auto& [nbr, ed] : nbrs) {
                if (!first) std::cout << ", ";
                std::cout << nbr << "(d:" << format_double(ed.distance)
                          << ", t:" << format_double(ed.time_val) << ")";
                first = false;
            }
            std::cout << "]\n";
        }
    }
};

// ============================================================
// QueryResult
// ============================================================

struct QueryResult {
    std::string start;
    std::string end_node;
    std::vector<std::string> path;
    double total_distance = 0.0;
    double total_time     = 0.0;
};

// ============================================================
// NavigationService  (Dijkstra + DFS)
// ============================================================

class NavigationService {
public:
    /*
     * Dijkstra's algorithm.
     * optimize_by: "distance" or "time"
     * Returns { path, total_distance, total_time }.
     * On failure returns { {}, 0.0, 0.0 }.
     */
    std::tuple<std::vector<std::string>, double, double>
    find_optimal_path(const Graph& graph,
                      const std::string& start,
                      const std::string& end,
                      const std::string& optimize_by = "distance") const
    {
        if (!graph.has_node(start) || !graph.has_node(end))
            return {{}, 0.0, 0.0};

        // (weight, node_name)
        using Item = std::pair<double, std::string>;
        std::priority_queue<Item, std::vector<Item>, std::greater<Item>> pq;

        std::unordered_map<std::string, double> min_w;

        // parent[node] = { parent_node, edge_distance, edge_time }
        // parent[start] = { "", 0, 0 }  <- sentinel: start has no parent
        struct ParentInfo { std::string node; double dist; double time; };
        std::unordered_map<std::string, ParentInfo> parent;

        min_w[start] = 0.0;
        parent[start] = {"", 0.0, 0.0};
        pq.push({0.0, start});

        while (!pq.empty()) {
            auto [w, cur] = pq.top(); pq.pop();

            if (cur == end) break;

            auto it = min_w.find(cur);
            if (it != min_w.end() && w > it->second) continue;

            for (const auto& nbr : graph.neighbors(cur)) {
                const EdgeData& ed = graph.get_edge_data(cur, nbr);
                double ew = (optimize_by == "time") ? ed.time_val : ed.distance;
                double nw = w + ew;

                auto nit = min_w.find(nbr);
                if (nit == min_w.end() || nw < nit->second) {
                    min_w[nbr] = nw;
                    parent[nbr] = {cur, ed.distance, ed.time_val};
                    pq.push({nw, nbr});
                }
            }
        }

        if (!parent.count(end)) return {{}, 0.0, 0.0};

        // Reconstruct path from end → start, then reverse.
        std::vector<std::string> path;
        double total_dist = 0.0, total_time = 0.0;

        std::string cur = end;
        while (true) {
            path.push_back(cur);
            const ParentInfo& pi = parent.at(cur);
            if (pi.node.empty()) break;          // reached start sentinel
            total_dist += pi.dist;
            total_time += pi.time;
            cur = pi.node;
        }
        std::reverse(path.begin(), path.end());

        return {path, round1(total_dist), round1(total_time)};
    }

    /*
     * Iterative DFS exploration from start.
     * Neighbours are pushed in reverse order so they are visited
     * left-to-right (same behaviour as the Python implementation).
     */
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
};

// ============================================================
// History
// ============================================================

class History {
public:
    std::vector<std::vector<std::string>> stack;

    void push(const std::vector<std::string>& path) {
        if (!path.empty()) stack.push_back(path);
    }

    void clear() { stack.clear(); }

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

// ============================================================
// CsvRepository
// ============================================================

class CsvRepository {
public:
    Graph load_graph(const std::string& nodes_file,
                     const std::string& edges_file) const
    {
        Graph graph;

        // --- nodes ---
        std::ifstream nf(nodes_file);
        if (!nf) { std::cout << "Tidak bisa membuka: " << nodes_file << '\n'; return graph; }

        std::string line;
        if (!std::getline(nf, line)) return graph;
        auto hdr = split_csv(line);

        int name_col = -1;
        for (int i = 0; i < (int)hdr.size(); ++i)
            if (hdr[i] == "name") { name_col = i; break; }

        if (name_col < 0) {
            std::cout << "nodes.csv wajib punya kolom 'name'.\n";
            return graph;
        }

        while (std::getline(nf, line)) {
            auto f = split_csv(line);
            if ((int)f.size() > name_col && !f[name_col].empty())
                graph.add_node(f[name_col]);
        }

        // --- edges ---
        std::ifstream ef(edges_file);
        if (!ef) { std::cout << "Tidak bisa membuka: " << edges_file << '\n'; return graph; }

        if (!std::getline(ef, line)) return graph;
        hdr = split_csv(line);

        int from_col = -1, to_col = -1, dist_col = -1, time_col = -1;
        for (int i = 0; i < (int)hdr.size(); ++i) {
            if      (hdr[i] == "from")     from_col = i;
            else if (hdr[i] == "to")       to_col   = i;
            else if (hdr[i] == "distance") dist_col = i;
            else if (hdr[i] == "time")     time_col = i;
        }

        if (from_col < 0 || to_col < 0) {
            std::cout << "edges.csv wajib punya kolom 'from' dan 'to'.\n";
            return graph;
        }

        while (std::getline(ef, line)) {
            auto f = split_csv(line);
            int n = (int)f.size();
            if (n <= to_col) continue;

            std::string src = f[from_col];
            std::string tgt = f[to_col];
            if (src.empty() || tgt.empty()) continue;

            double dist     = (dist_col >= 0 && n > dist_col && !f[dist_col].empty())
                                  ? std::stod(f[dist_col]) : 1.0;
            double time_val = (time_col >= 0 && n > time_col && !f[time_col].empty())
                                  ? std::stod(f[time_col]) : 1.0;

            graph.add_edge(src, tgt, dist, time_val);
        }

        return graph;
    }

    std::vector<std::pair<std::string, std::string>>
    load_queries(const std::string& query_file) const
    {
        std::vector<std::pair<std::string, std::string>> queries;

        std::ifstream f(query_file);
        if (!f) { std::cout << "Tidak bisa membuka: " << query_file << '\n'; return queries; }

        std::string line;
        if (!std::getline(f, line)) return queries;
        auto hdr = split_csv(line);

        int start_col = -1, end_col = -1;
        for (int i = 0; i < (int)hdr.size(); ++i) {
            if      (hdr[i] == "start") start_col = i;
            else if (hdr[i] == "end")   end_col   = i;
        }

        if (start_col < 0 || end_col < 0) {
            std::cout << "query.csv wajib punya kolom 'start' dan 'end'.\n";
            return queries;
        }

        while (std::getline(f, line)) {
            auto flds = split_csv(line);
            int n = (int)flds.size();
            if (n <= end_col) continue;

            std::string s = flds[start_col];
            std::string e = flds[end_col];
            if (!s.empty() && !e.empty())
                queries.push_back({s, e});
        }
        return queries;
    }

    void save_result(const std::string& filename,
                     const std::vector<QueryResult>& results) const
    {
        std::ofstream f(filename);
        if (!f) { std::cout << "Tidak bisa menulis ke: " << filename << '\n'; return; }

        f << "start,end,path,distance,time\n";
        for (const auto& r : results) {
            f << r.start << ',' << r.end_node << ',';
            for (size_t i = 0; i < r.path.size(); ++i) {
                if (i) f << '-';
                f << r.path[i];
            }
            f << ',' << format_double(r.total_distance)
              << ',' << format_double(r.total_time) << '\n';
        }
    }

    void save_history(const std::string& filename,
                      const std::vector<std::vector<std::string>>& history_stack) const
    {
        std::ofstream f(filename);
        if (!f) { std::cout << "Tidak bisa menulis ke: " << filename << '\n'; return; }

        f << "no,path\n";
        for (size_t i = 0; i < history_stack.size(); ++i) {
            f << (i + 1) << ',';
            for (size_t j = 0; j < history_stack[i].size(); ++j) {
                if (j) f << '-';
                f << history_stack[i][j];
            }
            f << '\n';
        }
    }
};

// ============================================================
// SmartNavigationCLI
// ============================================================

class SmartNavigationCLI {
public:
    explicit SmartNavigationCLI(const std::string& base_dir = ".")
        : base_dir_(base_dir),
          data_dir_(base_dir + "/data"),
          output_dir_(base_dir + "/output")
    {}

    void run() {
        ensure_dir(data_dir_);
        ensure_dir(output_dir_);

        while (true) {
            print_menu();
            std::cout << "Pilih menu: ";
            std::string choice = read_line();

            if      (choice == "1") cmd_add_node();
            else if (choice == "2") cmd_add_edge();
            else if (choice == "3") graph_.display();
            else if (choice == "4") cmd_manual_query();
            else if (choice == "5") cmd_dfs();
            else if (choice == "6") history_.display();
            else if (choice == "7") cmd_load_csv();
            else if (choice == "8") cmd_batch_query();
            else if (choice == "9") cmd_export_history();
            else if (choice == "0") { std::cout << "Keluar dari program.\n"; break; }
            else    std::cout << "Pilihan tidak valid. Coba lagi.\n";
        }
    }

private:
    std::string base_dir_;
    std::string data_dir_;
    std::string output_dir_;

    Graph              graph_;
    History            history_;
    NavigationService  nav_;
    CsvRepository      csv_;

    // --------------------------------------------------------
    // I/O helpers
    // --------------------------------------------------------

    static std::string read_line() {
        std::string s;
        std::getline(std::cin, s);
        return trim(s);
    }

    static void print_menu() {
        std::cout << "\n=== Smart Navigation System ===\n"
                  << "1. Tambah Node\n"
                  << "2. Tambah Edge\n"
                  << "3. Tampilkan Graph\n"
                  << "4. Find Optimal Path (Manual)\n"
                  << "5. DFS Exploration\n"
                  << "6. Tampilkan History\n"
                  << "7. Load Graph dari CSV\n"
                  << "8. Batch Query dari CSV + Export Result\n"
                  << "9. Export History\n"
                  << "0. Keluar\n";
    }

    // Formats a path with per-edge weights shown inline.
    // Output example:  A --(1.5)--> B --(2.0)--> C
    std::string format_path(const std::vector<std::string>& path,
                            const std::string& criteria) const
    {
        if (path.empty()) return "";
        std::string out;
        for (size_t i = 0; i + 1 < path.size(); ++i) {
            EdgeData ed = graph_.get_edge_data(path[i], path[i + 1]);
            double val  = (criteria == "time") ? ed.time_val : ed.distance;
            out += path[i] + " --(" + format_double(val) + ")--> ";
        }
        out += path.back();
        return out;
    }

    static std::string join_path(const std::string& dir, const std::string& file) {
        if (dir.empty()) return file;
        char last = dir.back();
        if (last == '/' || last == '\\') return dir + file;
        return dir + '/' + file;
    }

    // --------------------------------------------------------
    // Menu commands
    // --------------------------------------------------------

    void cmd_add_node() {
        std::cout << "Masukkan nama node: ";
        std::string node = read_line();
        if (node.empty()) { std::cout << "Node tidak boleh kosong.\n"; return; }
        graph_.add_node(node);
        std::cout << "Node '" << node << "' ditambahkan.\n";
    }

    void cmd_add_edge() {
        std::cout << "Node asal: ";
        std::string source = read_line();
        std::cout << "Node tujuan: ";
        std::string target = read_line();
        if (source.empty() || target.empty()) {
            std::cout << "Node asal/tujuan tidak boleh kosong.\n";
            return;
        }

        std::cout << "Distance (default 1.0): ";
        std::string dist_in = read_line();
        std::cout << "Time (default 1.0): ";
        std::string time_in = read_line();

        double dist = 1.0, time_val = 1.0;
        try {
            if (!dist_in.empty()) dist     = std::stod(dist_in);
            if (!time_in.empty()) time_val = std::stod(time_in);
        } catch (const std::exception&) {
            std::cout << "Input distance/time harus berupa angka.\n";
            return;
        }

        graph_.add_edge(source, target, dist, time_val);
        std::cout << "Edge '" << source << "' <-> '" << target
                  << "' (d:" << format_double(dist)
                  << ", t:" << format_double(time_val) << ") ditambahkan.\n";
    }

    void cmd_manual_query() {
        std::cout << "Start node: ";
        std::string start = read_line();
        std::cout << "End node: ";
        std::string end   = read_line();

        if (!graph_.has_node(start) || !graph_.has_node(end)) {
            std::cout << "Node tidak ditemukan. Silakan coba lagi.\n";
            return;
        }

        std::cout << "Optimize by (1) Distance or (2) Time [default: 1]: ";
        std::string crit_in  = read_line();
        std::string criteria = (crit_in == "2") ? "time" : "distance";

        auto [path, total_dist, total_time] =
            nav_.find_optimal_path(graph_, start, end, criteria);

        if (path.empty()) {
            std::cout << "Path dari " << start << " ke " << end << " tidak ditemukan.\n";
            return;
        }

        history_.push(path);
        std::cout << "Optimal path (" << criteria << "): "
                  << format_path(path, criteria) << '\n';
        std::cout << "Total Distance: " << format_double(total_dist) << '\n';
        std::cout << "Total Time: "     << format_double(total_time)  << '\n';
    }

    void cmd_dfs() {
        std::cout << "Start node DFS: ";
        std::string start = read_line();
        auto result = nav_.dfs_exploration(graph_, start);
        if (result.empty()) {
            std::cout << "Node tidak ditemukan atau graph kosong.\n";
            return;
        }
        std::cout << "DFS exploration:\n";
        for (size_t i = 0; i < result.size(); ++i) {
            if (i) std::cout << " -> ";
            std::cout << result[i];
        }
        std::cout << '\n';
    }

    void cmd_load_csv() {
        std::cout << "Masukkan nama file nodes (default: krl/nodes.csv): ";
        std::string nodes_in = read_line();
        std::cout << "Masukkan nama file edges (default: krl/edges.csv): ";
        std::string edges_in = read_line();

        std::string nodes_name = nodes_in.empty() ? "krl/nodes.csv" : nodes_in;
        std::string edges_name = edges_in.empty() ? "krl/edges.csv" : edges_in;

        std::string nodes_file = join_path(data_dir_, nodes_name);
        std::string edges_file = join_path(data_dir_, edges_name);

        // Verify files exist before loading.
        {
            std::ifstream nf(nodes_file), ef(edges_file);
            if (!nf || !ef) {
                std::cout << nodes_name << " atau " << edges_name
                          << " belum ada di folder data/.\n";
                return;
            }
        }

        graph_ = csv_.load_graph(nodes_file, edges_file);
        std::cout << "Graph berhasil dimuat dari "
                  << nodes_name << " dan " << edges_name << ".\n";
    }

    void cmd_batch_query() {
        std::cout << "Masukkan nama file query (default: query.csv): ";
        std::string query_in = read_line();
        std::string query_name = query_in.empty() ? "query.csv" : query_in;
        std::string query_file = join_path(data_dir_, query_name);

        auto queries = csv_.load_queries(query_file);
        if (queries.empty()) {
            std::cout << "Tidak ada query valid di file.\n";
            return;
        }

        std::cout << "Optimize by (1) Distance or (2) Time [default: 1]: ";
        std::string crit_in  = read_line();
        std::string criteria = (crit_in == "2") ? "time" : "distance";

        std::vector<QueryResult> results;

        for (const auto& [start, end] : queries) {
            if (!graph_.has_node(start) || !graph_.has_node(end)) {
                std::cout << "[SKIP] Node invalid: " << start << " -> " << end << '\n';
                continue;
            }

            auto [path, total_dist, total_time] =
                nav_.find_optimal_path(graph_, start, end, criteria);

            if (path.empty()) {
                std::cout << "[SKIP] Path tidak ditemukan: " << start << " -> " << end << '\n';
                continue;
            }

            history_.push(path);
            results.push_back({start, end, path, total_dist, total_time});

            std::cout << start << " -> " << end << ": "
                      << format_path(path, criteria)
                      << " (dist=" << format_double(total_dist)
                      << ", time=" << format_double(total_time) << ")\n";
        }

        if (results.empty()) {
            std::cout << "Tidak ada result yang diekspor.\n";
            return;
        }

        std::string result_file = join_path(output_dir_, "result.csv");
        csv_.save_result(result_file, results);
        std::cout << "Result disimpan ke: " << result_file << '\n';
    }

    void cmd_export_history() {
        std::string history_file = join_path(output_dir_, "history.csv");
        csv_.save_history(history_file, history_.stack);
        std::cout << "History disimpan ke: " << history_file << '\n';
    }
};

// ============================================================
// main
// ============================================================

// Probe candidate directories in order; return the first one that has a
// data/ subdirectory, so the program works no matter where it is launched from.
// static std::string find_base_dir() {
//     const char* candidates[] = {
//         ".",                                    // already inside the repo root
//         "Smart-Navigation-System-Documentation" // launched from the parent CODE/ dir
//     };
//     for (const char* dir : candidates) {
//         std::string probe = std::string(dir) + "/data";
//         struct stat st{};
//         if (stat(probe.c_str(), &st) == 0 && (st.st_mode & S_IFDIR))
//             return dir;
//     }
//     return "."; // fallback
// }

int main() {
    SmartNavigationCLI app(".");
    app.run();
    return 0;
}
