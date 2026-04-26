"""Navigation service containing BFS and DFS operations."""

from collections import deque

from smart_navigation.core.graph import Graph


class NavigationService:
    """Service for graph traversal and pathfinding."""

    def bfs_shortest_path(self, graph: Graph, start: str, end: str) -> list[str]:
        if not graph.has_node(start) or not graph.has_node(end):
            return []

        visited = set([start])
        queue = deque([start])
        parent: dict[str, str | None] = {start: None}

        while queue:
            current = queue.popleft()
            if current == end:
                break

            for neighbor in graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        if end not in parent:
            return []

        path = []
        cur: str | None = end
        while cur is not None:
            path.append(cur)
            cur = parent[cur]

        path.reverse()
        return path

    def dfs_exploration(self, graph: Graph, start: str) -> list[str]:
        if not graph.has_node(start):
            return []

        visited = set()
        stack = [start]
        result = []

        while stack:
            node = stack.pop()
            if node in visited:
                continue

            visited.add(node)
            result.append(node)

            for neighbor in reversed(graph.neighbors(node)):
                if neighbor not in visited:
                    stack.append(neighbor)

        return result
