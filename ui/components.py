"""Reusable Streamlit components for the dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.graph_builder import DataBundle, GraphData, NodeInsight


def inject_custom_css() -> None:
    """Inject lightweight modern styling."""
    st.markdown(
        """
        <style>
        .main > div {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }
        .block-container {
            max-width: 1200px;
            padding-top: 1.2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        .ui-card {
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 1rem 1.1rem;
            background: linear-gradient(140deg, #ffffff 0%, #f8fafc 100%);
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
            margin-bottom: 0.9rem;
        }
        .ui-title {
            font-size: 1.08rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.35rem;
        }
        .ui-meta {
            color: #475569;
            font-size: 0.93rem;
        }
        .section-divider {
            height: 1px;
            background: linear-gradient(90deg, #e2e8f0, transparent);
            margin: 1.2rem 0 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.title("Smart Navigation Dashboard")
    st.caption(
        "UI interaktif berbasis Streamlit + Pyvis untuk eksplorasi node, edge, dan insight relasi."
    )


def render_metrics(graph_data: GraphData) -> None:
    graph = graph_data.graph
    total_nodes = graph.number_of_nodes()
    total_edges = graph.number_of_edges()
    avg_degree = round((2 * total_edges / total_nodes), 2) if total_nodes else 0.0

    try:
        import networkx as nx

        connected_components = nx.number_connected_components(graph) if total_nodes else 0
    except Exception:  # noqa: BLE001
        connected_components = 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Nodes", total_nodes)
    col2.metric("Total Edges", total_edges)
    col3.metric("Avg Degree", avg_degree)
    col4.metric("Connected Components", connected_components)


def render_legend() -> None:
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("**Legend Node Category**")
    c1, c2, c3 = st.columns(3)
    c1.markdown("<span style='color:#ef4444'>●</span> High Degree", unsafe_allow_html=True)
    c2.markdown("<span style='color:#0ea5e9'>●</span> Medium Degree", unsafe_allow_html=True)
    c3.markdown("<span style='color:#94a3b8'>●</span> Low Degree", unsafe_allow_html=True)


def render_node_detail(insight: NodeInsight) -> None:
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("Node Detail")

    if insight.category == "unknown":
        st.info("Pilih node dari sidebar untuk melihat detail.")
        return

    st.markdown(
        f"""
        <div class="ui-card">
          <div class="ui-title">Node: {insight.selected_node}</div>
          <div class="ui-meta">Degree: {insight.degree} | Category: {insight.category}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 3])
    col1.write("**Neighbors**")
    if insight.neighbors:
        col1.write(", ".join(insight.neighbors))
    else:
        col1.write("Tidak ada tetangga.")

    col2.write("**Related Edges**")
    if insight.related_edges:
        for source, target in insight.related_edges:
            col2.write(f"- {source} - {target}")
    else:
        col2.write("Tidak ada relasi.")


def _safe_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({"info": ["Data kosong"]})
    return df


def render_data_expanders(bundle: DataBundle) -> None:
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.subheader("Data Explorer")

    with st.expander("Query Data (data/query.csv)", expanded=False):
        st.dataframe(_safe_table(bundle.query_df), use_container_width=True)

    with st.expander("Result Data (output/result.csv)", expanded=False):
        st.dataframe(_safe_table(bundle.result_df), use_container_width=True)

    with st.expander("History Data (output/history.csv)", expanded=False):
        st.dataframe(_safe_table(bundle.history_df), use_container_width=True)


def render_warnings(warnings: list[str]) -> None:
    for warning in warnings:
        st.warning(warning)
