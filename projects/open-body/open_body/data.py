"""Streaming input validation and compact 10 Hz tracking context."""

from pathlib import Path
from collections import Counter
import gzip
import json
import zipfile
import numpy as np
import pandas as pd

try:
    import orjson

    loads = orjson.loads
except ImportError:
    loads = json.loads


def iter_frames(path):
    path = Path(path)
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as z:
            names = [
                n
                for n in z.namelist()
                if n.endswith(".jsonl")
                and not n.startswith("__MACOSX/")
                and not Path(n).name.startswith("._")
            ]
            if len(names) != 1:
                raise ValueError("Expected exactly one JSONL ZIP member")
            with z.open(names[0]) as f:
                for line in f:
                    if line.strip():
                        yield loads(line)
    else:
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rb") as f:
            for line in f:
                if line.strip():
                    yield loads(line)


def clock_seconds(stamp):
    h, m, s = stamp.split(":")
    return 3600 * int(h) + 60 * int(m) + float(s)


class Tracking:
    def __init__(self, path, metadata):
        self.metadata = metadata
        self.ids = [p["id"] for p in metadata["players"]]
        if len(set(self.ids)) != len(self.ids):
            raise ValueError("Duplicate roster ID")
        self.lookup = {p: i for i, p in enumerate(self.ids)}
        self.teams = np.array([p["team_id"] for p in metadata["players"]])
        n = max(p["end_frame"] for p in metadata["match_periods"]) + 10
        self.xy = np.full((n, len(self.ids), 2), np.nan, dtype=np.float32)
        self.detected = np.zeros((n, len(self.ids)), bool)
        self.ball = np.full((n, 2), np.nan, dtype=np.float32)
        self.period = np.zeros(n, dtype=np.int8)
        self.clock = np.full(n, np.nan, dtype=float)
        audit = Counter()
        previous = -1
        for row in iter_frames(path):
            f = row["frame"]
            period = row["period"]
            if f <= previous:
                raise ValueError("Tracking frames must be strictly increasing")
            if period is None:
                previous = f
                audit["outside_period_frames"] += 1
                continue
            if not 0 <= f < n or period not in [1, 2]:
                raise ValueError("Invalid tracking frame/period")
            previous = f
            self.period[f] = period
            self.clock[f] = clock_seconds(row["timestamp"])
            players = row["player_data"]
            pids = [p["player_id"] for p in players]
            if len(set(pids)) != len(pids):
                raise ValueError("Duplicate player within tracking frame")
            for p in players:
                if p["player_id"] not in self.lookup:
                    raise ValueError("Unknown tracking player")
                i = self.lookup[p["player_id"]]
                if p["x"] is not None and p["y"] is not None:
                    self.xy[f, i] = p["x"], p["y"]
                self.detected[f, i] = p["is_detected"]
            b = row["ball_data"]
            if b and b.get("x") is not None and b.get("y") is not None:
                self.ball[f] = b["x"], b["y"]
            audit["frames"] += 1
            audit[f"period_{period}_frames"] += 1
        self.audit = dict(audit)

    def context(self, frame, player_id, period, team_id):
        if frame < 5 or frame >= len(self.period) or self.period[frame] != period:
            return None
        i = self.lookup[player_id]
        pos = self.xy[frame, i]
        if not np.isfinite(pos).all():
            return None
        opp = self.xy[frame, self.teams != team_id]
        dist = np.linalg.norm(opp - pos, axis=1)
        dist = dist[np.isfinite(dist)]
        if len(dist) < 8:
            return None
        old = self.xy[frame - 5, i]
        if self.period[frame - 5] != period or not np.isfinite(old).all():
            return None
        speed = np.linalg.norm(pos - old) / 0.5
        if speed > 12:
            return None
        return {
            "pos": pos,
            "nearest_opponent_m": float(dist.min()),
            "opponents_within_5m": int((dist < 5).sum()),
            "pre_speed_mps": float(speed),
            "nearest_opponent_vector": opp[
                np.nanargmin(np.linalg.norm(opp - pos, axis=1))
            ]
            - pos,
            "ball_vector": self.ball[max(0, frame - 2)] - pos,
            "receiver_detected": bool(self.detected[frame, i]),
        }


def load_metadata(root, match):
    return json.loads((Path(root) / f"{match}_match.json").read_text())


def reception_events(root, match, cfg):
    """No pose-based selection here; unknown labels are never mapped to failures."""
    table = pd.read_csv(
        Path(root) / f"{match}_dynamic_events.csv",
        keep_default_na=False,
        low_memory=False,
    )
    if table.event_id.duplicated().any():
        raise ValueError("Duplicate event ID within match")
    meta = load_metadata(root, match)
    players = {p["id"]: p for p in meta["players"]}
    pp = table[
        table.event_type.eq("player_possession") & table.start_type.eq("pass_reception")
    ].copy()
    audit = Counter({"all_events": len(table), "pass_receptions": len(pp)})
    result = []
    for r in pp.to_dict("records"):

        def reject(k):
            audit[k] += 1

        if r["is_player_possession_start_matched"] not in [True, "True"]:
            reject("unmatched_start")
            continue
        pid = int(r["player_id"])
        role = players[pid]["player_role"]["position_group"]
        if players[pid]["player_role"]["acronym"] == "GK":
            reject("goalkeeper")
            continue
        end = r["end_type"]
        success = r["pass_outcome"] == "successful"
        if end == "unknown" or (
            end == "pass"
            and r["pass_outcome"] not in ["successful", "unsuccessful", "offside"]
        ):
            reject("unknown_outcome")
            continue
        if end == "pass" and success and r["player_targeted_x_reception"] == "":
            reject("missing_success_destination")
            continue
        start, endf = int(r["frame_start"]), int(r["frame_end"])
        duration = float(r["duration"])
        home_sign = (
            1 if meta["home_team_side"][int(r["period"]) - 1] == "left_to_right" else -1
        )
        expected_sign = (
            home_sign if int(r["team_id"]) == meta["home_team"]["id"] else -home_sign
        )
        if expected_sign != (1 if r["attacking_side"] == "left_to_right" else -1):
            raise ValueError("Event and metadata attacking direction disagree")
        if abs(duration - (endf - start) / 10) > 0.11:
            raise ValueError("Duration/frame mismatch")
        if duration < 0:
            raise ValueError("Negative duration")
        # Event coordinates use a 105 x 68 reference pitch, independently checked against tracking.
        scale_x = float(meta["pitch_length"]) / 105
        gain = (
            (float(r["player_targeted_x_reception"]) - float(r["x_start"])) * scale_x
            if end == "pass" and success
            else np.nan
        )
        label = int(
            end == "pass"
            and success
            and duration <= cfg["release_seconds"]
            and gain >= cfg["progress_metres"]
        )
        epv = (
            float(r["possession_epv_for_end"]) - float(r["possession_epv_for_start"])
            if r["possession_epv_for_end"] != "" and r["possession_epv_for_start"] != ""
            else np.nan
        )
        result.append(
            {
                "match_id": match,
                "event_id": r["event_id"],
                "frame": start,
                "period": int(r["period"]),
                "player_id": pid,
                "player_name": r["player_name"],
                "team_id": int(r["team_id"]),
                "position_group": role,
                "phase_index": int(r["phase_index"]),
                "attack_sign": 1 if r["attacking_side"] == "left_to_right" else -1,
                "event_x": float(r["x_start"]) * scale_x,
                "event_y": float(r["y_start"]) * float(meta["pitch_width"]) / 68,
                "duration": duration,
                "end_type": end,
                "pass_outcome": r["pass_outcome"],
                "gain_m": gain,
                "target": label,
                "retained_proxy": (
                    1
                    if (end == "pass" and success) or end == "foul_suffered"
                    else (
                        0
                        if end == "possession_loss" or (end == "pass" and not success)
                        else np.nan
                    )
                ),
                "epv_delta_for": epv,
                "vendor_pressure": r["overall_pressure_start_id"],
            }
        )
    audit["label_eligible"] = len(result)
    return pd.DataFrame(result), dict(audit)


def build_receptions(raw, match, cfg):
    meta = load_metadata(raw, match)
    track = Tracking(Path(raw) / f"{match}_tracking_extrapolated.jsonl", meta)
    events, audit = reception_events(raw, match, cfg)
    rows = []
    residuals = []
    for r in events.to_dict("records"):
        ctx = track.context(r["frame"], r["player_id"], r["period"], r["team_id"])
        if ctx is None:
            continue
        pos = ctx["pos"]
        sgn = r["attack_sign"]
        expected = np.array([r["event_x"], r["event_y"]])
        residual = float(np.linalg.norm(pos * sgn - expected))
        residuals.append(residual)
        if residual > 3:
            continue
        r.update(
            {
                k: ctx[k]
                for k in [
                    "nearest_opponent_m",
                    "opponents_within_5m",
                    "pre_speed_mps",
                    "receiver_detected",
                ]
            }
        )
        r.update(
            x=float(pos[0] * sgn),
            abs_y=float(abs(pos[1])),
            tracking_event_residual_m=residual,
            ball_dx=float(ctx["ball_vector"][0]),
            ball_dy=float(ctx["ball_vector"][1]),
            opp_dx=float(ctx["nearest_opponent_vector"][0]),
            opp_dy=float(ctx["nearest_opponent_vector"][1]),
        )
        if not np.isfinite([r[k] for k in cfg["baseline_features"]]).all():
            continue
        rows.append(r)
    audit.update(
        tracking=track.audit,
        baseline_eligible=len(rows),
        join_residual_before_gate_quantiles_m=np.quantile(
            residuals, [0, 0.5, 0.9, 0.99, 1]
        ).tolist()
        if residuals
        else [],
        residual_gate_m=3,
    )
    return pd.DataFrame(rows), audit, track
