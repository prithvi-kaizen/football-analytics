# Possession Lab public research explorer

The static site runs the existing Python research models in a browser Web Worker
using Pyodide 0.29.2, NumPy and pandas. There is no paid API, inference server,
account, upload endpoint or JavaScript reimplementation of the research models.
Precomputed defaults make the first view available while the numerical runtime
loads. Changed playground settings execute Python on the visitor's device.

From the possession-lab package directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python explorer/scripts/vendor_runtime.py
.venv/bin/python explorer/scripts/build.py
.venv/bin/python -m http.server 8080 --directory explorer/dist
```

Build prerequisites are sibling checkouts of the public official challenge and
public Metrica samples at the commits listed in THIRD_PARTY.md. A fresh checkout:

```bash
git clone https://github.com/metrica-sports/more-than-a-hack-2027.git ../more-than-a-hack-2027
git -C ../more-than-a-hack-2027 checkout f8f2629ff1e0985f81d7e59d8413678514ee1530
git clone https://github.com/metrica-sports/sample-data.git ../public-sample-data
git -C ../public-sample-data checkout e706dd506b360d69d9d123d5b8026e7294b13996
```

The build has an explicit public-file allowlist. It never scans for match assets
or reads MTAH_DATA_DIR. It verifies the frozen Phase 1 files and official source.
The exported source zip excludes credentials, Git metadata, local runtimes and
downloaded full datasets. Research code is MIT; public dataset terms are separate.

The browser runtime has its own Pyodide-pinned numerical versions, recorded in
each computation's runtime metadata. It is not the native Python 3.14.2 lock.
Compare the deterministic default fixture across runtimes during browser QA;
do not claim universal byte parity across numerical versions without testing.
The pinned runtime and its numerical wheels are served with the site. Run
`python explorer/scripts/vendor_runtime.py` once before building a fresh checkout;
wheel hashes are checked against the Pyodide package lock. The runtime adds about
20 MB to the static deployment and does not call an external CDN at inference time.
An initialization failure leaves the saved examples usable and reports that
changed settings cannot run until the runtime is available.

Public sample accuracy is deliberately unavailable. Synthetic scenario scores
are diagnostics for that scenario, not estimates of real-match generalization.
The paired observability demonstration uses hypothetical independent cues;
it does not claim they exist in a real tracking or tagging product.

## Free static hosting

Publish only `dist/` to GitHub Pages, Cloudflare Pages or another static host.
Use relative asset paths so subdirectory hosting works. No secret or server
environment is required. Free plan availability/limits depend on the provider.
The supplied Sites manifest targets the same static output. Public source is
available as `dist/possession-lab-source.zip`, with research, tests and build code.

Run `bash scripts/reproduce_explorer.sh` for Python checks and the static build.
Existing phase reproduction scripts and all historical benchmarks stay intact.
