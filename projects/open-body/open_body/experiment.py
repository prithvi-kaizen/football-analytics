"""Matched-sample ablation with fixed, match-separated evaluation."""

from pathlib import Path
from collections import Counter
import hashlib
import json
import numpy as np
import pandas as pd
from .data import Tracking, load_metadata
from .orientation import extract_match, make_features, gate
from .models import compare


def run(root, cfg):
    root = Path(root)
    out = root / "outputs"
    marker = json.loads((out / "BASELINE_VALIDATED.json").read_text())
    assert (
        marker["sha256"]
        == hashlib.sha256((out / "receptions_baseline.csv").read_bytes()).hexdigest()
    ), "Rerun baseline"
    assert (
        marker["config_sha256"]
        == hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
    ), "Rerun baseline after config change"
    data = pd.read_csv(out / "receptions_baseline.csv")
    parts = []
    audit = {}
    windows_by_match = {}
    manifest = json.loads((root / "docs/source/MANIFEST.json").read_text())
    for m in cfg["matches"]:
        subset = data[data.match_id.eq(m)].copy()
        cache = out / f"cache/{m}"
        archive = root / f"data/raw/{m}.jsonl.zip"
        expected = manifest["files"][f"raw/{m}.jsonl.zip"]
        assert archive.stat().st_size == expected["size_bytes"], "Incomplete archive"
        digest = hashlib.file_digest(archive.open("rb"), "sha256").hexdigest()
        assert digest == expected["sha256"], "Pose checksum failure"
        track = Tracking(
            root / f"data/raw/{m}_tracking_extrapolated.jsonl",
            load_metadata(root / "data/raw", m),
        )
        key = {
            "pose_sha256": digest,
            "baseline_sha256": marker["sha256"],
            "orientation_code_sha256": hashlib.sha256(
                (Path(__file__).parent / "orientation.py").read_bytes()
            ).hexdigest(),
            "config_sha256": marker["config_sha256"],
        }
        if (cache / "key.json").exists() and json.loads(
            (cache / "key.json").read_text()
        ) == key:
            windows = json.loads((cache / "shoulder_windows.json").read_text())
            pa = json.loads((cache / "pose_audit.json").read_text())
        else:
            windows, pa = extract_match(archive, subset, track, cfg, cache)
            (cache / "key.json").write_text(json.dumps(key, indent=2) + "\n")
        windows_by_match[m] = windows
        features, reasons = make_features(subset, windows, cfg)
        for idx, r in features.iterrows():
            f = int(r.frame)
            i = track.lookup[int(r.player_id)]
            movement = (
                track.xy[f + 5, i] - track.xy[f, i]
                if f + 5 < len(track.period) and track.period[f + 5] == r.period
                else np.array([np.nan, np.nan])
            )
            norm = float(np.linalg.norm(movement))
            features.loc[idx, "post_movement_alignment_descriptive"] = (
                float(np.dot(movement, [np.cos(r.heading), np.sin(r.heading)]) / norm)
                if norm > 0.25
                else np.nan
            )
        parts.append(features)
        valid = set(features.event_id)
        selection = []
        for selected in [True, False]:
            g = subset[subset.event_id.isin(valid).eq(selected)]
            selection.append(
                {
                    "pose_eligible": selected,
                    "n": len(g),
                    "prevalence": float(g.target.mean()) if len(g) else None,
                    "mean_x_m": float(g.x.mean()) if len(g) else None,
                    "mean_nearest_opponent_m": float(g.nearest_opponent_m.mean())
                    if len(g)
                    else None,
                    "receiver_detected_fraction": float(g.receiver_detected.mean())
                    if len(g)
                    else None,
                }
            )
        audit[str(m)] = {
            "pose": pa,
            "reception_feature_gates": reasons,
            "reception_window_sample_gates": dict(
                Counter(gate(s, cfg) for window in windows.values() for s in window)
            ),
            "baseline_n": len(subset),
            "orientation_n": len(features),
            "orientation_reception_coverage": len(features) / len(subset),
            "selection": selection,
            "feature_coverage_by_role": subset.assign(
                pose_eligible=subset.event_id.isin(valid)
            )
            .groupby("position_group")
            .pose_eligible.agg(["count", "sum", "mean"])
            .reset_index()
            .to_dict("records"),
        }
    features = pd.concat(parts, ignore_index=True)
    features.to_csv(out / "receptions_orientation.csv", index=False)
    (out / "coverage.json").write_text(json.dumps(audit, indent=2) + "\n")
    results = []
    predictions = []
    directions = [
        (cfg["train_match"], cfg["test_match"]),
        (cfg["test_match"], cfg["train_match"]),
    ]
    for tr, te in directions:
        r, p = compare(
            features[features.match_id.eq(tr)], features[features.match_id.eq(te)], cfg
        )
        results.append(r)
        predictions.append(p)
    pd.concat(predictions).to_csv(out / "heldout_predictions.csv", index=False)
    cases = [
        (f"error_{value:g}cm", {"shoulder_error_cm": value}, 0, 0)
        for value in cfg["sensitivity_error_cm"]
    ]
    cases += [
        (
            "no_smoothing" if value == 0 else f"smooth_{value * 1000:g}ms",
            {"smooth_seconds": value},
            0,
            0,
        )
        for value in cfg["sensitivity_smooth_seconds"]
    ]
    cases += [
        (f"cutoff_{abs(value) * 1000:g}ms_earlier", {}, value, 0)
        for value in cfg["sensitivity_timing_seconds"]
    ]
    cases += [
        (f"noise_{value:g}deg", {}, 0, value)
        for value in cfg["sensitivity_angle_noise_degrees"]
    ]
    sensitivity = []
    for name, override, shift, noise in cases:
        c = {**cfg, **override}
        fs = []
        for m in cfg["matches"]:
            f, _ = make_features(
                data[data.match_id.eq(m)],
                windows_by_match[m],
                {**c, "seed": c["seed"] + m},
                shift,
                noise,
            )
            fs.append(f)
        frame = pd.concat(fs, ignore_index=True)
        for tr, te in directions:
            train = frame[frame.match_id.eq(tr)]
            test = frame[frame.match_id.eq(te)]
            if len(train) < 30 or len(test) < 30 or train.target.nunique() < 2:
                sensitivity.append(
                    {
                        "case": name,
                        "train_match": tr,
                        "test_match": te,
                        "status": "insufficient observations",
                    }
                )
                continue
            r, _ = compare(train, test, c)
            r.update(
                case=name,
                overrides=override,
                feature_cutoff_shift_s=shift,
                noise_degrees=noise,
            )
            sensitivity.append(r)
    for tr, te in directions:
        train = features[
            features.match_id.eq(tr) & features.position_group.eq("Midfield")
        ]
        test = features[
            features.match_id.eq(te) & features.position_group.eq("Midfield")
        ]
        if len(train) >= 30 and len(test) >= 30 and train.target.nunique() == 2:
            r, _ = compare(train, test, cfg)
            r["case"] = "midfield_only"
            sensitivity.append(r)
        else:
            sensitivity.append(
                {
                    "case": "midfield_only",
                    "train_match": tr,
                    "test_match": te,
                    "status": "insufficient observations",
                }
            )
    (out / "sensitivity_results.json").write_text(
        json.dumps(sensitivity, indent=2) + "\n"
    )
    categories = []
    for (m, cat), g in features.groupby(["match_id", "orientation_category"]):
        n = len(g)
        p = float(g.target.mean())
        z = 1.959963984540054
        den = 1 + z * z / n
        centre = (p + z * z / (2 * n)) / den
        half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
        categories.append(
            {
                "match_id": int(m),
                "category": cat,
                "n": n,
                "fast_progressive_fraction": p,
                "wilson_95_low": float(centre - half),
                "wilson_95_high": float(centre + half),
                "median_release_duration_s": float(g.duration.median()),
                "retained_proxy_n": int(g.retained_proxy.notna().sum()),
                "successful_pass_or_foul_fraction_among_known": float(
                    g.retained_proxy.mean()
                ),
                "epv_delta_for_n": int(g.epv_delta_for.notna().sum()),
                "mean_vendor_epv_delta_for": float(g.epv_delta_for.mean()),
                "mean_next_500ms_movement_alignment_descriptive": float(
                    g.post_movement_alignment_descriptive.mean()
                ),
            }
        )
    pd.DataFrame(categories).to_csv(out / "orientation_categories.csv", index=False)
    criterion = (
        results[0]["delta_log_loss"] < 0
        and results[1]["delta_log_loss"] < 0
        and results[0]["delta_log_loss_95ci"]["high"] < 0
    )
    summary = {
        "question": cfg["primary_outcome"],
        "primary": results[0],
        "reverse_diagnostic": results[1],
        "pilot_criterion_met": bool(criterion),
        "two_match_generalisation_limit": True,
        "baseline_features": cfg["baseline_features"],
        "orientation_features": cfg["orientation_features"],
        "configuration": cfg,
    }
    (out / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return summary
