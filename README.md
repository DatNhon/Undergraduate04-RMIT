# Undergraduate04-RMIT

## How to run
1) Demo mode (default):
```bash
   python main.py
   ```

  You can also run the legacy wrapper:
```bash
  python smart_path_finder.py
```

2) Interactive mode:
```bash
   python main.py --mode interactive --nodes 3000 --avg-degree 4
   ```

3) Query mode (explicit input):
```bash
   python main.py --mode query --nodes 3000 --source 10 --destination 120 \
     --departure-hour 8 --avoid-nodes 11,12 --avoid-edges 20-21,22-23
    ```

4) Benchmark mode:
```bash
   python main.py --mode benchmark --nodes 3000 --benchmark-queries 50
   ```

5) Try different data structures:
```bash
 python main.py --mode benchmark --nodes 3000 --graph-structure list
 
  python main.py --mode benchmark --nodes 3000 --graph-structure compact

  python main.py --mode benchmark --nodes 3000 --graph-structure both
  ```

6) Visualize nodes/graph (PNG output):
```bash 
python main.py --mode visualize --nodes 1200 --output-image map.png
```

7) Visualize with a query path overlay:
```bash
 python main.py --mode visualize --nodes 1200 --source 5 --destination 980 \
    --departure-hour 8 --avoid-nodes 12,13 --avoid-edges 20-21,40-41 \
    --output-image map_with_paths.png
```