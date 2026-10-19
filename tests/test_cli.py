import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "scripts/analyse.py"), *args],
                              cwd=ROOT, capture_output=True, text=True)

    def test_demo_summary_and_unknown_category(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "results.csv"
            result = self.run_cli("--output", str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(out.with_suffix(".summary.json").read_text())
            self.assertEqual(summary["origin_count"], 320)
            self.assertEqual(summary["bands"], {"near": 24, "moderate": 137, "far": 159})
            result = self.run_cli("--category", "missing", "--output", str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            with out.open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertTrue(all(r["access_band"] == "unknown" and r["distance_m"] == "" for r in rows))

    def test_invalid_input_does_not_replace_existing_output(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "results.csv"
            out.write_text("existing output")
            result = self.run_cli("--near", "5000", "--far", "3000", "--output", str(out))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(out.read_text(), "existing output")

    def test_formula_names_are_escaped(self):
        with tempfile.TemporaryDirectory() as temp:
            facilities = Path(temp) / "facilities.csv"
            facilities.write_text('id,name,category,x,y\na,=1+1,clinic,590250,7112250\n')
            out = Path(temp) / "results.csv"
            result = self.run_cli("--facilities", str(facilities), "--output", str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            with out.open() as stream:
                self.assertEqual(next(csv.DictReader(stream))["nearest_name"], "'=1+1")


if __name__ == "__main__":
    unittest.main()
