# Bring a community data pack

## Required files

| Dataset | Geometry | Required attributes |
|---|---|---|
| Community samples | Single Point | Stable public sample ID recommended; QGIS outputs the source feature ID |
| Facilities | Single Point | Unique ID, name, category |
| Optional context | Any appropriate geometry | Source, licence, publication/verification date |

In QGIS, use a GeoPackage wherever practical. WGS84 lon/lat inputs are acceptable when their CRS is assigned correctly: the processing tool transforms them. CSV mode requires preprojected `x` and `y` metre coordinates; a `--crs` flag cannot reproject a CSV.

Use header-only templates under `data/templates/`. Store local sensitive work under `data/private/`, which is ignored by Git. An ignore rule does not remove previously committed data.

## Candidate sources to investigate

- Municipal or provincial facility registers: request current records and permission for public redistribution.
- OpenStreetMap: https://www.openstreetmap.org/copyright . ODbL conditions and attribution apply. An available point is not necessarily current or complete. No OSM data is bundled in this release.
- Municipal Demarcation Board: https://www.demarcation.org.za/ . Investigate appropriate boundary products and their terms if boundaries are needed.
- Government open-data portals and local libraries/community organisations: verify the actual dataset, its licence, update date, coordinates and service classification before use.

These are candidate sources, not approved licences or promises that a complete dataset is available. No data scraper or automated remote ingestion is enabled.

## Record every source

For each input, record title, publisher, exact source URL, licence, release date, retrieval date, coverage, CRS, known gaps, redistribution rights and local verification date. Keep raw source snapshots separate from cleaned outputs. Use stable facility IDs to deduplicate records and manually review suspected duplicates or co-located facilities.

## Release review

Confirm facilities and opening hours with the responsible organisation or community validators. Remove personal contacts and household locations. Keep public facility contacts only where publication is justified. Clearly separate verified facts, uncertain records and missing information. Publish a corrections contact/process before a real release.
