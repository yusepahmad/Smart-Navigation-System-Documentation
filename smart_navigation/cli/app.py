"""CLI application orchestration."""

from pathlib import Path

from smart_navigation.core.graph import Graph
from smart_navigation.core.history import History
from smart_navigation.io.csv_repository import CsvRepository
from smart_navigation.models.query_result import QueryResult
from smart_navigation.services.navigation_service import NavigationService


class SmartNavigationCLI:
    """Interactive command line application."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.output_dir = self.base_dir / "output"

        self.graph = Graph()
        self.history = History()

        self.navigation_service = NavigationService()
        self.csv_repository = CsvRepository()

    def _print_menu(self) -> None:
        print("\n=== Smart Navigation System ===")
        print("1. Tambah Node")
        print("2. Tambah Edge")
        print("3. Tampilkan Graph")
        print("4. BFS Shortest Path (Manual)")
        print("5. DFS Exploration")
        print("6. Tampilkan History")
        print("7. Load Graph dari CSV")
        print("8. Batch Query dari CSV + Export Result")
        print("9. Export History")
        print("0. Keluar")

    def _format_path(self, path: list[str]) -> str:
        return " -> ".join(path)

    def _run_manual_query(self) -> QueryResult | None:
        start = input("Start node: ").strip()
        end = input("End node: ").strip()

        if not self.graph.has_node(start) or not self.graph.has_node(end):
            print("Node tidak ditemukan. Silakan coba lagi.")
            return None

        path = self.navigation_service.bfs_shortest_path(self.graph, start, end)
        if not path:
            print(f"Path dari {start} ke {end} tidak ditemukan.")
            return None

        self.history.push(path)
        result = QueryResult(start=start, end=end, path=path)

        print(f"Shortest path: {self._format_path(path)}")
        print(f"Distance: {result.distance}")
        return result

    def _run_batch_query(self) -> list[QueryResult]:
        query_file = self.data_dir / "query.csv"
        if not query_file.exists():
            print(f"File query tidak ditemukan: {query_file}")
            return []

        queries = self.csv_repository.load_queries(query_file)
        if not queries:
            print("Tidak ada query valid di file.")
            return []

        results: list[QueryResult] = []

        for query in queries:
            start = query["start"]
            end = query["end"]

            if not self.graph.has_node(start) or not self.graph.has_node(end):
                print(f"[SKIP] Node invalid: {start} -> {end}")
                continue

            path = self.navigation_service.bfs_shortest_path(self.graph, start, end)
            if not path:
                print(f"[SKIP] Path tidak ditemukan: {start} -> {end}")
                continue

            self.history.push(path)
            result = QueryResult(start=start, end=end, path=path)
            results.append(result)
            print(f"{start} -> {end}: {self._format_path(path)} (distance={result.distance})")

        return results

    def _load_graph_from_csv(self) -> None:
        nodes_file = self.data_dir / "nodes.csv"
        edges_file = self.data_dir / "edges.csv"

        if not nodes_file.exists() or not edges_file.exists():
            print("nodes.csv atau edges.csv belum ada di folder data/.")
            return

        self.graph = self.csv_repository.load_graph(nodes_file, edges_file)
        print("Graph berhasil dimuat dari CSV.")

    def run(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        while True:
            self._print_menu()
            choice = input("Pilih menu: ").strip()

            if choice == "1":
                node = input("Masukkan nama node: ").strip()
                if not node:
                    print("Node tidak boleh kosong.")
                    continue
                self.graph.add_node(node)
                print(f"Node '{node}' ditambahkan.")

            elif choice == "2":
                source = input("Node asal: ").strip()
                target = input("Node tujuan: ").strip()
                if not source or not target:
                    print("Node asal/tujuan tidak boleh kosong.")
                    continue
                self.graph.add_edge(source, target)
                print(f"Edge '{source}' <-> '{target}' ditambahkan.")

            elif choice == "3":
                print(self.graph.to_display_string())

            elif choice == "4":
                self._run_manual_query()

            elif choice == "5":
                start = input("Start node DFS: ").strip()
                result = self.navigation_service.dfs_exploration(self.graph, start)
                if not result:
                    print("Node tidak ditemukan atau graph kosong.")
                else:
                    print("DFS exploration:")
                    print(self._format_path(result))

            elif choice == "6":
                print(self.history.to_display_string())

            elif choice == "7":
                self._load_graph_from_csv()

            elif choice == "8":
                results = self._run_batch_query()
                if not results:
                    print("Tidak ada result yang diekspor.")
                    continue

                result_file = self.output_dir / "result.csv"
                self.csv_repository.save_result(result_file, results)
                print(f"Result disimpan ke: {result_file}")

            elif choice == "9":
                history_file = self.output_dir / "history.csv"
                self.csv_repository.save_history(history_file, self.history.stack)
                print(f"History disimpan ke: {history_file}")

            elif choice == "0":
                print("Keluar dari program.")
                break

            else:
                print("Pilihan tidak valid. Coba lagi.")
