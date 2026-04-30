Smart Path Finder

Submission Contents
- `main.py` is the launcher for the system.
- `README.txt` documents setup, execution, input, and output.
- Source modules: `app.py`, `path_finder.py`, `graph_models.py`.

1. Environment Setup
- Python 3.10 or newer is recommended.
- No third-party dependencies required.

2. How to Run the Program
Run the launcher from the project root:
```bash
python main.py
```

Other supported modes:
```bash
python main.py --mode interactive --nodes 3000 --avg-degree 4
python main.py --mode query --nodes 3000 --source 10 --destination 120 --departure-hour 8 --avoid-nodes 11,12 --avoid-edges 20-21,22-23
python main.py --mode benchmark --nodes 3000 --benchmark-queries 50
```

3. Input Format
The program accepts command-line arguments.

Required in query mode:
- `--source`: start node index
- `--destination`: target node index
- `--departure-hour`: integer from 0 to 23

Optional arguments:
- `--nodes`: number of generated nodes
- `--avg-degree`: target average degree of the graph
- `--seed`: random seed for reproducible graphs
- `--avoid-nodes`: comma-separated node list such as `5,20,21`
- `--avoid-edges`: comma-separated edge list in `u-v` format such as `1-2,3-4`
- `--graph-structure`: `list`, `compact`, or `both`

Each query uses:
- source node
- destination node
- departure hour
- optional avoided nodes
- optional avoided edges

4. Output Description
For each query, the program prints two results:
- distance-optimised path
- time-optimised path

Each result includes:
- the sequence of path nodes
- total distance in kilometres
- total travel time in minutes
