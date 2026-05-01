"""Entry point and compatibility API for Smart Navigation System."""

from pathlib import Path

from smart_navigation.cli import SmartNavigationCLI
from smart_navigation.io import CsvRepository
from smart_navigation.models import QueryResult


_csv_repository = CsvRepository()


def load_graph(nodes_file: str | Path, edges_file: str | Path):
    return _csv_repository.load_graph(nodes_file, edges_file)


def load_queries(query_file: str | Path):
    return _csv_repository.load_queries(query_file)


def save_result(filename: str | Path, data: list[dict[str, object]]):
    mapped: list[QueryResult] = []
    for row in data:
        path = row.get("path", [])
        if not isinstance(path, list):
            path = []
        mapped.append(
            QueryResult(
                start=str(row.get("start", "")),
                end=str(row.get("end", "")),
                path=path,
            )
        )
    _csv_repository.save_result(filename, mapped)


def save_history(filename: str | Path, history_stack: list[list[str]]):
    _csv_repository.save_history(filename, history_stack)


def main() -> None:
    app = SmartNavigationCLI(base_dir=Path(__file__).resolve().parent)
    app.run()


if __name__ == "__main__":
    main()
