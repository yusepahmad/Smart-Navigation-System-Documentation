"""Graph data preparation and rendering utilities for Streamlit UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import networkx as nx
import pandas as pd


@dataclass
class NodeVisual:
    """Visual metadata for a node."""

    node_id: str
    degree: int
    category: str
    color: str
    size: int


@dataclass
class GraphData:
    """Graph container with UI-specific metadata."""

    graph: nx.Graph
    node_visuals: dict[str, NodeVisual]
    path_edges: set[tuple[str, str]] = field(default_factory=set)


@dataclass
class NodeInsight:
    """Detailed node insight for side panel display."""

    selected_node: str
    degree: int
    neighbors: list[str]
    related_edges: list[tuple[str, str]]
    category: str


@dataclass
class DataBundle:
    """CSV datasets loaded for dashboard."""

    nodes_df: pd.DataFrame
    edges_df: pd.DataFrame
    query_df: pd.DataFrame
    result_df: pd.DataFrame
    history_df: pd.DataFrame
    warnings: list[str] = field(default_factory=list)


def _safe_read_csv(path: str | Path, label: str, warnings: list[str]) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        warnings.append(f"{label} tidak ditemukan: {file_path}")
        return pd.DataFrame()

    try:
        return pd.read_csv(file_path)
    except Exception as exc:
        warnings.append(f"Gagal membaca {label}: {exc}")
        return pd.DataFrame()


def _ensure_columns(df: pd.DataFrame, columns: list[str], label: str, warnings: list[str]) -> pd.DataFrame:
    if df.empty:
        return df

    missing = [col for col in columns if col not in df.columns]
    if missing:
        warnings.append(f"Kolom {label} tidak lengkap. Missing: {', '.join(missing)}")
        return pd.DataFrame(columns=columns)

    return df


def _edge_key(source: str, target: str) -> tuple[str, str]:
    return tuple(sorted((source, target)))


def _color_from_degree(degree: int) -> tuple[str, str]:
    if degree >= 4:
        return "high", "#ef4444"
    if degree >= 2:
        return "medium", "#0ea5e9"
    return "low", "#94a3b8"


def load_csv_bundle(
    nodes_path: str | Path = "data/nodes.csv",
    edges_path: str | Path = "data/edges.csv",
    query_path: str | Path = "data/query.csv",
    result_path: str | Path = "output/result.csv",
    history_path: str | Path = "output/history.csv",
) -> DataBundle:
    """Load all dashboard CSV files and return a structured bundle."""
    warnings: list[str] = []

    nodes_df = _safe_read_csv(nodes_path, "nodes.csv", warnings)
    edges_df = _safe_read_csv(edges_path, "edges.csv", warnings)
    query_df = _safe_read_csv(query_path, "query.csv", warnings)
    result_df = _safe_read_csv(result_path, "result.csv", warnings)
    history_df = _safe_read_csv(history_path, "history.csv", warnings)

    nodes_df = _ensure_columns(nodes_df, ["id", "name"], "nodes.csv", warnings)
    edges_df = _ensure_columns(edges_df, ["from", "to"], "edges.csv", warnings)
    query_df = _ensure_columns(query_df, ["start", "end"], "query.csv", warnings)

    if not result_df.empty:
        minimum_cols = ["start", "end", "path", "distance"]
        missing = [col for col in minimum_cols if col not in result_df.columns]
        if missing:
            warnings.append("Kolom result.csv tidak lengkap. Path highlighting dinonaktifkan.")
            result_df = pd.DataFrame(columns=minimum_cols)

    if not history_df.empty and "path" not in history_df.columns:
        warnings.append("Kolom history.csv tidak lengkap. History table akan dikosongkan.")
        history_df = pd.DataFrame(columns=["no", "path"])

    return DataBundle(
        nodes_df=nodes_df,
        edges_df=edges_df,
        query_df=query_df,
        result_df=result_df,
        history_df=history_df,
        warnings=warnings,
    )


def build_graph_data(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> GraphData:
    """Build network graph and visual metadata from nodes and edges data."""
    graph = nx.Graph()

    if not nodes_df.empty and "name" in nodes_df.columns:
        node_names = [str(name).strip() for name in nodes_df["name"].dropna().tolist()]
        for node_name in node_names:
            if node_name:
                graph.add_node(node_name)

    if not edges_df.empty and {"from", "to"}.issubset(edges_df.columns):
        for _, row in edges_df.iterrows():
            source = str(row["from"]).strip()
            target = str(row["to"]).strip()
            if source and target:
                graph.add_edge(source, target)

    node_visuals: dict[str, NodeVisual] = {}
    for node in graph.nodes:
        degree = int(graph.degree(node))
        category, color = _color_from_degree(degree)
        size = 18 + (degree * 4)
        node_visuals[node] = NodeVisual(
            node_id=node,
            degree=degree,
            category=category,
            color=color,
            size=size,
        )

    return GraphData(graph=graph, node_visuals=node_visuals)


def extract_path_edges(result_df: pd.DataFrame) -> set[tuple[str, str]]:
    """Extract all path edges from result.csv path column."""
    path_edges: set[tuple[str, str]] = set()
    if result_df.empty or "path" not in result_df.columns:
        return path_edges

    for raw_path in result_df["path"].dropna().astype(str):
        nodes = [node.strip() for node in raw_path.split("-") if node.strip()]
        for idx in range(len(nodes) - 1):
            path_edges.add(_edge_key(nodes[idx], nodes[idx + 1]))

    return path_edges


def apply_degree_filter(graph_data: GraphData, min_degree: int) -> GraphData:
    """Return filtered GraphData containing nodes with degree >= min_degree."""
    selected_nodes = [
        node_id
        for node_id, visual in graph_data.node_visuals.items()
        if visual.degree >= min_degree
    ]

    filtered_graph = graph_data.graph.subgraph(selected_nodes).copy()
    filtered_visuals = {
        node_id: visual
        for node_id, visual in graph_data.node_visuals.items()
        if node_id in filtered_graph
    }

    filtered_path_edges = {
        edge
        for edge in graph_data.path_edges
        if edge[0] in filtered_graph and edge[1] in filtered_graph
    }

    return GraphData(
        graph=filtered_graph,
        node_visuals=filtered_visuals,
        path_edges=filtered_path_edges,
    )


def compute_node_insight(graph_data: GraphData, selected_node: str) -> NodeInsight:
    """Compute selected node details for UI panel."""
    if selected_node not in graph_data.graph:
        return NodeInsight(
            selected_node=selected_node,
            degree=0,
            neighbors=[],
            related_edges=[],
            category="unknown",
        )

    neighbors = sorted(list(graph_data.graph.neighbors(selected_node)))
    related_edges = [_edge_key(selected_node, neighbor) for neighbor in neighbors]
    visual = graph_data.node_visuals[selected_node]

    return NodeInsight(
        selected_node=selected_node,
        degree=visual.degree,
        neighbors=neighbors,
        related_edges=related_edges,
        category=visual.category,
    )


def render_network(
    graph_data: GraphData,
    selected_node: str | None,
    mode: str,
    height: int,
    width: int,
) -> str:
    """Render GraphData with Pyvis and return generated HTML."""
    from pyvis.network import Network

    network = Network(
        height=f"{height}px",
        width=f"{width}px",
        directed=False,
        notebook=False,
        bgcolor="#f8fafc",
        font_color="#0f172a",
    )

    network.set_options(
        """
        {
          "physics": {
            "enabled": true,
            "forceAtlas2Based": {
              "gravitationalConstant": -35,
              "springLength": 130,
              "springConstant": 0.07
            },
            "solver": "forceAtlas2Based",
            "stabilization": {
              "enabled": true,
              "iterations": 120
            }
          },
          "interaction": {
            "hover": true,
            "zoomView": true,
            "dragNodes": true,
            "tooltipDelay": 150
          }
        }
        """
    )

    highlighted_edges: set[tuple[str, str]] = set()
    if selected_node and selected_node in graph_data.graph and mode == "neighbors only":
        highlighted_edges = {
            _edge_key(selected_node, neighbor)
            for neighbor in graph_data.graph.neighbors(selected_node)
        }
    elif mode == "path from result.csv":
        highlighted_edges = set(graph_data.path_edges)

    for node_id, visual in graph_data.node_visuals.items():
        border_width = 4 if selected_node and node_id == selected_node else 1
        node_color = {
            "border": "#0f172a" if selected_node == node_id else "#cbd5e1",
            "background": visual.color,
            "highlight": {"border": "#111827", "background": visual.color},
            "hover": {"border": "#111827", "background": visual.color},
        }
        network.add_node(
            node_id,
            label=node_id,
            title=f"Node: {node_id}<br>Degree: {visual.degree}<br>Category: {visual.category}",
            size=visual.size,
            color=node_color,
            borderWidth=border_width,
            shape="dot",
        )

    for source, target in graph_data.graph.edges:
        key = _edge_key(source, target)
        is_highlighted = key in highlighted_edges
        network.add_edge(
            source,
            target,
            color="#f97316" if is_highlighted else "#94a3b8",
            width=4 if is_highlighted else 1,
            title=f"Relasi: {source} - {target}",
        )

    return network.generate_html()
