# Smart Path Finder: Algorithm Design and Evaluation

## 1. Problem Overview

The project models a road network as a sparse weighted graph and returns two route suggestions for each query:

1. A path that minimizes total distance.
2. A path that minimizes total travel time.

Each road stores two kinds of information:

- a fixed distance in kilometers
- 24 hourly travel-time values in minutes, one for each hour of the day

The routing problem is therefore not a plain shortest-path problem. It is a time-dependent shortest-path problem with optional constraints:

- avoid selected nodes
- avoid selected edges
- use a chosen departure hour

## 2. Algorithm Design

### 2.1 Graph Representation

The codebase separates graph storage from path search:

- `graph_models.py` contains the graph data structures.
- `smart_path_finder.py` contains the routing algorithm.
- `app.py` contains graph generation, benchmarking, and visualization.

Two graph representations are supported:

- `RoadGraph`: adjacency-list representation
- `CompactRoadGraph`: forward-star / compact array-based representation

Both store the same logical road network, but the compact version reduces pointer and object overhead.

### 2.2 Routing Algorithm

The routing logic uses Dijkstra's algorithm with a binary min-heap priority queue from `heapq`.

For each query, the algorithm runs twice:

- once with distance as the primary objective
- once with travel time as the primary objective

This produces two independent route recommendations.

### 2.3 Why Dijkstra Works Here

Dijkstra's algorithm is appropriate because all edge costs are non-negative. That means once the smallest tentative cost for a node is removed from the priority queue, it does not need to be revisited with a smaller cost.

The implementation extends the classic algorithm in three ways:

- it supports time-dependent edge travel times
- it skips avoided nodes during relaxation
- it skips avoided edges by normalizing each edge as `(min(u, v), max(u, v))`

### 2.4 Time-Dependent Travel

The travel time for an edge depends on the hour at which the edge is entered.

The algorithm tracks cumulative travel time from the departure hour and computes:

`hour_index = (departure_hour + cumulative_minutes / 60) mod 24`

That hour index is used to select the correct travel-time value for the next edge.

This makes the search dynamic, because the cost of the next edge can change as the route progresses.

### 2.5 Tie-Breaking Rules

The search uses a primary objective and a secondary tie-break rule:

- Distance mode:
  - primary: total distance
  - tie-break: lower total travel time
- Time mode:
  - primary: total travel time
  - tie-break: lower total distance

This ensures stable and deterministic route selection when two paths are equally good under the main objective.

### 2.6 Output

For each mode, the program returns:

- the node sequence of the path
- total distance in kilometers
- total travel time in minutes

If no valid route exists under the constraints, the result is `None`.

## 3. Evaluation

### 3.1 Theoretical Evaluation

The project can be evaluated from a complexity and data-structure perspective.

#### Overall Complexity Summary

Let:

- `V` be the number of nodes
- `E` be the number of edges
- `Q` be the number of benchmark queries

The main operations have the following costs:

- graph generation: `O(V + E)`
- one routing query: `O((V + E) log V)`
- one full query returning both routes: `O(2 * (V + E) log V)`
- benchmark with `Q` queries: `O(Q * (V + E) log V)`

These bounds assume a sparse road network and a binary heap priority queue.

| Component | Time Complexity | Space Complexity |
| --- | --- | --- |
| Graph generation | `O(V + E)` | `O(V + E)` |
| One Dijkstra run | `O((V + E) log V)` | `O(V)` |
| Full query returning both routes | `O(2 * (V + E) log V)` | `O(V)` |
| Benchmark with `Q` queries | `O(Q * (V + E) log V)` | `O(V)` |
| Adjacency-list storage | `O(V + E)` | `O(V + E)` |
| Compact forward-star storage | `O(V + E)` | `O(V + E)` |

#### Time Complexity

For one Dijkstra run on a sparse graph:

- `O((V + E) log V)` using a binary heap

Because the program computes both distance-optimized and time-optimized routes, the overall query cost is:

- `O(2 * (V + E) log V)`

In practice, the constant factor is small because the two runs share the same graph and reuse the same search logic.

#### Space Complexity

Both graph representations use linear memory in the size of the network:

- adjacency list: `O(V + E)`
- compact forward-star: `O(V + E)`

The compact version usually performs better in memory-sensitive settings because it stores edges in arrays rather than in many small Python objects.

#### Complexity by Component

- `graph_models.py`
   - storing the graph: `O(V + E)`
   - converting to compact form: `O(V + E)`
- `smart_path_finder.py`
   - one Dijkstra run: `O((V + E) log V)`
   - two route searches per query: `O(2 * (V + E) log V)`
- `app.py`
   - graph generation: `O(V + E)`
   - benchmark loop: `O(Q * (V + E) log V)`

#### Expected Trade-offs

- `RoadGraph`
  - easier to inspect and update
  - simpler for teaching and debugging
  - higher object overhead
- `CompactRoadGraph`
  - more memory efficient
  - better for large graphs
  - slightly less readable

### 3.2 Empirical Evaluation

A practical evaluation should compare the implementations under several scenarios:

1. Scale study
   - test graphs with `1000`, `3000`, `5000`, and `10000` nodes
2. Query load study
   - vary `--benchmark-queries` such as `50`, `100`, `200`, and `500`
3. Structure study
   - compare `--graph-structure list`, `compact`, and `both`
4. Constraint study
   - test with and without avoided nodes and avoided edges
5. Time-of-day study
   - compare off-peak departures with peak-hour departures

### 3.3 Metrics to Report

The most useful metrics are:

- average runtime per query
- feasible path ratio
- consistency between list and compact graph results
- total distance returned
- total travel time returned

### 3.4 Example Benchmark Commands

```bash
python main.py --mode benchmark --nodes 3000 --benchmark-queries 100 --graph-structure both
python main.py --mode benchmark --nodes 10000 --benchmark-queries 100 --graph-structure both
python main.py --mode query --nodes 3000 --source 10 --destination 2000 --departure-hour 8 --avoid-nodes 11,12 --avoid-edges 20-21,22-23
```

### 3.5 Interpreting Results

When reviewing the results, the following questions matter most:

- Does the compact structure produce the same answers as the adjacency-list structure?
- Does runtime increase roughly linearly with graph size and query count?
- Do avoid-node and avoid-edge constraints reduce the feasible-path ratio?
- Do peak-hour departure times produce longer travel times than off-peak departures?

A strong evaluation should show that the algorithm remains correct under both graph representations and that the compact structure offers practical efficiency benefits on larger graphs.

## 4. Conclusion

The project uses a time-dependent, constraint-aware version of Dijkstra's algorithm to solve two routing problems: shortest distance and shortest travel time. The separation of graph storage, path finding, and CLI code makes the implementation easier to maintain and evaluate. The design is suitable for sparse road networks with thousands of nodes, and the evaluation should focus on both algorithmic complexity and real runtime behavior.
