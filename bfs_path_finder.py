from __future__ import annotations

from collections import deque
from typing import Iterable, List, Optional, Sequence, Tuple

from graph_models import CompactRoadGraph, PathResult, RoadGraph


class BfsPathFinder:
    def __init__(self, graph: RoadGraph | CompactRoadGraph):
        self.graph = graph

    def route(
        self,
        source: int,
        destination: int,
        departure_hour: int,
        avoid_nodes: Optional[Iterable[int]] = None,
        avoid_edges: Optional[Iterable[Tuple[int, int]]] = None,
    ) -> Optional[PathResult]:
        if not (0 <= source < self.graph.node_count):
            raise ValueError("source node is out of range")
        if not (0 <= destination < self.graph.node_count):
            raise ValueError("destination node is out of range")
        if not (0 <= departure_hour <= 23):
            raise ValueError("departure_hour must be in range 0..23")

        nodes_to_avoid = set(avoid_nodes or [])
        edges_to_avoid = {
            self._normalise_edge(edge[0], edge[1])
            for edge in (avoid_edges or [])
        }

        if source in nodes_to_avoid or destination in nodes_to_avoid:
            return None
        if source == destination:
            return PathResult(
                path_nodes=[source],
                total_distance_km=0.0,
                total_travel_minutes=0.0,
            )

        visited = [False] * self.graph.node_count
        predecessor = [-1] * self.graph.node_count
        best_distance = [0.0] * self.graph.node_count
        best_time = [0.0] * self.graph.node_count

        visited[source] = True
        queue = deque([source])

        while queue:
            current = queue.popleft()
            if current == destination:
                break

            current_minutes = best_time[current]
            hour_index = int((departure_hour + current_minutes / 60.0) % 24)

            for (
                nxt,
                edge_distance,
                hourly_times,
            ) in self._iter_neighbours(current):
                if visited[nxt]:
                    continue
                if nxt in nodes_to_avoid:
                    continue
                if self._normalise_edge(current, nxt) in edges_to_avoid:
                    continue

                edge_time = hourly_times[hour_index]
                visited[nxt] = True
                predecessor[nxt] = current
                best_distance[nxt] = best_distance[current] + edge_distance
                best_time[nxt] = best_time[current] + edge_time
                queue.append(nxt)

        if not visited[destination]:
            return None

        path_nodes = self._reconstruct_path(
            predecessor,
            source,
            destination,
        )

        return PathResult(
            path_nodes=path_nodes,
            total_distance_km=round(best_distance[destination], 3),
            total_travel_minutes=round(best_time[destination], 3),
        )

    @staticmethod
    def _reconstruct_path(
        predecessor: Sequence[int],
        source: int,
        destination: int,
    ) -> List[int]:
        path: List[int] = []
        current = destination
        while current != -1:
            path.append(current)
            if current == source:
                break
            current = predecessor[current]
        path.reverse()
        return path

    @staticmethod
    def _normalise_edge(u: int, v: int) -> Tuple[int, int]:
        return (u, v) if u < v else (v, u)

    def _iter_neighbours(
        self,
        node: int,
    ) -> Iterable[Tuple[int, float, Tuple[float, ...]]]:
        if isinstance(self.graph, RoadGraph):
            for edge in self.graph.adjacency[node]:
                yield (
                    edge.to_node,
                    edge.distance_km,
                    edge.hourly_travel_minutes,
                )
            return

        for edge_data in self.graph.iter_edges(node):
            yield edge_data
