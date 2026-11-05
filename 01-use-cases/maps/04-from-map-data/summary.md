# From map data: summary

**Purpose.** Show the maps half working with no text behind it: a dataset
that arrives as points, loaded, questioned in SQL, mapped with its time
dimension, and handed to QGIS.

**Workflow.** GOV bounding-box query → 1,715 places, 3,721 dated names →
records → DuckDB spatial → six questions with their SQL → map, SQLite,
GeoPackage.

**Findings.** The data's own structure shows on the map: 552 German names
end and 955 Polish names begin in 1945; a village can carry thirteen
spellings; towns are 23 of 1,715 objects, the rest parishes, districts and
estates. Any spreadsheet with coordinates goes through the same path.

**Limits.** One rectangle; GOV's coverage and dating are uneven (most names
have no years at all); coordinates are modern.
