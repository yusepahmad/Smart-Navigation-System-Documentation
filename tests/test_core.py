import csv
import tempfile
import unittest
from pathlib import Path

from main import load_graph, load_queries, save_history, save_result
from smart_navigation.core import Graph
from smart_navigation.models import QueryResult
from smart_navigation.services import NavigationService


class TestGraph(unittest.TestCase):
    def test_add_node_unique(self):
        graph = Graph()
        graph.add_node("A")
        graph.add_node("A")
        self.assertEqual(list(graph.adj.keys()), ["A"])

    def test_add_edge_undirected(self):
        graph = Graph()
        graph.add_edge("A", "B")
        self.assertIn("B", graph.adj["A"])
        self.assertIn("A", graph.adj["B"])


class TestNavigationService(unittest.TestCase):
    def setUp(self):
        self.graph = Graph()
        self.graph.add_edge("A", "B")
        self.graph.add_edge("A", "D")
        self.graph.add_edge("B", "C")
        self.graph.add_edge("B", "E")
        self.graph.add_edge("D", "E")
        self.service = NavigationService()

    def test_bfs_found(self):
        path = self.service.bfs_shortest_path(self.graph, "A", "E")
        self.assertEqual(path, ["A", "B", "E"])
        self.assertEqual(len(path) - 1, 2)

    def test_bfs_invalid_node(self):
        path = self.service.bfs_shortest_path(self.graph, "A", "Z")
        self.assertEqual(path, [])

    def test_bfs_not_found(self):
        disconnected = Graph()
        disconnected.add_edge("A", "B")
        disconnected.add_edge("C", "D")
        path = self.service.bfs_shortest_path(disconnected, "A", "D")
        self.assertEqual(path, [])

    def test_dfs(self):
        result = self.service.dfs_exploration(self.graph, "A")
        self.assertTrue(result)
        self.assertEqual(result[0], "A")
        self.assertEqual(set(result), {"A", "B", "C", "D", "E"})
        self.assertEqual(len(result), len(set(result)))


class TestCsvIO(unittest.TestCase):
    def test_load_and_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            nodes_file = tmp_path / "nodes.csv"
            edges_file = tmp_path / "edges.csv"
            query_file = tmp_path / "query.csv"
            result_file = tmp_path / "result.csv"
            history_file = tmp_path / "history.csv"

            nodes_file.write_text("id,name\n0,A\n1,B\n2,C\n", encoding="utf-8")
            edges_file.write_text("from,to\nA,B\nB,C\n", encoding="utf-8")
            query_file.write_text("start,end\nA,C\n", encoding="utf-8")

            graph = load_graph(nodes_file, edges_file)
            self.assertTrue(graph.has_node("A"))
            self.assertTrue(graph.has_node("C"))
            self.assertIn("B", graph.neighbors("A"))

            queries = load_queries(query_file)
            self.assertEqual(queries, [{"start": "A", "end": "C"}])

            rows = [{"start": "A", "end": "C", "path": ["A", "B", "C"]}]
            save_result(result_file, rows)
            save_history(history_file, [["A", "B", "C"]])

            with result_file.open("r", encoding="utf-8") as file:
                result_rows = list(csv.DictReader(file))
            with history_file.open("r", encoding="utf-8") as file:
                history_rows = list(csv.DictReader(file))

            self.assertEqual(result_rows[0]["path"], "A-B-C")
            self.assertEqual(result_rows[0]["distance"], "2")
            self.assertEqual(history_rows[0]["no"], "1")
            self.assertEqual(history_rows[0]["path"], "A-B-C")

    def test_query_result_distance(self):
        result = QueryResult(start="A", end="C", path=["A", "B", "C"])
        self.assertEqual(result.distance, 2)


if __name__ == "__main__":
    unittest.main()
