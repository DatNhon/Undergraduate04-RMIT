Smart Path Finder

Overview
This program generates a large-scale road graph and computes two route suggestions
for each query:
1. Path that minimises total distance
2. Path that minimises total travel time

Graph model
- Nodes represent locations
- Undirected edges represent roads
- Each edge stores:
  - `distance_km` (fixed)
  - 24 hourly travel times in minutes (index 0..23)

The generated map supports thousands of nodes and a sparse, road-like edge density
controlled by average degree.

Environment setup
- Python 3.10+ recommended
- No external libraries required
- Optional for visualization: Pillow (`pip install Pillow`)

How to run
1) Demo mode (default):
   python main.py

2) Interactive mode:
   python main.py --mode interactive --nodes 3000 --avg-degree 4

3) Query mode (explicit input):
   python main.py --mode query --nodes 3000 --source 10 --destination 120 \
     --departure-hour 8 --avoid-nodes 11,12 --avoid-edges 20-21,22-23

4) Benchmark mode:
   python main.py --mode benchmark --nodes 3000 --benchmark-queries 50

5) Try different data structures:
  python main.py --mode benchmark --nodes 3000 --graph-structure list
  python main.py --mode benchmark --nodes 3000 --graph-structure compact
  python main.py --mode benchmark --nodes 3000 --graph-structure both

6) Visualize nodes/graph (PNG output):
  python main.py --mode visualize --nodes 1200 --output-image map.png

7) Visualize with a query path overlay:
  python main.py --mode visualize --nodes 1200 --source 5 --destination 980 \
    --departure-hour 8 --avoid-nodes 12,13 --avoid-edges 20-21,40-41 \
    --output-image map_with_paths.png

Input format
Each query includes:
- source node (mandatory)
- destination node (mandatory)
- departure hour (0..23)
- avoid nodes (optional, comma-separated)
- avoid edges (optional, comma-separated `u-v` format)

CLI arguments:
- `--nodes`: number of nodes in generated graph
- `--avg-degree`: target average degree
- `--seed`: random seed for reproducibility
- `--mode`: `demo`, `interactive`, `query`, `benchmark`
- `--mode`: `demo`, `interactive`, `query`, `benchmark`, `visualize`
- `--source`, `--destination`: query endpoints (required in `query` mode)
- `--departure-hour`: hour for time-dependent edge traversal
- `--avoid-nodes`: comma list (example: `5,20,21`)
- `--avoid-edges`: edge list (example: `1-2,3-4`)
- `--graph-structure`: `list`, `compact`, or `both`
- `--output-image`: PNG file path for visualization output
- `--image-width`, `--image-height`: visualization image size

Output format
For each query, the program prints:
- distance-optimised path:
  - node sequence
  - total distance (km)
  - total travel time (minutes)
- time-optimised path:
  - node sequence
  - total distance (km)
  - total travel time (minutes)

For `visualize` mode, the program also creates a PNG image:
- all nodes and edges of the generated map
- source and destination nodes (if provided)
- avoid nodes (if provided)
- distance-optimised path overlay (red)
- time-optimised path overlay (blue)

Design notes
- Both route types use Dijkstra-based shortest path search.
- Distance mode uses distance as objective and travel time as tie-break.
- Time mode uses time as objective and distance as tie-break.
- Time-dependent routing uses current hour derived from cumulative travel time.
- Edge hourly travel-time lists can be updated through graph methods.
- Two graph data structures are implemented:
  - adjacency list (`RoadGraph`)
  - compact array-based forward-star representation (`CompactRoadGraph`)

Technical report guidance (rubric-aligned)

1) Design and analysis of algorithms & data structures
- Problem model:
  - Map is represented as a sparse undirected graph G=(V,E)
  - Each edge stores fixed distance and 24 hourly travel-time values
- Data structures implemented:
  - `RoadGraph` (adjacency list using dictionary of edge lists)
  - `CompactRoadGraph` (forward-star arrays: `head`, `to_node`,
    `distance_km`, `hourly_travel_minutes`, `next_edge`)
- Routing algorithm:
  - Dijkstra with min-heap priority queue (`heapq`)
  - Two objective modes:
    - distance-minimised path
    - time-minimised path
  - Tie-break rule:
    - distance mode tie-breaks by lower total travel time
    - time mode tie-breaks by lower total distance
- Constraint handling:
  - Avoided nodes are skipped during relaxation
  - Avoided edges are filtered using normalised `(min(u,v), max(u,v))`
- Time-dependent travel:
  - Traversal time for each edge uses hour index derived from
    cumulative minutes from departure hour
- Complexity (with binary heap and sparse graph assumptions):
  - Single-objective Dijkstra time: O((V+E) log V)
  - Query computes both objectives: O(2*(V+E) log V)
  - Memory:
    - adjacency list: O(V+E)
    - compact forward-star: O(V+E)
  - Graph generation: approximately O(V+E)

2) Theoretical and empirical evaluation
- Theoretical evaluation section should include:
  - asymptotic runtime and memory for each data structure
  - assumptions: sparse road network, non-negative edge costs,
    valid connectivity constraints
  - discussion of trade-offs:
    - adjacency list: simpler updates/readability
    - compact structure: lower pointer/object overhead
- Empirical evaluation section should include multiple scenarios:
  - Scale study: vary `--nodes` (e.g., 1000, 3000, 5000, 10000)
  - Query load study: vary `--benchmark-queries` (e.g., 50, 200, 500)
  - Structure study: compare `--graph-structure list|compact|both`
  - Constraint study: with/without avoid nodes and avoid edges
  - Time-of-day study: compare off-peak vs peak departure hours
- Minimum recommended commands:
  - `python main.py --mode benchmark --nodes 3000 --benchmark-queries 100 --graph-structure both`
  - `python main.py --mode benchmark --nodes 10000 --benchmark-queries 100 --graph-structure both`
  - `python main.py --mode query --nodes 3000 --source 10 --destination 2000 --departure-hour 8 --avoid-nodes 11,12 --avoid-edges 20-21,22-23`
- Metrics to report in tables/figures:
  - average runtime per query
  - feasible path ratio
  - result consistency between structures
  - total distance and total time of returned paths

Note:
- To target the "Excellent" band, ensure evaluation uses sufficiently
  large graphs (thousands of nodes), compares multiple scenarios, and
  justifies assumptions clearly in the report text.

Demo video
Add your demo video link here before submission.
