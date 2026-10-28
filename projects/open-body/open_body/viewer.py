"""Export deterministic real clips and an offline, dependency-free analysis viewer."""

from pathlib import Path
import json
import math
import numpy as np
import pandas as pd
from .data import Tracking, load_metadata, iter_frames
from .orientation import shoulder_measurement, gate

SKELETON = [
    ("nose", "neck"),
    ("neck", "lShoulder"),
    ("neck", "rShoulder"),
    ("lShoulder", "rShoulder"),
    ("lShoulder", "lElbow"),
    ("lElbow", "lWrist"),
    ("rShoulder", "rElbow"),
    ("rElbow", "rWrist"),
    ("neck", "midHip"),
    ("midHip", "lHip"),
    ("midHip", "rHip"),
    ("lHip", "rHip"),
    ("lHip", "lKnee"),
    ("lKnee", "lAnkle"),
    ("rHip", "rKnee"),
    ("rKnee", "rAnkle"),
    ("lAnkle", "lHeel"),
    ("lAnkle", "lBigToe"),
    ("rAnkle", "rHeel"),
    ("rAnkle", "rBigToe"),
]


def export_clip(root, match, rows, cfg):
    meta = load_metadata(root / "data/raw", match)
    track = Tracking(root / f"data/raw/{match}_tracking_extrapolated.jsonl", meta)
    midfield = rows[rows.position_group.eq("Midfield")].sort_values("frame")
    if midfield.empty:
        return None
    event = midfield.iloc[0]
    pid = int(event.player_id)
    centre = event.frame * 2.5
    start = math.ceil(centre - 25)
    end = math.floor(centre + 75)
    roster = {p["id"]: p for p in meta["players"]}
    clip = []
    for row in iter_frames(root / f"data/raw/{match}.jsonl.zip"):
        f = row["frame"]
        if f < start:
            continue
        if f > end:
            break
        if row["period"] != event.period:
            continue
        tf = f * 2 // 5
        players = []
        for player_id, i in track.lookup.items():
            pos = track.xy[tf, i]
            if not np.isfinite(pos).all():
                continue
            p = roster[player_id]
            players.append(
                {
                    "id": player_id,
                    "x": float(pos[0]),
                    "y": float(pos[1]),
                    "home": p["team_id"] == meta["home_team"]["id"],
                    "number": p["number"],
                    "detected": bool(track.detected[tf, i]),
                }
            )
        selected = next((p for p in row["player_data"] if p["player_id"] == pid), None)
        measurement = (
            shoulder_measurement(selected) if selected else {"reason": "no_pose"}
        )
        heading = (
            measurement.get("heading") if gate(measurement, cfg) == "valid" else None
        )
        joints = None
        if selected and selected.get("joints"):
            raw = selected["joints"]
            origin = np.array(raw["midHip"]["xyz"], float)
            joints = {
                name: [round(float(x), 5) for x in np.array(value["xyz"]) - origin]
                for name, value in raw.items()
            }
        ball = track.ball[tf]
        xy = track.xy[tf, track.lookup[pid]]
        residual = None
        if selected and selected["x"] is not None and np.isfinite(xy).all():
            residual = math.hypot(selected["x"] - xy[0], selected["y"] - xy[1])
        valid = heading is not None and residual is not None and residual <= 2
        clip.append(
            {
                "pose_frame": f,
                "tracking_frame": tf,
                "t": round((f - centre) / 25, 3),
                "clock": row["timestamp"],
                "players": players,
                "ball": ball.astype(float).tolist()
                if np.isfinite(ball).all()
                else None,
                "joints": joints,
                "heading": heading if valid else None,
                "pose_status": "valid raw shoulders"
                if valid
                else gate(measurement, cfg)
                if heading is None
                else "native tracking mismatch",
            }
        )
    return {
        "match_id": match,
        "fixture": meta["home_team"]["short_name"]
        + " v "
        + meta["away_team"]["short_name"],
        "player_id": pid,
        "player_name": event.player_name,
        "event_id": event.event_id,
        "period": int(event.period),
        "reception_frame_10hz": int(event.frame),
        "duration": float(event.duration),
        "target": int(event.target),
        "end_type": event.end_type,
        "pass_outcome": event.pass_outcome,
        "attack_sign": int(event.attack_sign),
        "pitch_length": meta["pitch_length"],
        "pitch_width": meta["pitch_width"],
        "frames": clip,
    }


def run(root, cfg):
    root = Path(root)
    out = root / "outputs"
    rows = pd.read_csv(out / "receptions_orientation.csv")
    results = json.loads((out / "results.json").read_text())
    coverage = json.loads((out / "coverage.json").read_text())
    clips = [
        export_clip(root, m, rows[rows.match_id.eq(m)], cfg) for m in cfg["matches"]
    ]
    clips = [c for c in clips if c]
    payload = {
        "results": results,
        "coverage": {
            m: {
                k: v[k]
                for k in [
                    "baseline_n",
                    "orientation_n",
                    "orientation_reception_coverage",
                    "selection",
                ]
            }
            for m, v in coverage.items()
        },
        "clips": clips,
        "skeleton": SKELETON,
        "categories": pd.read_csv(out / "orientation_categories.csv").to_dict(
            "records"
        ),
        "sensitivity": json.loads((out / "sensitivity_results.json").read_text()),
    }
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"))
    (out / "viewer_data.json").write_text(encoded + "\n")
    template = (Path(__file__).parent / "web/viewer.html").read_text()
    # This is artifact assembly; UI features live directly in their HTML/CSS/JS sources.
    html = template.replace(
        "<!-- DATA_PAYLOAD -->",
        '<script id="dataset" type="application/json">'
        + encoded.replace("</", "<\\/")
        + "</script>",
    )
    html = html.replace(
        "/* VIEWER_STYLE */", (Path(__file__).parent / "web/viewer.css").read_text()
    )
    html = html.replace(
        "/* VIEWER_SCRIPT */", (Path(__file__).parent / "web/viewer.js").read_text()
    )
    (out / "viewer.html").write_text(html)
    print("Wrote offline viewer with", len(clips), "real clips")
