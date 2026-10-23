"""Package derived research results, never raw events, for the public dashboard."""

import csv
import gzip
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
CORE = ["events.py", "analysis.py", "xt.py", "pipeline.py", "data.py"]
PHASE_FIELDS = ["sequence_key", "match_id", "team", "period", "clock", "elapsed_seconds", "active_seconds",
                "passes", "completed_passes", "progression", "shots", "xg", "positive_xt", "net_xt",
                "score_state", "home_score_before", "away_score_before"]
TEXT = {"sequence_key", "team", "score_state", "competition", "season", "date", "split"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path, fields=None):
    result = []
    with path.open(newline="") as source:
        for row in csv.DictReader(source):
            item = {}
            for key in fields or row.keys():
                value = row[key]
                item[key] = value if key in TEXT else (float(value) if value else None)
            result.append(item)
    return result


def dataset(name):
    output = ROOT / "outputs" / name
    manifest = json.loads((output / "manifest.json").read_text())
    for field in CORE:
        key = f"possession_danger/{field}"
        if sha(ROOT / key) != manifest["code_sha256"][key]:
            raise ValueError(f"Analytics changed: {key}. Rerun the analysis before packaging.")
    for name_to_check in ["summary.json", "xt_model.json", "team_matches.csv", "possessions.csv", "score_states.csv"]:
        if sha(output / name_to_check) != manifest["output_sha256"][name_to_check]:
            raise ValueError(f"Analysis checksum mismatch: {name_to_check}")
    summary = json.loads((output / "summary.json").read_text())
    # A diagnostic source event identifier is unnecessary in the hosted analysis.
    summary["cleaning"].pop("records", None)
    totals = rows(output / "team_matches.csv")
    phases = rows(output / "possessions.csv", PHASE_FIELDS)
    model = json.loads((output / "xt_model.json").read_text())
    fixtures = []
    for comp, season in [(182, 281), (37, 281), (135, 281), (131, 281), (49, 107)]:
        rel = f"data/matches/{comp}/{season}.json"
        source = next((s for s in manifest["sources"] if s["url"].endswith(rel)), None)
        if source is None:
            continue
        cached = ROOT / "data/raw" / manifest["revision"] / rel
        if sha(cached) != source["sha256"]:
            raise ValueError(f"Fixture catalog checksum mismatch: {rel}")
        selected = {int(r["match_id"]) for r in totals}
        for match in json.loads(cached.read_text()):
            if match["match_id"] in selected:
                fixtures.append({"match_id": match["match_id"], "date": match["match_date"],
                                 "home": match["home_team"]["home_team_name"], "away": match["away_team"]["away_team_name"],
                                 "home_score": match["home_score"], "away_score": match["away_score"]})
    return {"id": name, "sample": summary["sample"], "summary": summary,
            "team_matches": totals, "score_states": rows(output / "score_states.csv"),
            "phase_columns": PHASE_FIELDS, "phases": [[p[k] for k in PHASE_FIELDS] for p in phases],
            "fixtures": fixtures, "model": {k: model[k] for k in ["nx", "ny", "value", "counts", "train_matches"]},
            "provenance": {"source_revision": manifest["revision"], "generated_at": manifest["generated_at"],
                           "analysis_hashes": {k: v for k, v in manifest["output_sha256"].items() if k in ["summary.json", "team_matches.csv", "possessions.csv", "score_states.csv"]}}}


def package():
    web = ROOT / "web"
    web.mkdir(exist_ok=True)
    payload = {"schema_version": 1, "classification": "Derived research analysis; not raw StatsBomb event data",
               "datasets": [dataset("liga-f"), dataset("all-leagues-sample")]}
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    digest = hashlib.sha256(data).hexdigest()
    archive = web / "snapshot.json.gz"
    archive.write_bytes(gzip.compress(data, compresslevel=9, mtime=0))
    vendor = web / "vendor"
    vendor.mkdir(exist_ok=True)
    for file in ["plotly.min.js", "LICENSE-plotly.txt"]:
        shutil.copyfile(ROOT.parent / "invisible-runner/web/vendor" / file, vendor / file)
    assets = ["index.html", "app.js", "metrics.js", "style.css", "vendor/plotly.min.js", "vendor/LICENSE-plotly.txt"]
    downloads = {"statsbomb-logo.png": "assets/statsbomb-logo.png", "findings.md": "outputs/liga-f/findings.md",
                 "possession-vs-threat.png": "outputs/liga-f/possession-vs-threat.png", "possession-vs-threat.svg": "outputs/liga-f/possession-vs-threat.svg",
                 "statsbomb-terms.pdf": "docs/source/LICENSE.pdf", "source-audit.md": "docs/source-audit.md"}
    bundle = {"schema_version": 1, "snapshot": {"archive": archive.name, "archive_sha256": sha(archive),
               "path": f"snapshot.{digest[:16]}.json.gz", "sha256": digest},
               "assets": {file: sha(web / file) for file in assets},
               "downloads": {name: {"source": source, "sha256": sha(ROOT / source)} for name, source in downloads.items()}}
    (web / "bundle.json").write_text(json.dumps(bundle, indent=2) + "\n")
    print(f"Derived snapshot: {len(data):,} bytes; {archive.stat().st_size:,} compressed; SHA-256 {digest}")


if __name__ == "__main__":
    package()
