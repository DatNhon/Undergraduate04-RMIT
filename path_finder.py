from __future__ import annotations

from heapq import heappop, heappush
from typing import Iterable, List, Optional, Sequence, Set, Tuple

from graph_models import CompactRoadGraph, PathResult, RoadGraph


class SmartPathFinder:
    def __init__(self, graph: RoadGraph | CompactRoadGraph):
        self.graph = graph

    def route(
        self,
        source: int,
        destination: int,
        departure_hour: int,
        avoid_nodes: Optional[Iterable[int]] = None,
        avoid_edges: Optional[Iterable[Tuple[int, int]]] = None,
    ) -> Tuple[Optional[PathResult], Optional[PathResult]]:
        nodes_to_avoid = set(avoid_nodes or [])
        edges_to_avoid = {
            self._normalise_edge(edge[0], edge[1])
            for edge in (avoid_edges or [])
        }

        shortest_distance_path = self._dijkstra(
            source=source,
            destination=destination,
            departure_hour=departure_hour,
            avoid_nodes=nodes_to_avoid,
            avoid_edges=edges_to_avoid,
            optimise_for="distance",
        )

        shortest_time_path = self._dijkstra(
            source=source,
            destination=destination,
            departure_hour=departure_hour,
            avoid_nodes=nodes_to_avoid,
            avoid_edges=edges_to_avoid,
            optimise_for="time",
        )

        return shortest_distance_path, shortest_time_path

    def _dijkstra(
        self,
        source: int,
        destination: int,
        departure_hour: int,
        avoid_nodes: Set[int],
        avoid_edges: Set[Tuple[int, int]],
        optimise_for: str,
    ) -> Optional[PathResult]:
        if not (0 <= source < self.graph.node_count):
            raise ValueError("source node is out of range")
        if not (0 <= destination < self.graph.node_count):
            raise ValueError("destination node is out of range")
        if not (0 <= departure_hour <= 23):
            raise ValueError("departure_hour must be in range 0..23")
        if optimise_for not in {"distance", "time"}:
            raise ValueError("optimise_for must be 'distance' or 'time'")

        if source in avoid_nodes or destination in avoid_nodes:
            return None

        inf = float("inf")
        best_cost = [inf] * self.graph.node_count
        best_distance = [inf] * self.graph.node_count
        best_time = [inf] * self.graph.node_count
        predecessor = [-1] * self.graph.node_count

        best_cost[source] = 0.0
        best_distance[source] = 0.0
        best_time[source] = 0.0

        heap: List[Tuple[float, float, int]] = []
        heappush(heap, (0.0, 0.0, source))

        while heap:
            cost_so_far, _, current = heappop(heap)
            if cost_so_far > best_cost[current]:
                continue
            if current == destination:
                break

            current_minutes = best_time[current]
            hour_index = int((departure_hour + current_minutes / 60.0) % 24)

            for (
                nxt,
                edge_distance,
                hourly_times,
            ) in self._iter_neighbours(current):
                if nxt in avoid_nodes:
                    continue
                if self._normalise_edge(current, nxt) in avoid_edges:
                    continue

                edge_time = hourly_times[hour_index]
                candidate_distance = best_distance[current] + edge_distance
                candidate_time = best_time[current] + edge_time

                if optimise_for == "distance":
                    candidate_cost = candidate_distance
                    tie_value = candidate_time
                    current_tie = best_time[nxt]
                else:
                    candidate_cost = candidate_time
                    tie_value = candidate_distance
                    current_tie = best_distance[nxt]

                should_update = False
                if candidate_cost < best_cost[nxt] - 1e-12:
                    should_update = True
                elif abs(candidate_cost - best_cost[nxt]) <= 1e-12:
                    if tie_value < current_tie - 1e-12:
                        should_update = True

                if should_update:
                    best_cost[nxt] = candidate_cost
                    best_distance[nxt] = candidate_distance
                    best_time[nxt] = candidate_time
                    predecessor[nxt] = current
                    heappush(
                        heap,
                        (candidate_cost, candidate_time, nxt),
                    )

        if predecessor[destination] == -1 and source != destination:
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
