"""Parallel read-only spatial queries must remain deterministic."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "processing"))
from accessmap_sa import Facility, NearestIndex, assess


class ConcurrentQueriesTests(unittest.TestCase):
    def test_shared_immutable_index_is_safe_for_parallel_requests(self):
        facilities = [Facility(str(i), f"Facility {i}", "clinic", float(i * 25), float(i % 7 * 40))
                      for i in range(200)]
        index = NearestIndex(facilities)
        points = [(float(i * 13), float(i % 19 * 21)) for i in range(100)]
        expected = [assess(index, x, y) for x, y in points]
        workers = 12
        gate = threading.Barrier(workers)

        def query_all(_):
            gate.wait(timeout=15)
            return [assess(index, x, y) for x, y in points]

        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(query_all, range(workers)))
        self.assertEqual(results, [expected] * workers)
        self.assertEqual([assess(index, x, y) for x, y in points], expected)


if __name__ == "__main__":
    unittest.main()
