/*
 * Smart Navigation System — Pure C CLI
 * Converted from cli_app.cpp (C++17) to C99.
 *
 * What changed from C++:
 *   - std::map / unordered_map  → fixed-size arrays + linear search
 *   - std::priority_queue       → manual binary min-heap
 *   - std::string               → char[] with MAX_NAME_LEN
 *   - std::vector               → fixed-size arrays with a count field
 *   - std::ifstream / ofstream  → FILE*
 *   - std::cout / cin           → printf / fgets
 *   - classes with methods      → structs + standalone functions
 *   - try / catch               → strtod + endptr validation
 *   - structured bindings       → explicit struct member access
 *   - std::reverse              → manual swap loop
 *   - std::tuple return values  → output-pointer parameters
 *
 * Large structs (Graph, History, MinHeap, query/result buffers) are
 * declared as static globals to stay off the call stack.
 *
 * Compile:
 *   MSVC  : cl /std:c11 /O2 /W3 /Fe:cli_app_c.exe cli_app.c
 *   GCC   : gcc -std=c99 -O2 -Wall -o cli_app_c cli_app.c -lm
 *
 * Run from Smart-Navigation-System-Documentation/ (or CODE/ — the
 * program probes both for a data/ subdirectory automatically).
 */

/* Suppress MSVC "safe CRT" warnings for standard C functions. */
#ifdef _MSC_VER
#  define _CRT_SECURE_NO_WARNINGS
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <ctype.h>
#include <sys/stat.h>

#ifdef _WIN32
#  include <direct.h>
#  define MAKE_DIR(p) _mkdir(p)
#else
#  define MAKE_DIR(p) mkdir((p), 0755)
#endif

/* ================================================================
 * Compile-time limits
 * ================================================================ */
#define MAX_NODES          200   /* enough for KRL + manual additions  */
#define MAX_NAME_LEN       128   /* max chars in a node name           */
#define MAX_EDGES_PER_NODE  30   /* max neighbours per node            */
#define MAX_PATH           200   /* max nodes in a single path         */
#define MAX_HISTORY        300   /* max paths stored in history        */
#define MAX_QUERIES        300   /* max rows in query.csv              */
#define MAX_RESULTS        300   /* max results in one batch run       */
#define MAX_HEAP           8000  /* max items in the Dijkstra heap     */
#define MAX_DFS_STACK      4000  /* max items in the DFS stack         */
#define MAX_LINE          1024   /* max bytes per CSV line             */
#define MAX_FIELDS          12   /* max comma-separated fields per row */
#define MAX_PATH_STR      8192   /* max bytes for formatted path string*/

/* ================================================================
 * Data types
 * ================================================================ */

typedef struct {
    double distance;
    double time_val;
} EdgeData;

typedef struct {
    int      target;   /* index into Graph.nodes[]  */
    EdgeData data;
} Edge;

typedef struct {
    char name[MAX_NAME_LEN];
    Edge edges[MAX_EDGES_PER_NODE];
    int  edge_count;
} GraphNode;

typedef struct {
    GraphNode nodes[MAX_NODES];
    int       node_count;
} Graph;

typedef struct {
    int path[MAX_PATH];   /* node indices  */
    int length;
} HistoryEntry;

typedef struct {
    HistoryEntry entries[MAX_HISTORY];
    int          count;
} History;

typedef struct {
    char   start[MAX_NAME_LEN];
    char   end_node[MAX_NAME_LEN];
    int    path[MAX_PATH];
    int    path_len;
    double total_distance;
    double total_time;
} QueryResult;

typedef struct {
    char start[MAX_NAME_LEN];
    char end_node[MAX_NAME_LEN];
} QueryPair;

/* Min-heap item: (weight, node_index) */
typedef struct { double w; int idx; } HeapItem;

typedef struct {
    HeapItem items[MAX_HEAP];
    int      size;
} MinHeap;

/* Parent-tracking entry used during Dijkstra path reconstruction.
   parent_idx == -2  →  node not yet reached
   parent_idx == -1  →  this node is the start (sentinel: no parent) */
typedef struct {
    int    parent_idx;
    double edge_dist;
    double edge_time;
} ParentInfo;

/* App bundles graph, history and working directories together. */
typedef struct {
    char    data_dir[512];
    char    output_dir[512];
    Graph   graph;
    History history;
} App;

/* ================================================================
 * Static globals  (keep large objects off the call stack)
 * ================================================================ */
static App       g_app;
static MinHeap   g_heap;
static double    g_min_w[MAX_NODES];
static ParentInfo g_parent[MAX_NODES];
static int       g_dfs_stack[MAX_DFS_STACK];
static int       g_dfs_visited[MAX_NODES];
static QueryPair  g_queries[MAX_QUERIES];
static QueryResult g_results[MAX_RESULTS];
static int       g_dfs_result[MAX_NODES];

/* ================================================================
 * Utility
 * ================================================================ */

/* Trim leading and trailing whitespace in-place. */
static void trim_str(char *s) {
    if (!s) return;
    int len = (int)strlen(s);
    while (len > 0 && (unsigned char)s[len - 1] <= ' ') s[--len] = '\0';
    int start = 0;
    while (start < len && (unsigned char)s[start] <= ' ') start++;
    if (start > 0) memmove(s, s + start, (size_t)(len - start + 1));
}

/* Write "%.1f" representation of v into buf. */
static void fmt_double(double v, char *buf, int buf_size) {
    snprintf(buf, buf_size, "%.1f", v);
}

/* Round to one decimal place. */
static double round1(double v) {
    return floor(v * 10.0 + 0.5) / 10.0;
}

/* Split a CSV line by commas; trim each field; return field count. */
static int split_csv(const char *line,
                     char fields[][MAX_NAME_LEN], int max_fields) {
    int count = 0;
    const char *p = line;
    while (*p && count < max_fields) {
        const char *start = p;
        while (*p && *p != ',' && *p != '\n' && *p != '\r') p++;
        int len = (int)(p - start);
        if (len >= MAX_NAME_LEN) len = MAX_NAME_LEN - 1;
        strncpy(fields[count], start, (size_t)len);
        fields[count][len] = '\0';
        trim_str(fields[count]);
        count++;
        if (*p == ',') p++;
    }
    return count;
}

/* Create a directory; silently ignore EEXIST. */
static void ensure_dir(const char *path) { MAKE_DIR(path); }

/* Join dir and file with '/'; write result into out. */
static void path_join(const char *dir, const char *file,
                      char *out, int out_size) {
    if (!dir || !dir[0]) {
        strncpy(out, file, out_size - 1);
        out[out_size - 1] = '\0';
        return;
    }
    char last = dir[strlen(dir) - 1];
    if (last == '/' || last == '\\')
        snprintf(out, out_size, "%s%s", dir, file);
    else
        snprintf(out, out_size, "%s/%s", dir, file);
}

/* Read one line from stdin; strip newline; trim whitespace. */
static void read_line(char *buf, int size) {
    if (!fgets(buf, size, stdin)) { buf[0] = '\0'; return; }
    int len = (int)strlen(buf);
    while (len > 0 && (buf[len - 1] == '\n' || buf[len - 1] == '\r'))
        buf[--len] = '\0';
    trim_str(buf);
}

/* Return 1 if path is an existing directory, 0 otherwise. */
static int dir_exists(const char *path) {
    struct stat st;
    if (stat(path, &st) != 0) return 0;
    return (st.st_mode & S_IFDIR) != 0;
}

/* Probe for a data/ subdirectory; return the best base directory. */
static const char *find_base_dir(void) {
    static const char *candidates[] = {
        ".",
        "Smart-Navigation-System-Documentation",
        NULL
    };
    char probe[512];
    for (int i = 0; candidates[i]; i++) {
        snprintf(probe, sizeof(probe), "%s/data", candidates[i]);
        if (dir_exists(probe)) return candidates[i];
    }
    return ".";
}

/* ================================================================
 * Graph
 * ================================================================ */

static void graph_init(Graph *g) { g->node_count = 0; }

/* Return node index, or -1 if not found. */
static int graph_find(const Graph *g, const char *name) {
    for (int i = 0; i < g->node_count; i++)
        if (strcmp(g->nodes[i].name, name) == 0) return i;
    return -1;
}

/* Add node if not present; return its index, or -1 on error. */
static int graph_add_node(Graph *g, const char *raw) {
    char name[MAX_NAME_LEN];
    strncpy(name, raw, MAX_NAME_LEN - 1);
    name[MAX_NAME_LEN - 1] = '\0';
    trim_str(name);
    if (!name[0]) return -1;

    int idx = graph_find(g, name);
    if (idx >= 0) return idx;

    if (g->node_count >= MAX_NODES) {
        fprintf(stderr, "Max node count (%d) reached.\n", MAX_NODES);
        return -1;
    }
    idx = g->node_count++;
    strncpy(g->nodes[idx].name, name, MAX_NAME_LEN - 1);
    g->nodes[idx].name[MAX_NAME_LEN - 1] = '\0';
    g->nodes[idx].edge_count = 0;
    return idx;
}

/* Add or update a single directed edge from node[src_idx] to target. */
static void node_add_edge(GraphNode *node, int target,
                           double dist, double time_val) {
    for (int i = 0; i < node->edge_count; i++) {
        if (node->edges[i].target == target) {
            node->edges[i].data.distance = dist;
            node->edges[i].data.time_val = time_val;
            return;
        }
    }
    if (node->edge_count >= MAX_EDGES_PER_NODE) {
        fprintf(stderr, "Max edges per node (%d) reached.\n", MAX_EDGES_PER_NODE);
        return;
    }
    Edge *e = &node->edges[node->edge_count++];
    e->target       = target;
    e->data.distance = dist;
    e->data.time_val = time_val;
}

/* Add a bidirectional weighted edge (creates both directions). */
static void graph_add_edge(Graph *g, const char *raw_src,
                            const char *raw_tgt,
                            double dist, double time_val) {
    char src[MAX_NAME_LEN], tgt[MAX_NAME_LEN];
    strncpy(src, raw_src, MAX_NAME_LEN - 1); src[MAX_NAME_LEN - 1] = '\0'; trim_str(src);
    strncpy(tgt, raw_tgt, MAX_NAME_LEN - 1); tgt[MAX_NAME_LEN - 1] = '\0'; trim_str(tgt);
    if (!src[0] || !tgt[0]) return;

    int si = graph_add_node(g, src);
    int ti = graph_add_node(g, tgt);
    if (si < 0 || ti < 0) return;

    node_add_edge(&g->nodes[si], ti, dist, time_val);
    node_add_edge(&g->nodes[ti], si, dist, time_val);
}

static int graph_has_node(const Graph *g, const char *name) {
    return graph_find(g, name) >= 0;
}

/* Return EdgeData for (src→tgt); returns default {1,1} if not found. */
static EdgeData graph_edge_data(const Graph *g, int si, int ti) {
    EdgeData def = {1.0, 1.0};
    if (si < 0 || si >= g->node_count) return def;
    const GraphNode *n = &g->nodes[si];
    for (int i = 0; i < n->edge_count; i++)
        if (n->edges[i].target == ti) return n->edges[i].data;
    return def;
}

/* Print adjacency list sorted alphabetically (selection sort — n ≤ 200). */
static void graph_display(const Graph *g) {
    if (g->node_count == 0) { printf("(graph kosong)\n"); return; }

    /* Sort node indices by name */
    int sn[MAX_NODES];
    for (int i = 0; i < g->node_count; i++) sn[i] = i;
    for (int i = 0; i < g->node_count - 1; i++) {
        int best = i;
        for (int j = i + 1; j < g->node_count; j++)
            if (strcmp(g->nodes[sn[j]].name, g->nodes[sn[best]].name) < 0) best = j;
        if (best != i) { int t = sn[i]; sn[i] = sn[best]; sn[best] = t; }
    }

    char db[16], tb[16];
    for (int ni = 0; ni < g->node_count; ni++) {
        const GraphNode *node = &g->nodes[sn[ni]];

        /* Sort edge indices by neighbour name */
        int se[MAX_EDGES_PER_NODE];
        for (int j = 0; j < node->edge_count; j++) se[j] = j;
        for (int j = 0; j < node->edge_count - 1; j++) {
            int best = j;
            for (int k = j + 1; k < node->edge_count; k++) {
                int a = node->edges[se[k]].target;
                int b = node->edges[se[best]].target;
                if (strcmp(g->nodes[a].name, g->nodes[b].name) < 0) best = k;
            }
            if (best != j) { int t = se[j]; se[j] = se[best]; se[best] = t; }
        }

        printf("%s -> [", node->name);
        for (int j = 0; j < node->edge_count; j++) {
            const Edge *e = &node->edges[se[j]];
            fmt_double(e->data.distance, db, sizeof(db));
            fmt_double(e->data.time_val,  tb, sizeof(tb));
            if (j > 0) printf(", ");
            printf("%s(d:%s, t:%s)", g->nodes[e->target].name, db, tb);
        }
        printf("]\n");
    }
}

/* ================================================================
 * Min-Heap  (used by Dijkstra)
 * ================================================================ */

static void heap_init(MinHeap *h) { h->size = 0; }

static void heap_push(MinHeap *h, double w, int idx) {
    if (h->size >= MAX_HEAP) { fprintf(stderr, "Heap overflow.\n"); return; }
    int i = h->size++;
    h->items[i].w   = w;
    h->items[i].idx = idx;
    /* Sift up */
    while (i > 0) {
        int p = (i - 1) / 2;
        if (h->items[p].w > h->items[i].w) {
            HeapItem tmp = h->items[p]; h->items[p] = h->items[i]; h->items[i] = tmp;
            i = p;
        } else break;
    }
}

static HeapItem heap_pop(MinHeap *h) {
    HeapItem result = h->items[0];
    h->items[0] = h->items[--h->size];
    /* Sift down */
    int i = 0;
    for (;;) {
        int l = 2*i+1, r = 2*i+2, s = i;
        if (l < h->size && h->items[l].w < h->items[s].w) s = l;
        if (r < h->size && h->items[r].w < h->items[s].w) s = r;
        if (s == i) break;
        HeapItem tmp = h->items[s]; h->items[s] = h->items[i]; h->items[i] = tmp;
        i = s;
    }
    return result;
}

/* ================================================================
 * Dijkstra
 *
 * Uses the static globals g_heap, g_min_w, g_parent to avoid
 * allocating these large arrays on the call stack.
 *
 * Returns 1 if a path was found, 0 otherwise.
 * out_path[] receives node indices (length *out_len).
 * use_time: 0 = minimise distance, 1 = minimise time.
 * ================================================================ */
static int dijkstra(const Graph *g,
                    int start, int end, int use_time,
                    int *out_path, int *out_len,
                    double *out_dist, double *out_time) {
    int n = g->node_count;

    for (int i = 0; i < n; i++) {
        g_min_w[i]            = DBL_MAX;
        g_parent[i].parent_idx = -2;  /* not reached */
        g_parent[i].edge_dist  = 0.0;
        g_parent[i].edge_time  = 0.0;
    }
    g_min_w[start]            = 0.0;
    g_parent[start].parent_idx = -1;  /* sentinel: start has no parent */

    heap_init(&g_heap);
    heap_push(&g_heap, 0.0, start);

    while (g_heap.size > 0) {
        HeapItem item = heap_pop(&g_heap);
        double w = item.w;
        int    cur = item.idx;

        if (cur == end) break;
        if (w > g_min_w[cur]) continue;   /* stale entry — skip */

        const GraphNode *node = &g->nodes[cur];
        for (int ei = 0; ei < node->edge_count; ei++) {
            const Edge *e = &node->edges[ei];
            int    nbr = e->target;
            double ew  = use_time ? e->data.time_val : e->data.distance;
            double nw  = w + ew;

            if (nw < g_min_w[nbr]) {
                g_min_w[nbr]             = nw;
                g_parent[nbr].parent_idx = cur;
                g_parent[nbr].edge_dist  = e->data.distance;
                g_parent[nbr].edge_time  = e->data.time_val;
                heap_push(&g_heap, nw, nbr);
            }
        }
    }

    /* No path found? */
    if (g_parent[end].parent_idx == -2 && end != start) {
        *out_len = 0; *out_dist = 0.0; *out_time = 0.0;
        return 0;
    }

    /* Reconstruct: backtrack end → start, then reverse. */
    int    tmp[MAX_PATH];
    int    len = 0;
    double td = 0.0, tt = 0.0;

    int cur = end;
    while (cur != -1 && len < MAX_PATH) {
        tmp[len++] = cur;
        const ParentInfo *pi = &g_parent[cur];
        if (pi->parent_idx == -1) break;   /* reached start sentinel */
        td += pi->edge_dist;
        tt += pi->edge_time;
        cur = pi->parent_idx;
    }
    for (int i = 0; i < len / 2; i++) {   /* reverse */
        int t = tmp[i]; tmp[i] = tmp[len - 1 - i]; tmp[len - 1 - i] = t;
    }
    memcpy(out_path, tmp, (size_t)len * sizeof(int));
    *out_len  = len;
    *out_dist = round1(td);
    *out_time = round1(tt);
    return 1;
}

/* ================================================================
 * DFS Exploration
 *
 * Uses static globals g_dfs_stack and g_dfs_visited.
 * Neighbours are pushed in reverse order → visited left-to-right,
 * consistent with the Python and C++ implementations.
 * ================================================================ */
static int dfs_exploration(const Graph *g, int start,
                            int *out_result, int *out_count) {
    if (start < 0) return 0;

    memset(g_dfs_visited, 0, (size_t)g->node_count * sizeof(int));
    int top = 0, count = 0;

    g_dfs_stack[top++] = start;

    while (top > 0) {
        int node = g_dfs_stack[--top];
        if (g_dfs_visited[node]) continue;

        g_dfs_visited[node] = 1;
        out_result[count++] = node;

        const GraphNode *gn = &g->nodes[node];
        for (int i = gn->edge_count - 1; i >= 0; i--) {
            int nbr = gn->edges[i].target;
            if (!g_dfs_visited[nbr]) {
                if (top >= MAX_DFS_STACK) {
                    fprintf(stderr, "DFS stack overflow.\n"); break;
                }
                g_dfs_stack[top++] = nbr;
            }
        }
    }
    *out_count = count;
    return 1;
}

/* ================================================================
 * History
 * ================================================================ */

static void history_init(History *h) { h->count = 0; }

static void history_push(History *h, const int *path, int len) {
    if (len == 0 || h->count >= MAX_HISTORY) return;
    HistoryEntry *e = &h->entries[h->count++];
    int cl = len < MAX_PATH ? len : MAX_PATH;
    memcpy(e->path, path, (size_t)cl * sizeof(int));
    e->length = cl;
}

static void history_display(const History *h, const Graph *g) {
    if (h->count == 0) { printf("(history kosong)\n"); return; }
    for (int i = 0; i < h->count; i++) {
        printf("%d. ", i + 1);
        const HistoryEntry *e = &h->entries[i];
        for (int j = 0; j < e->length; j++) {
            if (j > 0) putchar('-');
            printf("%s", g->nodes[e->path[j]].name);
        }
        putchar('\n');
    }
}

/* ================================================================
 * format_path — write "A --(w)--> B --(w)--> C" into out_buf
 * ================================================================ */
static void format_path(const Graph *g, const int *path, int path_len,
                         int use_time, char *out_buf, int out_size) {
    out_buf[0] = '\0';
    if (path_len == 0) return;
    int written = 0;
    char wbuf[16];
    for (int i = 0; i + 1 < path_len && written < out_size - 1; i++) {
        EdgeData ed = graph_edge_data(g, path[i], path[i + 1]);
        double val  = use_time ? ed.time_val : ed.distance;
        fmt_double(val, wbuf, sizeof(wbuf));
        written += snprintf(out_buf + written, out_size - written,
                            "%s --(%s)--> ", g->nodes[path[i]].name, wbuf);
    }
    if (written < out_size - 1)
        snprintf(out_buf + written, out_size - written,
                 "%s", g->nodes[path[path_len - 1]].name);
}

/* ================================================================
 * CSV Repository
 * ================================================================ */

static int csv_load_graph(Graph *g,
                           const char *nodes_file,
                           const char *edges_file) {
    graph_init(g);

    /* ---- nodes ---- */
    FILE *nf = fopen(nodes_file, "r");
    if (!nf) { printf("Tidak bisa membuka: %s\n", nodes_file); return 0; }

    char line[MAX_LINE];
    char fields[MAX_FIELDS][MAX_NAME_LEN];

    if (!fgets(line, sizeof(line), nf)) { fclose(nf); return 0; }
    int nc = split_csv(line, fields, MAX_FIELDS);

    int name_col = -1;
    for (int i = 0; i < nc; i++)
        if (strcmp(fields[i], "name") == 0) { name_col = i; break; }

    if (name_col < 0) {
        printf("nodes.csv wajib punya kolom 'name'.\n");
        fclose(nf); return 0;
    }
    while (fgets(line, sizeof(line), nf)) {
        int n = split_csv(line, fields, MAX_FIELDS);
        if (n > name_col && fields[name_col][0])
            graph_add_node(g, fields[name_col]);
    }
    fclose(nf);

    /* ---- edges ---- */
    FILE *ef = fopen(edges_file, "r");
    if (!ef) { printf("Tidak bisa membuka: %s\n", edges_file); return 0; }

    if (!fgets(line, sizeof(line), ef)) { fclose(ef); return 0; }
    int ec = split_csv(line, fields, MAX_FIELDS);

    int from_col=-1, to_col=-1, dist_col=-1, time_col=-1;
    for (int i = 0; i < ec; i++) {
        if      (!strcmp(fields[i],"from"))     from_col = i;
        else if (!strcmp(fields[i],"to"))       to_col   = i;
        else if (!strcmp(fields[i],"distance")) dist_col = i;
        else if (!strcmp(fields[i],"time"))     time_col = i;
    }
    if (from_col < 0 || to_col < 0) {
        printf("edges.csv wajib punya kolom 'from' dan 'to'.\n");
        fclose(ef); return 0;
    }

    while (fgets(line, sizeof(line), ef)) {
        int n = split_csv(line, fields, MAX_FIELDS);
        if (n <= to_col) continue;
        char *src = fields[from_col], *tgt = fields[to_col];
        if (!src[0] || !tgt[0]) continue;

        double dist = (dist_col>=0 && n>dist_col && fields[dist_col][0])
                       ? atof(fields[dist_col]) : 1.0;
        double tv   = (time_col>=0 && n>time_col && fields[time_col][0])
                       ? atof(fields[time_col]) : 1.0;
        graph_add_edge(g, src, tgt, dist, tv);
    }
    fclose(ef);
    return 1;
}

static int csv_load_queries(const char *query_file) {
    FILE *f = fopen(query_file, "r");
    if (!f) { printf("Tidak bisa membuka: %s\n", query_file); return 0; }

    char line[MAX_LINE];
    char fields[MAX_FIELDS][MAX_NAME_LEN];

    if (!fgets(line, sizeof(line), f)) { fclose(f); return 0; }
    int hc = split_csv(line, fields, MAX_FIELDS);

    int start_col=-1, end_col=-1;
    for (int i = 0; i < hc; i++) {
        if      (!strcmp(fields[i],"start")) start_col = i;
        else if (!strcmp(fields[i],"end"))   end_col   = i;
    }
    if (start_col < 0 || end_col < 0) {
        printf("query.csv wajib punya kolom 'start' dan 'end'.\n");
        fclose(f); return 0;
    }

    int count = 0;
    while (fgets(line, sizeof(line), f) && count < MAX_QUERIES) {
        int n = split_csv(line, fields, MAX_FIELDS);
        if (n <= end_col || !fields[start_col][0] || !fields[end_col][0]) continue;
        strncpy(g_queries[count].start,    fields[start_col], MAX_NAME_LEN-1);
        strncpy(g_queries[count].end_node, fields[end_col],   MAX_NAME_LEN-1);
        g_queries[count].start[MAX_NAME_LEN-1]    = '\0';
        g_queries[count].end_node[MAX_NAME_LEN-1] = '\0';
        count++;
    }
    fclose(f);
    return count;
}

static void csv_save_result(const char *filename, int count,
                             const Graph *g) {
    FILE *f = fopen(filename, "w");
    if (!f) { printf("Tidak bisa menulis ke: %s\n", filename); return; }

    fprintf(f, "start,end,path,distance,time\n");
    char db[16], tb[16];
    for (int i = 0; i < count; i++) {
        const QueryResult *r = &g_results[i];
        fprintf(f, "%s,%s,", r->start, r->end_node);
        for (int j = 0; j < r->path_len; j++) {
            if (j > 0) fputc('-', f);
            fprintf(f, "%s", g->nodes[r->path[j]].name);
        }
        fmt_double(r->total_distance, db, sizeof(db));
        fmt_double(r->total_time,     tb, sizeof(tb));
        fprintf(f, ",%s,%s\n", db, tb);
    }
    fclose(f);
}

static void csv_save_history(const char *filename, const History *h,
                              const Graph *g) {
    FILE *f = fopen(filename, "w");
    if (!f) { printf("Tidak bisa menulis ke: %s\n", filename); return; }

    fprintf(f, "no,path\n");
    for (int i = 0; i < h->count; i++) {
        fprintf(f, "%d,", i + 1);
        const HistoryEntry *e = &h->entries[i];
        for (int j = 0; j < e->length; j++) {
            if (j > 0) fputc('-', f);
            fprintf(f, "%s", g->nodes[e->path[j]].name);
        }
        fputc('\n', f);
    }
    fclose(f);
}

/* ================================================================
 * Menu
 * ================================================================ */

static void print_menu(void) {
    printf("\n=== Smart Navigation System ===\n"
           "1. Tambah Node\n"
           "2. Tambah Edge\n"
           "3. Tampilkan Graph\n"
           "4. Find Optimal Path (Manual)\n"
           "5. DFS Exploration\n"
           "6. Tampilkan History\n"
           "7. Load Graph dari CSV\n"
           "8. Batch Query dari CSV + Export Result\n"
           "9. Export History\n"
           "0. Keluar\n");
}

/* ================================================================
 * Menu commands
 * ================================================================ */

static void cmd_add_node(App *app) {
    char name[MAX_NAME_LEN];
    printf("Masukkan nama node: ");
    read_line(name, sizeof(name));
    if (!name[0]) { printf("Node tidak boleh kosong.\n"); return; }
    graph_add_node(&app->graph, name);
    printf("Node '%s' ditambahkan.\n", name);
}

static void cmd_add_edge(App *app) {
    char src[MAX_NAME_LEN], tgt[MAX_NAME_LEN];
    char dist_in[32], time_in[32];

    printf("Node asal: ");   read_line(src,     sizeof(src));
    printf("Node tujuan: "); read_line(tgt,     sizeof(tgt));
    if (!src[0] || !tgt[0]) {
        printf("Node asal/tujuan tidak boleh kosong.\n"); return;
    }
    printf("Distance (default 1.0): "); read_line(dist_in, sizeof(dist_in));
    printf("Time (default 1.0): ");     read_line(time_in, sizeof(time_in));

    double dist = 1.0, tv = 1.0;
    if (dist_in[0]) {
        char *ep; dist = strtod(dist_in, &ep);
        if (*ep != '\0') { printf("Input distance harus berupa angka.\n"); return; }
    }
    if (time_in[0]) {
        char *ep; tv = strtod(time_in, &ep);
        if (*ep != '\0') { printf("Input time harus berupa angka.\n"); return; }
    }

    graph_add_edge(&app->graph, src, tgt, dist, tv);
    char db[16], tb[16];
    fmt_double(dist, db, sizeof(db));
    fmt_double(tv,   tb, sizeof(tb));
    printf("Edge '%s' <-> '%s' (d:%s, t:%s) ditambahkan.\n", src, tgt, db, tb);
}

static void cmd_manual_query(App *app) {
    char sname[MAX_NAME_LEN], ename[MAX_NAME_LEN];
    printf("Start node: "); read_line(sname, sizeof(sname));
    printf("End node: ");   read_line(ename, sizeof(ename));

    if (!graph_has_node(&app->graph, sname) ||
        !graph_has_node(&app->graph, ename)) {
        printf("Node tidak ditemukan. Silakan coba lagi.\n"); return;
    }

    printf("Optimize by (1) Distance or (2) Time [default: 1]: ");
    char cb[8]; read_line(cb, sizeof(cb));
    int use_time = (strcmp(cb, "2") == 0);

    int si = graph_find(&app->graph, sname);
    int ei = graph_find(&app->graph, ename);

    int    path[MAX_PATH], path_len;
    double total_dist, total_time;

    if (!dijkstra(&app->graph, si, ei, use_time,
                  path, &path_len, &total_dist, &total_time)) {
        printf("Path dari %s ke %s tidak ditemukan.\n", sname, ename);
        return;
    }

    history_push(&app->history, path, path_len);

    static char path_str[MAX_PATH_STR];
    format_path(&app->graph, path, path_len, use_time, path_str, sizeof(path_str));

    char db[16], tb[16];
    fmt_double(total_dist, db, sizeof(db));
    fmt_double(total_time, tb, sizeof(tb));

    printf("Optimal path (%s): %s\n",
           use_time ? "time" : "distance", path_str);
    printf("Total Distance: %s\n", db);
    printf("Total Time: %s\n",     tb);
}

static void cmd_dfs(App *app) {
    char sname[MAX_NAME_LEN];
    printf("Start node DFS: ");
    read_line(sname, sizeof(sname));

    int si = graph_find(&app->graph, sname);
    if (si < 0) { printf("Node tidak ditemukan atau graph kosong.\n"); return; }

    int count = 0;
    dfs_exploration(&app->graph, si, g_dfs_result, &count);

    if (count == 0) { printf("Node tidak ditemukan atau graph kosong.\n"); return; }

    printf("DFS exploration:\n");
    for (int i = 0; i < count; i++) {
        if (i > 0) printf(" -> ");
        printf("%s", app->graph.nodes[g_dfs_result[i]].name);
    }
    putchar('\n');
}

static void cmd_load_csv(App *app) {
    char nodes_in[256], edges_in[256];
    printf("Masukkan nama file nodes (default: krl/nodes.csv): ");
    read_line(nodes_in, sizeof(nodes_in));
    printf("Masukkan nama file edges (default: krl/edges.csv): ");
    read_line(edges_in, sizeof(edges_in));

    const char *nn = nodes_in[0] ? nodes_in : "krl/nodes.csv";
    const char *en = edges_in[0] ? edges_in : "krl/edges.csv";

    char nf[512], ef[512];
    path_join(app->data_dir, nn, nf, sizeof(nf));
    path_join(app->data_dir, en, ef, sizeof(ef));

    /* Verify both files exist before loading */
    FILE *tf1 = fopen(nf, "r"), *tf2 = fopen(ef, "r");
    if (!tf1 || !tf2) {
        if (tf1) fclose(tf1);
        if (tf2) fclose(tf2);
        printf("%s atau %s belum ada di folder data/.\n", nn, en);
        return;
    }
    fclose(tf1); fclose(tf2);

    if (csv_load_graph(&app->graph, nf, ef))
        printf("Graph berhasil dimuat dari %s dan %s.\n", nn, en);
}

static void cmd_batch_query(App *app) {
    char query_in[256];
    printf("Masukkan nama file query (default: query.csv): ");
    read_line(query_in, sizeof(query_in));
    const char *qn = query_in[0] ? query_in : "query.csv";

    char qf[512];
    path_join(app->data_dir, qn, qf, sizeof(qf));

    int qcount = csv_load_queries(qf);
    if (qcount == 0) { printf("Tidak ada query valid di file.\n"); return; }

    printf("Optimize by (1) Distance or (2) Time [default: 1]: ");
    char cb[8]; read_line(cb, sizeof(cb));
    int use_time = (strcmp(cb, "2") == 0);

    int rcount = 0;
    static char path_str[MAX_PATH_STR];

    for (int i = 0; i < qcount; i++) {
        const char *sn = g_queries[i].start;
        const char *en = g_queries[i].end_node;

        if (!graph_has_node(&app->graph, sn) ||
            !graph_has_node(&app->graph, en)) {
            printf("[SKIP] Node invalid: %s -> %s\n", sn, en);
            continue;
        }

        int si = graph_find(&app->graph, sn);
        int ei = graph_find(&app->graph, en);
        int path[MAX_PATH], path_len;
        double td, tt;

        if (!dijkstra(&app->graph, si, ei, use_time, path, &path_len, &td, &tt)) {
            printf("[SKIP] Path tidak ditemukan: %s -> %s\n", sn, en);
            continue;
        }

        history_push(&app->history, path, path_len);

        QueryResult *r = &g_results[rcount++];
        strncpy(r->start,    sn, MAX_NAME_LEN-1); r->start[MAX_NAME_LEN-1]    = '\0';
        strncpy(r->end_node, en, MAX_NAME_LEN-1); r->end_node[MAX_NAME_LEN-1] = '\0';
        memcpy(r->path, path, (size_t)path_len * sizeof(int));
        r->path_len       = path_len;
        r->total_distance = td;
        r->total_time     = tt;

        format_path(&app->graph, path, path_len, use_time, path_str, sizeof(path_str));
        char db[16], tb[16];
        fmt_double(td, db, sizeof(db));
        fmt_double(tt, tb, sizeof(tb));
        printf("%s -> %s: %s (dist=%s, time=%s)\n", sn, en, path_str, db, tb);
    }

    if (rcount == 0) { printf("Tidak ada result yang diekspor.\n"); return; }

    char rf[512];
    path_join(app->output_dir, "result.csv", rf, sizeof(rf));
    csv_save_result(rf, rcount, &app->graph);
    printf("Result disimpan ke: %s\n", rf);
}

static void cmd_export_history(App *app) {
    char hf[512];
    path_join(app->output_dir, "history.csv", hf, sizeof(hf));
    csv_save_history(hf, &app->history, &app->graph);
    printf("History disimpan ke: %s\n", hf);
}

/* ================================================================
 * Application init & main loop
 * ================================================================ */

static void app_init(App *app, const char *base_dir) {
    snprintf(app->data_dir,   sizeof(app->data_dir),   "%s/data",   base_dir);
    snprintf(app->output_dir, sizeof(app->output_dir), "%s/output", base_dir);
    graph_init(&app->graph);
    history_init(&app->history);
}

static void app_run(App *app) {
    ensure_dir(app->data_dir);
    ensure_dir(app->output_dir);

    char choice[8];
    for (;;) {
        print_menu();
        printf("Pilih menu: ");
        read_line(choice, sizeof(choice));

        if      (!strcmp(choice,"1")) cmd_add_node(app);
        else if (!strcmp(choice,"2")) cmd_add_edge(app);
        else if (!strcmp(choice,"3")) graph_display(&app->graph);
        else if (!strcmp(choice,"4")) cmd_manual_query(app);
        else if (!strcmp(choice,"5")) cmd_dfs(app);
        else if (!strcmp(choice,"6")) history_display(&app->history, &app->graph);
        else if (!strcmp(choice,"7")) cmd_load_csv(app);
        else if (!strcmp(choice,"8")) cmd_batch_query(app);
        else if (!strcmp(choice,"9")) cmd_export_history(app);
        else if (!strcmp(choice,"0")) { printf("Keluar dari program.\n"); break; }
        else    printf("Pilihan tidak valid. Coba lagi.\n");
    }
}

/* ================================================================
 * main
 * ================================================================ */
int main(void) {
    app_init(&g_app, find_base_dir());
    app_run(&g_app);
    return 0;
}
