# Smart Path Finder Demo Video Script (4 Members, Max 10 Minutes)

## Goal
Produce a clear demo video (<= 10 minutes) where all 4 group members appear and cover:
- Environment setup
- Running the program
- Executing queries
- Presenting and evaluating outputs

## Total Duration Plan
- Target total: 9:30 (keep 30 seconds buffer)

## Roles
- Member 1: Introduction + environment setup
- Member 2: Program run + project structure
- Member 3: Query execution (normal + constrained)
- Member 4: Output interpretation + evaluation + closing

## Pre-Recording Checklist
- All members are visible at least once on camera.
- Terminal font is readable (zoom in if needed).
- Repo is already opened at project root.
- Python virtual environment exists and can run `python`.
- Keep one clean terminal for commands.
- Keep `doc/TECHNICAL_REPORT.md` open for metric reference.

---

## Timestamped Script (What To Say + What To Do)

## 0:00 - 0:40 | Member 1 (Opening)
### On Screen
- Camera on Member 1
- Project folder visible in editor

### Script
"Hello, we are Group [Your Group Name], and this is our Smart Path Finder demo.
In this video, all four of us will demonstrate environment setup, running the program, executing routing queries, and evaluating the outputs."

"I am [Member 1 Name]. Next, I will show the environment setup."

---

## 0:40 - 2:10 | Member 1 (Environment Setup)
### On Screen
- Switch to terminal

### Commands
```bash
pwd
ls
python --version
```

If using virtual environment:
```bash
source .venv/bin/activate
python --version
```

Optional quick sanity check:
```bash
python main.py --help
```

### Script
"We are in the project root, and Python is installed correctly."

"Our entry point is `main.py`, which supports benchmark and query modes."

"Now we hand over to Member 2 to run the program end-to-end."

---

## 2:10 - 3:40 | Member 2 (Run Program + Benchmark)
### On Screen
- Terminal + brief look at key files (`main.py`, `app.py`, `graph_models.py`, `smart_path_finder.py`)

### Commands
Quick benchmark run:
```bash
python main.py --mode benchmark --nodes 1000 --avg-degree 4 --benchmark-queries 20 --graph-structure both --seed 42
```

### Script
"I am [Member 2 Name]. Here we run benchmark mode, which builds synthetic road graphs and tests query performance."

"This command compares both graph structures: adjacency list and compact representation."

"After execution, we get timing and consistency-related output."

"Next, Member 3 will execute interactive-style query examples."

---

## 3:40 - 6:40 | Member 3 (Execute Queries)
### On Screen
- Terminal output in focus

### Query A: Standard route
```bash
python main.py --mode query --nodes 3000 --source 10 --destination 2000 --departure-hour 8 --graph-structure both --seed 42
```

### Script
"I am [Member 3 Name]. This first query requests routes from node 10 to node 2000 at 8 AM using both graph structures."

"The program returns distance-optimized and time-optimized paths, including total distance and travel minutes."

### Query B: With constraints (avoid nodes and edges)
```bash
python main.py --mode query --nodes 3000 --source 10 --destination 2000 --departure-hour 8 --avoid-nodes 11,12,13,14 --avoid-edges 20-21,22-23 --graph-structure both --seed 42
```

### Script
"Now we add constraints by avoiding selected nodes and edges."

"This demonstrates practical rerouting behavior and how constraints can change path quality and feasibility."

"I will now pass to Member 4 for output evaluation and conclusion."

---

## 6:40 - 9:00 | Member 4 (Present and Evaluate Outputs)
### On Screen
- Split view: terminal results + `doc/TECHNICAL_REPORT.md` (Section 3.2.4)

### Script
"I am [Member 4 Name]. We now evaluate the outputs against our measured results in the report."

"Key observations:"
- "Both structures are consistent in routing results in our benchmark."
- "In our current environment, adjacency list is slightly faster than compact across tested sizes."
- "As graph size increases, query and generation times increase, matching expected scaling trends."
- "With constraints, the system can produce different detours or reduce feasible paths, which is expected."

"So our implementation is correct, reproducible, and scalable for the required problem size."

"Thank you for watching our demo."

---

## 9:00 - 9:30 | All Members On Screen (Required)
### On Screen
- All 4 members visible together

### Script
"We are [Member 1], [Member 2], [Member 3], and [Member 4].
This concludes our Smart Path Finder demonstration. Thank you."

---

## Backup Plan (If a Command Fails During Recording)
Use these fallback commands:

1) Show help
```bash
python main.py --help
```

2) Smaller benchmark for quick success
```bash
python main.py --mode benchmark --nodes 500 --avg-degree 4 --benchmark-queries 10 --graph-structure both --seed 42
```

3) Simpler query
```bash
python main.py --mode query --nodes 1000 --source 1 --destination 500 --departure-hour 9 --graph-structure both --seed 42
```

If needed, say:
"For time, we are using a smaller input here, but the full benchmark results are documented in our technical report."

---

## Submission Tips
- Keep final video between 9:00 and 9:50.
- Ensure each member speaks clearly and appears on camera.
- Do not cut away before showing final outputs.
- Keep terminal output readable and avoid fast scrolling.
