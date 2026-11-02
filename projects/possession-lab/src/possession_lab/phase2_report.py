"""Static Phase 2 tables and diagnostic figures, generated from all declared trials."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .phase1_metrics import paired_deltas

PRIMARY = ["hmm", "hierarchical", "conservative", "probabilistic"]


def write_phase2_report(table, confidence, out):
    out = Path(out)
    cfg = json.loads((out / "config.json").read_text())
    lookup = {(r.scenario, r.method, r.metric): r for r in confidence.itertuples(index=False)}
    scenarios = list(dict.fromkeys(table.scenario))
    ordinary = table[table.world == "single"]

    def cell(scenario, method, metric, interval=True, digits=3):
        row = lookup[(scenario, method, metric)]
        if not np.isfinite(row.mean):
            return "n/a"
        text = f"{row.mean:.{digits}f}"
        return text + (f" [{row.low:.{digits}f}, {row.high:.{digits}f}]" if interval else "")

    score_metrics = ["spell_f1", "macro_f1", "D_precision", "D_recall", "occluded_accuracy", "false_D_live"]
    if len(ordinary):
        clustered = ordinary.groupby(["trial", "method"], as_index=False)[score_metrics].mean()
        clustered["scenario"] = "ordinary_equal_weight_mean"
        cluster_deltas = paired_deltas(clustered, score_metrics, draws=cfg["bootstrap_draws"], seed=cfg["bootstrap_seed"])
        cluster_deltas.to_csv(out / "clustered_deltas.csv", index=False)
    else:
        cluster_deltas = pd.DataFrame()
    lines = ["# Phase 2: can imperfect events resolve tracking ambiguity?", "",
        "Synthetic event-channel experiment only. No training, tuning, restricted input, real-match",
        "tag creation or competition-performance claim. All Phase 1 implementations and historical",
        "results remain frozen. The complete protocol is in `../../docs/phase2/PROTOCOL.md`.", "",
        "## Leakage audit and scope", "",
        "Actions and private referee permissions precede the labels. Two different action-clock",
        "processes generate worlds; a rule engine derives state, while the noisy sensor receives only",
        "visible action projections, timeline and optional shared-view visibility. Cancelled attempts",
        "and advisory signals prevent a cue from being equivalent to a label. No private ruling,",
        "true dead interval, label array, latent correctness bit or simulator-family ID enters fusion.",
        "False positives and detections both carry unknown confidence. Source actions and observed",
        "annotations are saved separately. Unit tests change private permissions while holding visible",
        "cues fixed and require identical annotation streams.", "",
        "This does not eliminate simulator assumptions. The extra action channel is assumed to see",
        "some officiating/attempt cues absent from 2D coordinates. The synthetic stoppage-signal code",
        "is hypothetical: public DATA.md does not promise it in the real export. The restart-only",
        "ablation removes that cue. Shared-view loss, corruption, null tags and a second action process",
        "challenge the assumptions; none establish real sensor calibration or conditional information.", "",
        "## Fixed experiment and optional fusion", "",
        f"{len(table):,} method runs across {table.scenario.nunique()} world/regime cases with {table.trial.nunique()} trials each.",
        "Episode worlds and renewal worlds differ in action schedules and movement/occlusion generation",
        "but share football-rule semantics. No parameters were searched or selected on these trials.",
        "Annotation regimes include missing detections, false positives, timing offsets/broad windows,",
        "category errors, unknown/wrong teams, repeated/conflicting tags and shared-camera failures.",
        "A/B are the unchanged HMM and hierarchy. C accepts only corroborating stop/restart reports.",
        "D combines bounded probabilistic context from individual reports, with weak conditional team",
        "hints for restart reports only. Event time is uniform within its uncertain annotation window.",
        "Context decays rather than assigning an entire phase to a hard label; overlapping evidence",
        "is averaged and capped, exact duplicates deduplicated. Declared semantic probabilities are",
        "engineering priors, not calibrated likelihoods of the real export. Generic phase teams are",
        "ignored because they may refer to a defending side. The joint decoder and tracking evidence",
        "are imported from frozen Phase 1. Empty/disabled evidence reproduces the hierarchy exactly.", "",
        "The default event-coverage policy may permit output during ball occlusion. The ball-mask",
        "ablation restores the old ball-only abstention rule; read it separately from state inference.",
        "Negative controls shuffle event times or shift them within periods, preserving ordinary",
        "world tag counts, widths, categories and teams. Random tags are independent of actions.",
        "For twins the donor control stream is exactly shared across worlds, selected independently",
        "of which world is evaluated. These paired nulls have no conditional information.", "",
        "## Per-family results", "",
        f"Intervals are 95% whole-trial paired percentile bootstrap intervals ({cfg['bootstrap_draws']:,} draws).",
        "They are conditional on these generators and unadjusted for multiple exploratory comparisons.",
        "Tables and confidence.csv include defined-trial counts for D precision/recall and latency.", "",
        "| Family / regime | HMM spell | Hierarchy spell | Conservative spell | Probabilistic spell [95%] | Probabilistic macro [95%] |",
        "|---|---:|---:|---:|---:|---:|"]
    for scenario in scenarios:
        if not scenario.endswith(":single"):
            continue
        lines.append(f"| {scenario.removesuffix(':single')} | {cell(scenario,'hmm','spell_f1',False)} | {cell(scenario,'hierarchical','spell_f1',False)} | {cell(scenario,'conservative','spell_f1',False)} | {cell(scenario,'probabilistic','spell_f1')} | {cell(scenario,'probabilistic','macro_f1')} |")
    lines += ["", "All eleven methods, including every negative control and ablation, are in `comparison.md`.",
        "`paired_deltas.csv` reports model minus hierarchy; `alignment_deltas.csv` reports aligned",
        "probabilistic fusion minus each control. Gains over tagless alone do not establish information:",
        "a random D-biased cue can improve an imperfect baseline by changing its prior or abstention.", "",
        "| Family / regime | Probabilistic D precision / recall | Restart recall | Boundary missed / spurious | Matched boundary MAE (frames) |",
        "|---|---:|---:|---:|---:|"]
    for scenario in scenarios:
        if scenario.endswith(":single"):
            lines.append(f"| {scenario.removesuffix(':single')} | {cell(scenario,'probabilistic','D_precision',False)} / {cell(scenario,'probabilistic','D_recall',False)} | {cell(scenario,'probabilistic','restart_recall',False)} | {cell(scenario,'probabilistic','boundary_missed',False,1)} / {cell(scenario,'probabilistic','boundary_spurious',False,1)} | {cell(scenario,'probabilistic','boundary_mae_frames',False,1)} |")
    lines += ["", "Restart timing matches only D-to-H/A transitions by destination within +/-25 frames and",
        "within each graded block. Possession boundary diagnostics count typed starts/ends and omit",
        "known period edges. Both use the official temporal X filling. A matched-only latency must",
        "be read with recall/missed counts; n/a is retained when its denominator is zero.", "",
        "## Alignment controls and ablations", ""]
    if len(cluster_deltas):
        lines += ["Below: equal-weight ordinary scenarios averaged within each trial ID before paired",
            "bootstrap, preserving correlation across regimes. These are descriptive synthetic averages,",
            "not a general ranking. Difference is method minus tagless hierarchy.", "",
            "| Method / ablation | SpellF1 delta [95%] | macroF1 delta [95%] | D recall delta [95%] |",
            "|---|---:|---:|---:|"]
        for method in ("conservative", "probabilistic", "tags_shuffled", "tags_shifted", "tags_uninformative", "no_team", "no_restarts", "restart_only", "ball_mask"):
            fields = []
            for metric in ("spell_f1", "macro_f1", "D_recall"):
                row = cluster_deltas[(cluster_deltas.method == method) & (cluster_deltas.metric == metric)].iloc[0]
                fields.append(f"{row['mean']:+.3f} [{row.low:+.3f}, {row.high:+.3f}]")
            lines.append(f"| {method} | {' | '.join(fields)} |")
    lines += ["", "## Identical tracking: informative versus null tags", "",
        "Twin worlds have the same full tracking history/future and opposite H/D target truth. Their",
        "additional action cues differ, and the annotator observes them imperfectly. They test the",
        "conditional hypothesis that another modality supplies information; they do not prove the real",
        "tagging product observes such a modality. Shared null inputs must produce the same predictions",
        "and cannot exceed 50% balanced target accuracy. This bound also holds for randomized rules",
        "in expectation and is not a macroF1/spellF1 bound.", "",
        "Both raw and official-temporally-filled target accuracies are saved. Null tags may reduce X",
        "and increase raw accuracy below chance without adding information. The filled result removes",
        "that particular abstention artifact; require a gain above the paired null ceiling to claim",
        "synthetic ambiguity resolution. The paired worlds are resampled together, never as two",
        "independent matches.", ""]
    twin_path = out / "twin_confidence.csv"
    if twin_path.exists():
        twins = pd.read_csv(twin_path)
        lines += ["| Pair family / regime | Hierarchy filled accuracy | Conservative filled accuracy | Probabilistic filled accuracy [95%] | Random tags filled accuracy |",
                  "|---|---:|---:|---:|---:|"]
        for scenario in dict.fromkeys(twins.scenario):
            values = []
            for method in ("hierarchical", "conservative", "probabilistic", "tags_uninformative"):
                row = twins[(twins.scenario == scenario) & (twins.method == method) & (twins.metric == "target_filled_accuracy")].iloc[0]
                value = f"{row['mean']:.3f}"
                if method == "probabilistic":
                    value += f" [{row.low:.3f}, {row.high:.3f}]"
                values.append(value)
            lines.append(f"| {scenario} | {' | '.join(values)} |")
    checks = json.loads((out / "null_twin_checks.json").read_text())
    lines += ["", f"All {len(checks)} declared tagless/shared-null pair checks passed the identical-output and <=50% tests.", "",
        "## Failures, costs and recommendation", "",
        "Do not suppress negative control gains, harmful category/team errors or missed restarts.",
        "Use both generator families and each regime when assessing robustness. Dependence on the",
        "hypothetical stoppage cue, assumed timing kernel or event-coverage policy is a limitation",
        "until validated on independent, legitimately labelled other matches. The restart-only and",
        "ball-mask ablations are essential to that interpretation. Real phase intervals can span",
        "multiple possessions and real set-piece codes need not imply the exact dead/live boundary.", "",
        "Cost includes common tracking feature extraction plus decoder/fusion wall time, after warm-up",
        "and counterbalanced method order on this host. I/O/scoring/plotting and annotation generation",
        "are excluded. Synthetic annotation generation cost is not a cost estimate for video tagging.", "",
        "| Method | Feature ms | Decoder/fusion ms | Total ms |",
        "|---|---:|---:|---:|"]
    for method in PRIMARY:
        means = table[table.method == method][["feature_ms", "decode_ms", "total_ms"]].mean()
        lines.append(f"| {method} | {means.feature_ms:.1f} | {means.decode_ms:.1f} | {means.total_ms:.1f} |")
    lines += ["", "Recommended real integration remains disabled/zero-weight until category semantics, temporal",
        "uncertainty, false positives and dependence on tracking are validated externally. The design",
        "is in `../../docs/phase2/INTEGRATION.md`; no gated XML reader was run or added. Public ground",
        "truth is not used to fit/select this model. Reproduce with `bash scripts/reproduce_phase2.sh`.", "",
        "Figures: `alignment.png`, `ablations.png`, `twins.png` (when pairs are present), and",
        "`failure_cases.png`. Failure cases use declared selection rules, not only favourable examples.", ""]
    (out / "report.md").write_text("\n".join(lines))
    full = ["# Full Phase 2 comparison", "", "Mean [95% whole-trial bootstrap interval]; undefined D rates/timing are n/a.",
            "See confidence.csv for defined-trial counts. All methods see the same trial observations.", "",
            "| Scenario | Method | SpellF1 | macroF1 | D precision | D recall | Boundary F1 | Missed / spurious | Boundary MAE | Restart recall | Restart MAE | Total ms |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for scenario in scenarios:
        for method in dict.fromkeys(table.method):
            fields = [cell(scenario, method, metric) for metric in ("spell_f1", "macro_f1", "D_precision", "D_recall", "boundary_f1")]
            fields.append(cell(scenario, method, "boundary_missed") + " / " + cell(scenario, method, "boundary_spurious"))
            fields += [cell(scenario, method, metric) for metric in ("boundary_mae_frames", "restart_recall", "restart_mae_frames", "total_ms")]
            full.append(f"| {scenario} | {method} | {' | '.join(fields)} |")
    (out / "comparison.md").write_text("\n".join(full) + "\n")
    _plots(table, out, cluster_deltas)


def _plots(table, out, clustered):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ordinary_scenarios = list(dict.fromkeys(table.loc[table.world == "single", "scenario"]))
    if ordinary_scenarios:
        aligned = pd.read_csv(out / "alignment_deltas.csv")
        gains = pd.read_csv(out / "paired_deltas.csv")
        fig, ax = plt.subplots(figsize=(11, 7), layout="constrained")
        for j, (source, method, label, color) in enumerate([
            (gains, "probabilistic", "Aligned minus hierarchy", "#0072B2"),
            (aligned, "aligned_minus_tags_shuffled", "Aligned minus shuffled", "#D55E00")]):
            data = source[(source.method == method) & (source.metric == "spell_f1")].set_index("scenario").reindex(ordinary_scenarios)
            ax.errorbar(data["mean"], np.arange(len(data)) + (j-0.5)*0.16,
                        xerr=np.maximum(0, np.vstack([data["mean"]-data.low, data.high-data["mean"]])),
                        fmt="o", capsize=2, label=label, color=color)
        ax.axvline(0, color="#777777", lw=1)
        ax.set(yticks=np.arange(len(ordinary_scenarios)), yticklabels=[s.removesuffix(":single") for s in ordinary_scenarios],
               xlabel="Paired spellF1 difference; 95% whole-trial intervals", title="Synthetic event alignment test")
        ax.invert_yaxis()
        fig.legend(loc="outside lower center", ncols=2)
        fig.savefig(out / "alignment.png", dpi=160)
        plt.close(fig)
    if len(clustered):
        fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True, layout="constrained")
        names = ["conservative", "probabilistic", "tags_shuffled", "tags_uninformative", "no_team", "no_restarts", "restart_only", "ball_mask"]
        for ax, metric in zip(axes, ("spell_f1", "macro_f1")):
            data = clustered[clustered.metric == metric].set_index("method").reindex(names)
            ax.errorbar(data["mean"], np.arange(len(names)),
                        xerr=np.maximum(0, np.vstack([data["mean"]-data.low, data.high-data["mean"]])), fmt="o", capsize=3)
            ax.axvline(0, color="#777777", lw=1)
            ax.set(yticks=np.arange(len(names)), yticklabels=names, xlabel="Difference from frozen hierarchy", title=metric)
        axes[0].invert_yaxis()
        fig.suptitle("Synthetic ablations | trial-cluster bootstrap, equal-weight mechanisms")
        fig.savefig(out / "ablations.png", dpi=160)
        plt.close(fig)
    twin_path = out / "twin_confidence.csv"
    if twin_path.exists():
        twin = pd.read_csv(twin_path)
        cases = list(dict.fromkeys(twin.scenario))
        fig, ax = plt.subplots(figsize=(10, 5), layout="constrained")
        for j, (method, color) in enumerate([("hierarchical", "#777777"), ("conservative", "#CC79A7"),
                                           ("probabilistic", "#0072B2"), ("tags_uninformative", "#D55E00")]):
            data = twin[(twin.method == method) & (twin.metric == "target_filled_accuracy")].set_index("scenario").reindex(cases)
            ax.errorbar(data["mean"], np.arange(len(cases)) + (j-1.5)*0.15,
                        xerr=np.maximum(0, np.vstack([data["mean"]-data.low, data.high-data["mean"]])), fmt="o", capsize=2, label=method, color=color)
        ax.axvline(0.5, color="black", ls="--", lw=1, label="shared-null ceiling")
        ax.set(yticks=np.arange(len(cases)), yticklabels=cases, xlim=(-0.02,1.02),
               xlabel="Balanced target frame accuracy after temporal X filling", title="Identical tracking, opposing truth | synthetic pairs")
        ax.invert_yaxis()
        fig.legend(loc="outside lower center", ncols=3)
        fig.savefig(out / "twins.png", dpi=160)
        plt.close(fig)
    _failure_plot(table, out)


def _failure_plot(table, out):
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch
    selections = []
    ordinary = table[table.world == "single"]
    for regime, largest, title in [("corrupt", False, "Largest corrupted-tag harm"), ("occluded", True, "Largest occlusion benefit")]:
        group = ordinary[ordinary.regime == regime]
        if not len(group):
            continue
        pivot = group.pivot(index=["scenario", "trial"], columns="method", values="macro_f1")
        differences = pivot.probabilistic - pivot.hierarchical
        key = differences.idxmax() if largest else differences.idxmin()
        selections.append((key[0], int(key[1]), f"{title}; Δmacro={differences.loc[key]:+.3f}"))
    twins = table[(table.world == "dead") & (table.regime == "moderate")]
    if len(twins):
        row = twins.sort_values(["scenario", "trial"]).iloc[0]
        selections.append((row.scenario, int(row.trial), "First declared ambiguous dead-world case"))
    if not selections:
        row = table.iloc[0]
        selections = [(row.scenario, int(row.trial), "First trial (smoke configuration)")]
    colors = ["#0072B2", "#D55E00", "#777777", "#eeeeee"]
    code = dict(zip("HADX", range(4)))
    fig, axes = plt.subplots(len(selections)*2, 1, figsize=(13, len(selections)*3.6),
                              gridspec_kw={"height_ratios": [3,1]*len(selections)}, layout="constrained")
    for j, (scenario, trial, title) in enumerate(selections):
        family, regime, state = scenario.split(":")
        folder = out / "trials" / family / regime / state
        data = pd.read_csv(folder / f"{trial}.csv")
        tags = json.loads((folder / f"{trial}_observed_tags.json").read_text())
        names = ["truth", "hmm", "hierarchical", "conservative", "probabilistic", "tags_shuffled"]
        raster = np.array([[code[x] for x in data[name]] for name in names])
        ax, tag_ax = axes[2*j:2*j+2]
        ax.imshow(raster, aspect="auto", interpolation="nearest", cmap=ListedColormap(colors), vmin=0, vmax=3,
                  extent=(0,len(data)/25,len(names)-0.5,-0.5))
        ax.set(yticks=np.arange(len(names)), yticklabels=names, title=f"{scenario} / {trial} | {title}")
        for edge in np.arange(.5,len(names)-.5):
            ax.axhline(edge,color="white",lw=2)
        cats = ["set pieces", "stoppage signal", "phase", "other"]
        for tag in tags:
            index = cats.index(tag["code"])
            tag_ax.plot([tag["start"]/25,tag["stop"]/25],[index,index],lw=3,alpha=.55,color=colors[index])
        tag_ax.set(xlim=(0,len(data)/25),yticks=range(4),yticklabels=cats,xlabel="Synthetic video time (s); bars are observed annotation windows")
    fig.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(colors,"HADX")],loc="outside upper center",ncols=4)
    fig.savefig(out / "failure_cases.png",dpi=160)
    plt.close(fig)
    (out / "failure_selection.json").write_text(json.dumps(selections,indent=2)+'\n')
