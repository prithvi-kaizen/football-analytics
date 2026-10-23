"""Publish 12 attributed analytical cases and aggregates, never raw 360 JSON."""

# ruff: noqa: E402
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd

from passlab.choices import evaluate_candidates
from passlab.data import REVISION, write_json
from passlab.viz import pitch_figure


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package():
    output, web = ROOT / "outputs", ROOT / "web"
    provenance = json.loads((output / "provenance.json").read_text())
    if provenance["selection"] != "all" or provenance["revision"] != REVISION:
        raise ValueError("Publication requires the reviewed full pinned run")
    for name, expected in provenance["output_hashes"].items():
        if digest(output / name) != expected:
            raise ValueError(f"Output integrity failure: {name}")
    passes = pd.read_csv(output / "passes.csv")
    queue = pd.read_csv(output / "review-queue.csv")
    scenes = json.loads((output / "scenes.json").read_text())
    bundles = json.loads((output / "model-bundles.json").read_text())
    summary = json.loads((output / "run-summary.json").read_text())
    if not set(queue.match_id) <= set(summary["split"]["test"]):
        raise ValueError("Review queue contains a training match")
    eligible = passes[passes.event_id.isin(queue.event_id)].sort_values(
        ["date", "match_id", "period", "seconds", "event_id"]
    )
    cases = []
    (web / "cases").mkdir(parents=True, exist_ok=True)
    logo = mpimg.imread(ROOT / "assets/statsbomb-logo.png")
    for tournament, group in eligible.groupby("tournament", sort=True):
        # First flagged event in each of the earliest six distinct held-out matches.
        chosen = group.drop_duplicates("match_id").head(6)
        if len(chosen) != 6:
            raise ValueError(f"Need six distinct held-out matches for {tournament}")
        for _, row in chosen.iterrows():
            scene = scenes[row.event_id]
            candidates = evaluate_candidates(row.to_dict(), scene, bundles["target_360"])
            case_id = f"case-{len(cases) + 1:02d}"
            targets = []
            for _, candidate in candidates.iterrows():
                path = Path("cases") / f"{case_id}-{candidate.candidate_id}.png"
                fig = pitch_figure(scene, candidate.candidate_id)
                fig.texts[-1].set_text(
                    "Attack left to right. Camera area shaded. Anonymous frame-local T labels."
                )
                fig.texts[-1].set_fontsize(8)
                ax_logo = fig.add_axes([0.83, 0.004, 0.14, 0.047])
                ax_logo.imshow(logo)
                ax_logo.axis("off")
                fig.savefig(web / path, dpi=110, metadata={"Software": "Pass Decision Lab"})
                plt.close(fig)
                targets.append(
                    {
                        "id": candidate.candidate_id,
                        "figure": path.as_posix(),
                        "proxyChosen": bool(candidate.proxy_target),
                        "flagged": bool(candidate.review_flag),
                        "probability": None if pd.isna(candidate.xpass) else round(float(candidate.xpass), 8),
                        "forwardGain": round(float(candidate.forward_gain), 3),
                        "distance": round(float(candidate.distance), 3),
                        "laneClearance": None
                        if pd.isna(candidate.lane_clearance)
                        else round(float(candidate.lane_clearance), 3),
                        "expectedGain": None
                        if pd.isna(candidate.expected_forward_gain)
                        else round(float(candidate.expected_forward_gain), 3),
                        "withholdingReasons": candidate.support_warning,
                    }
                )
            cases.append(
                {
                    "id": case_id,
                    "tournament": tournament,
                    "match": row.label,
                    "date": row.date,
                    "matchId": int(row.match_id),
                    "eventId": row.event_id,
                    "possession": int(row.possession),
                    "period": int(row.period),
                    "clock": f"{int(row.minute):02d}:{int(row.second):02d}",
                    "player": row.player,
                    "team": row.team,
                    "completed": bool(row.complete),
                    "proxyTarget": scene["target_candidate_id"],
                    "targets": targets,
                }
            )
    metrics = pd.read_csv(output / "metrics.csv")
    calibration = pd.read_csv(output / "calibration.csv")
    public = {
        "schemaVersion": 1,
        "revision": REVISION,
        "summary": {
            k: summary[k]
            for k in [
                "matches",
                "eligible_passes",
                "frames_with_defenders",
                "recipient_proxies",
                "candidate_audit",
            ]
        },
        "trainingMatches": len(summary["split"]["train"]),
        "testMatches": len(summary["split"]["test"]),
        "caseSelection": "First flagged event in each of the earliest six distinct held-out matches per tournament; 12 cases total. Not representative or selected by predicted gain.",
        "cases": cases,
        "metrics": json.loads(metrics.to_json(orient="records")),
        "calibration": json.loads(calibration.to_json(orient="records")),
    }
    write_json(web / "analysis.json", public)
    for name in ["calibration.png", "calibration.svg", "metrics.csv", "calibration.csv"]:
        shutil.copyfile(output / name, web / name)
    findings = (
        (output / "findings.md")
        .read_text()
        .replace("../docs/source/LICENSE.pdf", "LICENSE-statsbomb.pdf")
        .replace("../assets/statsbomb-logo.png", "statsbomb-logo.png")
    )
    (web / "findings.md").write_text(findings)
    shutil.copyfile(ROOT / "assets/statsbomb-logo.png", web / "statsbomb-logo.png")
    shutil.copyfile(ROOT / "docs/source/LICENSE.pdf", web / "LICENSE-statsbomb.pdf")
    assets = [p for p in sorted(web.rglob("*")) if p.is_file() and p.name != "bundle.json"]
    write_json(
        web / "bundle.json",
        {
            "schemaVersion": 1,
            "revision": REVISION,
            "caseCount": len(cases),
            "analysisOutputHashes": provenance["output_hashes"],
            "assets": {p.relative_to(web).as_posix(): digest(p) for p in assets},
        },
    )
    print(
        f"Packaged {len(cases)} cases, {sum(len(c['targets']) for c in cases)} attributed figures; no raw snapshots."
    )


if __name__ == "__main__":
    package()
