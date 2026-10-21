"""Reproducible ingestion -> cleaning -> detection -> validation -> publication assets."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform

import numpy as np
import pandas as pd

from .analysis import RunConfig, compare_provider, detect_runs
from .data import annotate_context, fetch_match, parse_tracking, sha256, smooth_tracking


def code_fingerprint() -> str:
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def runtime_versions() -> dict:
    packages = ["numpy", "pandas", "scipy", "pyarrow", "matplotlib", "mplsoccer", "plotly", "streamlit"]
    return {"python": platform.python_version(), "platform": platform.platform(),
            "packages": {package: version(package) for package in packages}}


def analyze(bundle: dict, output: Path, config: RunConfig = RunConfig()) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    paths = {key: Path(value) for key, value in bundle["paths"].items()}
    metadata = json.loads(paths["metadata"].read_text())
    if metadata["id"] != bundle["match_id"]:
        raise ValueError("Metadata does not match requested match")
    # The clean cache includes source and implementation hashes, not just filenames.
    fingerprint = code_fingerprint()
    runtime = runtime_versions()
    key = hashlib.sha256(json.dumps(dict(code=fingerprint, inputs={k: sha256(v) for k, v in paths.items()},
                                        window=config.smoothing_window, max_speed=config.max_speed_mps,
                                        runtime=runtime),
                                    sort_keys=True).encode()).hexdigest()
    cache = paths["tracking"].parent / "processed" / key
    cache.mkdir(parents=True, exist_ok=True)
    events, phases = pd.read_csv(paths["events"]), pd.read_csv(paths["phases"])
    clean_file, audit_file = cache / "tracking.parquet", cache / "audit.json"
    if clean_file.exists() and audit_file.exists():
        saved = json.loads(audit_file.read_text())
        if saved["clean_sha256"] == sha256(clean_file):
            clean, audit = pd.read_parquet(clean_file), saved["audit"]
        else:
            clean_file.unlink()
    if not clean_file.exists() or not audit_file.exists():
        tracking, audit = parse_tracking(paths["tracking"], metadata)
        tracking = annotate_context(tracking, phases, events, metadata)
        clean = smooth_tracking(tracking, config.smoothing_window, config.max_speed_mps)
        audit.update(raw_jump_rows=int(clean.raw_jump.sum()),
                     smoothed_missing_rows=int(clean.sx.isna().sum()),
                     in_play_player_rows=int(clean.phase_team.notna().sum()),
                     first_frame=int(clean.frame.min()), last_frame=int(clean.frame.max()),
                     periods=sorted(map(int, clean.period.unique())),
                     detected_fraction=float(clean.detected.mean()))
        clean.to_parquet(clean_file, index=False)
        audit_file.write_text(json.dumps(dict(audit=audit, clean_sha256=sha256(clean_file)), indent=2) + "\n")
    runs = detect_runs(clean, metadata, config)
    validation = compare_provider(runs, events, clean)
    sensitivity = []
    for speed in [4.5, 5., 5.5]:
        candidate = runs if speed == config.speed_mps else detect_runs(clean, metadata, replace(config, speed_mps=speed))
        sensitivity.append(dict(speed_mps=speed, min_distance_m=config.min_distance_m,
                                runs=len(candidate), median_distance_m=float(candidate.distance_m.median()) if len(candidate) else None))
    manifest = dict(**bundle, config=asdict(config), code_sha256=fingerprint, runtime=runtime, clean_cache_key=key,
                    clean_path=str(clean_file.resolve()), audit=audit, validation=validation,
                    sensitivity=sensitivity, metadata=metadata,
                    run_count=len(runs), metric_valid_count=int(runs.free_area_delta_m2.notna().sum()))
    runs.to_csv(output / "runs.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(output / "sensitivity.csv", index=False)
    # Summary is portable; machine-local paths are isolated in the runtime manifest.
    manifest["outputs"] = dict(runs_sha256=sha256(output / "runs.csv"),
                               sensitivity_sha256=sha256(output / "sensitivity.csv"))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    from .report import write_report
    write_report(runs, clean, manifest, output)
    return manifest


def run_project(project: Path, match_id: int, seconds: int | None = 300,
                config: RunConfig = RunConfig()) -> dict:
    bundle = fetch_match(project / "data" / "raw", match_id, seconds)
    scope = "full" if seconds is None else f"sample-{seconds}s"
    return analyze(bundle, project / "outputs" / f"{match_id}-{scope}", config)
