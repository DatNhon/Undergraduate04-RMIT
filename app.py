from __future__ import annotations

from math import sqrt
from random import Random
from time import perf_counter
import tracemalloc
from typing import List, Optional, Sequence, Set, Tuple

from graph_models import CompactRoadGraph, PathResult, RoadGraph
from smart_path_finder import SmartPathFinder


def generate_large_scale_graph(
    node_count: int,
    avg_degree: int,
    seed: int,
) -> RoadGraph:
    """Generate a synthetic road network.

    Nodes are placed on a noisy grid. Edges connect local neighbours and
    random long-range links until the desired average degree is reached.
    """
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

        return [
            max(1.0, round(base_minutes * mul * rng.uniform(0.9, 1.1), 3))
            for mul in multipliers
        ]

    def add_edge(u: int, v: int) -> None:
        if u == v:
            return
        key = (u, v) if u < v else (v, u)
        if key in existing_edges:
            return
        distance = edge_distance(u, v)
        graph.add_undirected_edge(u, v, distance, hourly_profile(distance))
        existing_edges.add(key)

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
    """Parse a comma-separated list of integers (empty -> [])."""
    if not raw_value.strip():
        return []
    return [
        int(token.strip())
        for token in raw_value.split(",")
        if token.strip()
    ]


def parse_edge_list(raw_value: str) -> List[Tuple[int, int]]:
    """Parse a comma-separated list of edges in 'u-v' format."""
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
    """Print a `PathResult` to stdout in a compact format."""
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
    """Execute a single routing query and display both results."""
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
    """Run `query_count` random routing queries and summarize results."""
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

        total_distance_mode += elapsed
        total_time_mode += elapsed

    print(f"Benchmark summary ({label}):")
    print(f"  queries={query_count}")
    print(f"  feasible distance paths={success_distance}/{query_count}")
    print(f"  feasible time paths={success_time}/{query_count}")
    print(
        "  query time (ms): "
        f"{(total_distance_mode / query_count) * 1000.0:.3f}"
    )
    print(
        "  feasible (%): "
        f"{((success_distance + success_time) / (2 * query_count)) * 100:.2f}"
    )


def _same_result(
    left: Optional[PathResult],
    right: Optional[PathResult],
) -> bool:
    """Return True if two `PathResult` objects are numerically equal."""
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
    """Compare runtime and result consistency between representations."""
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
    """Prompt the user for query parameters and run a single query."""
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
    """Generate and execute a random demo query (for quick checks)."""
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
        choices=("demo", "interactive", "query", "benchmark"),
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
        "--graph-structure",
        choices=("list", "compact", "both"),
        default="list",
        help="graph data structure: adjacency list, compact arrays, or both",
    )
    args = parser.parse_args()

    tracemalloc.start()

    print(
        "Generating graph with "
        f"{args.nodes:,} nodes (avg_degree={args.avg_degree})..."
    )
    graph_start = perf_counter()
    graph = generate_large_scale_graph(
        node_count=args.nodes,
        avg_degree=args.avg_degree,
        seed=args.seed,
    )
    gen_time_ms = (perf_counter() - graph_start) * 1000.0
    _, peak_bytes = tracemalloc.get_traced_memory()
    peak_memory_mb = peak_bytes / (1024 * 1024)
    if args.mode != "benchmark" and args.graph_structure == "both":
        raise ValueError(
            "--graph-structure both is only valid in benchmark mode"
        )

    if args.mode == "benchmark" and args.graph_structure == "both":
        print("Building compact graph representation...")
        run_benchmark_comparison(
            list_graph=graph,
            query_count=args.benchmark_queries,
            seed=args.seed + 1000,
        )
        print(f"Graph generation time (ms): {gen_time_ms:.3f}")
        print(f"Peak memory (MB): {peak_memory_mb:.3f}")
        tracemalloc.stop()
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
        print(f"Graph generation time (ms): {gen_time_ms:.3f}")
        print(f"Peak memory (MB): {peak_memory_mb:.3f}")
        tracemalloc.stop()
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
        print(f"Graph generation time (ms): {gen_time_ms:.3f}")
        print(f"Peak memory (MB): {peak_memory_mb:.3f}")
        tracemalloc.stop()
        return

    run_demo(path_finder, args.nodes, args.seed + 2000)
    print(f"Graph generation time (ms): {gen_time_ms:.3f}")
    print(f"Peak memory (MB): {peak_memory_mb:.3f}")
    tracemalloc.stop()


if __name__ == "__main__":
    main()
