# Historical synthetic benchmarks

`history.tar.gz` preserves 2,047 reviewed files from outputs/synthetic,
outputs/phase1 and outputs/phase2. These are generated synthetic results only.
The manifest includes the archive checksum and every member's SHA-256.

Run `python scripts/restore_benchmarks.py` from the project directory before the
research tests. Restoration checks every file before writing, rejects unsafe paths
and refuses to overwrite changed local results. The 108 original CSVs and Phase 1
freeze checks are preserved. Public comparison reports are also in reports/.

No official public-label files, actual-match tracking, restricted assets or private
logs are included in this archive. Reproduce new experiments using the pinned
configurations and existing phase scripts rather than changing historical outputs.
