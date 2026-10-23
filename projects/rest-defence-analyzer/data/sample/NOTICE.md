# DFL open-data extract

Original data owner: **Deutsche Fußball Liga (DFL)**.

Bassek, M., Rein, R., Weber, H. & Memmert, D. (2025). *An integrated dataset of spatiotemporal and event data in elite soccer*. Scientific Data 12, 195. https://doi.org/10.1038/s41597-025-04505-y

Original source: https://doi.org/10.6084/m9.figshare.28196177.v1

Licence: **Creative Commons Attribution 4.0 International**, https://creativecommons.org/licenses/by/4.0/

Changes: tracking is restricted to firstHalf native frames 10000–14500 of match J03WPY; XML wrappers are reconstructed around unchanged original frame lines. All 22 active players and the ball are included. Match metadata and events are unmodified original files. Compression is lossless. `manifest.json` records original XML and compressed-file SHA-256 hashes. `docs/source/sample-ranges.json` records exact original byte ranges, range hashes and source identity.

Coordinates in the source extract remain unchanged. Application outputs rotate coordinates and derive metrics as explained in the methodology. No endorsement by the DFL or authors is implied.
