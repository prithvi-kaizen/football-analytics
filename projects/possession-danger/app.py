from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from possession_danger.analysis import classify, team_summary
from possession_danger.data import digest
from possession_danger.viz import INK, PAPER, RUST, TEAL, pitch_model, pitch_sequence, scatter, style, timeline
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
st.set_page_config(page_title="Is possession actually dangerous?", layout="wide")
# Keep metric definitions and caveats readable; Streamlit fades captions by default.
st.html("<style>[data-testid='stCaptionContainer'] { opacity: 1; }</style>")


@st.cache_data
def load_output(path: str, fingerprint: str):
    root = Path(path)
    manifest = json.loads((root / "manifest.json").read_text())
    for name in ["summary.json", "xt_model.json", "possessions.csv", "actions.csv", "team_matches.csv", "score_states.csv"]:
        if digest(root / name) != manifest["output_sha256"][name]:
            raise ValueError(f"Output integrity check failed for {name}; regenerate this dataset")
    return ({name: pd.read_csv(root / f"{name}.csv", dtype={"season": str}, low_memory=False) for name in ["possessions", "actions", "team_matches", "score_states"]},
            json.loads((root / "summary.json").read_text()), json.loads((root / "xt_model.json").read_text()))


st.title("Is possession actually dangerous?")
st.caption("Possession volume, territory and attacking value in women's football. Data: StatsBomb Open Data.")
outputs = [p for p in (ROOT / "outputs").glob("*") if p.is_dir() and not p.name.startswith(".") and all((p / f).exists() for f in ["summary.json", "manifest.json", "possessions.csv", "actions.csv", "team_matches.csv", "score_states.csv", "xt_model.json"])]
outputs.sort(key=lambda p: (p.name != "liga-f", p.name))
if not outputs:
    st.info("No analysis has been generated yet. Run the sample pipeline from this project's directory.")
    st.code("python -m possession_danger.cli download --sample 6\npython -m possession_danger.cli run --sample 6 --offline")
    st.stop()

with st.sidebar:
    st.header("Analysis scope")
    dataset = st.selectbox("Dataset", outputs, format_func=lambda p: p.name)
    split = st.selectbox("Match split", ["Held-out matches", "Training matches", "All matches (descriptive)"])
    st.caption("The latest 20% of matches per league are held out. The xT grid is always fitted on training matches only.")
    st.image(str(ROOT / "assets" / "statsbomb-logo.png"), width=180)
    st.markdown("[Source and licence](https://github.com/hudl/open-data)")

try:
    with st.spinner("Loading validated analysis…"):
        fingerprint = str((dataset / "manifest.json").stat().st_mtime_ns)
        frames, summary, model = load_output(str(dataset), fingerprint)
except (OSError, ValueError, KeyError) as exc:
    st.error(f"The analysis output could not be read: {exc}. Regenerate it with the pipeline.")
    st.stop()
if summary["sample"]:
    st.warning("Smoke-test sample: these fixtures demonstrate the pipeline. They cannot support a season-level conclusion.")
if split != "Held-out matches":
    st.info("This is a descriptive view containing training matches. Use held-out matches for the primary comparison.")

totals = frames["team_matches"].copy()
if split != "All matches (descriptive)":
    totals = totals.loc[totals.split.eq("test" if split == "Held-out matches" else "train")]
with st.sidebar:
    competition = st.selectbox("Competition", sorted(totals.competition.unique()))
totals = totals.loc[totals.competition.eq(competition)]
if totals.empty:
    st.info("No matches in this selection. Choose a different dataset or split.")
    st.stop()
names = sorted(totals.team.unique())
default = next((i for i, name in enumerate(names) if "Barcelona" in name), 0)
with st.sidebar:
    focus = st.selectbox("Focus team", names, index=default)
match_ids = totals.match_id.unique()
seq = frames["possessions"].loc[frames["possessions"].match_id.isin(match_ids)].copy()
actions = frames["actions"].loc[frames["actions"].match_id.isin(match_ids)].copy()
st.caption(f"{competition} · {len(match_ids)} fixtures · {totals.date.min()} to {totals.date.max()} · source revision 4b73468fc5")

comparison, match_lab, methods = st.tabs(["Team comparison", "Match lab", "Methods & validation"])
with comparison:
    focus_totals = totals.loc[totals.team.eq(focus)]
    st.subheader(f"{focus}: where the ball goes matters")
    cols = st.columns(3)
    cols[0].metric("Active possession-time share", f"{focus_totals.possession_pct.mean():.1f}%")
    cols[1].metric("Final-third pass share", f"{focus_totals.field_tilt.mean():.1f}%")
    cols[2].metric("Positive move xT share", f"{focus_totals.threat_share.mean():.1f}%")
    st.caption(f"Means of match-level shares over {len(focus_totals)} fixtures. Active time unions recorded on-ball action durations; it is not official possession. Field tilt counts completed passes starting in the final third.")
    metric = st.radio("Compare possession with", ["Threat creation", "Territorial control"], horizontal=True)
    st.plotly_chart(scatter(totals, focus, "threat_share" if metric == "Threat creation" else "field_tilt"), width="stretch")
    st.caption("Each point is one team in one match. The dashed line marks equal shares. Positive move xT sums increases from successful passes and carries; repeated advances can accumulate value.")
    st.subheader("Threat per 100 possessions")
    table = team_summary(totals)
    chart = px.bar(table.sort_values("xt_per_100"), x="xt_per_100", y="team", orientation="h",
                   labels={"xt_per_100": "Positive move xT / 100 possessions", "team": ""},
                   color=table.sort_values("xt_per_100").team.eq(focus).map({True: focus, False: "Other teams"}),
                   color_discrete_map={focus: TEAL, "Other teams": RUST})
    st.plotly_chart(style(chart, max(350, 30 * len(table))), width="stretch")
    st.caption("Ratios use summed xT / summed possessions. Opponent schedules differ; this is a descriptive comparison within the selected league.")
    st.dataframe(table.drop(columns="competition").round(3), hide_index=True, width="stretch")
    st.download_button("Download team comparison CSV", table.to_csv(index=False), "team-comparison.csv", "text/csv")

    st.subheader("While winning, drawing and losing")
    states = frames["score_states"].loc[frames["score_states"].match_id.isin(match_ids) & frames["score_states"].team.eq(focus)]
    state_table = states.groupby("score_state", as_index=False).agg(active_seconds=("active_seconds", "sum"), positive_xt=("positive_xt", "sum"), shots=("shots", "sum"), xg=("xg", "sum"))
    state_table["active_minutes"] = state_table.active_seconds / 60
    state_table["xt_per_active_minute"] = state_table.positive_xt / state_table.active_minutes.replace(0, float("nan"))
    state_table["observed_state"] = state_table.score_state.str.title()
    st.plotly_chart(style(px.bar(state_table, x="observed_state", y="xt_per_active_minute", color_discrete_sequence=[TEAL],
                                 labels={"observed_state": "Score state before the action", "xt_per_active_minute": "Positive move xT / active possession minute"},
                                 category_orders={"observed_state": ["Winning", "Drawing", "Losing"]})), width="stretch")
    st.dataframe(state_table.drop(columns=["active_seconds", "observed_state"]).round(3), hide_index=True, width="stretch")
    st.caption("Unobserved states are omitted. Rates divide by active possession minutes in that state, not match minutes. Small exposures can produce unstable rates. Goal shots belong to the pre-goal state.")
    st.subheader("Compare teams in the same score state")
    all_states = frames["score_states"].loc[frames["score_states"].match_id.isin(match_ids)]
    state_comparison = all_states.groupby(["team", "score_state"], as_index=False).agg(
        active_seconds=("active_seconds", "sum"), positive_xt=("positive_xt", "sum"),
        matches=("match_id", "nunique"))
    state_comparison["active_minutes"] = state_comparison.active_seconds / 60
    state_comparison["xt_per_active_minute"] = state_comparison.positive_xt / state_comparison.active_minutes.replace(0, float("nan"))
    matrix = state_comparison.pivot(index="team", columns="score_state", values="xt_per_active_minute").reindex(columns=["winning", "drawing", "losing"])
    heatmap = px.imshow(matrix, text_auto=".2f", aspect="auto", color_continuous_scale="YlGnBu", zmin=0,
                        labels={"x": "Score state before action", "y": "", "color": "xT / active min"})
    st.plotly_chart(style(heatmap, max(330, 32 * len(matrix))), width="stretch")
    st.caption("Blank cells mean no observed exposure. Each rate uses that team's active possession time at that score state; opponent, venue and game context remain unadjusted.")
    st.dataframe(state_comparison.drop(columns="active_seconds").round(3), hide_index=True, width="stretch")

with match_lab:
    st.subheader("Follow one match")
    focus_ids = focus_totals.match_id.tolist()
    labels = {}
    for mid in focus_ids:
        rows = totals.loc[totals.match_id.eq(mid)]
        labels[mid] = f"{rows.iloc[0].date} · {' vs '.join(rows.team.tolist())} · {mid}"
    mid = st.selectbox("Match", focus_ids, format_func=lambda value: labels[value])
    match_seq = seq.loc[seq.match_id.eq(mid)].copy()
    match_actions = actions.loc[actions.match_id.eq(mid)].copy()
    teams = [focus] + [name for name in match_seq.team.unique() if name != focus]
    max_minute = max(1, int((match_seq.clock.max() + match_seq.elapsed_seconds.max()) / 60) + 1)
    window = st.slider("Timeline window (elapsed playing minutes)", 0, max_minute, (0, max_minute))
    st.plotly_chart(timeline(match_seq, teams, window), width="stretch")
    st.caption("Cumulative value is booked at possession start. The elapsed clock concatenates periods including stoppage time and excludes halftime breaks.")
    period_starts = match_seq.groupby("period").clock.min().to_dict()
    st.caption("Period starts on this clock: " + ", ".join(f"P{p} at {t / 60:.1f} min" for p, t in period_starts.items()))
    visible = match_seq.loc[match_seq.clock.between(window[0] * 60, window[1] * 60)].copy()
    st.subheader("Long possessions with little immediate threat")
    left, right = st.columns(2)
    long_seconds = left.slider("Minimum elapsed duration (seconds)", 10, 90, 30, 5)
    low_xt = right.slider("Positive move xT ceiling", .001, .05, .01, .001, format="%.3f")
    quiet = visible.loc[visible.elapsed_seconds.ge(long_seconds) & visible.positive_xt.lt(low_xt) & visible.shots.eq(0)].sort_values("elapsed_seconds", ascending=False)
    columns = ["sequence_key", "team", "period", "possession", "elapsed_seconds", "active_seconds", "passes", "progression", "positive_xt", "net_xt", "score_state"]
    if quiet.empty:
        st.info("No possessions meet these duration, xT and no-shot rules in the selected window. Lower the duration or raise the xT ceiling.")
    else:
        st.dataframe(quiet[columns].round(3), hide_index=True, width="stretch")
    st.caption("Low immediate threat does not mean wasteful. Protecting a lead and drawing opponents out cannot be verified here.")
    visible["style"] = classify(visible, long_seconds=long_seconds, low_xt=low_xt)
    st.caption(f"Exploratory styles: high volume / low threat = elapsed ≥ {long_seconds}s OR ≥ 10 passes, positive xT < {low_xt:.3f}, no shot. Direct / high threat = elapsed ≤ 15s, ≤ 4 passes, positive xT ≥ 0.05. Everything else is Other.")
    style_counts = visible.groupby(["team", "style"], as_index=False).size()
    st.dataframe(style_counts, hide_index=True, width="stretch")
    if visible.empty:
        st.info("No possession starts in this time window. Widen the timeline window to inspect a sequence.")
    else:
        st.subheader("Inspect a possession")
        choices = visible.sort_values("elapsed_seconds", ascending=False).sequence_key.tolist()
        lookup = visible.set_index("sequence_key")
        chosen = st.selectbox("Possession", choices, format_func=lambda key: f"{lookup.loc[key, 'team']} · P{lookup.loc[key, 'period']} #{lookup.loc[key, 'possession']} · {lookup.loc[key, 'elapsed_seconds']:.1f}s · +xT {lookup.loc[key, 'positive_xt']:.3f}")
        one = lookup.loc[chosen]
        st.caption(f"Started {one.score_state}; score at start (home-away) {one.home_score_before}-{one.away_score_before}. Net progression {one.progression:.1f} StatsBomb coordinate units. Style: {one['style']}.")
        selected_actions = match_actions.loc[match_actions.sequence_key.eq(chosen)]
        if selected_actions.empty:
            st.info("This chain has no eligible pass, carry or non-penalty shot to map.")
        else:
            fig = pitch_sequence(selected_actions, f"{one.team} · possession {one.possession} · {one.passes} passes")
            st.pyplot(fig, width="stretch")
            plt.close(fig)
            st.dataframe(selected_actions[["index", "player", "type", "t", "x", "y", "end_x", "end_y", "complete", "xt_delta", "positive_xt", "xg", "score_state"]].round(4), hide_index=True, width="stretch")

with methods:
    st.subheader("Definitions you can inspect")
    st.markdown("""
- **Possession sequence:** contiguous StatsBomb possession ID, bounded by period and split again when the other team passes, carries, shoots, dribbles, miscontrols, is dispossessed or shields the ball. The provider's `possession_team` is the original starter, not necessarily the current attacker. Defensive pressures and tackles do not switch control. A sequence must contain at least one on-ball anchor.
- **Elapsed duration:** first owner on-ball action to last action end, capped at the next possession boundary. Idle gaps remain in this span.
- **Active possession time:** union of recorded owner on-ball action intervals, capped at the boundary. Overlaps count once. Shares divide by both teams' active time.
- **Pass count:** attempted owner passes. A completed StatsBomb pass has no outcome field; unknown and injury-clearance outcomes are failures here.
- **Progression:** last controlled location x minus first location x, in 120 × 80 pitch units. Coordinates already face the event team's attacking right; no halftime rotation.
- **Field tilt:** share of completed passes starting in the attacking third (x ≥ 80). This measures an on-ball territorial proxy.
- **xT:** a 12 × 8 location-only Markov model solving V = r + TV. The reward is empirical non-penalty goals per eligible action. Transitions use completed passes/carries divided by all eligible actions, including failures. Explicit losses absorb at zero. Unobserved cells have value zero.
- **Move value:** signed V(end) − V(start) for successful passes/carries. Positive xT sums only increases; net xT retains backward costs. Neither is the probability that the possession scores. Turnover value is reported separately in pipeline outputs.
- **Score state:** score before the indexed action. Own-goal-against counts once; paired own-goal-for is ignored. Shootouts are excluded. Sequence start state and action-level state have different meanings.
""")
    fig = pitch_model(model)
    st.pyplot(fig, width="stretch")
    plt.close(fig)
    st.caption("Training goal counts drive this surface. It is exploratory and can be noisy in rare cells. The supplied shot xG is used only for descriptive comparison, not xT fitting.")
    st.subheader("Validation and provenance")
    st.json({"coverage": summary["coverage"], "train_matches": summary["train_matches"], "test_matches": summary["test_matches"], "model": summary["model"], "cleaning": summary.get("cleaning", {}), "checks": summary["checks"]})
    st.caption("The Brier score checks held-out one-step shot choice against a training-rate baseline. It does not validate the full xT scoring horizon. Match-separated evaluation avoids event-level leakage; opponent schedules and finishing luck remain confounders.")
    with st.expander("Read the local source audit"):
        st.markdown((ROOT / "docs/source-audit.md").read_text())
    st.markdown("[Original source and licence](https://github.com/hudl/open-data) · [Original xT explanation](https://karun.in/blog/expected-threat.html) · [socceraction reference](https://socceraction.readthedocs.io/en/stable/documentation/valuing_actions/xT.html)")
    st.markdown("""A quiet possession can have tactical value when managing a lead or moving opponents. This event-only analysis cannot establish intent, off-ball pressure, fatigue or causal control. Cross-league comparisons are unadjusted. The data's research terms restrict commercial exploitation and raw-data redistribution; provider data and branding retain their original terms.""")
    if (dataset / "findings.md").exists():
        st.download_button("Download findings report", (dataset / "findings.md").read_text(), "possession-findings.md", "text/markdown")
    if (dataset / "possession-vs-threat.png").exists():
        st.download_button("Download reproducible chart", (dataset / "possession-vs-threat.png").read_bytes(), "possession-vs-threat.png", "image/png")
