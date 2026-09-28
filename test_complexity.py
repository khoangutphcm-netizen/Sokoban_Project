"""
CHẠY BẰNG DÒNG NÀY:
python -m unittest test_complexity.py
"""

import statistics
import time
import tracemalloc
import unittest
from pathlib import Path

from core.map_loader import load_map
from search.astar import a_star_search
from search.ucs import uniform_cost_search


MAP_PATH = Path(__file__).resolve().parent / "example_map.txt"
REPETITIONS = 5
ALGORITHMS = (
    ("UCS", uniform_cost_search),
    ("A*", a_star_search),
)


def benchmark_searches(initial_state, grid, repetitions=REPETITIONS):
    samples = {
        name: {"seconds": [], "peak_bytes": [], "visited": [], "outcomes": []}
        for name, _ in ALGORITHMS
    }

    for run_number in range(repetitions):
        algorithms = ALGORITHMS if run_number % 2 == 0 else tuple(reversed(ALGORITHMS))
        for name, search in algorithms:
            start = time.perf_counter()
            actions, cost, visited = search(initial_state, grid)
            samples[name]["seconds"].append(time.perf_counter() - start)
            samples[name]["visited"].append(visited)
            samples[name]["outcomes"].append((actions is not None, cost))

            tracemalloc.start()
            try:
                search(initial_state, grid)
                _, peak_bytes = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            samples[name]["peak_bytes"].append(peak_bytes)

    summary = {}
    for name, measurements in samples.items():
        summary[name] = {
            "median_seconds": statistics.median(measurements["seconds"]),
            "median_peak_bytes": statistics.median(measurements["peak_bytes"]),
            "median_visited": statistics.median(measurements["visited"]),
            "outcomes": measurements["outcomes"],
        }
    return summary


class SearchComplexityExperiment(unittest.TestCase):
    def test_compare_ucs_and_astar(self):
        grid, initial_state = load_map(str(MAP_PATH))
        results = benchmark_searches(initial_state, grid)

        ucs = results["UCS"]
        astar = results["A*"]
        self.assertTrue(all(outcome == ucs["outcomes"][0] for outcome in ucs["outcomes"]))
        self.assertTrue(all(outcome == astar["outcomes"][0] for outcome in astar["outcomes"]))
        self.assertEqual(ucs["outcomes"][0][0], astar["outcomes"][0][0])
        if ucs["outcomes"][0][0]:
            self.assertEqual(ucs["outcomes"][0][1], astar["outcomes"][0][1])

        print(f"\nComplexity comparison on {MAP_PATH.name} ({REPETITIONS} runs; medians)")
        print(f"{'Metric':<28} {'UCS':>14} {'A*':>14}")
        print("-" * 58)
        print(
            f"{'Runtime (seconds)':<28} "
            f"{ucs['median_seconds']:>14.6f} {astar['median_seconds']:>14.6f}"
        )
        print(
            f"{'Peak traced memory (KiB)':<28} "
            f"{ucs['median_peak_bytes'] / 1024:>14.2f} "
            f"{astar['median_peak_bytes'] / 1024:>14.2f}"
        )
        print(
            f"{'Visited states (median)':<28} "
            f"{ucs['median_visited']:>14.0f} {astar['median_visited']:>14.0f}"
        )
        print(f"Solved: UCS={ucs['outcomes'][0][0]}, A*={astar['outcomes'][0][0]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)