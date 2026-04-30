# Undergraduate04-RMIT

Smart Path Finder: Time-dependent shortest path routing with Dijkstra's algorithm.

## Requirements

- **Python 3.10+** (no external dependencies)

## Setup

```bash
# Clone and navigate to project directory
cd Assignment_group

# Run directly (no installation needed)
python main.py
```

## How to Run

### 1. Demo Mode (default)
Generates a random route with constraints:
```bash
python main.py
```

### 2. Interactive Mode
Prompts for source, destination, departure hour, and constraints:
```bash
python main.py --mode interactive
```

### 3. Query Mode
Specify exact endpoints and parameters:
```bash
python main.py --mode query --source 10 --destination 120 \
  --departure-hour 8 --avoid-nodes 11,12 --avoid-edges 20-21,22-23
```

### 4. Benchmark Mode
Run performance tests on random queries:
```bash
python main.py --mode benchmark --benchmark-queries 100
```

### 5. Compare Graph Structures
Test list vs compact graph representations:
```bash
python main.py --mode benchmark --nodes 3000 --graph-structure both
```

## Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--mode` | demo | Execution mode: demo, interactive, query, benchmark |
| `--nodes` | 3000 | Number of nodes in generated graph |
| `--avg-degree` | 4 | Average node degree |
| `--seed` | 42 | Random seed for reproducibility |
| `--source` | - | Start node (required in query mode) |
| `--destination` | - | End node (required in query mode) |
| `--departure-hour` | 8 | Departure hour (0-23) |
| `--avoid-nodes` | - | Comma-separated nodes to avoid (e.g., `11,12,13`) |
| `--avoid-edges` | - | Comma-separated edges to avoid (e.g., `20-21,22-23`) |
| `--benchmark-queries` | 50 | Number of random queries to run in benchmark |
| `--graph-structure` | list | Graph representation: list, compact, or both |

## Output

Each query returns two results:
- **Distance-optimised path**: Minimizes total distance (km)
- **Time-optimised path**: Minimizes total travel time (minutes)

Example output:
```
Query:
  source=10
  destination=120
  departure_hour=8
  avoid_nodes=[11, 12]
  avoid_edges=[(20, 21), (22, 23)]

Distance-optimised path:
  Nodes: 10 -> 45 -> 78 -> 120
  Total distance: 156.234 km
  Total travel time: 245.6 minutes

Time-optimised path:
  Nodes: 10 -> 32 -> 89 -> 120
  Total distance: 172.456 km
  Total travel time: 198.3 minutes
```