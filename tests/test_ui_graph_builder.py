import unittest

import pandas as pd

from ui.graph_builder import (
    apply_degree_filter,
    build_graph_data,
    compute_node_insight,
    extract_path_edges,
)


class TestGraphBuilder(unittest.TestCase):
    def test_build_graph_data_and_categories(self):
        nodes_df = pd.DataFrame({"id": [0, 1, 2, 3], "name": ["A", "B", "C", "D"]})
        edges_df = pd.DataFrame({"from": ["A", "A", "A", "B"], "to": ["B", "C", "D", "C"]})

        graph_data = build_graph_data(nodes_df, edges_df)

        self.assertEqual(graph_data.graph.number_of_nodes(), 4)
        self.assertEqual(graph_data.graph.number_of_edges(), 4)
        self.assertEqual(graph_data.node_visuals["A"].degree, 3)
        self.assertEqual(graph_data.node_visuals["A"].category, "medium")

    def test_compute_node_insight(self):
        nodes_df = pd.DataFrame({"id": [0, 1, 2], "name": ["A", "B", "C"]})
        edges_df = pd.DataFrame({"from": ["A", "A"], "to": ["B", "C"]})
        graph_data = build_graph_data(nodes_df, edges_df)

        insight = compute_node_insight(graph_data, "A")
        self.assertEqual(insight.degree, 2)
        self.assertEqual(insight.category, "medium")
        self.assertEqual(insight.neighbors, ["B", "C"])

    def test_extract_path_edges(self):
        result_df = pd.DataFrame(
            {
                "start": ["A", "C"],
                "end": ["E", "D"],
                "path": ["A-B-E", "C-B-A-D"],
                "distance": [2, 3],
            }
        )

        path_edges = extract_path_edges(result_df)

        self.assertIn(("A", "B"), path_edges)
        self.assertIn(("B", "E"), path_edges)
        self.assertIn(("A", "D"), path_edges)
        self.assertIn(("B", "C"), path_edges)

    def test_apply_degree_filter(self):
        nodes_df = pd.DataFrame({"id": [0, 1, 2], "name": ["A", "B", "C"]})
        edges_df = pd.DataFrame({"from": ["A", "A"], "to": ["B", "C"]})
        graph_data = build_graph_data(nodes_df, edges_df)

        filtered = apply_degree_filter(graph_data, min_degree=2)

        self.assertEqual(sorted(list(filtered.graph.nodes())), ["A"])
        self.assertEqual(filtered.graph.number_of_edges(), 0)


if __name__ == "__main__":
    unittest.main()
