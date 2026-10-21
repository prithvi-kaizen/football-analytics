"""Export real Python results and sampled replays into a portable static release."""

from dataclasses import replace
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from invisible_runner.analysis import RunConfig, detect_runs
from invisible_runner.data import sha256
from invisible_runner.pipeline import code_fingerprint
from invisible_runner.viz import replay_frames


def records(frame):
    return json.loads(frame.to_json(orient="records", double_precision=15))


def package():
    output = ROOT / "outputs/1886347-full"
    manifest = json.loads((output / "manifest.json").read_text())
    if manifest["code_sha256"] != code_fingerprint():
        raise SystemExit("Analytical sources changed. Reproduce the full-match pipeline before packaging.")
    if sha256(output / "runs.csv") != manifest["outputs"]["runs_sha256"]:
        raise SystemExit("Published run CSV does not match its manifest.")
    clean_path = Path(manifest["clean_path"])
    clean_audit = json.loads((clean_path.parent / "audit.json").read_text())
    if sha256(clean_path) != clean_audit["clean_sha256"]:
        raise SystemExit("Processed tracking failed its integrity check.")
    tracking = pd.read_parquet(clean_path)
    metadata = manifest["metadata"]
    public_metadata = {key: metadata[key] for key in ["id", "date_time", "home_team", "away_team", "pitch_length", "pitch_width", "home_team_side"]}
    public_metadata["players"] = {str(p["id"]): {key: p[key] for key in ["id", "team_id", "short_name", "number"]} for p in metadata["players"]}
    payload = dict(schema_version=1, metadata=public_metadata,
                   provenance=json.loads((output / "provenance.json").read_text()), profiles={})
    expected_counts = {p["speed_mps"]: p["runs"] for p in manifest["sensitivity"]}
    for speed in [4.5, 5., 5.5]:
        config = replace(RunConfig(**manifest["config"]), speed_mps=speed)
        runs = pd.read_csv(output / "runs.csv") if speed == 5 else detect_runs(tracking, metadata, config)
        if len(runs) != expected_counts[speed]:
            raise SystemExit(f"Profile {speed} differs from the reviewed sensitivity count.")
        runs = runs.sort_values(["start_frame", "player_id"])
        rows = records(runs)
        for index, run in enumerate(runs.itertuples(index=False)):
            series = pd.Series(run._asdict())
            clip = tracking[tracking.period.eq(run.period) & tracking.frame.between(run.start_frame, run.end_frame)]
            frames, timeline = replay_frames(clip, series, metadata, config)
            replay = []
            for i, frame in enumerate(frames):
                shot = frame["shot"]
                first = shot.iloc[0]
                replay.append(dict(frame=frame["frame"], elapsed_s=float(timeline.iloc[i].elapsed_s),
                                   free_area_m2=None if pd.isna(timeline.iloc[i].free_area_m2) else float(timeline.iloc[i].free_area_m2),
                                   players=[[int(p.player_id), round(p.sx, 3), round(p.sy, 3), bool(p.detected)] for p in shot.itertuples()],
                                   ball=[round(float(first.ball_x), 3), round(float(first.ball_y), 3), bool(first.ball_detected)],
                                   **{key: frame[key].round(3).tolist() for key in ["stable", "gained", "lost"]}))
            row = rows[index]
            row["replay"] = replay
            if row["free_area_start_m2"] is not None:
                if replay[0]["free_area_m2"] != row["free_area_start_m2"] or replay[-1]["free_area_m2"] != row["free_area_end_m2"]:
                    raise SystemExit(f"Replay endpoint mismatch: {run.run_id}")
        payload["profiles"][f"{speed:.1f}"] = dict(config=vars(config), runs=rows)
        print(f"Packaged {speed:g} m/s profile: {len(rows)} real runs", flush=True)
    data = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()
    digest = hashlib.sha256(data).hexdigest()
    archive = ROOT / "web/snapshot.json.gz"
    archive.write_bytes(gzip.compress(data, compresslevel=9, mtime=0))
    assets = ["index.html", "app.js", "style.css", "vendor/plotly.min.js", "vendor/LICENSE-plotly.txt"]
    bundle = dict(schema_version=1, snapshot=dict(archive="snapshot.json.gz", archive_sha256=sha256(archive),
                                                 path=f"snapshot.{digest[:16]}.json.gz", sha256=digest),
                  assets={name: sha256(ROOT / "web" / name) for name in assets},
                  profiles={key: len(profile["runs"]) for key, profile in payload["profiles"].items()})
    (ROOT / "web/bundle.json").write_text(json.dumps(bundle, indent=2) + "\n")
    print(f"Snapshot: {len(data):,} bytes, {archive.stat().st_size:,} compressed; SHA-256 {digest}")


if __name__ == "__main__":
    package()
