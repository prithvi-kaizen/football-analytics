from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json
import os
import tempfile
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "possession-danger-mpl"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd
matplotlib.rcParams["svg.hashsalt"] = "possession-danger-v1"

from .data import REVISION, digest, write_json

TEAL = "#006B68"
RUST = "#A34526"
PAPER = "#FAF8F3"
INK = "#252A28"


def write_report(output, totals, possessions, summary):
    heldout = totals.loc[totals.split.eq("test")]
    fig, ax = plt.subplots(figsize=(10, 7), facecolor=PAPER)
    ax.set_facecolor(PAPER)
    other = heldout.loc[~heldout.team.str.contains("Barcelona", regex=False)]
    barca = heldout.loc[heldout.team.str.contains("Barcelona", regex=False)]
    ax.scatter(other.possession_pct, other.threat_share, color=RUST, alpha=.75, s=35, label="Other teams")
    if not barca.empty:
        ax.scatter(barca.possession_pct, barca.threat_share, color=TEAL, marker="D", s=85, edgecolor=INK, linewidth=.6, label="Barcelona")
    ax.plot([0, 100], [0, 100], color="#797C76", linestyle="--", linewidth=1, label="Equal shares")
    ax.set(xlim=(0, 100), ylim=(0, 100), xlabel="Active possession-time share (%)", ylabel="Positive move xT share (%)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=INK)
    ax.legend(loc="upper left", frameon=False)
    fig.suptitle("Does possession become danger?", x=.12, ha="left", fontsize=23, color=INK, fontweight="bold")
    subtitle = f"Held-out team-match observations • {summary['test_matches']} fixtures • " + ("SMOKE TEST ONLY" if summary["sample"] else " / ".join(x["competition"] for x in summary["coverage"]))
    ax.set_title(subtitle, loc="left", fontsize=10, pad=18, color=INK)
    fig.text(.12, .06, "xT fitted on separate training matches. Shares are proxies, not official possession or scoring probabilities.", fontsize=9, color=INK)
    fig.text(.12, .028, f"Data: StatsBomb Open Data | revision {REVISION[:10]} | positive move xT can count repeated advances.", fontsize=8, color=INK)
    logo = Path(__file__).parents[1] / "assets" / "statsbomb-logo.png"
    if logo.exists():
        logo_ax = fig.add_axes([.8, .005, .16, .045])
        logo_ax.imshow(mpimg.imread(logo))
        logo_ax.axis("off")
    fig.subplots_adjust(bottom=.16, top=.84)
    fig.savefig(output / "possession-vs-threat.png", dpi=180, facecolor=PAPER)
    fig.savefig(output / "possession-vs-threat.svg", facecolor=PAPER, metadata={"Date": None})
    plt.close(fig)
    comparison = summary["barcelona_heldout"]
    lines = ["# Does Barcelona's possession create danger?", "",
             "**Data: StatsBomb Open Data. Research analysis; no tactical intent is inferred.**", "",
             f"Pinned source: `{REVISION}`. Coverage: {summary['matches']} fixtures; {summary['train_matches']} training matches and {summary['test_matches']} held-out matches. Latest 20% per competition held out, rounded up. All actions from a match stay in one split.", ""]
    if summary["sample"]:
        lines += ["**This is a six-match-style functional smoke test, not season evidence. Do not generalise these numbers to Barcelona or its league.**", ""]
    if comparison:
        c = comparison
        low, high = c["bootstrap_95_interval"]
        direction = "higher" if c["difference_xt_per_100"] > 0 else "lower"
        lines += [f"In the {c['matches']} held-out Barcelona fixtures, Barcelona averaged {c['mean_possession_pct']:.1f}% of active possession time, {c['mean_field_tilt']:.1f}% of final-third completed passes, and {c['mean_threat_share']:.1f}% of positive move xT.", "",
                  f"Barcelona generated {c['barca_xt_per_100']:.2f} positive move xT per 100 possessions; its opponents in those same fixtures generated {c['opponent_xt_per_100']:.2f}. Barcelona's rate was {direction} in this selected held-out schedule. The paired difference was {c['difference_xt_per_100']:+.2f} per 100 possessions (95% paired fixture-bootstrap interval {low:+.2f} to {high:+.2f}; 2,000 resamples, seed 2026). This interval omits model-fitting uncertainty and may be unstable with few fixtures.", "",
                  "These are descriptive comparisons under one location-only model. They do not establish that possession causes danger, nor that the team dominates every opponent or every score state.", ""]
    else:
        lines += ["No held-out Barcelona fixture is present. This selection cannot answer the Barcelona question.", ""]
    quiet = possessions.loc[possessions.split.eq("test") & possessions.shots.eq(0) & possessions.positive_xt.lt(.01)].sort_values("elapsed_seconds", ascending=False)
    if len(quiet):
        q = quiet.iloc[0]
        lines += [f"The longest held-out possession with no shot and less than 0.01 positive move xT belonged to {q.team}: match {q.match_id}, period {q.period}, possession {q.possession}. It lasted {q.elapsed_seconds:.1f} seconds, contained {q.passes} passes, and began while {q.score_state}. This describes its immediate output, not its tactical usefulness.", ""]
    v = summary["model"]["validation"]
    lines += ["## Validation", "",
              f"All {summary['matches']} final scorelines reconcile with event goals, including own-goals. xT converged in {summary['model']['iterations']} iterations (Bellman residual {summary['model']['residual']:.2g}). On {v['heldout_actions']:,} held-out actions, shot-choice Brier score was {v['shot_choice_brier']:.5f}, against {v['constant_shot_choice_brier']:.5f} for a constant training-rate baseline; lower is better. {v['unseen_cell_fraction']:.1%} of held-out actions began in unseen training cells. This checks one-step shot choice, not full xT calibration.", "",
              f"Duration cleaning flagged {summary.get('cleaning', {}).get('tiny_negative_duration_repairs', 0)} tiny negative durations. Values in [-0.1, 0) seconds contribute zero time, with original values and affected records retained in the audit output. Larger negative durations fail validation.", "",
              "## Definitions and limits", "",
              "Possessions follow StatsBomb IDs, split at period boundaries and whenever the other team performs an attacking on-ball action (pass, carry, shot, dribble, miscontrol, dispossession or shield). The provider's possession_team names the starter and can persist through opposition attacks; it is retained separately. Defensive pressures and tackles do not switch the analytical owner. A sequence requires at least one on-ball anchor. All source passes, shots and shot xG reconcile to sequence totals. Elapsed span runs from first owner on-ball action to last action end, capped at the next sequence. Active time unions owner action-duration intervals, excluding idle gaps and overlaps. Field tilt is each team's share of completed passes starting at x ≥ 80 on the 120 × 80 pitch.", "",
              "The 12 × 8 xT grid uses empirical non-penalty goals and transitions from passes/carries. Failed moves, miscontrols, dispossessions and failed dribbles absorb at zero. Values solve V = r + TV. Signed successful-move value is V(end) - V(start). Positive move xT sums only increases; it can count repeated advances and is not a possession-goal probability. Penalties are excluded from fitting and xT but included in observed shot/xG totals.", "",
              "Score state is reconstructed before each event; a goal shot belongs to the pre-goal state. A possession's start state describes the whole chain, while score-state tables use action-level state. StatsBomb xG is supplied, not trained here; its original training data is unknown, so it is a descriptive supporting metric rather than a leakage-free model benchmark.", "",
              "A low-threat possession may protect a lead, rest a team or draw opponents out. No off-ball tracking or causal evidence here can verify those explanations. No opponent-strength adjustment or cross-league equivalence is claimed. xT can reflect finishing luck and small cell counts; grid sensitivity and external-season validation remain future work.", "",
              "## Reproduce", "", "See README.md for the exact sample and full-league commands. `manifest.json` records source URLs, revision, cached-file hashes, split IDs, package versions, code hashes and output hashes. The PNG/SVG chart is regenerated by the same pipeline.", "",
              "## Sources", "", "- [StatsBomb Open Data and terms](https://github.com/hudl/open-data)",
              "- [Official five-league release](https://www.hudl.com/blog/statsbomb-free-womens-data-wsl-ligaf-bundesliga-seriea-nwsl)",
              "- [Karun Singh: Introducing Expected Threat](https://karun.in/blog/expected-threat.html)",
              "- [socceraction: expected threat](https://socceraction.readthedocs.io/en/stable/documentation/valuing_actions/xT.html)", ""]
    (output / "findings.md").write_text("\n".join(lines))


def render_existing(output: Path):
    """Refresh presentation from hash-verified analysis; never silently recompute evidence."""
    manifest = json.loads((output / "manifest.json").read_text())
    for name in ["summary.json", "team_matches.csv", "possessions.csv"]:
        if digest(output / name) != manifest["output_sha256"][name]:
            raise ValueError(f"Analysis output changed: {name}; rerun the pipeline")
    summary = json.loads((output / "summary.json").read_text())
    write_report(output, pd.read_csv(output / "team_matches.csv"), pd.read_csv(output / "possessions.csv"), summary)
    for name in ["findings.md", "possession-vs-threat.png", "possession-vs-threat.svg"]:
        manifest["output_sha256"][name] = digest(output / name)
    root = Path(__file__).parents[1]
    manifest["presentation_code_sha256"] = {name: digest(root / name) for name in ["app.py", "possession_danger/report.py", "possession_danger/viz.py", ".streamlit/config.toml"]}
    manifest["rendered_at"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "manifest.json", manifest)
    print(f"Rendered report and chart from verified evidence in {output}", flush=True)
