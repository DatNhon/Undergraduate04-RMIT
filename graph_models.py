from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


@dataclass(frozen=True)
class Edge:
    to_node: int
    distance_km: float
    hourly_travel_minutes: Tuple[float, ...]


@dataclass(frozen=True)
class PathResult:
    path_nodes: List[int]
    total_distance_km: float
    total_travel_minutes: float


class RoadGraph:
    def __init__(self, node_count: int):
        self.node_count = node_count
        self.adjacency: Dict[int, List[Edge]] = {
            node: [] for node in range(node_count)
        }
        self.node_positions: Optional[List[Tuple[float, float]]] = None

    def add_undirected_edge(
        self,
        u: int,
        v: int,
        distance_km: float,
        hourly_minutes: Sequence[float],
    ) -> None:
        if u == v:
            return
        if len(hourly_minutes) != 24:
            raise ValueError("hourly_minutes must have exactly 24 values")

        hours_tuple = tuple(float(value) for value in hourly_minutes)
        self.adjacency[u].append(
            Edge(v, round(float(distance_km), 3), hours_tuple)
        )
        self.adjacency[v].append(
            Edge(u, round(float(distance_km), 3), hours_tuple)
        )

    def update_edge_hourly_times(
        self,
        u: int,
        v: int,
        new_hourly_minutes: Sequence[float],
    ) -> bool:
        if len(new_hourly_minutes) != 24:
            raise ValueError("new_hourly_minutes must have exactly 24 values")

        updated_uv = self._update_directed(u, v, tuple(new_hourly_minutes))
        updated_vu = self._update_directed(v, u, tuple(new_hourly_minutes))
        return updated_uv and updated_vu

    def _update_directed(
        self,
        from_node: int,
        to_node: int,
        hourly_minutes: Tuple[float, ...],
    ) -> bool:
        neighbours = self.adjacency.get(from_node, [])
        for idx, edge in enumerate(neighbours):
            if edge.to_node == to_node:
                neighbours[idx] = Edge(
                    to_node=edge.to_node,
                    distance_km=edge.distance_km,
                    hourly_travel_minutes=hourly_minutes,
                )
                return True
        return False


class CompactRoadGraph:
    def __init__(self, node_count: int):
        self.node_count = node_count
        self.head: List[int] = [-1] * node_count
        self.to_node: List[int] = []
        self.distance_km: List[float] = []
        self.hourly_travel_minutes: List[Tuple[float, ...]] = []
        self.next_edge: List[int] = []
        self.node_positions: Optional[List[Tuple[float, float]]] = None

    def add_directed_edge(
        self,
        from_node: int,
        to_node: int,
        distance_km: float,
        hourly_minutes: Sequence[float],
    ) -> None:
        if len(hourly_minutes) != 24:
            raise ValueError("hourly_minutes must have exactly 24 values")

        self.to_node.append(to_node)
        self.distance_km.append(float(distance_km))
        self.hourly_travel_minutes.append(
            tuple(float(v) for v in hourly_minutes)
        )
        self.next_edge.append(self.head[from_node])
        self.head[from_node] = len(self.to_node) - 1

    def add_undirected_edge(
        self,
        u: int,
        v: int,
        distance_km: float,
        hourly_minutes: Sequence[float],
    ) -> None:
        if u == v:
            return
        self.add_directed_edge(u, v, distance_km, hourly_minutes)
        self.add_directed_edge(v, u, distance_km, hourly_minutes)

    def iter_edges(
        self,
        from_node: int,
    ) -> Iterable[Tuple[int, float, Tuple[float, ...]]]:
        edge_idx = self.head[from_node]
        while edge_idx != -1:
            yield (
                self.to_node[edge_idx],
                self.distance_km[edge_idx],
                self.hourly_travel_minutes[edge_idx],
            )
            edge_idx = self.next_edge[edge_idx]

    @classmethod
    def from_road_graph(cls, road_graph: RoadGraph) -> "CompactRoadGraph":
        compact = cls(road_graph.node_count)
        compact.node_positions = road_graph.node_positions
        seen: Set[Tuple[int, int]] = set()
        for u in range(road_graph.node_count):
            for edge in road_graph.adjacency[u]:
                key = (
                    (u, edge.to_node)
                    if u < edge.to_node
                    else (edge.to_node, u)
                )
                if key in seen:
                    continue
                seen.add(key)
                compact.add_undirected_edge(
                    u,
                    edge.to_node,
                    edge.distance_km,
                    edge.hourly_travel_minutes,
                )
        return compact
