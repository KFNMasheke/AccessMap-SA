# Method and interpretation

1. Select a single service category, trimming whitespace and ignoring case.
2. Reproject both point layers into a suitable local projected metre CRS in QGIS. The CSV tool expects already-projected coordinates.
3. Build a balanced two-dimensional KD tree from the selected facility points.
4. For each representative point, find the minimum Euclidean distance. Exact ties resolve by facility ID, in lexical order.
5. Classify using unrounded distances: near <= near threshold; moderate > near and <= far; far > far. Store the unrounded distance in metres. Format only for presentation.
6. If no facility is recorded for a category, classify unknown with null distance and facility fields.

## Scope and limitations

- The synthetic demo uses WGS 84 / UTM zone 35S, EPSG:32735. Projection suitability, axis units and distortion must be checked for every real area. Metre units alone do not guarantee an appropriate projection; do not use Web Mercator for measurement.
- A 500 m grid represents sampled cell centres, not population, households, administrative wards or exact catchments. Its symbols must not be interpreted as continuous coverage boundaries.
- Thresholds are user-defined exploratory settings. They do not establish compliance with any government norm.
- Sample-point counts are not population coverage percentages. A future population-weighted analysis needs licensed, current population data and a separately validated method.
- A nearby service may be closed, full, unaffordable, unsafe to reach or inaccessible. Straight-line distance ignores roads, rivers, fences and transport.
- Facilities beyond an analysis boundary can be the nearest. Include surrounding services and compare results with a larger surrounding extent until distances stabilise. The tool does not automatically fetch or clip datasets.
- Source completeness and verification dates must accompany real results. Missing records are not proof of service absence.
- The QGIS tool validates required layers, finite point coordinates, single-part geometries, valid CRS, metre units, unique selected facility IDs and ordered finite thresholds. An invalid selected feature stops the run rather than silently hiding it.
- Canceled or failed runs may leave partial outputs. Discard them. Input attributes are intentionally not copied into results.

## Validation

The pure-Python tests use an independently calculated 3-4-5 triangle, exact band boundaries, invalid values, stable ties and randomized KD-tree comparisons against exhaustive search. Integration checks reopen a relocated project, verify layers/layouts, compare all 320 demo results, exercise CRS transformation and reject invalid settings.

The native concept uses the same projected point coordinates and Euclidean method; no GPS is requested and its fixed demo origin is displayed. Native installation, screen-reader and battery testing remain pilot prerequisites.
