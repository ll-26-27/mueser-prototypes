---
title: Historical map overlay — what Allmaps can put under the points
description: For every resolved point on the route, ask the Allmaps index which georeferenced IIIF map scans cover it, measure each sheet's scale and check its control points → a table of candidate sheets; the viewer's overlay toggle takes any sound annotation URL.
author: claude
created: 2026-11-04
---

# Historical map overlay: what Allmaps can put under the points

The map viewer in this repository has a **historical map overlay** toggle.
It loads an [Allmaps](https://allmaps.org) georeference annotation (a small
JSON file that says which pixels of a IIIF map scan correspond to which
coordinates) with the `@allmaps/maplibre` plugin and warps the scan onto the
base map, with an opacity slider. Any library's IIIF map works, including
Harvard Library's, once someone has georeferenced it in the Allmaps editor.

## What happened

`operations/01-find-georeferenced-maps.py` asked `api.allmaps.org/maps?intersects=<lon>,<lat>`
for each of the 21 resolved points of the 1786 route and wrote
`outputs/georeferenced-maps.csv`: 4,200 (place, sheet) rows, 200 per point,
which is the index's page size. For each sheet it records the annotation
URL, the IIIF image and its holder, the number of ground control points,
and the **spread of those control points in degrees**, which is the scale
of the sheet: a world map spans 300° of longitude, a city plan a fraction
of one.

| scale (from control-point spread) | sheets |
|---|---|
| continental or world | 4,191 |
| regional (under 8° × 6°) | 6 |
| city (under 0.5° × 0.5°) | 3 |

None of the nine regional or city sheets actually contains the point it was
returned for: their control points sit elsewhere (a Scottish sheet returned
for Memel; a "Historischer Atlas von Berlin" sheet whose three control
points lie in the Gulf of Guinea; a David Rumsey Berlin plan whose thirty
points span the globe). The index matches on the warped mask, and a badly
georeferenced sheet has a mask anywhere. **So the viewer ships with the
overlay toggle disabled** rather than with a wrong map, and this table is
the record of what was checked.

## How to add a real overlay

1. Find a map of the region in a IIIF collection (Harvard Library,
   David Rumsey, the Staatsbibliothek zu Berlin, the SLUB's Deutsche
   Fotothek). A good start for this route: a Prussian provincial map of the
   1780s–1820s.
2. Open its IIIF manifest or image in **https://editor.allmaps.org**, place
   at least four control points on towns you can identify, draw the mask,
   and copy the annotation URL from the editor.
3. Put it in `.env` as `ALLMAPS_ANNOTATION_URL=…` (or pass
   `--allmaps-annotation` to `build_map`) and rebuild the map. The toggle
   turns on.
4. Check it: the warped sheet should sit on the base map's rivers and coast.
   If it does not, the control points are wrong, not the viewer.

The plugin, the import and the call sequence are in
`src/mueser/maps/web/map-template.html` (`setupAllmaps`). Allmaps is for
display; for analysis in QGIS, export a GeoTIFF from the same control points.

## Rights

Allmaps hosted services under their published terms; the sheets listed in
the CSV belong to their holders (David Rumsey Map Collection, Boston Public
Library, Bodleian, NYPL, NLS, UvA, Leiden, Gallica and others) under the
licences stated on their pages. Nothing is copied here but URLs and numbers.
