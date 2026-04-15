# flake8: noqa

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import sqrt
from random import Random
from time import perf_counter
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
        self.hourly_travel_minutes.append(tuple(float(v) for v in hourly_minutes))
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
                key = (u, edge.to_node) if u < edge.to_node else (edge.to_node, u)
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

            for nxt, edge_distance, hourly_times in self._iter_neighbours(current):
                if nxt in avoid_nodes:
                    continue
                if self._normalise_edge(current, nxt) in avoid_edges:
                    continue

                edge_time = hourly_times[hour_index]
                candidate_distance = (
                    best_distance[current] + edge_distance
                )
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


def generate_large_scale_graph(
    node_count: int,
    avg_degree: int,
    seed: int,
) -> RoadGraph:
    if node_count < 2:
        raise ValueError("node_count must be >= 2")
    if avg_degree < 2:
        raise ValueError("avg_degree must be >= 2")

    rng = Random(seed)
    graph = RoadGraph(node_count)

    width = int(sqrt(node_count))
    if width * width < node_count:
        width += 1

    coordinates: List[Tuple[float, float]] = []
    for node in range(node_count):
        row = node // width
        col = node % width
        x = col + rng.uniform(-0.2, 0.2)
        y = row + rng.uniform(-0.2, 0.2)
        coordinates.append((x, y))

    graph.node_positions = coordinates

    existing_edges: Set[Tuple[int, int]] = set()

    def edge_distance(u: int, v: int) -> float:
        ux, uy = coordinates[u]
        vx, vy = coordinates[v]
        base = sqrt((ux - vx) ** 2 + (uy - vy) ** 2)
        return max(0.3, base * rng.uniform(1.4, 2.3))

    def hourly_profile(distance_km: float) -> List[float]:
        base_speed = rng.uniform(26.0, 58.0)
        base_minutes = distance_km / base_speed * 60.0

        multipliers = [1.0] * 24
        for hour in range(24):
            if hour in {7, 8, 9, 17, 18, 19}:
                multipliers[hour] = rng.uniform(1.45, 1.95)
            elif hour in {6, 10, 16, 20}:
                multipliers[hour] = rng.uniform(1.2, 1.45)
            elif hour in {0, 1, 2, 3, 4, 5, 22, 23}:
                multipliers[hour] = rng.uniform(0.8, 1.0)
            else:
                multipliers[hour] = rng.uniform(1.0, 1.2)

        profile = [
            max(1.0, round(base_minutes * mul * rng.uniform(0.9, 1.1), 3))
            for mul in multipliers
        ]
        return profile

    def add_edge(u: int, v: int) -> None:
        if u == v:
            return
        key = (u, v) if u < v else (v, u)
        if key in existing_edges:
            return
        distance = edge_distance(u, v)
        graph.add_undirected_edge(u, v, distance, hourly_profile(distance))
        existing_edges.add(key)

    # Build a connected sparse road network through a near-grid structure.
    for node in range(node_count):
        right = node + 1
        down = node + width

        if (node % width) != (width - 1) and right < node_count:
            add_edge(node, right)
        if down < node_count:
            add_edge(node, down)

    target_edge_count = max(
        len(existing_edges),
        node_count * avg_degree // 2,
    )

    # Add extra local and occasional long edges to mimic real roads.
    while len(existing_edges) < target_edge_count:
        u = rng.randrange(node_count)
        if rng.random() < 0.82:
            step = rng.randint(1, max(2, width // 2))
            direction = rng.choice((-1, 1, -width, width))
            v = u + direction * step
            if v < 0 or v >= node_count:
                continue
        else:
            v = rng.randrange(node_count)
        add_edge(u, v)

    return graph


def parse_int_list(raw_value: str) -> List[int]:
    if not raw_value.strip():
        return []
    return [int(token.strip()) for token in raw_value.split(",") if token.strip()]


def parse_edge_list(raw_value: str) -> List[Tuple[int, int]]:
    if not raw_value.strip():
        return []

    result: List[Tuple[int, int]] = []
    chunks = [chunk.strip() for chunk in raw_value.split(",") if chunk.strip()]
    for chunk in chunks:
        if "-" not in chunk:
            raise ValueError(
                "edge format must be u-v,u-v (example: 2-5,10-11)"
            )
        left, right = chunk.split("-", 1)
        result.append((int(left.strip()), int(right.strip())))
    return result


def print_path_result(label: str, result: Optional[PathResult]) -> None:
    print(label)
    if result is None:
        print("  No feasible path found with given constraints.")
        return

    print(f"  Path nodes: {result.path_nodes}")
    print(f"  Total distance (km): {result.total_distance_km:.3f}")
    print(f"  Total travel time (minutes): {result.total_travel_minutes:.3f}")


def run_single_query(
    path_finder: SmartPathFinder,
    source: int,
    destination: int,
    departure_hour: int,
    avoid_nodes: Sequence[int],
    avoid_edges: Sequence[Tuple[int, int]],
) -> None:
    print("Query:")
    print(f"  source={source}")
    print(f"  destination={destination}")
    print(f"  departure_hour={departure_hour}")
    print(f"  avoid_nodes={list(avoid_nodes)}")
    print(f"  avoid_edges={list(avoid_edges)}")

    distance_path, time_path = path_finder.route(
        source=source,
        destination=destination,
        departure_hour=departure_hour,
        avoid_nodes=avoid_nodes,
        avoid_edges=avoid_edges,
    )

    print_path_result("Distance-optimised path:", distance_path)
    print_path_result("Time-optimised path:", time_path)


def run_benchmark(
    path_finder: SmartPathFinder,
    node_count: int,
    query_count: int,
    seed: int,
    label: str,
) -> None:
    rng = Random(seed)

    total_distance_mode = 0.0
    total_time_mode = 0.0
    success_distance = 0
    success_time = 0

    for _ in range(query_count):
        source = rng.randrange(node_count)
        destination = rng.randrange(node_count)
        while destination == source:
            destination = rng.randrange(node_count)

        departure_hour = rng.randrange(24)

        start = perf_counter()
        distance_path, time_path = path_finder.route(
            source,
            destination,
            departure_hour,
        )
        elapsed = perf_counter() - start

        if distance_path is not None:
            success_distance += 1
        if time_path is not None:
            success_time += 1

        # One route() computes both objectives.
        total_distance_mode += elapsed
        total_time_mode += elapsed

    print(f"Benchmark summary ({label}):")
    print(f"  queries={query_count}")
    print(f"  feasible distance paths={success_distance}/{query_count}")
    print(f"  feasible time paths={success_time}/{query_count}")
    print(
        "  average runtime per query "
        f"(both optimisations): {total_distance_mode / query_count:.6f} sec"
    )


def _same_result(
    left: Optional[PathResult],
    right: Optional[PathResult],
) -> bool:
    if left is None or right is None:
        return left is None and right is None
    return (
        left.path_nodes == right.path_nodes
        and abs(left.total_distance_km - right.total_distance_km) <= 1e-9
        and abs(left.total_travel_minutes - right.total_travel_minutes) <= 1e-9
    )


def run_benchmark_comparison(
    list_graph: RoadGraph,
    query_count: int,
    seed: int,
) -> None:
    list_finder = SmartPathFinder(list_graph)
    compact_graph = CompactRoadGraph.from_road_graph(list_graph)
    compact_finder = SmartPathFinder(compact_graph)

    rng = Random(seed)
    queries: List[Tuple[int, int, int]] = []
    for _ in range(query_count):
        source = rng.randrange(list_graph.node_count)
        destination = rng.randrange(list_graph.node_count)
        while destination == source:
            destination = rng.randrange(list_graph.node_count)
        departure_hour = rng.randrange(24)
        queries.append((source, destination, departure_hour))

    list_elapsed = 0.0
    compact_elapsed = 0.0
    consistent_results = 0

    for source, destination, departure_hour in queries:
        start = perf_counter()
        list_distance, list_time = list_finder.route(
            source,
            destination,
            departure_hour,
        )
        list_elapsed += perf_counter() - start

        start = perf_counter()
        compact_distance, compact_time = compact_finder.route(
            source,
            destination,
            departure_hour,
        )
        compact_elapsed += perf_counter() - start

        if _same_result(list_distance, compact_distance) and _same_result(
            list_time,
            compact_time,
        ):
            consistent_results += 1

    print("Benchmark comparison (list vs compact):")
    print(f"  queries={query_count}")
    print(
        "  list avg runtime: "
        f"{list_elapsed / query_count:.6f} sec"
    )
    print(
        "  compact avg runtime: "
        f"{compact_elapsed / query_count:.6f} sec"
    )
    print(
        "  result consistency: "
        f"{consistent_results}/{query_count} queries"
    )


def interactive_mode(path_finder: SmartPathFinder) -> None:
    print("Enter query values.")
    source = int(input("source node: ").strip())
    destination = int(input("destination node: ").strip())
    departure_hour = int(input("departure hour [0..23]: ").strip())
    avoid_nodes_raw = input("avoid nodes (comma list, optional): ").strip()
    avoid_edges_raw = input("avoid edges (u-v,u-v, optional): ").strip()

    avoid_nodes = parse_int_list(avoid_nodes_raw)
    avoid_edges = parse_edge_list(avoid_edges_raw)

    run_single_query(
        path_finder,
        source,
        destination,
        departure_hour,
        avoid_nodes,
        avoid_edges,
    )


def run_demo(path_finder: SmartPathFinder, node_count: int, seed: int) -> None:
    rng = Random(seed)
    source = rng.randrange(node_count)
    destination = rng.randrange(node_count)
    while destination == source:
        destination = rng.randrange(node_count)

    departure_hour = 8
    avoid_nodes = [
        rng.randrange(node_count)
        for _ in range(2)
    ]
    avoid_edges = [
        (rng.randrange(node_count), rng.randrange(node_count))
        for _ in range(2)
    ]

    run_single_query(
        path_finder,
        source,
        destination,
        departure_hour,
        avoid_nodes,
        avoid_edges,
    )


def _all_unique_edges(
    graph: RoadGraph | CompactRoadGraph,
) -> List[Tuple[int, int]]:
    edges: List[Tuple[int, int]] = []
    seen: Set[Tuple[int, int]] = set()

    if isinstance(graph, RoadGraph):
        for u in range(graph.node_count):
            for edge in graph.adjacency[u]:
                key = (u, edge.to_node) if u < edge.to_node else (edge.to_node, u)
                if key in seen:
                    continue
                seen.add(key)
                edges.append(key)
        return edges

    for u in range(graph.node_count):
        for v, _, _ in graph.iter_edges(u):
            key = (u, v) if u < v else (v, u)
            if key in seen:
                continue
            seen.add(key)
            edges.append(key)
    return edges


def _get_positions(
    graph: RoadGraph | CompactRoadGraph,
) -> List[Tuple[float, float]]:
    if graph.node_positions is not None:
        return graph.node_positions

    width = int(sqrt(graph.node_count))
    if width * width < graph.node_count:
        width += 1

    positions: List[Tuple[float, float]] = []
    for node in range(graph.node_count):
        row = node // width
        col = node % width
        positions.append((float(col), float(row)))
    return positions


def render_graph_image(
    graph: RoadGraph | CompactRoadGraph,
    output_path: str,
    image_width: int,
    image_height: int,
    distance_path: Optional[PathResult],
    time_path: Optional[PathResult],
    source: Optional[int],
    destination: Optional[int],
    avoid_nodes: Sequence[int],
) -> None:
    try:
        from PIL import Image, ImageDraw  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required for visualization. Install with: pip install Pillow"
        ) from exc

    if image_width < 300 or image_height < 300:
        raise ValueError("image size must be at least 300x300")

    positions = _get_positions(graph)
    xs = [x for x, _ in positions]
    ys = [y for _, y in positions]

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    span_x = max(max_x - min_x, 1e-9)
    span_y = max(max_y - min_y, 1e-9)
    padding = 30

    def project(node: int) -> Tuple[float, float]:
        x, y = positions[node]
        px = padding + (x - min_x) / span_x * (image_width - 2 * padding)
        py = padding + (y - min_y) / span_y * (image_height - 2 * padding)
        return px, py

    image = Image.new("RGB", (image_width, image_height), (250, 250, 250))
    draw = ImageDraw.Draw(image)

    for u, v in _all_unique_edges(graph):
        ux, uy = project(u)
        vx, vy = project(v)
        draw.line((ux, uy, vx, vy), fill=(205, 210, 215), width=1)

    if distance_path is not None and len(distance_path.path_nodes) >= 2:
        for i in range(len(distance_path.path_nodes) - 1):
            u = distance_path.path_nodes[i]
            v = distance_path.path_nodes[i + 1]
            ux, uy = project(u)
            vx, vy = project(v)
            draw.line((ux, uy, vx, vy), fill=(220, 20, 60), width=3)

    if time_path is not None and len(time_path.path_nodes) >= 2:
        for i in range(len(time_path.path_nodes) - 1):
            u = time_path.path_nodes[i]
            v = time_path.path_nodes[i + 1]
            ux, uy = project(u)
            vx, vy = project(v)
            draw.line((ux, uy, vx, vy), fill=(30, 100, 220), width=3)

    avoid_set = set(avoid_nodes)
    base_radius = 2

    for node in range(graph.node_count):
        x, y = project(node)
        color = (70, 70, 70)
        radius = base_radius

        if node in avoid_set:
            color = (245, 140, 40)
            radius = 3

        if source is not None and node == source:
            color = (50, 170, 70)
            radius = 5

        if destination is not None and node == destination:
            color = (180, 40, 40)
            radius = 5

        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=color,
            outline=color,
        )

    image.save(output_path)


def run_visualization(
    path_finder: SmartPathFinder,
    source: Optional[int],
    destination: Optional[int],
    departure_hour: int,
    avoid_nodes: Sequence[int],
    avoid_edges: Sequence[Tuple[int, int]],
    output_image: str,
    image_width: int,
    image_height: int,
) -> None:
    distance_path: Optional[PathResult] = None
    time_path: Optional[PathResult] = None

    if source is not None and destination is not None:
        distance_path, time_path = path_finder.route(
            source=source,
            destination=destination,
            departure_hour=departure_hour,
            avoid_nodes=avoid_nodes,
            avoid_edges=avoid_edges,
        )
        print_path_result("Distance-optimised path:", distance_path)
        print_path_result("Time-optimised path:", time_path)

    render_graph_image(
        graph=path_finder.graph,
        output_path=output_image,
        image_width=image_width,
        image_height=image_height,
        distance_path=distance_path,
        time_path=time_path,
        source=source,
        destination=destination,
        avoid_nodes=avoid_nodes,
    )
    print(f"Saved visualization image to: {output_image}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Smart Path Finder (distance + time optimised routes)",
    )
    parser.add_argument(
        "--nodes",
        type=int,
        default=3000,
        help="number of map nodes (thousands recommended)",
    )
    parser.add_argument(
        "--avg-degree",
        type=int,
        default=4,
        help="target average node degree",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed for graph generation",
    )
    parser.add_argument(
        "--mode",
        choices=("demo", "interactive", "query", "benchmark", "visualize"),
        default="demo",
        help="execution mode",
    )
    parser.add_argument("--source", type=int)
    parser.add_argument("--destination", type=int)
    parser.add_argument(
        "--departure-hour",
        type=int,
        default=8,
        help="start hour for travel-time calculations",
    )
    parser.add_argument(
        "--avoid-nodes",
        type=str,
        default="",
        help="comma-separated node IDs to avoid",
    )
    parser.add_argument(
        "--avoid-edges",
        type=str,
        default="",
        help="comma-separated edge list in u-v format",
    )
    parser.add_argument(
        "--benchmark-queries",
        type=int,
        default=50,
        help="number of random queries for benchmark mode",
    )
    parser.add_argument(
        "--output-image",
        type=str,
        default="graph_visualization.png",
        help="output PNG filename for visualize mode",
    )
    parser.add_argument(
        "--image-width",
        type=int,
        default=1400,
        help="visualization image width",
    )
    parser.add_argument(
        "--image-height",
        type=int,
        default=900,
        help="visualization image height",
    )
    parser.add_argument(
        "--graph-structure",
        choices=("list", "compact", "both"),
        default="list",
        help="graph data structure: adjacency list, compact arrays, or both",
    )
    args = parser.parse_args()

    print(
        "Generating graph with "
        f"{args.nodes:,} nodes (avg_degree={args.avg_degree})..."
    )
    graph = generate_large_scale_graph(
        node_count=args.nodes,
        avg_degree=args.avg_degree,
        seed=args.seed,
    )
    if args.mode != "benchmark" and args.graph_structure == "both":
        raise ValueError("--graph-structure both is only valid in benchmark mode")

    if args.mode == "benchmark" and args.graph_structure == "both":
        print("Building compact graph representation...")
        run_benchmark_comparison(
            list_graph=graph,
            query_count=args.benchmark_queries,
            seed=args.seed + 1000,
        )
        return

    if args.graph_structure == "compact":
        print("Building compact graph representation...")
        active_graph = CompactRoadGraph.from_road_graph(graph)
    else:
        active_graph = graph

    path_finder = SmartPathFinder(active_graph)
    print("Graph ready.")

    if args.mode == "benchmark":
        run_benchmark(
            path_finder=path_finder,
            node_count=args.nodes,
            query_count=args.benchmark_queries,
            seed=args.seed + 1000,
            label=args.graph_structure,
        )
        return

    if args.mode == "interactive":
        interactive_mode(path_finder)
        return

    if args.mode == "query":
        if args.source is None or args.destination is None:
            raise ValueError("query mode requires --source and --destination")

        run_single_query(
            path_finder=path_finder,
            source=args.source,
            destination=args.destination,
            departure_hour=args.departure_hour,
            avoid_nodes=parse_int_list(args.avoid_nodes),
            avoid_edges=parse_edge_list(args.avoid_edges),
        )
        return

    if args.mode == "visualize":
        run_visualization(
            path_finder=path_finder,
            source=args.source,
            destination=args.destination,
            departure_hour=args.departure_hour,
            avoid_nodes=parse_int_list(args.avoid_nodes),
            avoid_edges=parse_edge_list(args.avoid_edges),
            output_image=args.output_image,
            image_width=args.image_width,
            image_height=args.image_height,
        )
        return

    run_demo(path_finder, args.nodes, args.seed + 2000)


if __name__ == "__main__":
    main()
