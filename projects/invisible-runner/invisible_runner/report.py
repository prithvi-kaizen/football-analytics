"""Publication charts and factual summaries from actual pipeline outputs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mplsoccer import Pitch
import pandas as pd

from .analysis import RunConfig, receiving_patch

INK = "#172b29"
ATTACK = "#12675c"
DEFEND = "#934323"
PAPER = "#faf8f1"


def pitch_snapshot(tracking: pd.DataFrame, run: pd.Series, metadata: dict, frame: int):
    pitch = Pitch(pitch_type="skillcorner", pitch_length=metadata["pitch_length"],
                  pitch_width=metadata["pitch_width"], pitch_color=PAPER, line_color="#77847d",
                  linewidth=.8)
    fig, ax = pitch.draw(figsize=(10, 6.5))
    fig.set_facecolor(PAPER)
    shot = tracking[tracking.frame.eq(frame)].dropna(subset=["sx", "sy"])
    for team_id, group in shot.groupby("team_id"):
        color = ATTACK if team_id == run.team_id else DEFEND
        for detected, visible in group.groupby("detected"):
            pitch.scatter(visible.sx, visible.sy, ax=ax, s=100,
                          facecolor=color if detected else PAPER, edgecolor=color, linewidth=1.5, zorder=4)
    path = tracking[tracking.player_id.eq(run.player_id) & tracking.frame.between(run.start_frame, run.end_frame)]
    pitch.plot(path.sx, path.sy, color=INK, lw=2, ax=ax, zorder=3)
    pitch.arrows([run.start_x], [run.start_y], [run.end_x], [run.end_y], color=INK, ax=ax, width=1.5)
    runner = shot[shot.player_id.eq(run.player_id)]
    pitch.scatter(runner.sx, runner.sy, marker="*", s=350, color=INK, ax=ax, zorder=5)
    ball = shot.iloc[0] if len(shot) else None
    if ball is not None and pd.notna(ball.ball_x) and pd.notna(ball.ball_y):
        pitch.scatter([ball.ball_x], [ball.ball_y], s=45, c="black", ax=ax, zorder=6)
    ax.set_title(f"{run.player_name} | frame {frame}\nFilled: detected; hollow: extrapolated", color=INK, loc="left", fontsize=12)
    return fig


def write_report(runs: pd.DataFrame, tracking: pd.DataFrame, manifest: dict, output: Path):
    valid = runs.dropna(subset=["free_area_delta_m2"])
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, ax = plt.subplots(figsize=(10, 6), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    categories = [("Runner fully detected", runs.runner_detected_fraction.eq(1), ATTACK, "o"),
                  ("Runner includes extrapolation", runs.runner_detected_fraction.lt(1), DEFEND, "x")]
    for label, mask, color, marker in categories:
        points = runs[mask].dropna(subset=["free_area_delta_m2"])
        if len(points):
            ax.scatter(points.distance_m, points.free_area_delta_m2, label=f"{label} (n={len(points)})",
                       color=color, marker=marker, alpha=.7, s=40)
    ax.axhline(0, color=INK, lw=.9)
    ax.set(xlabel="Run distance (m)", ylabel="Change in teammate's fixed receiving patch (m²)")
    ax.spines[["top", "right"]].set_visible(False)
    if len(valid):
        ax.legend(frameon=False, fontsize=9)
    else:
        ax.text(.5, .5, "No runs with valid space estimates", transform=ax.transAxes, ha="center")
    m = manifest["metadata"]
    title = f"{m['home_team']['short_name']} vs {m['away_team']['short_name']}"
    fig.suptitle("Space changes during off-ball runs", x=.1, ha="left", color=INK, fontsize=19, fontweight="bold")
    ax.set_title(f"{title} | {manifest['scope']} | {len(valid)} valid of {len(runs)} detected runs", loc="left", fontsize=10, pad=15)
    fig.text(.1, .02, "SkillCorner / PySport open data. Retrospective geometric estimates; association does not establish causation.", fontsize=8, color=INK)
    fig.subplots_adjust(left=.1, right=.97, bottom=.15, top=.80)
    fig.savefig(output / "space-change.png", dpi=180)
    fig.savefig(output / "space-change.svg")
    plt.close(fig)
    if len(runs):
        # A deterministic example: the earliest run, never selected for a large space gain.
        example = runs.sort_values(["start_frame", "player_id"]).iloc[0]
        fig = pitch_snapshot(tracking, example, m, int(example.end_frame))
        fig.savefig(output / "example-run.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
    observed_runner = int(runs.runner_detected_fraction.eq(1).sum())
    observed_context = runs[(runs.runner_detected_fraction.eq(1)) & runs.context_endpoint_detected_fraction.eq(1)
                            & runs.ball_endpoint_detected]
    v = manifest["validation"]
    median = f"{runs.distance_m.median():.1f} m" if len(runs) else "unavailable"
    delta = f"{valid.free_area_delta_m2.median():+.1f} m²" if len(valid) else "unavailable"
    positive = int(valid.free_area_delta_m2.gt(0).sum())
    text = f"""# Can we credit footballers who never touch the ball?

## A reproducible baseline, not causal credit

This analysis reconstructs high-speed attacking movement from SkillCorner's public broadcast tracking. It asks whether nearby defenders and a preselected teammate's receiving space changed during each run. A run can be measured without being awarded credit for causing the change.

## Scope and results

- Match: {title}, {m['date_time'][:10]}; match ID {m['id']}.
- Scope: **{manifest['scope']}**; valid tracking frames {manifest['audit']['first_frame']} to {manifest['audit']['last_frame']}; periods {manifest['audit']['periods']}.
- {len(runs)} runs pass the fixed baseline; median run distance {median}.
- {observed_runner}/{len(runs)} runners are detected in every run frame. {observed_context.shape[0]}/{len(runs)} runs also have every contextual player detected at both endpoints and the ball detected at both endpoints. These denominators are distinct.
- Space estimates are available for {len(valid)}/{len(runs)} runs. {positive}/{len(valid)} have a positive change; the median change is {delta}. These are overlapping situations, not independent experimental observations.
- {int(runs.behind_line.sum())} runs cross the defensive-line proxy, {int(runs.wide_channel.sum())} enter a wide channel, and {int(runs.toward_space.sum())} increase runner clearance by at least 2 m. Categories may overlap.
- {v['baseline_runs_overlapping_provider']}/{len(runs)} baseline runs overlap a provider off-ball-run label at temporal IoU ≥0.3. The provider has {v['provider_runs_fully_in_scope']} fully contained labels in this scope. This checks alignment and definition differences; it is not measured accuracy or independent validation.

![Run distance and fixed-patch space change](space-change.png)

The chart separates fully detected runners from runners containing extrapolated positions. Even the fully detected-runner group can use extrapolated defenders or teammates. Larger measured space does not establish that the runner created it: ball movement, teammates, a defensive retreat or tracking errors may explain it. No tactical intent is inferred.

## Definitions and sensitivity

The default requires ≥{manifest['config']['speed_mps']} m/s, ≥{manifest['config']['min_duration_s']} s, ≥{manifest['config']['min_distance_m']} m path distance and ≥{manifest['config']['min_progress_m']} m progress toward goal. A phase confirms team possession; the player must be ≥3 m from the tracked ball and outside their provider possession intervals. Carrier identity is often missing, so off-ball status remains an estimate. Seven-frame Savitzky-Golay smoothing is retrospective.

Receiving space counts 1 m² cell centres within 6 m of a teammate's **starting position** that are at least 3 m from every opponent. The same pitch-clipped cells are compared at start and end. The teammate is the nearest eligible teammate at the run's start, never the one with the largest later improvement. This isolates a fixed area's changing geometry, not the area actually reachable by a receiver.

| Minimum speed (m/s) | Detected runs | Median distance (m) |
| --- | ---: | ---: |
"""
    for row in manifest["sensitivity"]:
        value = f"{row['median_distance_m']:.1f}" if row['median_distance_m'] is not None else "unavailable"
        text += f"| {row['speed_mps']:.1f} | {row['runs']} | {value} |\n"
    text += f"""
## Validation and limits

Unit tests cover parsing, IDs, centred metre coordinates and direction, period-aware timing, gaps/jumps, smoothing, no-ball exclusions, exact geometric calculations and cache integrity. The end-to-end run uses real source data. The space proxy omits pass accessibility, body orientation, offside and reaction times. There is no human-labelled accuracy study, fitted model or counterfactual estimate. Do not interpret this match or excerpt as a league ranking. Runs can fragment when speed or possession evidence changes.

Full source audit and formulas: [data audit](../../docs/data-audit.md), [methodology](../../docs/methodology.md).

## Reproduce and cite

From the project folder, run `.venv/bin/python -m invisible_runner run --match {m['id']} {'--full' if manifest['scope']=='full match' else '--seconds ' + str(manifest['sources']['tracking']['max_lines']//10)}`. The pipeline writes this report, CSVs, PNG/SVG chart and source/hash manifests together. Exact dependency versions are in `requirements-lock.txt`.

Source: [SkillCorner Open Data](https://github.com/SkillCorner/opendata/tree/{manifest['revision']}), with PySport; MIT license and copyright retained in `docs/source/LICENSE`. Tracking source SHA-256: `{manifest['sources']['tracking']['sha256']}`. Baseline code SHA-256: `{manifest['code_sha256']}`. No paid services or private footage are used.
"""
    (output / "findings.md").write_text(text)
    portable = {k: manifest[k] for k in ["match_id", "revision", "scope", "sources", "config", "code_sha256", "runtime", "audit", "validation", "sensitivity", "run_count", "metric_valid_count", "outputs"]}
    (output / "provenance.json").write_text(json.dumps(portable, indent=2) + "\n")
