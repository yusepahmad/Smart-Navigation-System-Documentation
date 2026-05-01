"""Navigation service containing Dijkstra and DFS operations."""

import heapq

from smart_navigation.core.graph import Graph


class NavigationService:
    """Service for graph traversal and pathfinding."""

    def find_optimal_path(self, graph: Graph, start: str, end: str, optimize_by: str = "distance") -> tuple[list[str], float, float]:
        """Finds the optimal path using Dijkstra's algorithm.
        
        Returns:
            tuple containing (path: list[str], total_distance: float, total_time: float)
            If no path is found, returns ([], 0.0, 0.0)
        """
        if not graph.has_node(start) or not graph.has_node(end):
            return [], 0.0, 0.0

        pq = [(0.0, start)]
        
        min_weights = {start: 0.0}
        
        parent: dict[str, tuple[str, float, float] | None] = {start: None}

        while pq:
            current_weight, current = heapq.heappop(pq)

            if current == end:
                break
                
            if current_weight > min_weights.get(current, float('inf')):
                continue

            for neighbor in graph.neighbors(current):
                edge_data = graph.get_edge_data(current, neighbor)
                edge_weight = edge_data.get(optimize_by, 1.0)
                
                new_weight = current_weight + edge_weight

                if new_weight < min_weights.get(neighbor, float('inf')):
                    min_weights[neighbor] = new_weight
                    parent[neighbor] = (current, edge_data.get('distance', 1.0), edge_data.get('time', 1.0))
                    heapq.heappush(pq, (new_weight, neighbor))

        if end not in parent:
            return [], 0.0, 0.0

        path = []
        cur: str | None = end
        total_dist = 0.0
        total_time = 0.0
        
        while cur is not None:
            path.append(cur)
            parent_info = parent[cur]
            if parent_info is not None:
                p_node, d, t = parent_info
                total_dist += d
                total_time += t
                cur = p_node
            else:
                cur = None

        path.reverse()
        return path, round(total_dist, 1), round(total_time, 1)

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
