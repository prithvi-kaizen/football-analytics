"""Generate a static experimental report from computed tables; no frontend or hosted service."""
from pathlib import Path
import json

import numpy as np

from .phase1_metrics import paired_deltas

PRIMARY = ["nearest", "state_machine", "hmm", "hierarchical"]


def write_report(table, confidence, diagnosis, out):
    out = Path(out)
    config = json.loads((out / "config.json").read_text())
    draws, seed = config["bootstrap_draws"], config["bootstrap_seed"]
    lookup = {(r.scenario, r.method, r.metric): r for r in confidence.itertuples(index=False)}
    scenarios = list(dict.fromkeys(table.scenario))

    def cell(scenario, method, metric, interval=True, digits=3):
        row = lookup[(scenario, method, metric)]
        if not np.isfinite(row.mean):
            return "n/a"
        value = f"{row.mean:.{digits}f}"
        return value + (f" [{row.low:.{digits}f}, {row.high:.{digits}f}]" if interval else "")

    ordinary = table[~table.scenario.str.startswith("twin_")]
    joint = ordinary.groupby(["trial", "method"], as_index=False)[["spell_f1", "macro_f1", "D_recall"]].mean()
    joint["scenario"] = "ordinary_scenarios"
    delta = paired_deltas(joint, ["spell_f1", "macro_f1", "D_recall"], draws=draws, seed=seed)
    delta.to_csv(out / "ablation_cluster_deltas.csv", index=False)
    lines = ["# Phase 1: failure-driven possession inference", "",
        "Synthetic results only. No public-label fitting/tuning, restricted-data ingestion, actual-match",
        "tag fabrication, or competition-performance claim. The original temporal baselines and scorer",
        "remain unchanged. The report is generated from saved results, not manually selected examples.", "",
        "## Checked failure mechanism", "",
        f"On the old stationary-live case (seed 101), {diagnosis['live_stationarity_fraction']:.1%} of live frames",
        f"crossed the stationarity threshold. The evidence function overwrote {diagnosis['control_overwritten_D']:,}",
        f"valid team-control observations with D, despite {diagnosis['live_out_of_bounds']} live out-of-bounds frames.",
        f"The state machine predicted D on {diagnosis['SM_live_D_fraction']:.1%} of live frames; the HMM on",
        f"{diagnosis['HMM_live_D_fraction']:.1%}. This was checked from distances, speed features, evidence and decoded",
        "outputs (`legacy_trace.csv`). The feature takes trailing medians of 0.4 s endpoint speeds;",
        "after enough observed values remain below 0.8 m/s, it accumulates stationary seconds. Short",
        "gaps can still leave enough values in the trailing window. `evidence()` assigns H/A first,",
        "then overwrites with D at >=1.2 s. Repeated D evidence resets the state-machine observation age",
        "and reconfirms D; the HMM repeatedly assigns a 0.9 versus 0.05 emission advantage. Temporal",
        "stickiness compounds the error but is not its initial cause.", "",
        "## Model and controlled comparisons", "",
        "The hierarchy has latent states live-H, live-A, dead-with-H-memory and dead-with-A-memory.",
        "The latter two both output D and do not claim dead-ball ownership. Two fixed logistic heads",
        "estimate live/dead and owner given live from geometry, motion and observation masks. Local",
        "probabilities become likelihood-ratio potentials relative to neutral hierarchical priors;",
        "this avoids favouring D merely because team evidence is absent. Weak stationarity evidence",
        "is additive, never a hard override. An explicit output mask abstains after 3 s without a",
        "reliable ball and on completely unobserved periods. It is separate from hidden-state inference.",
        "Live/dead duration and team continuity use independent Markov transition factors. Joint Viterbi",
        "finds the MAP path; scaled forward/backward gives normalized marginals. Inference is offline.",
        "The scores and marginals use uncalibrated engineering priors, not learned probabilities.", "",
        "Frame potentials are tempered by 0.2 because successive window-derived features are correlated;",
        "this is a declared heuristic, not an estimated correction. Feature coverage still counts track",
        "slots, not physical players, so fragmented slot inventories can alter apparent reliability.",
        "No calibration, log-loss validation or transfer to the official ATD distribution is established.", "",
        "All one-factor ablations retain the other inputs, priors and abstention rule. Legacy",
        "stationarity-off variants zero only the stationarity feature in a copy; the original functions",
        "are untouched. Hierarchical variants remove stationarity, make the unsafe missing-as-static",
        "assumption, remove live/dead durations, or remove owner continuity. Full parameters and the",
        "prospective protocol are in `config.json` and `../../docs/phase1/PROTOCOL.md`.", "",
        "## Independent synthetic evaluation", "",
        f"{table.trial.nunique()} trials per scenario; {table.scenario.nunique()} scenarios; {table.method.nunique()} methods; {len(table):,} method runs.",
        "Trial schedules, durations, starting teams, formations and trajectories vary. Observation",
        "families change the data-generating mechanism, not just the seed: IID loss, Markov bursts,",
        "transition-dependent loss, camera cropping, moving dead-ball players, live freezes, invisible",
        "stoppages, slot switches, outliers and short spells. All methods see identical observations",
        "within a trial. Synthetic player/carrier jumps and simple referee-state mechanisms remain",
        "major limitations. No parameters were selected using this evaluation.", "",
        f"Intervals below are 95% whole-trial percentile bootstrap intervals ({draws:,} draws), conditional",
        "on this generator. Methods use the same trial resamples. They are exploratory, unadjusted",
        "for multiple comparisons, and do not estimate uncertainty on real football matches.", "",
        "| Scenario | SM spell | HMM spell | Hierarchy spell [95%] | Hierarchy macro [95%] |",
        "|---|---:|---:|---:|---:|"]
    for scenario in scenarios:
        lines.append(f"| {scenario} | {cell(scenario,'state_machine','spell_f1',False)} | {cell(scenario,'hmm','spell_f1',False)} | {cell(scenario,'hierarchical','spell_f1')} | {cell(scenario,'hierarchical','macro_f1')} |")
    lines += ["", "Every method, including nearest and every ablation, has per-scenario macroF1, spellF1, D",
        "precision/recall, boundary errors and timing with confidence intervals in `comparison.md` and",
        "`confidence.csv`. `metrics.csv` contains every trial, denominator and raw error count.", "",
        "## D detection, possession boundaries and cost", "",
        "D precision is undefined if no graded frame was predicted D; D recall is undefined if there",
        "is no true D. These are n/a, not zero or perfect. Confidence tables include the number of",
        "defined trials, so conditional precision must be read with predicted-D counts and recall.",
        "Boundary diagnostics type both starts and ends by team, exclude known period edges, and",
        "match one-to-one within each graded block at +/-25 frames after the official X filling.",
        "The matched latency excludes missed boundaries; read missed/spurious counts beside it.", "",
        "| Scenario | Hierarchy D P / R | Missed / spurious boundaries | Matched MAE (frames) |",
        "|---|---:|---:|---:|"]
    for scenario in scenarios:
        lines.append(f"| {scenario} | {cell(scenario,'hierarchical','D_precision',False)} / {cell(scenario,'hierarchical','D_recall',False)} | {cell(scenario,'hierarchical','boundary_missed',False,1)} / {cell(scenario,'hierarchical','boundary_spurious',False,1)} | {cell(scenario,'hierarchical','boundary_mae_frames',False,1)} |")
    lines += ["", "Runtime below is a descriptive mean over ordinary scenarios/trials on this host, after warm-up",
        "with counterbalanced method order. It includes extraction plus decoding, and excludes scoring",
        "and I/O. The hierarchy also computes posterior marginals; baselines output labels only.",
        "No peak-memory benchmark or deployment-throughput claim is made. Per-scenario cost intervals",
        "are in the full table. Both Viterbi implementations use O(T K^2) time and O(T K) memory.", "",
        "| Method | Frame macroF1 | SpellF1 | Feature ms | Decode ms | Total ms | Real-time factor |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for name in PRIMARY:
        means = ordinary[ordinary.method == name][["macro_f1", "spell_f1", "feature_ms", "decode_ms", "total_ms", "realtime_factor"]].mean()
        lines.append(f"| {name} | {means.macro_f1:.3f} | {means.spell_f1:.3f} | {means.feature_ms:.1f} | {means.decode_ms:.1f} | {means.total_ms:.1f} | {means.realtime_factor:.5f} |")
    lines += ["", "These pooled means weight the declared scenarios equally; they are not a general ranking.", "",
        "## Ablations and failed hypotheses", "",
        "Deltas below are ablation minus full hierarchy, first averaging ordinary scenarios within",
        f"each trial ID, then bootstrapping the {table.trial.nunique()} trial clusters. This retains correlation between",
        "mechanisms sharing latent matches. Positive F1 deltas favour the ablation, not the full model.", "",
        "| Ablation | SpellF1 delta [95%] | macroF1 delta [95%] |",
        "|---|---:|---:|"]
    for method in ["hier_no_stationary", "hier_missing_as_static", "hier_no_duration", "hier_no_continuity"]:
        fields = []
        for metric in ("spell_f1", "macro_f1"):
            row = delta[(delta.method == method) & (delta.metric == metric)].iloc[0]
            fields.append(f"{row['mean']:+.3f} [{row.low:+.3f}, {row.high:+.3f}]")
        lines.append(f"| {method} | {' | '.join(fields)} |")
    lines += ["", "Removing the hard stationarity rule is not a complete dead-ball solution. On stationary-live",
        "trials the original SM and its stationarity-off variant have mean spellF1 "
        f"{cell('stationary_live','state_machine','spell_f1',False) if 'stationary_live' in scenarios else 'n/a'} and "
        f"{cell('stationary_live','sm_no_stationary','spell_f1',False) if 'stationary_live' in scenarios else 'n/a'}; "
        "on moving-dead trials the full hierarchy has D recall "
        f"{cell('moving_dead','hierarchical','D_recall',False) if 'moving_dead' in scenarios else 'n/a'}.",
        "Tracking stationarity is neither necessary nor sufficient for dead ball. Model confidence",
        "does not establish identifiability. Duration priors are not a replacement for missing referee",
        "evidence. In this suite, removing them increased aggregate frame macroF1 slightly but severely",
        "reduced spellF1, including on short-spell trials. Use the",
        "scenario-specific paired deltas rather than interpreting an aggregate as universal benefit.", "",
        "The hypothesized consistent benefit of masking missingness was not supported by this suite:",
        "the unsafe missing-as-static variant slightly increased aggregate macroF1, while its spellF1",
        "delta included zero. This exposes a weakness of these observation mechanisms as a validation",
        "of missing-data policy; it does not turn absent coordinates into physical static-ball evidence.",
        "Removing the already weak stationarity term also had little aggregate effect. The hierarchy",
        "is worse than the original HMM on several ordinary mechanisms, even though it rescues live",
        "freezes. It is not a universal replacement for the baseline.", "",
        "## Identifiability counterexamples", "",
        "Each twin family supplies the same complete tracking sequence, missingness, timestamps and",
        "periods for a live world and a dead world. Only an interval's truth differs. Static twins",
        "include a nearby apparent controller; invisible twins hide the ball while players move.",
        "Common visible motion before and after the target can represent either a live pass or a",
        "restart; the referee decision is absent. The inputs are noisy tracking observations, not",
        "a claim that every latent physical detail is equal in both worlds.",
        "No tracking-only deterministic method can output different labels for identical inputs.",
        "On the differing interval its two frame accuracies sum to at most 1 (possibly less when it",
        "abstains). Under an equal prior over the two worlds the maximum expected target accuracy",
        "is 50%, including for randomized rules. This is a frame-classification bound, not a bound",
        "of 0.5 on macroF1 or spellF1. Future context cannot help because the whole sequences match.",
        "`ambiguity_checks.json` verifies identical predictions across both worlds for every method",
        "and trial. Twin-live cases lack D and A, so even a perfect all-H frame prediction has",
        "official macroF1 1/3; absent classes are scored zero. Target accuracy and denominator counts",
        "in `metrics.csv` make this explicit. Twin worlds are not pooled as independent matches.", "",
        "## Recommendations and Smart Tagging seam", "",
        "Keep the original models as regression controls. Treat stationary live and moving-dead",
        "failures as negative controls in any further work. Use genuinely independent labelled other",
        "matches and match-level splits before calibrating or selecting priors. Expand physically",
        "coherent passing/referee scenarios with new trial IDs for later model revisions.",
        "Read `docs/phase1/SMART_TAGGING.md` in the package for the future interface derived from public",
        "DATA.md. Phase intervals must retain unknown teams, overlap conflicts and unknown confidence;",
        "a restart window is not an exact whistle timestamp. The implementation validates loader-shaped",
        "records in memory using fictional examples only and never converts phases to truth labels.",
        "No tags are ingested or fused in this experiment. Restricted integration remains disabled",
        "here and belongs in a separate human-run environment outside Codex access.", ""]
    (out / "report.md").write_text("\n".join(lines))
    details = ["# Per-scenario comparison", "", "All cells: mean [95% whole-trial bootstrap interval]. D rates and latency use defined trials only.",
               "See confidence.csv for defined-trial counts; metrics.csv for every trial and denominator.", "",
               "| Scenario | Method | SpellF1 | macroF1 | D precision | D recall | Boundary F1 | Missed / spurious | MAE frames | Total ms |",
               "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for scenario in scenarios:
        for name in sorted(set(table.method)):
            fields = [cell(scenario, name, metric) for metric in ("spell_f1", "macro_f1", "D_precision", "D_recall", "boundary_f1")]
            fields += [cell(scenario, name, "boundary_missed") + " / " + cell(scenario, name, "boundary_spurious"),
                       cell(scenario, name, "boundary_mae_frames"), cell(scenario, name, "total_ms", digits=1)]
            details.append(f"| {scenario} | {name} | {' | '.join(fields)} |")
    (out / "comparison.md").write_text("\n".join(details) + "\n")
    _plot(confidence, out / "spell_uncertainty.png")


def _plot(confidence, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = confidence[(confidence.metric == "spell_f1") & ~confidence.scenario.str.startswith("twin_")]
    scenarios = list(dict.fromkeys(rows.scenario))
    fig, ax = plt.subplots(figsize=(10, 7), layout="constrained")
    for j, (method, color) in enumerate([("state_machine", "#777777"), ("hmm", "#D55E00"), ("hierarchical", "#0072B2")]):
        selected = rows[rows.method == method].set_index("scenario").reindex(scenarios)
        values = selected["mean"].to_numpy()
        lower = np.maximum(0, values - selected.low.to_numpy())
        upper = np.maximum(0, selected.high.to_numpy() - values)
        ax.errorbar(values, np.arange(len(scenarios)) + (j - 1) * 0.18,
                    xerr=np.array([lower, upper]), fmt="o", ms=4, capsize=2, label=method, color=color)
    ax.set(yticks=np.arange(len(scenarios)), yticklabels=scenarios, xlim=(-0.03, 1.03),
           xlabel="Possession spell F1; 95% whole-trial bootstrap intervals",
           title=f"Synthetic trials only | {int(rows.trials.iloc[0])} randomized matches per mechanism")
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    fig.legend(loc="outside lower center", ncols=3)
    fig.savefig(path, dpi=160)
    plt.close(fig)
