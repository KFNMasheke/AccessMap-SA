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

    def test_summary_cannot_overwrite_input_and_ids_are_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / 'results.summary.json'
            source.write_text('id,x,y\na,590250,7112250\n')
            result = self.run_cli('--origins', str(source), '--output', str(Path(temp) / 'results.csv'))
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(source.read_text().startswith('id,x,y'))
            source.write_text('id,x,y\na,590250,7112250\n a ,590250,7112250\n')
            result = self.run_cli('--origins', str(source), '--output', str(Path(temp) / 'other.csv'))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('unique', result.stderr)

    def test_failed_staging_preserves_existing_files(self):
        import importlib.util
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location('csv_analysis', ROOT / 'scripts/analyse.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'results.csv'
            out.write_text('previous CSV')
            sidecar = out.with_suffix('.summary.json')
            sidecar.write_text('previous summary')
            with patch.object(module.os, 'fsync', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    module.write_outputs(out, [{'id': 'example'}], {})
            self.assertEqual(out.read_text(), 'previous CSV')
            self.assertEqual(sidecar.read_text(), 'previous summary')
            self.assertEqual(len(list(Path(temp).iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
