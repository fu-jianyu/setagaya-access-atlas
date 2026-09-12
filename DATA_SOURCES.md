# Data sources and transformations

## OpenStreetMap

© OpenStreetMap contributors. OSM-derived source extracts, retained network, POIs, boundary, route tables and derived database content are provided under the [Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/). Attribution and access to the license: [OpenStreetMap copyright](https://www.openstreetmap.org/copyright).

- Snapshot: 2026-09-12 13:27:06 UTC; Setagaya boundary relation 1759474.
- Source queries: `scripts/fetch_data.py`; original extract files: `raw/`.
- Reconstruction: `scripts/prepare_data.py`; numeric metadata: `dist/data/metadata.json`.
- 28,000 retained buffered routing nodes, 41,869 edges; 15,752 ward street segments displayed.
- 6,090 POIs including surrounding facilities; 2,134 inside the ward.
- Public street skeleton: service alleys and independent footpaths are omitted; geometry nodes are simplified while retained path lengths are preserved; disconnected components are discarded.
- Facilities connect to retained junctions by a straight connector of at most 350 m. Same-name, same-type nearby records are deduplicated as documented in the script.
- Distances use float32 metres. Gzip streams are stored in ordered binary chunks without changing their decompressed bytes.

The processed database and underlying source snapshot are both included to support inspection and reconstruction. The model output and processing are the project's work, not an official OSM accessibility product.

## Geospatial Information Authority of Japan (GSI)

The 29 background PNG tiles in `dist/tiles/` come from the GSI pale map (`pale`) tile service, acquired by `scripts/fetch_assets.py`. Source: [GSI tile catalogue](https://maps.gsi.go.jp/development/). See [GSI Website Terms of Use](https://www.gsi.go.jp/ENGLISH/page_e30236.html) and [source attribution guidance](https://web2.gsi.go.jp/LAW/2930-meizi.html).

The app overlays its own OSM-derived street colors and labels on the GSI map. Those additions and accessibility results were not created or endorsed by GSI. Backgrounds are cached only for the bundled area and are enlarged beyond their maximum native zoom. Keep map source attribution visible in presentations and screenshots.

## Leaflet

Leaflet 1.9.4 is bundled in `dist/vendor/`. Its BSD 2-Clause license and copyright notice are reproduced in `dist/vendor/Leaflet-LICENSE.txt`.

## Research assumptions

Walking times use retained shortest road distances and facility connectors. Signals, slopes, openings and detailed entrances are not modelled. Supply weights of 1–4 are declared type scenarios. Competition demand assigns one unit to each retained inside-ward junction, not census population. Ordinary street scores combine endpoints and, for streets longer than 200 m, a midpoint; graph centralities have the mapping conventions stated in the guide.

Method citations and the 17 parameter configurations are available in `dist/guide.html` and the in-app Data & methods panel. A formula identity under these assumptions is different from empirical validation against travel behavior.
