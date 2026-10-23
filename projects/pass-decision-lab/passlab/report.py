"""Reproducible aggregate outputs; no redistribution of source snapshots."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import REVISION
from .models import calibration_table

PAPER, INK, TEAL, RUST = "#faf7f0", "#202c32", "#086b69", "#a43d25"


def calibration_chart(predictions, metrics, output: Path, assets: Path):
    plt.rcParams.update(
        {
            "svg.hashsalt": "passlab-2026",
            "font.family": "DejaVu Sans",
            "text.color": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
        }
    )
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 5.6), gridspec_kw={"width_ratios": [1.2, 1]})
    fig.set_facecolor(PAPER)
    selected = metrics[(metrics.population == "context") & (metrics.estimator != "boosted")]
    names = {"mean": "Training mean", "event": "Event origin + period", "360": "Event + 360 context"}
    for _, m in selected.iterrows():
        if m.features == "mean":
            continue
        pred = predictions[predictions.model_id == m.model_id]
        c = calibration_table(pred)
        c = c[c.n >= 30]
        color = TEAL if m.features == "360" else RUST
        left.plot(
            c.predicted,
            c.observed,
            marker="o" if m.features == "360" else "s",
            color=color,
            label=names[m.features],
            linewidth=2,
        )
    left.plot([0, 1], [0, 1], "--", color="#69757a", lw=1, label="Perfect calibration")
    left.set(
        xlim=(0, 1),
        ylim=(0, 1),
        xlabel="Mean predicted completion",
        ylabel="Observed completion",
        title="Does predicted completion match observation?",
    )
    left.legend(loc="upper left", frameon=False, fontsize=9)
    upper_bound = (
        max(
            selected.log_loss.max(),
            selected.log_loss_ci_high.max() if selected.log_loss_ci_high.notna().any() else 0,
        )
        * 1.25
    )
    for i, (_, m) in enumerate(selected.iterrows()):
        color = TEAL if m.features == "360" else RUST if m.features == "event" else "#69757a"
        right.barh(i, m.log_loss, color=color, height=0.56)
        right.text(upper_bound * 0.98, i, f"{m.log_loss:.3f}", ha="right", va="center", fontsize=10)
        if pd.notna(m.log_loss_ci_low):
            # Bootstrap percentile bounds need not bracket the original statistic.
            right.hlines(i, m.log_loss_ci_low, m.log_loss_ci_high, color=INK, lw=1.7)
            right.plot([m.log_loss_ci_low, m.log_loss_ci_high], [i, i], "|", color=INK)
    right.set_yticks(range(len(selected)), [names[x] for x in selected.features])
    right.invert_yaxis()
    right.set(
        xlim=(0, upper_bound), xlabel="Held-out log loss (lower is better)", title="Fixed logistic baselines"
    )
    for ax in (left, right):
        ax.set_facecolor(PAPER)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["bottom", "left"]].set_color("#9cabae")
        ax.title.set_fontsize(11)
    fig.suptitle(
        "What does a visible defensive context add?",
        x=0.06,
        ha="left",
        fontsize=20,
        fontfamily="DejaVu Serif",
        color=INK,
    )
    n = int(selected.iloc[0]["n"])
    games = int(selected.iloc[0].test_matches)
    fig.text(
        0.06,
        0.86,
        f"{n:,} ground-foot passes in {games} held-out matches; same rows in both models.",
        fontsize=10,
    )
    fig.text(
        0.06,
        0.10,
        "Features exclude recorded endpoints, length, angle and future events. Context models do not rate target choices.",
        fontsize=9,
    )
    fig.text(
        0.06,
        0.065,
        "Bins: fixed tenths; only n ≥ 30 drawn. Loss intervals: 95% match bootstrap, ≥4 test games.",
        fontsize=9,
    )
    fig.text(
        0.06, 0.03, f"Data: StatsBomb Open Data | {REVISION[:10]} | Euro 2024 + Women’s Euro 2025", fontsize=9
    )
    logo = assets / "statsbomb-logo.png"
    if logo.exists():
        ax_logo = fig.add_axes([0.835, 0.018, 0.12, 0.055])
        ax_logo.imshow(mpimg.imread(logo))
        ax_logo.axis("off")
    fig.subplots_adjust(left=0.075, right=0.94, top=0.77, bottom=0.23, wspace=0.65)
    fig.savefig(
        output / "calibration.png", dpi=180, facecolor=PAPER, metadata={"Software": "Pass Decision Lab"}
    )
    fig.savefig(output / "calibration.svg", facecolor=PAPER, metadata={"Date": None})
    plt.close(fig)


def write_findings(df, audits, metrics, split, omissions, output: Path, sample, candidate_audit=None):
    context = df[df.has_frame & df.has_opponents.fillna(False)]
    target = context[context.has_target]
    excluded = context[~context.has_target]

    def rate(d):
        return f"{d.complete.mean():.1%}" if len(d) else "unavailable"

    lines = [
        "# Can AI identify missed progressive passes?",
        "",
        "This experiment produces a review queue of hypothetical visible lanes. It does not establish that a player missed a better pass.",
        "",
        f"Source revision: `{REVISION}`. Reproduce with `python -m passlab.pipeline "
        + ("--full" if sample is None else f"--sample {sample}")
        + " --models all`.",
        "",
        "## What was observed",
        "",
        f"- {df.match_id.nunique()} matches, {len(df):,} eligible ground-foot passes; {len(context):,} have a frame with visible defenders.",
        f"- The endpoint-free recipient proxy retains {len(target):,}/{len(context):,} ({len(target) / len(context):.1%}) of those observations.",
        f"- Retained proxy completion: {rate(target)}; excluded completion: {rate(excluded)}. This comparison describes selection, not model accuracy.",
        f"- Train/test match counts: {len(split['train'])}/{len(split['test'])}. Split seed: {split['seed']}.",
        "",
        "## Holdout evidence",
        "",
        "| Population | Model | Features | Train passes | Test passes | Log loss | Brier | AUC |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, m in metrics.iterrows():
        auc = f"{m.roc_auc:.3f}" if m.roc_auc is not None and np.isfinite(m.roc_auc) else "n/a"
        lines.append(
            f"| {m.population} | {m.estimator} | {m.features} | {m.train_n:,} | {m['n']:,} | {m.log_loss:.4f} | {m.brier:.4f} | {auc} |"
        )
    m = metrics[(metrics.population == "context") & (metrics.estimator == "logistic")].set_index("features")
    if {"event", "360"} <= set(m.index):
        delta = float(m.loc["360", "log_loss"] - m.loc["event", "log_loss"])
        lines += [
            "",
            f"Adding 360 origin context changes fixed-logistic holdout log loss by {delta:+.4f} on exactly the same passes. "
            "A negative difference is an improvement on this split. This is a narrow origin-only event comparison, not a replication of Hudl’s target-aware event baseline.",
        ]
    lines += [
        "",
        "![Calibration and held-out loss](calibration.png)",
        "",
        "Bars include 95% match-cluster bootstrap intervals when at least four test games exist. These are conditional on the fixed trained model and split; they do not measure retraining uncertainty. "
        "No target model, hyperparameter or review threshold was selected using holdout performance.",
        "",
        "## What the candidate estimates mean",
        "",
        "The candidate model uses a recent pre-pass actor location to place an annotated recipient into the anonymous current frame. "
        "That assignment can be wrong. The training population overrepresents recently involved players and annotated recipients. "
        "Geometry-only and spatial target models share this same selected population; their scores cannot be compared directly with the broader context population.",
        "",
        "Alternative recipients are current visible teammate positions. Only targets passing every marginal training-range guard and visibility check receive an experimental probability. "
        "Passing these guards does not establish joint statistical support, feasibility, offside legality or counterfactual calibration. "
        "Forward gain is target x minus origin x in normalized StatsBomb units. Expected positive gain is xPass times max(forward gain, 0), assigning zero gain on failure. "
        "It ignores the cost of a turnover and has no claim to represent goal threat.",
        "",
        "A review flag requires an inferred actual recipient, both targets inside the guards, an alternative at least 10 units forward, "
        "xPass at least 0.70 and expected positive gain at least 5 units above the inferred chosen target. These fixed exploratory cutoffs are not tactical truth. "
        "There is no observed outcome for an unchosen pass. No player ranking or tactical explanation is inferred.",
        "",
        "## Coverage and limitations",
        "",
        "| Tournament | Matches | Eligible passes | With observed defenders | Proxy targets |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for tournament, group in df.groupby("tournament"):
        c = group[group.has_frame & group.has_opponents.fillna(False)]
        lines.append(
            f"| {tournament} | {group.match_id.nunique()} | {len(group):,} | {len(c):,} | {int(c.has_target.sum()):,} |"
        )
    lines += [
        "",
        "Missing or off-camera opponents, absent player IDs, snapshot timing, recipient annotation and domain shift remain material limitations. "
        "The event pressure tag is retained for display but excluded from predictions because its timing can overlap event duration. "
        "No endpoint-derived length/angle, actual endpoint, duration, future receipt, result, player ID or match ID enters the model. "
        "The sample mode selects earliest matches and is a smoke test, not a representative tournament estimate.",
        "",
        "Per-match parsing audits, split membership, per-tournament model metrics, feature lists, source hashes and environment versions are stored locally in the run outputs. "
        "Raw snapshots and pass-level tables are deliberately excluded from version control under the source agreement.",
        "",
        "## Sources and attribution",
        "",
        "- [StatsBomb Open Data](https://github.com/hudl/open-data), event v4.0.0 and 360 v1.0.0 specifications; [data terms](../docs/source/LICENSE.pdf).",
        "- Conor Sharpe, [xPass 360: Upgrading Expected Pass Models](https://www.hudl.com/blog/xpass-360-upgrading-expected-pass-xpass-models), 17 June 2025. Conceptual reference; no equivalence to the proprietary model is claimed.",
        "",
        "![StatsBomb](../assets/statsbomb-logo.png)",
        "",
        "Original code is MIT licensed. StatsBomb data and branding retain the upstream terms; no commercial reuse or raw data redistribution is granted by this project.",
    ]
    if candidate_audit:
        i = lines.index("## What the candidate estimates mean")
        lines[i:i] = [
            "## The exploratory review queue",
            "",
            f"Of {candidate_audit['heldout_proxy_events']:,} held-out proxy events, "
            f"{candidate_audit['events_with_supported_chosen_proxy']:,} have a chosen-target proxy inside every marginal guard. "
            f"The fixed rules flag {candidate_audit['flagged_lanes']:,} candidate lanes in "
            f"{candidate_audit['flagged_events']:,} events. These are review hypotheses, not confirmed missed passes.",
            "",
            f"Across that held-out proxy population, {candidate_audit['supported_lanes']:,}/"
            f"{candidate_audit['candidate_lanes']:,} visible candidate lanes receive a probability. "
            "No candidate outcome is observed, so accuracy or value improvement of these flags cannot be measured here.",
            "",
        ]
    if omissions:
        lines += ["", "## Omitted experiments", "", *[f"- {x}" for x in omissions]]
    (output / "findings.md").write_text("\n".join(lines) + "\n")


def write_tournament_metrics(predictions, output):
    from .models import scores

    records = []
    for (model_id, tournament), g in predictions.groupby(["model_id", "tournament"]):
        records.append(
            {
                "model_id": model_id,
                "tournament": tournament,
                "matches": int(g.match_id.nunique()),
                **scores(g.complete, g.probability),
            }
        )
    (output / "tournament-metrics.json").write_text(json.dumps(records, indent=2, allow_nan=False))
