"""Freeze configuration, evaluate, and export the complete candidate catalogue."""
from __future__ import annotations
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
from marking_handoffs.baseline import build_segments, nearest
from marking_handoffs.data import load_match, clock
from marking_handoffs.graph import real_features
from marking_handoffs.temporal import assign, candidate_events
from marking_handoffs.evaluation import operational, phase_bootstrap
from marking_handoffs.synthetic import evaluate

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, rows):
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run():
    config_path = ROOT / "configs/pilot.json"
    config = json.loads(config_path.read_text())
    validation = json.loads((ROOT / "outputs/baseline-validation.json").read_text())
    if not all(v["validation"]["all_agree"] for v in validation.values()):
        raise RuntimeError("Baseline validation must pass first")
    config_hash = hashlib.sha256(config_path.read_bytes()).hexdigest()
    (ROOT / "outputs/frozen-config.json").write_text(json.dumps(dict(sha256=config_hash, config=config), indent=2) + "\n")
    metrics, synthetic_rows = evaluate(config)
    (ROOT / "outputs/synthetic-results.json").write_text(json.dumps(metrics, indent=2) + "\n")
    write_csv(ROOT / "outputs/synthetic-trajectories.csv", synthetic_rows)
    print("Synthetic", json.dumps(metrics), flush=True)
    results, catalogue, clips, sensitivity = {}, [], [], []
    assignments_file = gzip.open(ROOT / "outputs/assignments.csv.gz", "wt")
    assignment_writer = csv.writer(assignments_file)
    assignment_writer.writerow(["match_id", "phase", "segment_id", "frame", "attacker_id", "nearest_id", "proposed_id", "plausible_defenders", "attacker_detected", "all_defenders_detected"])
    edge_file = gzip.open(ROOT / "outputs/edges.csv.gz", "wt")
    edge_writer = csv.writer(edge_file)
    edge_writer.writerow(["match_id", "phase", "frame", "attacker_id", "defender_id", "distance_m", "radial_separation_mps", "goal_margin_m", "local_line_offset_m", "score_m_equivalent", "predicted_distance_m", "plausible", "both_detected"])
    for split in ["development", "heldout"]:
        mid = config[f"{split}_match"]
        data = load_match(ROOT / "data/raw", mid)
        segments = build_segments(data, config)
        features = [real_features(data, s, config) for s in segments]
        baseline = [nearest(s["distance"]) for s in segments]
        proposed = [assign(f, config) for f in features]
        results[split] = dict(match_id=mid, nearest=operational(segments, baseline, features),
                              proposed=operational(segments, proposed, features))
        jointly_assigned = sum(int((p >= 0).sum()) for p in proposed)
        results[split]["disagreement_when_proposed_assigned"] = sum(int(((p != b) & (p >= 0)).sum()) for p, b in zip(proposed, baseline)) / max(1, jointly_assigned)
        # Per frame, expose concentration of independently selected targets.
        loads = {}
        for s, labels in zip(segments, proposed):
            for k in np.flatnonzero(labels >= 0):
                key = int(s["frames"][k]), int(s["defenders"][labels[k]])
                loads[key] = loads.get(key, 0) + 1
        start_count = len(catalogue)
        for segment_id, (s, f, b, p) in enumerate(zip(segments, features, baseline, proposed)):
            ai, di, fr = s["attacker"], s["defenders"], s["frames"]
            for k, frame in enumerate(fr):
                assignment_writer.writerow([mid, s["phase"], segment_id, int(frame), int(data["ids"][ai]),
                                            int(data["ids"][di[b[k]]]), int(data["ids"][di[p[k]]]) if p[k] >= 0 else "",
                                            int(f["plausible"][k].sum()), int(data["detected"][frame, ai]),
                                            int(data["detected"][frame, di].all())])
            for k, j in zip(*np.where(f["edge"])):
                vals = [round(float(f[field][k, j]), 4) for field in ["distance", "radial", "goal_margin", "structure", "score", "predicted"]]
                edge_writer.writerow([mid, s["phase"], int(fr[k]), int(data["ids"][ai]), int(data["ids"][di[j]])] + vals +
                                     [int(f["plausible"][k, j]), int(data["detected"][fr[k], ai] and data["detected"][fr[k], di[j]])])
            for event in candidate_events(p, f, data["xy"][fr, ai], config):
                old, new, at = int(di[event["old"]]), int(di[event["new"]]), event["event_index"]
                frame = int(fr[at])
                players = {player["id"]: player for player in data["metadata"]["players"]}
                lo, hi = event["window_start"], event["window_end"]
                detection = data["detected"][fr[lo:hi, None], [ai, old, new]]
                event_id = f"{mid}-{s['phase']}-{int(data['ids'][ai])}-{frame}"
                entry = dict(id=event_id, split=split, match_id=mid, phase=s["phase"], segment_id=segment_id, period=s["period"],
                             frame=frame, clock=clock(frame, s["period"], data["metadata"]),
                             window_start_frame=int(fr[lo]), window_end_frame_exclusive=int(fr[hi-1])+1,
                             outgoing_last_frame=int(fr[event["outgoing_end"]-1]),
                             attacker_id=int(data["ids"][ai]), attacker=players[int(data["ids"][ai])]["short_name"],
                             outgoing_id=int(data["ids"][old]), outgoing=players[int(data["ids"][old])]["short_name"],
                             incoming_id=int(data["ids"][new]), incoming=players[int(data["ids"][new])]["short_name"],
                             category=event["category"], gap_s=event["gap_s"], longest_gap_s=event["longest_gap_s"],
                             unassigned_s=event["unassigned_s"], attacker_displacement_m=round(event["attacker_displacement_m"], 3),
                             involved_detected_fraction=round(float(detection.mean()), 4),
                             all_involved_detected=bool(detection.all()), ambiguous=event["ambiguous"],
                             alternative_margin_m=event["alternative_margin_m"],
                             shared_incoming=loads.get((frame, new), 0) > 1)
                catalogue.append(entry)
                # Replays remain within the eligible segment; playback is downsampled to 5 Hz.
                c0, c1 = max(0, at - 30), min(len(fr), at + 31)
                replay = []
                for k in range(c0, c1, 2):
                    frame_k = int(fr[k])
                    visible = np.flatnonzero(np.isfinite(data["xy"][frame_k]).all(axis=1))
                    positions = [[int(data["ids"][j]), round(float(data["xy"][frame_k, j, 0]) * s["sign"], 2),
                                  round(float(data["xy"][frame_k, j, 1]) * s["sign"], 2), int(data["teams"][j] == s["team"]),
                                  int(data["detected"][frame_k, j]), int(data["gk"][j])] for j in visible]
                    ball = [round(float(v) * s["sign"], 2) for v in data["ball"][frame_k]]
                    replay.append(dict(frame=frame_k, clock=clock(frame_k, s["period"], data["metadata"]), players=positions,
                                       ball=ball, assignment=int(data["ids"][di[p[k]]]) if p[k] >= 0 else None,
                                       nearest=int(data["ids"][di[b[k]]]), cover=int(f["plausible"][k].sum())))
                match_label = f"{data['metadata']['home_team']['short_name']} v {data['metadata']['away_team']['short_name']}"
                clips.append(dict(**entry, match=match_label, replay=replay))
        results[split]["candidate_counts"] = {kind: sum(e["category"] == kind for e in catalogue[start_count:]) for kind in ["continuous", "brief_gap", "gap"]}
        results[split]["all_involved_detected_candidates"] = sum(e["all_involved_detected"] for e in catalogue[start_count:])
        if split == "heldout":
            results[split]["phase_bootstrap"] = phase_bootstrap(segments, baseline, proposed, config["seed"], config["bootstrap_replicates"])
            variants = [("radius_4", dict(radius_m=4.0)), ("radius_8", dict(radius_m=8.0, release_radius_m=9.5, graph_radius_m=10.0, prediction_radius_m=10.0)),
                        ("confirm_3", dict(confirm_frames=3)), ("confirm_8", dict(confirm_frames=8)),
                        ("margin_0", dict(switch_margin_m=0.0)), ("margin_1_5", dict(switch_margin_m=1.5)),
                        ("no_motion", dict(motion_weight_s=0.0)), ("no_structure", dict(structure_weight=0.0)),
                        ("default", {})]
            for name, updates in variants:
                cfg = config | updates
                ff = [real_features(data, s, cfg) for s in segments]
                ll = [assign(f, cfg) for f in ff]
                ee = [event for s, f, lab in zip(segments, ff, ll) for event in candidate_events(lab, f, data["xy"][s["frames"], s["attacker"]], cfg)]
                mm = operational(segments, ll, ff)
                sensitivity.append(dict(variant=name, radius_m=cfg["radius_m"], confirm_frames=cfg["confirm_frames"],
                                         switch_margin_m=cfg["switch_margin_m"], candidates=len(ee),
                                         gap_candidates=sum(e["category"] == "gap" for e in ee),
                                         **{k: mm[k] for k in ["assigned_fraction", "identity_changes_per_attacker_minute", "short_runs_per_attacker_minute"]}))
            # Strict observability sensitivity, on a separately disclosed denominator.
            strict_segments = []
            for s in segments:
                fr, ai, di = s["frames"], s["attacker"], s["defenders"]
                mask = np.ones(len(fr), bool)
                for lag in range(4):
                    mask &= data["detected"][fr - lag, ai]
                    mask &= data["detected"][(fr - lag)[:, None], di].all(axis=1)
                indices = np.flatnonzero(mask)
                for chunk in np.split(indices, np.flatnonzero(np.diff(indices) != 1) + 1):
                    if len(chunk):
                        strict_segments.append(s | dict(frames=fr[chunk], distance=s["distance"][chunk]))
            strict_f = [real_features(data, s, config) for s in strict_segments]
            strict_b = [nearest(s["distance"]) for s in strict_segments]
            strict_p = [assign(f, config) for f in strict_f]
            strict_events = [e for s, f, lab in zip(strict_segments, strict_f, strict_p)
                             for e in candidate_events(lab, f, data["xy"][s["frames"], s["attacker"]], config)]
            results[split]["strict_observed_sensitivity"] = dict(
                definition="Attacker and all ten defenders detected at current and previous three frames; reset at every failed frame",
                nearest=operational(strict_segments, strict_b, strict_f),
                proposed=operational(strict_segments, strict_p, strict_f),
                candidate_counts={kind: sum(e["category"] == kind for e in strict_events) for kind in ["continuous", "brief_gap", "gap"]})
        print(split, json.dumps(results[split]), flush=True)
    assignments_file.close()
    edge_file.close()
    write_csv(ROOT / "outputs/candidates.csv", catalogue)
    write_csv(ROOT / "outputs/sensitivity.csv", sensitivity)
    (ROOT / "outputs/results.json").write_text(json.dumps(dict(config_sha256=config_hash, splits=results), indent=2) + "\n")
    (ROOT / "outputs/replays.json").write_text(json.dumps(clips, separators=(",", ":")) + "\n")
    print("Candidates", len(catalogue), flush=True)


if __name__ == "__main__":
    run()
