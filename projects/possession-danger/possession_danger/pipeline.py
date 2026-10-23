from __future__ import annotations

from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform
import tempfile

import pandas as pd

from .analysis import barcelona_comparison, classify, score_states, split_matches, team_matches, team_summary
from .data import Cache, REVISION, digest, write_json
from .events import action_rows, parse_events, possessions
from .xt import XT


def run(cache: Cache, matches: list[dict], output: Path, sample: bool = True):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Failed builds leave the previous verified output available.
    with tempfile.TemporaryDirectory(prefix=".possession-build-", dir=output.parent) as staging:
        built = Path(staging)
        summary = _run(cache, matches, built, sample)
        output.mkdir(parents=True, exist_ok=True)
        for path in sorted(built.iterdir(), key=lambda p: (p.name == "manifest.json", p.name)):
            path.replace(output / path.name)
    print(f"Published validated analysis to {output.resolve()}", flush=True)
    return summary


def _run(cache: Cache, matches: list[dict], output: Path, sample: bool):
    output.mkdir(parents=True, exist_ok=True)
    splits = split_matches(matches)
    all_events, all_possessions = [], []
    sources = []
    for i, match in enumerate(matches, 1):
        relative = f"data/events/{match['match_id']}.json"
        raw = cache.get(relative)
        events = parse_events(raw, match)
        seq, events = possessions(events)
        for frame in (events, seq):
            frame["date"] = match["match_date"]
            frame["competition"] = match["competition"]["competition_name"]
            frame["season"] = match["season"]["season_name"]
            frame["split"] = splits[match["match_id"]]
        all_events.append(events)
        all_possessions.append(seq)
        sources.append(cache.provenance(relative))
        if i % 20 == 0 or i == len(matches):
            print(f"Validated and segmented {i}/{len(matches)} matches", flush=True)
    events = pd.concat(all_events, ignore_index=True)
    seq = pd.concat(all_possessions, ignore_index=True)
    actions = action_rows(events)
    train, test = actions.loc[actions.split.eq("train")], actions.loc[actions.split.eq("test")]
    model = XT().fit(train)
    rated = model.rate(actions)
    xt_totals = rated.groupby("sequence_key").agg(positive_xt=("positive_xt", "sum"), net_xt=("xt_delta", "sum"), turnover_xt=("turnover_xt", "sum"))
    seq = seq.merge(xt_totals, on="sequence_key", how="left", validate="one_to_one")
    seq[["positive_xt", "net_xt", "turnover_xt"]] = seq[["positive_xt", "net_xt", "turnover_xt"]].fillna(0)
    seq["style"] = classify(seq)
    totals = team_matches(seq)
    states = score_states(events, rated)
    for name, frame in [("events", events), ("possessions", seq), ("actions", rated), ("team_matches", totals), ("score_states", states)]:
        frame.to_csv(output / f"{name}.csv", index=False)
    test_totals = totals.loc[totals.split.eq("test")]
    summary = {"sample": sample, "matches": len(matches), "events": len(events), "possessions": len(seq),
               "train_matches": sum(v == "train" for v in splits.values()),
               "test_matches": sum(v == "test" for v in splits.values()),
               "coverage": [{"competition": name, "matches": int(group.match_id.nunique()), "teams": int(group.team_id.nunique())}
                            for name, group in totals.groupby("competition")],
               "model": {"grid": [model.nx, model.ny], "iterations": model.iterations, "residual": model.residual,
                         "training_actions": len(train), "validation": model.evaluate(test)},
               "barcelona_heldout": barcelona_comparison(test_totals),
               "heldout_teams": json.loads(team_summary(test_totals).to_json(orient="records")),
               "cleaning": {"tiny_negative_duration_repairs": int(events.duration_repaired.sum()),
                            "control_switches_within_provider_chain": int(events.control_switch.sum()),
                            "controlled_events_outside_provider_starter": int((events.type.isin(["Pass", "Carry", "Shot", "Dribble", "Miscontrol", "Dispossessed", "Shield"]) & events.team_id.ne(events.provider_owner_id)).sum()),
                            "rule": "Durations in [-0.1, 0) seconds set to zero; raw duration retained. Larger negatives fail.",
                            "records": json.loads(events.loc[events.duration_repaired, ["match_id", "event_id", "index", "type", "raw_duration"]].to_json(orient="records"))},
               "checks": {"score_reconciliations": len(matches), "unique_event_ids": bool(events.event_id.is_unique),
                          "unique_sequences": bool(seq.sequence_key.is_unique),
                          "train_test_disjoint": not bool(set(train.match_id) & set(test.match_id)),
                          "max_possession_share_error": float((totals.groupby("match_id").possession_pct.sum() - 100).abs().max()),
                          "active_le_elapsed": bool((seq.active_seconds <= seq.elapsed_seconds + 1e-6).all()),
                          "pass_count_reconciles": int(seq.passes.sum()) == int(events.type.eq("Pass").sum()),
                          "shot_count_reconciles": int(seq.shots.sum()) == int(events.type.eq("Shot").sum()),
                          "shot_xg_reconciles": bool(abs(seq.xg.sum() - events.xg.sum()) < 1e-8)}}
    if not all(summary["checks"][key] for key in ["unique_event_ids", "unique_sequences", "train_test_disjoint", "active_le_elapsed", "pass_count_reconciles", "shot_count_reconciles", "shot_xg_reconciles"]):
        raise ValueError(f"Pipeline invariant failed: {summary['checks']}")
    write_json(output / "summary.json", summary)
    write_json(output / "xt_model.json", model.to_dict())
    catalog_sources = [cache.provenance("data/competitions.json")]
    for comp, season in sorted({(m["competition"]["competition_id"], m["season"]["season_id"]) for m in matches}):
        catalog_sources.append(cache.provenance(f"data/matches/{comp}/{season}.json"))
    package_root = Path(__file__).parent
    manifest = {"revision": REVISION, "generated_at": datetime.now(timezone.utc).isoformat(),
                "python": platform.python_version(), "dependencies": {name: version(name) for name in ["numpy", "pandas", "requests", "streamlit", "plotly", "mplsoccer", "matplotlib"]},
                "sample": sample, "split": {str(k): v for k, v in splits.items()},
                "sources": catalog_sources + sources,
                "code_sha256": {str(p.relative_to(package_root.parent)): digest(p) for p in sorted(package_root.glob("*.py"))},
                "run_configuration": {"test_fraction": 0.2, "grid": [12, 8], "sample": sample,
                                      "match_ids": [int(m["match_id"]) for m in matches]}}
    for name in ["app.py", "pyproject.toml", "requirements-lock.txt", ".streamlit/config.toml"]:
        path = package_root.parent / name
        if path.exists():
            manifest["code_sha256"][name] = digest(path)
    from .report import write_report
    write_report(output, totals, seq, summary)
    manifest["output_sha256"] = {p.name: digest(p) for p in output.iterdir() if p.is_file() and p.name != "manifest.json"}
    write_json(output / "manifest.json", manifest)
    print(f"Wrote {output.resolve()}\n{json.dumps(summary['checks'], indent=2)}", flush=True)
    return summary
