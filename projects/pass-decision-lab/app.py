"""Local Streamlit interface. Run the pipeline before launching."""

from __future__ import annotations

import json
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from passlab.choices import evaluate_candidates
from passlab.data import REVISION
from passlab.geometry import pass_geometry
from passlab.models import predict_bundle
from passlab.viz import calibration_plot, pitch_figure

ROOT = Path(__file__).resolve().parent
OUTPUT = Path(os.environ.get("PASSLAB_OUTPUT", ROOT / "outputs"))
st.set_page_config(page_title="Pass Decision Lab", layout="wide", initial_sidebar_state="collapsed")
st.html("""<style>
:root { color-scheme: light; }
.stApp { background: #faf7f0; color: #202c32; }
h1,h2,h3 { color: #202c32; }
h1 { font-family: Georgia,serif !important; font-weight: 500 !important; letter-spacing: -.035em; }
a { color: #086b69; }
button:focus-visible, input:focus-visible, [role="combobox"]:focus-visible {
outline: 3px solid #086b69 !important; outline-offset: 3px;
}
.stButton button { min-height: 44px; }
[data-testid="stCaptionContainer"] { color: #4b595b; }
[data-testid="stMainBlockContainer"] { max-width: 1380px; padding-top: 4.5rem; }
@media (max-width: 700px) {
 [data-testid="stMainBlockContainer"] { padding: 4.5rem 1rem 1rem; }
 h1 { font-size: 2rem !important; }
 [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
 [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex: 1 1 100% !important; min-width: 0 !important; }
}
</style>""")
st.title("Pass Decision Lab")
st.markdown(
    "Explore what the camera shows at a historical pass. Compare the recorded action with visible ground-pass scenarios."
)


@st.cache_data(show_spinner="Reading locally validated pass data…")
def load_data(path: str, stamp: int):
    p = Path(path)
    return (
        pd.read_csv(p / "passes.csv"),
        json.loads((p / "scenes.json").read_text()),
        pd.read_csv(p / "metrics.csv"),
        pd.read_csv(p / "predictions.csv"),
        json.loads((p / "model-bundles.json").read_text()),
        json.loads((p / "run-summary.json").read_text()),
    )


def probability_label(value):
    if pd.isna(value):
        return ""
    if value >= 0.9995:
        return ">99.9%"
    if value < 0.0005:
        return "<0.1%"
    return f"{value:.1%}"


def render_explorer(df, scenes, bundles, review_ids):
    st.info(
        "Candidate xPass is experimental: anonymous receivers, incomplete camera coverage and a selected training sample. "
        "A review flag is a prompt for video analysis, not proof of a missed better pass."
    )
    c1, c2 = st.columns([1, 1])
    tournament = c1.selectbox("Tournament", sorted(df.tournament.unique()))
    partition = c2.selectbox("Match partition", ["Held-out matches", "All matches"])
    pool = df[(df.tournament == tournament) & df.has_frame].copy()
    decision_view = st.selectbox("Decision view", ["All framed passes", "Experimental review flags"])
    if decision_view == "Experimental review flags":
        pool = pool[pool.event_id.isin(review_ids)]
    if partition == "Held-out matches":
        pool = pool[pool.partition == "test"]
    if pool.empty:
        st.info(
            "No passes meet this selection. Choose All framed passes, another tournament or match partition."
        )
        return
    matches = pool[["match_id", "label", "date"]].drop_duplicates().sort_values(["date", "match_id"])
    match_labels = {int(r.match_id): f"{r.date} · {r.label}" for _, r in matches.iterrows()}
    match_column, team_column = st.columns([2, 1])
    match_id = match_column.selectbox(
        "Match", matches.match_id.tolist(), format_func=lambda m: match_labels[m]
    )
    match_pool = pool[pool.match_id == match_id]
    team = team_column.selectbox("Team in possession", sorted(match_pool.team.unique()))
    team_pool = match_pool[match_pool.team == team]
    possessions = team_pool.groupby("possession", sort=True).agg(
        minute=("minute", "min"), passes=("event_id", "size"), period=("period", "first")
    )
    possession_column, pass_column = st.columns([1, 1])
    possession = possession_column.selectbox(
        "Historical possession",
        possessions.index.tolist(),
        format_func=lambda p: (
            f"Possession {p} · period {possessions.loc[p, 'period']} · "
            f"{possessions.loc[p, 'minute']} min · {possessions.loc[p, 'passes']} framed passes"
        ),
    )
    possession_passes = team_pool[team_pool.possession == possession].sort_values("event_index")
    descriptions = {
        r.event_id: f"{r.minute:02d}:{r.second:02d} · {r.player} · "
        f"{'completed' if r.complete else 'not completed'}"
        for _, r in possession_passes.iterrows()
    }
    event_id = pass_column.selectbox(
        "Pass in this possession", possession_passes.event_id.tolist(), format_func=lambda e: descriptions[e]
    )
    row = possession_passes[possession_passes.event_id == event_id].iloc[0]
    scene = scenes[event_id]
    candidates = evaluate_candidates(row.to_dict(), scene, bundles.get("target_360"))
    if row.partition == "train":
        st.warning(
            "This match was used for training. Its predictions are in-sample; model scores below use held-out matches only."
        )
    actual = (
        pass_geometry(scene["origin"], scene["actual_end"], scene["opponents"])
        if scene.get("actual_end")
        else {}
    )
    st.subheader(descriptions[event_id])
    st.caption(
        f"Period {row.period} · event {row.event_index} · {len(scene['teammates'])} visible teammates · "
        f"{len(scene['opponents'])} visible opponents · recorded collector pressure: "
        f"{'yes' if row.under_pressure else 'no'} (display only)"
    )
    if "360" in bundles and row.has_opponents:
        context_probability = float(predict_bundle(bundles["360"], pd.DataFrame([row]))[0])
        st.markdown(
            f"**Context-only xPass: {probability_label(context_probability)}.** This describes the observed pass context; "
            "it does not distinguish recipients."
        )
    if candidates.empty:
        st.info(
            "No valid non-actor teammates are present in this snapshot. The actual pass can still be inspected."
        )
        highlight = None
    else:
        ids = candidates.candidate_id.tolist()
        highlight = st.selectbox(
            "Highlight visible teammate", ids, format_func=lambda x: f"{x} (anonymous snapshot label)"
        )
    fig = pitch_figure(scene, highlight)
    st.pyplot(fig, width="stretch")
    plt.close(fig)
    if actual:
        st.caption(
            f"Recorded endpoint displacement: {actual['distance']:.1f} normalized units; "
            f"x gain {actual['forward_gain']:+.1f}. The solid line shows the recorded end, not a verified intended target."
        )
    if not candidates.empty:
        selected = candidates[candidates.candidate_id == highlight].iloc[0]
        if selected.supported:
            st.markdown(
                f"**{highlight}: experimental xPass {probability_label(selected.xpass)}**, forward gain "
                f"{selected.forward_gain:+.1f}, expected positive gain {selected.expected_forward_gain:.1f} units."
            )
        else:
            st.warning(
                f"{highlight}: probability withheld. {selected.support_warning}. Geometry remains inspectable."
            )
        if scene.get("target_candidate_id"):
            st.caption(
                f"Inferred chosen recipient: {scene['target_candidate_id']}. This uses only a recent earlier event "
                "and the current snapshot; anonymous identity is unverified."
            )
        else:
            st.caption(
                "The chosen recipient could not be mapped without endpoints. Any visible candidate may have been "
                "the intended receiver; no missed-pass comparison is made for this event."
            )
        st.subheader("Visible candidate lanes")
        st.caption(
            "All distances are normalized StatsBomb units. Forward gain is target x minus origin x. "
            "Expected positive gain = experimental xPass × max(forward gain, 0); failure has zero gain and no turnover penalty."
        )
        display = candidates[
            [
                "candidate_id",
                "proxy_target",
                "forward_gain",
                "distance",
                "lane_clearance",
                "lane_defenders_3",
                "xpass",
                "expected_forward_gain",
                "review_flag",
                "support_warning",
            ]
        ].copy()
        display["xpass"] = display["xpass"].map(probability_label)
        st.dataframe(
            display,
            hide_index=True,
            width="stretch",
            column_config={
                "candidate_id": "Teammate",
                "proxy_target": "Inferred chosen",
                "forward_gain": st.column_config.NumberColumn("Forward gain", format="%+.1f"),
                "distance": st.column_config.NumberColumn("Distance", format="%.1f"),
                "lane_clearance": st.column_config.NumberColumn("Nearest lane defender", format="%.1f"),
                "lane_defenders_3": "Defenders within 3 units",
                "xpass": st.column_config.TextColumn("Experimental xPass"),
                "expected_forward_gain": st.column_config.NumberColumn(
                    "Expected positive gain", format="%.1f"
                ),
                "review_flag": "Review flag",
                "support_warning": "Withholding reasons",
            },
        )
        st.caption(
            "A blank nearest-lane distance means no visible defender projects inside the segment; it is not an infinite clearance. "
            "A review flag requires a different inferred recipient, ≥10 units forward, xPass ≥70%, and ≥5 more expected positive units. "
            "The fixed rules do not establish offside legality or tactical superiority."
        )
    with st.expander("Inspect this source observation"):
        st.json(
            {
                "event_id": event_id,
                "match_id": int(match_id),
                "partition": row.partition,
                "target_history_age_seconds": row.get("history_age")
                if pd.notna(row.get("history_age"))
                else None,
                "target_history_distance_units": row.get("history_distance")
                if pd.notna(row.get("history_distance"))
                else None,
                "visible_area_available": bool(scene.get("visible_area")),
            }
        )
        st.link_button(
            "Open official match events",
            f"https://github.com/hudl/open-data/blob/{REVISION}/data/events/{match_id}.json",
        )


def main():
    required = [
        "passes.csv",
        "scenes.json",
        "metrics.csv",
        "predictions.csv",
        "model-bundles.json",
        "run-summary.json",
    ]
    if not all((OUTPUT / f).exists() for f in required):
        st.info(
            "No local analysis is available yet. Run the four-match smoke pipeline, then reload this page."
        )
        st.code("python -m passlab.pipeline --sample 2\nstreamlit run app.py", language="bash")
        return
    try:
        stamp = max((OUTPUT / f).stat().st_mtime_ns for f in required)
        df, scenes, metrics, predictions, bundles, summary = load_data(str(OUTPUT), stamp)
    except (ValueError, KeyError, OSError) as exc:
        st.error(
            f"Cannot read the local analysis: {exc}. Rerun the pipeline to create a complete output directory."
        )
        return
    st.caption(
        f"{summary['matches']} matches · {summary['eligible_passes']:,} eligible passes · "
        f"{summary['selection']} · StatsBomb source {REVISION[:10]}"
    )
    if summary["selection"] != "all":
        st.warning(
            "Smoke sample: these earliest matches test the pipeline. They do not represent either full tournament."
        )
    explore, checks, methods = st.tabs(["Explore a possession", "Model evidence", "Methods & sources"])
    with explore:
        queue_path = OUTPUT / "review-queue.csv"
        review_ids = set(pd.read_csv(queue_path).event_id) if queue_path.exists() else set()
        render_explorer(df, scenes, bundles, review_ids)
    with checks:
        st.subheader("What holds up in unseen matches?")
        st.markdown(
            "Every score uses whole held-out matches. The app uses the prespecified logistic model trained on the training partition; "
            "boosted trees provide a fixed comparison. Lower log loss and Brier are better; higher AUC is better."
        )
        population = st.selectbox(
            "Evaluation population",
            metrics.population.unique().tolist(),
            format_func=lambda x: (
                "All framed passes with visible defenders"
                if x == "context"
                else "Restricted recipient-proxy sample"
            ),
        )
        chosen_metrics = metrics[metrics.population == population]
        st.dataframe(chosen_metrics.drop(columns=["population"]), hide_index=True, width="stretch")
        st.caption(
            "Log-loss intervals are 95% held-out match-cluster bootstrap intervals, conditional on this fitted model; "
            "blank when fewer than four test matches are present. Calibration bins are fixed tenths, including their row counts on hover."
        )
        model_ids = chosen_metrics.model_id.tolist()
        selected_models = st.multiselect(
            "Models on calibration plot", model_ids, default=[x for x in model_ids if "/logistic/" in x]
        )
        pred = predictions[predictions.model_id.isin(selected_models)]
        st.plotly_chart(
            calibration_plot(pred),
            width="stretch",
            key="calibration",
            config={"displaylogo": False, "responsive": True},
        )
        st.subheader("How selective is the recipient proxy?")
        coverage = (
            df.assign(with_defenders=df.has_frame & df.has_opponents)
            .groupby("tournament")
            .agg(
                matches=("match_id", "nunique"),
                eligible_passes=("event_id", "size"),
                with_frames=("has_frame", "sum"),
                with_defenders=("with_defenders", "sum"),
                proxy_targets=("has_target", "sum"),
            )
        )
        st.dataframe(coverage, width="stretch")
        if summary["omissions"]:
            st.info("Omitted experiments: " + "; ".join(summary["omissions"]))
        st.caption(
            "The event baseline uses origin and period only. Target geometry comes from a 360/history proxy, "
            "so its geometry-only comparison is not a pure event-only model. These results do not replicate Hudl’s proprietary model."
        )
    with methods:
        st.subheader("A pass-choice experiment with explicit limits")
        st.markdown("""**Population.** Untyped ground passes played with the left or right foot, periods 1–4; unknown outcomes excluded.
A missing pass outcome denotes completion. Set pieces, aerial passes, recovery/interception pass types and shootouts are excluded.

**Coordinates.** StatsBomb 120 × 80 normalized units. Each actor’s team already attacks x=120, including in the second half.
The schematic line is not a measured ball trajectory.

**Recipient proxy.** The annotated recipient must have an earlier same-team actor event within five seconds.
Its origin must be within three units of the nearest current visible teammate, with a two-unit margin over the next teammate.
Only strictly earlier timestamps in the same period qualify. No recorded endpoint, future receipt or outcome enters the assignment.
Anonymous identity remains uncertain and the selected training sample can be strongly biased.

**Lane pressure.** Minimum point-to-segment distance among opponents projecting strictly inside the segment;
count within three units, nearest receiver opponent, nearest passer opponent and Gaussian proximity with sigma five.
These are geometric features, not proven interception or line-breaking measures.

**Prediction limits.** No unseen players are inferred. Candidate probabilities are withheld for missing features,
unknown/outside target visibility, off-pitch targets, or any feature outside its training 1st–99th percentile range.
These marginal checks do not establish joint support. We do not observe outcomes for unchosen passes,
receiver movement, offside legality, defender reactions or tactical intent.

**Validation.** Seed 2026; 25% of matches per tournament held out. Transformations fit on training rows only.
Logistic C=1 is fixed in advance. Boosting uses 100 iterations, seven leaves, learning rate .05 and no random-row early stopping.
There is no holdout-based tuning or refit on all matches. Context comparisons use exactly the same rows;
target experiments share a separate recipient-proxy cohort.

**Use.** Suitable for noncommercial research and review. A probability or forward-gain advantage is not evidence
that the player should have chosen that lane. Consult the source agreement before distributing data or commercial reuse.""")
        st.link_button("Source data and specifications", f"https://github.com/hudl/open-data/tree/{REVISION}")
        st.link_button(
            "Hudl’s June 2025 xPass 360 article",
            "https://www.hudl.com/blog/xpass-360-upgrading-expected-pass-xpass-models",
        )
        st.download_button(
            "Download aggregate findings",
            (OUTPUT / "findings.md").read_text(),
            "pass-decision-lab-findings.md",
            mime="text/markdown",
        )
    st.image(str(ROOT / "assets/statsbomb-logo.png"), width=150)
    st.caption(
        "Data: StatsBomb Open Data. Original code: MIT. Data and branding retain their upstream terms."
    )


main()
