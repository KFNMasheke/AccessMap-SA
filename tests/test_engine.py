import math
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "processing"))
from accessmap_sa import Facility, NearestIndex, assess


class EngineTests(unittest.TestCase):
    def test_known_triangle(self):
        result = assess(NearestIndex([Facility("a", "Clinic", "clinic", 300, 400)]), 0, 0)
        self.assertEqual(result["distance_m"], 500)

    def test_exact_band_boundaries(self):
        index = NearestIndex([Facility("a", "Clinic", "clinic", 0, 0)])
        for distance, band in [(0, "near"), (1000, "near"), (1000.01, "moderate"),
                               (3000, "moderate"), (3000.01, "far")]:
            self.assertEqual(assess(index, distance, 0)["access_band"], band)

    def test_unknown_is_not_far_or_zero(self):
        result = assess(NearestIndex([]), 0, 0)
        self.assertEqual(result["access_band"], "unknown")
        self.assertIsNone(result["distance_m"])

    def test_ties_are_stable(self):
        rows = [Facility("b", "B", "clinic", -1, 0), Facility("a", "A", "clinic", 1, 0)]
        for order in [rows, rows[::-1]]:
            self.assertEqual(assess(NearestIndex(order), 0, 0)["nearest_id"], "a")

    def test_invalid_inputs(self):
        for value in [math.inf, -math.inf, math.nan]:
            with self.assertRaises(ValueError):
                Facility("a", "A", "clinic", value, 0)
            with self.assertRaises(ValueError):
                assess(NearestIndex([]), value, 0)
        for thresholds in [(0, 1), (2, 1), (1, 1), (1, math.inf), (math.nan, 3)]:
            with self.assertRaises(ValueError):
                assess(NearestIndex([]), 0, 0, *thresholds)
        f = Facility("a", "A", "clinic", 0, 0)
        with self.assertRaises(ValueError):
            NearestIndex([f, f])

    def test_index_against_independent_exhaustive_search(self):
        rng = random.Random(2026)
        facilities = [Facility(str(n), str(n), "clinic", rng.uniform(-1e4, 1e4),
                               rng.uniform(-1e4, 1e4)) for n in range(400)]
        index = NearestIndex(facilities)
        for _ in range(100):
            x, y = rng.uniform(-2e4, 2e4), rng.uniform(-2e4, 2e4)
            expected = min(facilities, key=lambda f: (math.hypot(x-f.x, y-f.y), f.id))
            actual, distance = index.nearest(x, y)
            self.assertEqual(actual.id, expected.id)
            self.assertAlmostEqual(distance, math.hypot(x-expected.x, y-expected.y))


if __name__ == "__main__":
    unittest.main()
