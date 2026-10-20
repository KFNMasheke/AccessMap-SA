#!/usr/bin/env python3
"""Offline CSV analysis. Coordinates are EPSG:32735 by default, never lon/lat."""
import argparse
import csv
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "processing"))
from accessmap_sa import Facility, NearestIndex, assess, validate_thresholds, validate_xy


def read_csv(path, required):
    with open(path, newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not set(required).issubset(reader.fieldnames or []):
            raise ValueError(f"{path}: required columns are {', '.join(required)}")
        return list(reader)


def spreadsheet_safe(value):
    # Protect exported strings when opened in spreadsheet software.
    return "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value


def write_outputs(output, results, summary):
    """Stage both files before replacing either destination.

    Each replacement is atomic; two files are not one filesystem transaction.
    If the second replacement fails, rerun before consuming the pair.
    """
    staged = []
    try:
        for target in (output, output.with_suffix('.summary.json')):
            with tempfile.NamedTemporaryFile(mode='w', newline='', encoding='utf-8',
                                             dir=output.parent, delete=False) as stream:
                temporary = Path(stream.name)
                staged.append((temporary, target))
                if target == output:
                    writer = csv.DictWriter(stream, fieldnames=list(results[0]), lineterminator='\n')
                    writer.writeheader()
                    writer.writerows({k: spreadsheet_safe(v) for k, v in row.items()} for row in results)
                else:
                    json.dump(summary, stream, indent=2)
                    stream.write('\n')
                stream.flush()
                os.fsync(stream.fileno())
        for temporary, target in staged:
            os.replace(temporary, target)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def run(args):
    validate_thresholds(args.near, args.far)
    category = args.category.strip().casefold()
    if not category:
        raise ValueError("A non-empty category is required.")
    facilities = read_csv(args.facilities, ["id", "name", "category", "x", "y"])
    origins = read_csv(args.origins, ["id", "x", "y"])
    selected = [Facility(r["id"].strip(), r["name"].strip(), category, float(r["x"]), float(r["y"]))
                for r in facilities if r["category"].strip().casefold() == category]
    index = NearestIndex(selected)
    seen = set()
    results = []
    for row in origins:
        origin_id = row['id'].strip()
        if not origin_id or origin_id in seen:
            raise ValueError("Origin IDs must be non-empty and unique.")
        seen.add(origin_id)
        x, y = float(row["x"]), float(row["y"])
        validate_xy(x, y)
        result = assess(index, x, y, args.near, args.far)
        results.append({"origin_id": origin_id, "x": x, "y": y, **result,
                        "category": category, "near_m": args.near, "far_m": args.far,
                        "metric_crs": args.crs, "method": "projected_straight_line"})
    if not results:
        raise ValueError("No community points to assess.")
    output = Path(args.output)
    destinations = {output.resolve(), output.with_suffix('.summary.json').resolve()}
    if destinations & {Path(args.origins).resolve(), Path(args.facilities).resolve()}:
        raise ValueError("Output must not overwrite an input file.")
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = {"category": category, "origin_count": len(results),
               "facility_count": len(selected), "bands": dict(Counter(r["access_band"] for r in results)),
               "near_m": args.near, "far_m": args.far, "metric_crs": args.crs,
               "method": "projected_straight_line", "population_weighted": False,
               "note": "Counts represent sample points, not people. Missing facilities mean unknown."}
    write_outputs(output, results, summary)
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origins", default="data/demo_origins.csv")
    parser.add_argument("--facilities", default="data/demo_facilities.csv")
    parser.add_argument("--category", default="clinic")
    parser.add_argument("--near", type=float, default=1000)
    parser.add_argument("--far", type=float, default=3000)
    parser.add_argument("--crs", default="EPSG:32735", help="Metadata only: both CSVs must already use this projected metre CRS.")
    parser.add_argument("--output", default="outputs/clinic_access.csv")
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
