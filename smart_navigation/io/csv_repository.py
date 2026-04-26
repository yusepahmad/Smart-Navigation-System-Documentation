"""CSV repository for loading and saving graph/query/result/history data."""

import csv
from pathlib import Path

from smart_navigation.core.graph import Graph
from smart_navigation.models.query_result import QueryResult


class CsvRepository:
    """Repository for CSV-based persistence."""

    def load_graph(self, nodes_file: str | Path, edges_file: str | Path) -> Graph:
        graph = Graph()

        with Path(nodes_file).open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                graph.add_node(row.get("name", ""))

        with Path(edges_file).open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                graph.add_edge(row.get("from", ""), row.get("to", ""))

        return graph

    def load_queries(self, query_file: str | Path) -> list[dict[str, str]]:
        queries: list[dict[str, str]] = []

        with Path(query_file).open("r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                start = row.get("start", "").strip()
                end = row.get("end", "").strip()
                if start and end:
                    queries.append({"start": start, "end": end})

        return queries

    def save_result(self, filename: str | Path, data: list[QueryResult]) -> None:
        filename = Path(filename)
        filename.parent.mkdir(parents=True, exist_ok=True)

        with filename.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["start", "end", "path", "distance"])

            for row in data:
                writer.writerow([row.start, row.end, "-".join(row.path), row.distance])

    def save_history(self, filename: str | Path, history_stack: list[list[str]]) -> None:
        filename = Path(filename)
        filename.parent.mkdir(parents=True, exist_ok=True)

        with filename.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["no", "path"])

            for idx, path in enumerate(history_stack, 1):
                writer.writerow([idx, "-".join(path)])
