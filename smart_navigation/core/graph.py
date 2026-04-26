"""Graph model for Smart Navigation System."""


class Graph:
    """Undirected graph represented by adjacency list."""

    def __init__(self):
        self.adj: dict[str, list[str]] = {}

    def add_node(self, node: str) -> None:
        node = node.strip()
        if not node:
            return
        if node not in self.adj:
            self.adj[node] = []

    def add_edge(self, source: str, target: str) -> None:
        source = source.strip()
        target = target.strip()
        if not source or not target:
            return

        self.add_node(source)
        self.add_node(target)

        if target not in self.adj[source]:
            self.adj[source].append(target)
        if source not in self.adj[target]:
            self.adj[target].append(source)

    def has_node(self, node: str) -> bool:
        return node in self.adj

    def neighbors(self, node: str) -> list[str]:
        return self.adj.get(node, [])

    def to_display_string(self) -> str:
        if not self.adj:
            return "(graph kosong)"

        lines = []
        for node in sorted(self.adj.keys()):
            neighbors = ", ".join(self.adj[node])
            lines.append(f"{node} -> [{neighbors}]")
        return "\n".join(lines)
