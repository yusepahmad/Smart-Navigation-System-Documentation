"""Unified Streamlit UI for Smart Navigation System (Directed Graph, split view)."""

from __future__ import annotations

import heapq
import time
from pathlib import Path

import networkx as nx
import pandas as pd
import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph


BASE_DIR = Path(__file__).resolve().parent


st.set_page_config(
    page_title="Smart Navigation System - Realtime UI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _resolve_path(path_input: str) -> Path:
    path = Path(path_input)
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()


def _init_state() -> None:
    if "graph" not in st.session_state:
        st.session_state.graph = nx.DiGraph()
    if "history" not in st.session_state:
        st.session_state.history = []
    if "results" not in st.session_state:
        st.session_state.results = []
    if "selected_node" not in st.session_state:
        st.session_state.selected_node = None
    if "highlight_path_edges" not in st.session_state:
        st.session_state.highlight_path_edges = set()
    if "last_bfs_path" not in st.session_state:
        st.session_state.last_bfs_path = []
    if "last_dfs_path" not in st.session_state:
        st.session_state.last_dfs_path = []
    if "auto_loaded_graph" not in st.session_state:
        st.session_state.auto_loaded_graph = False
    # Animation state
    if "animation_steps" not in st.session_state:
        st.session_state.animation_steps = []
    if "animation_type" not in st.session_state:
        st.session_state.animation_type = ""
    if "animation_start" not in st.session_state:
        st.session_state.animation_start = ""
    if "animation_end" not in st.session_state:
        st.session_state.animation_end = ""
    if "animation_pos" not in st.session_state:
        st.session_state.animation_pos = {}


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1460px;
            padding-top: 0.85rem;
            padding-bottom: 0.75rem;
            padding-left: 1.2rem;
            padding-right: 1.2rem;
        }
        .main-flex { display: flex; gap: 20px; align-items: flex-start; }
        .left-scroll { flex: 1; max-height: 90vh; overflow-y: auto; padding-right: 10px; }
        .right-fixed { flex: 2; height: 90vh; overflow: hidden; }

        .st-key-split_root > div[data-testid="stHorizontalBlock"] {
            display: flex;
            gap: 20px;
            align-items: flex-start;
        }
        .st-key-split_root > div[data-testid="stHorizontalBlock"] > div:nth-child(1) {
            flex: 1 1 0;
            min-width: 320px;
            max-width: 460px;
        }
        .st-key-split_root > div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
            flex: 2 1 0;
            min-width: 0;
        }
        .st-key-split_root > div[data-testid="stHorizontalBlock"] > div:nth-child(1) > div {
            max-height: 90vh;
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 10px;
            scrollbar-gutter: stable;
        }
        .st-key-split_root > div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div {
            height: 90vh;
            overflow: hidden;
            border-left: 1px solid #e2e8f0;
            padding-left: 14px;
            box-shadow: inset 10px 0 18px -18px rgba(15, 23, 42, 0.25);
        }
        .panel-box {
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 0.9rem 0.95rem;
            background: linear-gradient(140deg, #ffffff 0%, #f8fafc 100%);
            margin-bottom: 0.9rem;
            box-shadow: 0 8px 16px rgba(15, 23, 42, 0.06);
        }
        .graph-shell {
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 0.45rem;
            background: #ffffff;
            margin-top: 0.5rem;
            overflow: hidden;
        }
        .anim-shell {
            border: 1px solid #fbbf24;
            border-radius: 14px;
            padding: 0.45rem;
            background: #fffbeb;
            margin-top: 0.5rem;
            overflow: hidden;
        }
        .legend-chip {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
            margin: 2px 3px;
        }
        .section-title {font-weight: 700; font-size: 1.02rem; color: #0f172a; margin-bottom: 0.55rem;}
        .mini-caption {color: #64748b; font-size: 0.9rem;}
        @media (max-width: 1100px) {
            .st-key-split_root > div[data-testid="stHorizontalBlock"] {
                display: block;
            }
            .st-key-split_root > div[data-testid="stHorizontalBlock"] > div:nth-child(1),
            .st-key-split_root > div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
                max-width: none;
                min-width: 0;
                width: 100%;
            }
            .st-key-split_root > div[data-testid="stHorizontalBlock"] > div:nth-child(1) > div,
            .st-key-split_root > div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div {
                height: auto;
                max-height: none;
                overflow: visible;
                border-left: none;
                padding-left: 0;
                box-shadow: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _graph_to_dataframes(graph: nx.DiGraph) -> tuple[pd.DataFrame, pd.DataFrame]:
    nodes_df = pd.DataFrame(
        [{"id": idx, "name": node} for idx, node in enumerate(sorted(graph.nodes()))]
    )
    edges_df = pd.DataFrame(
        [{"from": source, "to": target} for source, target in sorted(graph.edges())]
    )
    return nodes_df, edges_df


def _load_graph_from_csv(
    nodes_path: Path,
    edges_path: Path,
    *,
    show_feedback: bool = True,
    show_error: bool = True,
) -> bool:
    if not nodes_path.exists() or not edges_path.exists():
        if show_error:
            st.error("nodes.csv atau edges.csv tidak ditemukan.")
        return False

    try:
        nodes_df = pd.read_csv(nodes_path)
        edges_df = pd.read_csv(edges_path)
    except Exception as exc:  # noqa: BLE001
        if show_error:
            st.error(f"Gagal membaca CSV: {exc}")
        return False

    if "name" not in nodes_df.columns:
        if show_error:
            st.error("nodes.csv wajib punya kolom 'name'.")
        return False
    if not {"from", "to"}.issubset(edges_df.columns):
        if show_error:
            st.error("edges.csv wajib punya kolom 'from' dan 'to'.")
        return False

    graph = nx.DiGraph()
    for name in nodes_df["name"].dropna().astype(str):
        node = name.strip()
        if node:
            graph.add_node(node)

    for _, row in edges_df.iterrows():
        source = str(row["from"]).strip()
        target = str(row["to"]).strip()
        dist = float(row.get("distance", 1.0)) if "distance" in row else 1.0
        time_val = float(row.get("time", 1.0)) if "time" in row else 1.0
        if source and target:
            graph.add_edge(source, target, distance=dist, time=time_val)
            graph.add_edge(target, source, distance=dist, time=time_val)

    st.session_state.graph = graph
    if show_feedback:
        st.success("Graph berhasil dimuat dari CSV (Bidirectional/Undirected).")
    return True


def _save_result_to_csv(result_path: Path) -> None:
    result_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(st.session_state.results)
    if df.empty:
        df = pd.DataFrame(columns=["start", "end", "path", "distance"])
    df.to_csv(result_path, index=False)


def _save_history_to_csv(history_path: Path) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"no": idx, "path": path} for idx, path in enumerate(st.session_state.history, 1)]
    pd.DataFrame(rows).to_csv(history_path, index=False)


# ---------------------------------------------------------------------------
# Algorithm step computation (for animation)
# ---------------------------------------------------------------------------

def _compute_dijkstra_steps(
    graph: nx.DiGraph, start: str, end: str, criteria: str
) -> tuple[list[dict], list[str], float, float]:
    """Run Dijkstra step-by-step, collecting animation frames.

    Returns (steps, path, total_distance, total_time).
    """
    pq: list[tuple[float, str]] = [(0.0, start)]
    min_weights: dict[str, float] = {start: 0.0}
    parent: dict[str, str | None] = {start: None}
    visited: set[str] = set()
    steps: list[dict] = []

    while pq:
        w, node = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)

        # Reconstruct path to current node
        path_to_node: list[str] = []
        cur: str | None = node
        while cur is not None:
            path_to_node.append(cur)
            cur = parent.get(cur)
        path_to_node.reverse()

        path_edges = {
            (path_to_node[i], path_to_node[i + 1])
            for i in range(len(path_to_node) - 1)
        }
        frontier = {n for _, n in pq if n not in visited}

        steps.append({
            "visited": set(visited),
            "current": node,
            "frontier": frontier,
            "path_edges": path_edges,
            "current_path": path_to_node,
            "message": (
                f"Dijkstra: memproses '{node}' (cost={round(w, 1)}) | "
                f"Path sejauh ini: {' → '.join(path_to_node)}"
            ),
        })

        if node == end:
            break

        for neighbor in graph.successors(node):
            edge_data = graph[node][neighbor]
            edge_w = float(edge_data.get(criteria, 1.0))
            new_w = w + edge_w
            if new_w < min_weights.get(neighbor, float("inf")):
                min_weights[neighbor] = new_w
                parent[neighbor] = node
                heapq.heappush(pq, (new_w, neighbor))

    # Reconstruct final path
    if end in parent:
        path: list[str] = []
        cur2: str | None = end
        while cur2 is not None:
            path.append(cur2)
            cur2 = parent.get(cur2)
        path.reverse()
        total_dist = sum(
            graph[u][v].get("distance", 1.0) for u, v in zip(path[:-1], path[1:])
        )
        total_time = sum(
            graph[u][v].get("time", 1.0) for u, v in zip(path[:-1], path[1:])
        )
    else:
        path = []
        total_dist = 0.0
        total_time = 0.0

    return steps, path, round(total_dist, 1), round(total_time, 1)


def _compute_dfs_steps(
    graph: nx.DiGraph, start: str, end: str | None = None
) -> tuple[list[dict], list[str]]:
    """Run DFS step-by-step, collecting animation frames.

    If `end` is given, stops when end node is reached (pathfinding mode).
    Returns (steps, result_path).
    """
    stack: list[tuple[str, list[str]]] = [(start, [start])]
    visited: set[str] = set()
    steps: list[dict] = []
    result_path: list[str] = []

    while stack:
        node, path = stack.pop()
        if node in visited:
            continue
        visited.add(node)

        path_edges = {(path[i], path[i + 1]) for i in range(len(path) - 1)}
        stack_nodes = {n for n, _ in stack if n not in visited}

        steps.append({
            "visited": set(visited),
            "current": node,
            "frontier": stack_nodes,
            "path_edges": path_edges,
            "current_path": list(path),
            "message": (
                f"DFS: mengunjungi '{node}' | "
                f"Path saat ini: {' → '.join(path)}"
            ),
        })

        if end and node == end:
            result_path = list(path)
            break

        for neighbor in reversed(list(graph.successors(node))):
            if neighbor not in visited:
                stack.append((neighbor, path + [neighbor]))

    if not end:
        result_path = [s["current"] for s in steps]

    return steps, result_path


# ---------------------------------------------------------------------------
# Algorithm runners
# ---------------------------------------------------------------------------

def _run_bfs(start: str, end: str, criteria: str = "distance") -> None:
    graph = st.session_state.graph
    if not graph.has_node(start) or not graph.has_node(end):
        st.warning("Node start/end tidak ditemukan pada graph.")
        return

    steps, path, total_dist, total_time = _compute_dijkstra_steps(
        graph, start, end, criteria
    )

    if not path:
        st.warning(f"Tidak ada path dari {start} ke {end}.")
        return

    path_text = "-".join(path)
    st.session_state.history.append(path_text)
    st.session_state.results.append(
        {
            "start": start,
            "end": end,
            "path": path_text,
            "distance": total_dist,
            "time": total_time,
        }
    )
    st.session_state.last_bfs_path = path
    st.session_state.highlight_path_edges = {
        (path[i], path[i + 1]) for i in range(len(path) - 1)
    }

    # Store animation data
    st.session_state.animation_steps = steps
    st.session_state.animation_type = f"BFS / Dijkstra (optimasi: {criteria})"
    st.session_state.animation_start = start
    st.session_state.animation_end = end
    pos = nx.spring_layout(graph, seed=42)
    st.session_state.animation_pos = {
        n: (float(xy[0]), float(xy[1])) for n, xy in pos.items()
    }

    st.success(
        f"Optimal path ({criteria}): {' → '.join(path)} "
        f"| dist={total_dist}, time={total_time}"
    )


def _run_dfs(start: str, end: str | None = None, criteria: str = "distance") -> None:
    graph = st.session_state.graph
    if not graph.has_node(start):
        st.warning("Node start DFS tidak ditemukan.")
        return
    if end and not graph.has_node(end):
        st.warning("Node end DFS tidak ditemukan.")
        return

    steps, path = _compute_dfs_steps(graph, start, end if end else None)

    if end and not path:
        st.warning(f"DFS tidak menemukan path dari {start} ke {end}.")
        return

    path_text = "-".join(path)
    total_dist = 0.0
    total_time = 0.0

    if end and len(path) > 1:
        total_dist = round(
            sum(graph[u][v].get("distance", 1.0) for u, v in zip(path[:-1], path[1:])), 1
        )
        total_time = round(
            sum(graph[u][v].get("time", 1.0) for u, v in zip(path[:-1], path[1:])), 1
        )

    st.session_state.history.append(path_text)
    if end:
        st.session_state.results.append(
            {
                "start": start,
                "end": end,
                "path": path_text,
                "distance": total_dist,
                "time": total_time,
            }
        )
    st.session_state.last_dfs_path = path
    st.session_state.highlight_path_edges = {
        (path[i], path[i + 1]) for i in range(len(path) - 1)
    }

    # Store animation data
    st.session_state.animation_steps = steps
    st.session_state.animation_type = (
        f"DFS Pathfinding ({criteria})" if end else "DFS Exploration"
    )
    st.session_state.animation_start = start
    st.session_state.animation_end = end or ""
    pos = nx.spring_layout(graph, seed=42)
    st.session_state.animation_pos = {
        n: (float(xy[0]), float(xy[1])) for n, xy in pos.items()
    }

    if end:
        st.success(
            f"DFS path ({criteria}): {' → '.join(path)} "
            f"| dist={total_dist}, time={total_time}"
        )
    else:
        st.success(f"DFS traversal order: {' → '.join(path)}")


def _run_batch_query(query_path: Path, result_path: Path) -> None:
    if not query_path.exists():
        st.error(f"query.csv tidak ditemukan: {query_path}")
        return

    try:
        query_df = pd.read_csv(query_path)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Gagal membaca query.csv: {exc}")
        return

    if not {"start", "end"}.issubset(query_df.columns):
        st.error("query.csv wajib punya kolom 'start' dan 'end'.")
        return

    graph = st.session_state.graph
    ok_count = 0
    skip_count = 0

    for _, row in query_df.iterrows():
        start = str(row["start"]).strip()
        end = str(row["end"]).strip()
        if not graph.has_node(start) or not graph.has_node(end):
            skip_count += 1
            continue
        try:
            path = nx.shortest_path(graph, start, end)
        except nx.NetworkXNoPath:
            skip_count += 1
            continue

        path_text = "-".join(path)
        st.session_state.history.append(path_text)
        st.session_state.results.append(
            {
                "start": start,
                "end": end,
                "path": path_text,
                "distance": len(path) - 1,
            }
        )
        ok_count += 1

    if ok_count == 0:
        st.warning("Batch query selesai, tapi tidak ada result valid.")
        return

    _save_result_to_csv(result_path)
    st.success(f"Batch query selesai: {ok_count} result disimpan, {skip_count} query di-skip.")


# ---------------------------------------------------------------------------
# Graph visualization builders
# ---------------------------------------------------------------------------

def _degree_category(total_degree: int) -> tuple[str, str]:
    if total_degree >= 4:
        return "high", "#ef4444"
    if total_degree >= 2:
        return "medium", "#0ea5e9"
    return "low", "#94a3b8"


def _build_agraph(
    graph: nx.DiGraph,
    selected_node: str | None,
    min_degree: int,
    highlight_mode: str,
    custom_nodes: list[str],
    height: int = 380,
) -> str | None:
    visible_nodes = [
        n
        for n in graph.nodes()
        if (graph.in_degree(n) + graph.out_degree(n)) >= min_degree
    ]
    subgraph = graph.subgraph(visible_nodes).copy()

    if subgraph.number_of_nodes() == 0:
        st.info("Graph kosong setelah filter degree.")
        return None

    highlight_edges: set[tuple[str, str]] = set()
    if highlight_mode == "path":
        highlight_edges = set(st.session_state.highlight_path_edges)
    elif highlight_mode == "neighbors" and selected_node and selected_node in subgraph:
        for source, target in subgraph.out_edges(selected_node):
            highlight_edges.add((source, target))
        for source, target in subgraph.in_edges(selected_node):
            highlight_edges.add((source, target))
    elif highlight_mode == "custom selection" and custom_nodes:
        selected_set = set(custom_nodes)
        for source, target in subgraph.edges():
            if source in selected_set and target in selected_set:
                highlight_edges.add((source, target))

    nodes = []
    for node in subgraph.nodes():
        total_degree = subgraph.in_degree(node) + subgraph.out_degree(node)
        category, color = _degree_category(total_degree)
        size = 18 + (total_degree * 3)
        border_color = "#111827" if node == selected_node else "#cbd5e1"

        title = (
            f"Node: {node}<br>"
            f"In degree: {subgraph.in_degree(node)}<br>"
            f"Out degree: {subgraph.out_degree(node)}<br>"
            f"Category: {category}"
        )
        nodes.append(
            Node(
                id=node,
                label=node,
                size=size,
                color=color,
                shape="dot",
                title=title,
                borderWidth=4 if node == selected_node else 1,
                borderWidthSelected=5,
                font={"color": "#0f172a"},
            )
        )

    edges = []
    for source, target in subgraph.edges():
        color = "#94a3b8"
        width = 1.5

        if (source, target) in highlight_edges:
            color = "#f97316"
            width = 4
        elif selected_node:
            if source == selected_node:
                color = "#2563eb"
                width = 2.5
            elif target == selected_node:
                color = "#dc2626"
                width = 2.5

        dist = subgraph[source][target].get("distance", 1.0)
        time_val = subgraph[source][target].get("time", 1.0)
        label = f"d:{dist}, t:{time_val}"

        edges.append(
            Edge(
                source=source,
                target=target,
                label=label,
                color=color,
                width=width,
                title=f"Relasi: {source} -> {target} | d:{dist}, t:{time_val}",
                smooth=False,
            )
        )

    config = Config(
        width="100%",
        height=height,
        directed=True,
        physics=True,
        hierarchical=False,
        nodeHighlightBehavior=True,
        highlightColor="#fde68a",
        collapsible=False,
        staticGraph=False,
        staticGraphWithDragAndDrop=False,
    )

    clicked_node = agraph(nodes=nodes, edges=edges, config=config)
    return clicked_node


def _build_agraph_for_animation(
    graph: nx.DiGraph,
    step: dict,
    start: str,
    end: str,
    pos: dict[str, tuple[float, float]] | None = None,
    height: int = 320,
    step_idx: str | int = 0,
) -> None:
    """Build an agraph frame for a single animation step."""
    visited = step.get("visited", set())
    current = step.get("current", "")
    frontier = step.get("frontier", set())
    path_edges = step.get("path_edges", set())

    nodes = []
    for node in graph.nodes():
        if node == current:
            color, size = "#f59e0b", 24
        elif node == start and node != current:
            color, size = "#8b5cf6", 22
        elif end and node == end and node != current:
            color, size = "#ef4444", 22
        elif node in visited:
            color, size = "#22c55e", 18
        elif node in frontier:
            color, size = "#3b82f6", 18
        else:
            color, size = "#cbd5e1", 15

        node_kwargs = {
            "id": node,
            "label": node,
            "size": size,
            "color": color,
            "shape": "dot",
            "title": f"{node}",
            "font": {"color": "#0f172a", "size": 11},
        }
        if pos and node in pos:
            node_kwargs["x"] = pos[node][0] * 300
            node_kwargs["y"] = pos[node][1] * 300
            node_kwargs["fixed"] = True

        nodes.append(Node(**node_kwargs))

    edges = []
    for src, tgt in graph.edges():
        if (src, tgt) in path_edges:
            color, width = "#f97316", 4
        elif src in visited and tgt in visited:
            color, width = "#86efac", 2
        else:
            color, width = "#e2e8f0", 1

        edges.append(
            Edge(
                source=src,
                target=tgt,
                color=color,
                width=width,
                smooth=False,
            )
        )

    config = Config(
        width="100%",
        height=height,
        directed=True,
        physics=False,
        hierarchical=False,
        staticGraph=True,
        step_id=step_idx,
    )

    agraph(nodes=nodes, edges=edges, config=config)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _init_state()
    _inject_css()

    st.title("Smart Navigation System - Unified Realtime UI")
    st.caption("Single split-view: kiri untuk kontrol aksi, kanan untuk graph directed interaktif realtime.")

    split_root = st.container(key="split_root")
    with split_root:
        left_col, right_col = st.columns([1, 2], gap="large")

    with left_col:
        with st.expander("Data Source & File Paths", expanded=True):
            st.markdown('<div class="panel-box">', unsafe_allow_html=True)
            nodes_path_raw = st.text_input("Nodes CSV", "data/krl/nodes.csv")
            edges_path_raw = st.text_input("Edges CSV", "data/krl/edges.csv")
            query_path_raw = st.text_input("Query CSV", "data/query.csv")
            result_path_raw = st.text_input("Result CSV", "output/result.csv")
            history_path_raw = st.text_input("History CSV", "output/history.csv")

            nodes_path = _resolve_path(nodes_path_raw)
            edges_path = _resolve_path(edges_path_raw)
            query_path = _resolve_path(query_path_raw)
            result_path = _resolve_path(result_path_raw)
            history_path = _resolve_path(history_path_raw)

            if not st.session_state.auto_loaded_graph:
                _load_graph_from_csv(
                    nodes_path,
                    edges_path,
                    show_feedback=False,
                    show_error=False,
                )
                st.session_state.auto_loaded_graph = True

            c_load, c_reset = st.columns(2)

            if c_load.button("Load CSV", width="stretch"):
                _load_graph_from_csv(nodes_path, edges_path)
            if c_reset.button("Reset Graph", width="stretch"):
                st.session_state.graph = nx.DiGraph()
                st.session_state.history = []
                st.session_state.results = []
                st.session_state.highlight_path_edges = set()
                st.session_state.last_bfs_path = []
                st.session_state.last_dfs_path = []
                st.session_state.selected_node = None
                st.session_state.animation_steps = []
                st.success("State graph direset.")
            st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Graph Editing", expanded=False):
            st.markdown('<div class="panel-box">', unsafe_allow_html=True)
            with st.form("add_node_form", clear_on_submit=True):
                node_name = st.text_input("Tambah Node")
                submit_node = st.form_submit_button("Add Node", width="stretch")
                if submit_node:
                    name = node_name.strip()
                    if not name:
                        st.warning("Nama node tidak boleh kosong.")
                    else:
                        st.session_state.graph.add_node(name)
                        st.success(f"Node '{name}' ditambahkan.")

            with st.form("add_edge_form", clear_on_submit=True):
                edge_source = st.text_input("Edge Source (from)")
                edge_target = st.text_input("Edge Target (to)")
                submit_edge = st.form_submit_button("Add Directed Edge", width="stretch")
                if submit_edge:
                    source = edge_source.strip()
                    target = edge_target.strip()
                    if not source or not target:
                        st.warning("Source dan target wajib diisi.")
                    else:
                        st.session_state.graph.add_node(source)
                        st.session_state.graph.add_node(target)
                        st.session_state.graph.add_edge(source, target)
                        st.success(f"Edge directed '{source} -> {target}' ditambahkan.")
            st.markdown("</div>", unsafe_allow_html=True)

        graph_nodes = sorted(st.session_state.graph.nodes())
        node_options = [""] + graph_nodes

        with st.expander("Algorithms", expanded=True):
            st.markdown('<div class="panel-box">', unsafe_allow_html=True)

            # --- BFS / Dijkstra ---
            st.markdown("**Find Optimal Path (BFS / Dijkstra)**")
            bfs_col1, bfs_col2 = st.columns(2)
            bfs_start = bfs_col1.selectbox("Start Node", node_options, key="bfs_start")
            bfs_end = bfs_col2.selectbox("End Node", node_options, key="bfs_end")
            criteria = st.radio("Optimize By", options=["distance", "time"], horizontal=True)

            if st.button("Find Optimal Path", width="stretch", type="primary"):
                if not bfs_start or not bfs_end:
                    st.warning("Pilih node start dan end.")
                else:
                    _run_bfs(bfs_start, bfs_end, criteria=criteria)

            st.divider()

            # --- DFS ---
            st.markdown("**DFS (Depth-First Search)**")
            dfs_col1, dfs_col2 = st.columns(2)
            dfs_start = dfs_col1.selectbox("DFS Start", node_options, key="dfs_start")
            dfs_end = dfs_col2.selectbox(
                "DFS End (opsional)",
                node_options,
                key="dfs_end",
                help="Kosongkan untuk mode eksplorasi penuh. Isi untuk DFS pathfinding ke node tujuan.",
            )
            dfs_criteria = st.radio(
                "DFS Metric (untuk tampilkan distance/time)",
                options=["distance", "time"],
                horizontal=True,
                key="dfs_criteria",
            )

            if st.button("Run DFS", width="stretch"):
                if not dfs_start:
                    st.warning("Pilih node start untuk DFS.")
                else:
                    _run_dfs(
                        dfs_start,
                        end=dfs_end if dfs_end else None,
                        criteria=dfs_criteria,
                    )

            st.divider()

            if st.button("Run Batch Query + Save Result", width="stretch"):
                _run_batch_query(query_path, result_path)

            if st.button("Export History CSV", width="stretch"):
                _save_history_to_csv(history_path)
                st.success(f"History diexport ke: {history_path}")

            st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Realtime Filters & Highlight", expanded=True):
            st.markdown('<div class="panel-box">', unsafe_allow_html=True)
            max_degree = 0
            if st.session_state.graph.number_of_nodes() > 0:
                max_degree = max(
                    st.session_state.graph.in_degree(n) + st.session_state.graph.out_degree(n)
                    for n in st.session_state.graph.nodes()
                )

            min_degree = st.slider("Minimum Degree", 0, max_degree if max_degree else 0, 0)

            selected_node = st.selectbox(
                "Selected Node",
                options=["(none)"] + graph_nodes,
                index=0 if st.session_state.selected_node is None else 0,
                help="Klik node di graph atau pilih dari dropdown untuk detail.",
            )
            if selected_node == "(none)":
                selected_node_value = st.session_state.selected_node
            else:
                selected_node_value = selected_node

            highlight_mode = st.radio(
                "Highlight Mode",
                options=["neighbors", "path", "custom selection"],
                key="ui_highlight_mode",
                horizontal=True,
            )

            custom_nodes = st.multiselect(
                "Custom Node Selection",
                options=graph_nodes,
                default=[],
                help="Digunakan saat mode highlight = custom selection",
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Quick Logs", expanded=False):
            st.markdown('<div class="panel-box">', unsafe_allow_html=True)
            if st.session_state.last_bfs_path:
                st.write("BFS terakhir:", " → ".join(st.session_state.last_bfs_path))
            if st.session_state.last_dfs_path:
                st.write("DFS terakhir:", " → ".join(st.session_state.last_dfs_path))
            if not st.session_state.last_bfs_path and not st.session_state.last_dfs_path:
                st.caption("Belum ada hasil BFS/DFS di sesi ini.")
            st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # RIGHT COLUMN
    # -----------------------------------------------------------------------
    with right_col:
        graph = st.session_state.graph

        total_nodes = graph.number_of_nodes()
        total_edges = graph.number_of_edges()
        avg_degree = (
            round(
                sum(graph.in_degree(n) + graph.out_degree(n) for n in graph.nodes())
                / total_nodes,
                2,
            )
            if total_nodes
            else 0.0
        )
        components = nx.number_weakly_connected_components(graph) if total_nodes else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Nodes", total_nodes)
        m2.metric("Total Directed Edges", total_edges)
        m3.metric("Avg Total Degree", avg_degree)
        m4.metric("Weak Components", components)

        st.markdown('<div class="graph-shell">', unsafe_allow_html=True)
        clicked_node = _build_agraph(
            graph=graph,
            selected_node=selected_node_value,
            min_degree=min_degree,
            highlight_mode=highlight_mode,
            custom_nodes=custom_nodes,
            height=420,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if clicked_node:
            st.session_state.selected_node = clicked_node
            selected_node_value = clicked_node

        # -------------------------------------------------------------------
        # ANIMATION SECTION
        # -------------------------------------------------------------------
        if st.session_state.animation_steps:
            st.markdown("---")
            st.markdown(
                f"### Algorithm Animation — *{st.session_state.animation_type}*"
            )

            anim_graph = st.session_state.graph
            anim_steps = st.session_state.animation_steps
            anim_start = st.session_state.animation_start
            anim_end = st.session_state.animation_end
            anim_pos = st.session_state.animation_pos

            # Legend
            legend_html = """
            <div style="display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px 0;">
              <span style="background:#f59e0b;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">Current</span>
              <span style="background:#22c55e;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">Visited</span>
              <span style="background:#3b82f6;color:white;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">Frontier / Stack</span>
              <span style="background:#8b5cf6;color:white;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">Start</span>
              <span style="background:#ef4444;color:white;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">End</span>
              <span style="background:#cbd5e1;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;">Unvisited</span>
            </div>
            """
            st.markdown(legend_html, unsafe_allow_html=True)

            sp_col, btn_col = st.columns([3, 1])
            anim_speed = sp_col.slider(
                "Kecepatan animasi (detik/step)",
                min_value=0.1,
                max_value=2.0,
                value=0.5,
                step=0.1,
                key="anim_speed",
            )
            play_anim = btn_col.button("▶ Play", type="primary", key="play_anim_btn")

            step_info_placeholder = st.empty()
            anim_placeholder = st.empty()

            # Show initial (last) state by default
            if anim_steps:
                last_step = anim_steps[-1]
                with step_info_placeholder.container():
                    total = len(anim_steps)
                    st.caption(f"Step {total}/{total}: {last_step['message']}")
                with anim_placeholder.container():
                    st.markdown('<div class="anim-shell">', unsafe_allow_html=True)
                    _build_agraph_for_animation(
                    anim_graph, last_step, anim_start, anim_end, pos=anim_pos, height=320, step_idx="initial"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

            if play_anim:
                for i, step in enumerate(anim_steps):
                    with step_info_placeholder.container():
                        progress = (i + 1) / len(anim_steps)
                        st.progress(progress, text=f"Step {i + 1}/{len(anim_steps)}: {step['message']}")
                    with anim_placeholder.container():
                        st.markdown('<div class="anim-shell">', unsafe_allow_html=True)
                        _build_agraph_for_animation(
                        anim_graph, step, anim_start, anim_end, pos=anim_pos, height=320, step_idx=i
                        )
                        st.markdown("</div>", unsafe_allow_html=True)
                    time.sleep(anim_speed)

                # After animation ends, show final step
                with step_info_placeholder.container():
                    st.success(
                        f"Animasi selesai! Total {len(anim_steps)} langkah."
                    )

        # -------------------------------------------------------------------
        # NODE DETAIL
        # -------------------------------------------------------------------
        st.markdown("### Node Detail")
        effective_selected = st.session_state.selected_node or selected_node_value
        if effective_selected and graph.has_node(effective_selected):
            in_deg = graph.in_degree(effective_selected)
            out_deg = graph.out_degree(effective_selected)
            neighbors_out = sorted([target for _, target in graph.out_edges(effective_selected)])
            neighbors_in = sorted([source for source, _ in graph.in_edges(effective_selected)])

            d1, d2, d3 = st.columns(3)
            d1.metric("In Degree", in_deg)
            d2.metric("Out Degree", out_deg)
            d3.metric("Total", in_deg + out_deg)

            st.markdown(f"**Selected Node:** `{effective_selected}`")
            st.write("Outgoing:", ", ".join(neighbors_out) if neighbors_out else "-")
            st.write("Incoming:", ", ".join(neighbors_in) if neighbors_in else "-")
        else:
            st.info("Klik node pada graph (kanan) atau pilih dari control panel untuk melihat detail.")

        st.markdown("### Data Snapshots")
        nodes_df, edges_df = _graph_to_dataframes(graph)
        result_df = pd.DataFrame(st.session_state.results)
        history_df = pd.DataFrame(
            [{"no": idx, "path": p} for idx, p in enumerate(st.session_state.history, 1)]
        )

        with st.expander("Nodes (preview)", expanded=False):
            st.dataframe(
                nodes_df if not nodes_df.empty else pd.DataFrame({"info": ["kosong"]}),
                width="stretch",
            )
        with st.expander("Edges Directed (preview)", expanded=False):
            st.dataframe(
                edges_df if not edges_df.empty else pd.DataFrame({"info": ["kosong"]}),
                width="stretch",
            )
        with st.expander("Results (preview)", expanded=False):
            st.dataframe(
                result_df if not result_df.empty else pd.DataFrame({"info": ["kosong"]}),
                width="stretch",
            )
        with st.expander("History (preview)", expanded=False):
            st.dataframe(
                history_df if not history_df.empty else pd.DataFrame({"info": ["kosong"]}),
                width="stretch",
            )


if __name__ == "__main__":
    main()
