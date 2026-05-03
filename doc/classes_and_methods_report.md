# Classes and Methods Report

## 1. Purpose
This document provides a comprehensive inventory of the classes and methods used in the Smart Path Finder codebase. It is organized by file and describes what each class or function does, how it is used, and how it fits into the overall architecture.

## 2. Codebase Overview
The project is split into four main Python files:

- `main.py` is the entry point.
- `app.py` handles graph generation, command-line parsing, benchmarks, and interactive/query execution.
- `graph_models.py` defines the graph and result data structures.
- `smart_path_finder.py` implements the path-search algorithm.

## 3. Classes and Methods by File

### 3.1 `main.py`
`main.py` does not define any classes or custom methods. It only imports `main` from `app.py` and runs it when the file is executed directly.

### 3.2 `graph_models.py`

#### `Edge`
A frozen dataclass that represents one directed road segment.

Fields:
- `to_node`: destination node ID
- `distance_km`: fixed road distance
- `hourly_travel_minutes`: 24-element tuple containing time-dependent travel times

Methods:
- None. This is a data container only.

#### `PathResult`
A frozen dataclass used to return the final routing outcome.

Fields:
- `path_nodes`: ordered list of nodes in the path
- `total_distance_km`: total route distance
- `total_travel_minutes`: total route travel time

Methods:
- None. This is also a data container only.

#### `RoadGraph`
Adjacency-list graph representation.

Methods:
- `__init__(node_count)`
  - Creates an empty adjacency list for each node.
  - Stores optional `node_positions` for layout or debugging.

- `add_undirected_edge(u, v, distance_km, hourly_minutes)`
  - Adds the edge in both directions.
  - Validates that the hourly travel-time sequence has exactly 24 values.

- `update_edge_hourly_times(u, v, new_hourly_minutes)`
  - Replaces the hourly travel-time profile of an existing undirected edge.
  - Returns `True` only if both directions were updated.

- `_update_directed(from_node, to_node, hourly_minutes)`
  - Internal helper used by `update_edge_hourly_times`.
  - Replaces one directed adjacency entry.

#### `CompactRoadGraph`
Forward-star / compact array graph representation.

Methods:
- `__init__(node_count)`
  - Creates parallel arrays for heads, destinations, distances, travel times, and linked edges.

- `add_directed_edge(from_node, to_node, distance_km, hourly_minutes)`
  - Appends one directed edge into the compact structure.
  - Validates the 24-hour travel-time profile.

- `add_undirected_edge(u, v, distance_km, hourly_minutes)`
  - Adds both directions by calling `add_directed_edge` twice.

- `iter_edges(from_node)`
  - Yields outgoing edges from a given node.
  - Abstracts traversal of the compact representation.

- `from_road_graph(road_graph)`
  - Class method that converts a `RoadGraph` into a `CompactRoadGraph`.
  - Deduplicates undirected edges while copying them.

### 3.3 `smart_path_finder.py`

#### `SmartPathFinder`
This class implements the routing algorithm and supports both graph representations.

Methods:
- `__init__(graph)`
  - Stores either a `RoadGraph` or `CompactRoadGraph` instance.

- `route(source, destination, departure_hour, avoid_nodes=None, avoid_edges=None)`
  - Public entry point for routing.
  - Runs the algorithm twice:
    - once to minimize total distance
    - once to minimize total travel time
  - Returns a tuple of two `PathResult` objects or `None` values when no path exists.

- `_dijkstra(source, destination, departure_hour, avoid_nodes, avoid_edges, optimise_for)`
  - Core shortest-path algorithm.
  - Uses a priority queue and time-dependent edge costs.
  - Supports node and edge avoidance.
  - Implements tie-breaking based on the secondary objective.

- `_reconstruct_path(predecessor, source, destination)`
  - Rebuilds the final node sequence from predecessor links.

- `_normalise_edge(u, v)`
  - Converts an undirected edge into a canonical sorted tuple.
  - Used when checking avoided edges.

- `_iter_neighbours(node)`
  - Iterates over outgoing edges regardless of whether the graph is stored as adjacency lists or compact arrays.
  - Keeps the algorithm independent from graph storage details.

### 3.4 `app.py`

#### `generate_large_scale_graph(node_count, avg_degree, seed)`
Builds a synthetic sparse road network.

Responsibilities:
- Creates node coordinates
- Adds grid-like local connections
- Adds extra random edges to reach the target average degree
- Generates hourly travel-time profiles

#### `parse_int_list(raw_value)`
Parses comma-separated node IDs into a list of integers.

#### `parse_edge_list(raw_value)`
Parses comma-separated edge constraints in `u-v` format.

#### `print_path_result(label, result)`
Formats one route result for console output.

#### `run_single_query(path_finder, source, destination, departure_hour, avoid_nodes, avoid_edges)`
Executes one query and prints both route results.

#### `run_benchmark(path_finder, node_count, query_count, seed, label)`
Runs repeated random queries and prints summary timing information.

#### `_same_result(left, right)`
Internal helper that compares two `PathResult` values for equality within a small floating-point tolerance.

#### `run_benchmark_comparison(list_graph, query_count, seed)`
Compares the list-based graph implementation with the compact graph implementation on the same queries.

#### `interactive_mode(path_finder)`
Prompts the user for query input in the terminal.

#### `run_demo(path_finder, node_count, seed)`
Generates a random demo query and executes it.

#### `main()`
Program entry point.

Responsibilities:
- Defines CLI arguments
- Builds the graph
- Chooses the graph structure
- Dispatches to demo, interactive, query, or benchmark mode

## 4. Functional Summary
The codebase contains:

- 5 classes total
- 15 class methods
- 11 top-level functions in `app.py`
- 1 launcher file with no custom methods

## 5. Role of Each Component

- `Edge` and `PathResult` provide structured data exchange.
- `RoadGraph` is the simple adjacency-list representation.
- `CompactRoadGraph` is the memory-efficient representation.
- `SmartPathFinder` performs all routing logic.
- `app.py` provides the user interface and graph generation.
- `main.py` is the minimal executable wrapper.

## 6. Conclusion
The design separates data, algorithm, and interface concerns cleanly. This keeps the code easier to test, easier to explain in the report, and easier to maintain. The routing logic stays in one place, while graph construction and CLI behavior remain outside the algorithm layer.
