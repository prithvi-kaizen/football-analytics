# Hosting and release refresh

Possession Lab follows the portfolio's `projects/<name>/` convention. The reviewed
static release is in `web/release.tar.gz`; its manifest records all restored asset
hashes and an authored-source fingerprint. `python3 scripts/build_website.py` at the
repository root restores the project under `dist/possession-lab/` alongside the
existing sites. It uses only the Python standard library and makes no network calls.
The existing Vercel Git integration builds pushes to main. No server, API key or
paid inference service is needed. The original Sites URL remains available too.

The release contains only synthetic scenarios, attributed public Metrica excerpts,
research Python modules, reports and pinned Pyodide runtime assets. It excludes
restricted match files, private logs, official five-minute labels and full public
tracking downloads. Public sample accuracy is deliberately unavailable. Dataset
terms remain separate from the MIT code licence.

## Regenerate the release

1. Set up the native research environment and restore synthetic benchmarks as
   described in the project README.
2. Clone the public Metrica samples to the expected sibling location and pin them:

   ```sh
   git clone https://github.com/metrica-sports/sample-data.git ../public-sample-data
   git -C ../public-sample-data checkout e706dd506b360d69d9d123d5b8026e7294b13996
   ```

3. Run the full research tests. Fetch the hash-pinned runtime, then regenerate
   the original explorer bundle:

   ```sh
   python explorer/scripts/vendor_runtime.py
   python explorer/scripts/build.py
   python explorer/scripts/verify_bundle.py
   node --check explorer/web/app.js
   node --check explorer/web/worker.js
   ```

4. Review all public/synthetic fixtures and inspect browser controls before
   packaging. The packager overlays the authored HTML/CSS/JS, checks public-sample
   truth suppression and matches research source hashes to the reviewed build:

   ```sh
   python scripts/package_website.py --input explorer/dist
   python scripts/build_website.py
   ```

5. Run the portfolio build and publication tests. Commit the source, release and
   manifest together. The source fingerprint refuses a stale release.

The portfolio release links directly to the GitHub project for source; it does not
carry another source ZIP inside the website archive. Pyodide and its wheels remain
self-hosted, including original licence notices. The runtime is downloaded only
when visitors open the playground. Saved examples appear first; transient package
failures are retried and an explicit retry is available.

## Restore research history

`python scripts/restore_benchmarks.py` verifies and restores the reviewed synthetic
outputs from `benchmarks/history.tar.gz`. The archive and every member are checked,
paths must remain inside the project, and changed local files are preserved by
refusing to overwrite them. The public reports under `reports/` can be read directly
on GitHub without restoring the archive.
