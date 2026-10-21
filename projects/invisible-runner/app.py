"""Run with: streamlit run app.py. Downloads are explicit CLI operations."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from invisible_runner.analysis import RunConfig, detect_runs
from invisible_runner.data import sha256
from invisible_runner.viz import pitch_figure, replay_frames, space_timeline
from invisible_runner.report import ATTACK, DEFEND, INK, PAPER

PROJECT = Path(__file__).resolve().parent
st.set_page_config(page_title="The Invisible Runner", layout="wide")
st.html("""<style>
  .stApp { background: #faf8f1; color: #172b29; }
  .block-container { max-width: 1180px; padding-top: 4.5rem; padding-bottom: 3rem; }
  h1 { font-family: Georgia, serif !important; font-weight: 500 !important;
       font-size: clamp(2rem, 5vw, 3rem) !important; }
  h2,h3 { font-weight: 600 !important; }
  button:focus-visible, input:focus-visible, [role=slider]:focus-visible,
  [role=combobox]:focus-visible, summary:focus-visible, a:focus-visible {
    outline: 3px solid #934323 !important; outline-offset: 3px !important; }
  div[data-baseweb=select]>div, div[data-baseweb=input]>div,
  div[data-testid=stNumberInputContainer], div[data-testid=stForm] { border-color:#66746c !important; }
  button { min-height:44px; }
  .stCaption { color: #46554f; }
  @media (max-width: 640px) {
    .block-container { padding: 4.5rem .9rem 2rem; }
    [data-testid=stHorizontalBlock] { flex-wrap:wrap; gap:.5rem; }
    [data-testid=stColumn] { min-width:min(100%, 16rem); flex:1 1 100%; }
  }
</style>""")


@st.cache_data(show_spinner="Loading validated tracking and run data…", max_entries=2)
def load_dataset(path_string: str, modified: float):
    path = Path(path_string)
    manifest = json.loads((path / "manifest.json").read_text())
    if sha256(path / "runs.csv") != manifest["outputs"]["runs_sha256"]:
        raise ValueError("Run CSV checksum differs from its pipeline manifest. Rerun the pipeline.")
    clean_path = Path(manifest["clean_path"])
    audit = json.loads((clean_path.parent / "audit.json").read_text())
    if sha256(clean_path) != audit["clean_sha256"]:
        raise ValueError("Clean tracking checksum differs from its cache receipt. Rerun the pipeline.")
    return manifest, pd.read_csv(path / "runs.csv"), pd.read_parquet(clean_path)


@st.cache_data(show_spinner="Applying run thresholds…", max_entries=6)
def threshold_runs(clean_path: str, modified: float, metadata: dict, config: RunConfig):
    return detect_runs(pd.read_parquet(clean_path), metadata, config)


def reset_replay():
    st.session_state.playing = False
    st.session_state.frame_index = 0


def clock_label(seconds):
    return f"{int(seconds)//60:02d}:{seconds%60:04.1f}"


def value(number, unit="", signed=False):
    if pd.isna(number):
        return "Unavailable"
    return f"{number:+.1f}{unit}" if signed else f"{number:.1f}{unit}"


st.title("The Invisible Runner")
st.write("Measure attacking runs, defender movement and the space around a teammate.")
st.caption("SkillCorner / PySport open data · A-League 2024/25 · Deterministic, retrospective estimates")
datasets = sorted(p.parent for p in (PROJECT / "outputs").glob("*/manifest.json"))
if not datasets:
    st.info("No analyzed match yet. Run the small sample pipeline, then refresh this page.")
    st.code("python -m invisible_runner run --match 1886347 --seconds 300", language="bash")
    st.stop()

selected = st.selectbox("Dataset and scope", datasets, format_func=lambda p: p.name.replace("-", " · "), on_change=reset_replay)
try:
    manifest, original_runs, tracking = load_dataset(str(selected), (selected / "manifest.json").stat().st_mtime)
except (OSError, ValueError, KeyError) as exc:
    st.error(f"Cannot load this dataset: {exc}")
    st.code("python -m invisible_runner run --match 1886347 --seconds 300", language="bash")
    st.stop()

metadata = manifest["metadata"]
config = RunConfig(**manifest["config"])
title = f"{metadata['home_team']['short_name']} vs {metadata['away_team']['short_name']}"
st.subheader(title)
st.caption(f"{metadata['date_time'][:10]} · {manifest['scope']} · Pitch {metadata['pitch_length']} × {metadata['pitch_width']} m")
st.warning("Space changes are geometric associations. Extrapolated positions and other players' movement can explain them; they do not establish causal credit.", icon=None)

with st.expander("Run definition and thresholds"):
    st.write("Contiguous movement at the chosen speed, lasting at least 1 s and progressing at least 3 m toward goal. Team possession comes from in-play phases. The runner must be at least 3 m from the ball and outside their provider possession intervals. Touch-free status is estimated.")
    with st.form("thresholds"):
        c1, c2 = st.columns(2)
        speed = c1.slider("Minimum speed (m/s)", 4.0, 8.0, float(config.speed_mps), .5)
        distance = c2.slider("Minimum path distance (m)", 3.0, 20.0, float(config.min_distance_m), 1.0)
        submitted = st.form_submit_button("Recalculate runs")
        if submitted:
            st.session_state.applied_config = (str(selected), speed, distance)
            reset_replay()
    st.caption("Seven-frame centred smoothing. New thresholds are exploratory; the published report keeps the pipeline defaults.")

applied = st.session_state.get("applied_config")
if applied and applied[0] == str(selected):
    config = replace(config, speed_mps=applied[1], min_distance_m=applied[2])
    runs = threshold_runs(manifest["clean_path"], (selected / "manifest.json").stat().st_mtime, metadata, config)
else:
    runs = original_runs.copy()

team_names = {metadata[key]["id"]: metadata[key]["short_name"] for key in ["home_team", "away_team"]}
c1, c2, c3 = st.columns([1, 1, 1.5])
team = c1.selectbox("Team", ["All"] + list(team_names), format_func=lambda t: team_names.get(t, t), on_change=reset_replay)
kind = c2.selectbox("Run type", ["All", "Behind line", "Wide channel", "Toward space"], on_change=reset_replay)
visibility = c3.selectbox("Observation coverage", ["All estimates", "Runner fully detected", "Runner + context endpoints detected"], on_change=reset_replay)
filtered = runs.copy()
if team != "All":
    filtered = filtered[filtered.team_id.eq(team)]
if kind != "All":
    field = {"Behind line": "behind_line", "Wide channel": "wide_channel", "Toward space": "toward_space"}[kind]
    filtered = filtered[filtered[field].fillna(False).astype(bool)]
if visibility != "All estimates":
    filtered = filtered[filtered.runner_detected_fraction.eq(1)]
if visibility == "Runner + context endpoints detected":
    filtered = filtered[filtered.context_endpoint_detected_fraction.eq(1) & filtered.ball_endpoint_detected]

valid = filtered.dropna(subset=["free_area_delta_m2"])
run_noun = "run" if len(filtered) == 1 else "runs"
st.write(f"**{len(filtered)} {run_noun}** under the current filters · {len(valid)} with receiving-space estimates · speed ≥{config.speed_mps:g} m/s · distance ≥{config.min_distance_m:g} m")
export = filtered.to_csv(index=False)
st.download_button("Download filtered runs (CSV)", export, file_name=f"invisible-runner-{metadata['id']}-filtered.csv", mime="text/csv")
if filtered.empty:
    st.info("No runs meet these filters. Select All estimates, choose another run type or lower the thresholds.")
else:
    options = filtered.sort_values(["start_frame", "player_id"]).run_id.tolist()
    lookup = filtered.set_index("run_id", drop=False)
    run_id = st.selectbox("Run to inspect", options,
                          format_func=lambda rid: f"{lookup.loc[rid].player_name} · {clock_label(lookup.loc[rid].start_clock_s)} · {lookup.loc[rid].distance_m:.1f} m",
                          on_change=reset_replay)
    run = lookup.loc[run_id]
    clip = tracking[tracking.period.eq(run.period) & tracking.frame.between(run.start_frame, run.end_frame)]
    frames, timeline = replay_frames(clip, run, metadata, config)
    st.write(f"**{run.player_name}** · {value(run.duration_s, ' s')} · peak {value(run.peak_speed_mps, ' m/s')} · runner detected {run.runner_detected_fraction:.0%}")

    if "playing" not in st.session_state:
        reset_replay()

    def set_playing(state):
        st.session_state.playing = state
        if state and st.session_state.frame_index == len(frames) - 1:
            st.session_state.frame_index = 0

    @st.fragment(run_every=.5 if st.session_state.playing else None)
    def replay():
        a, b, c = st.columns(3)
        if a.button("Play run", disabled=st.session_state.playing):
            set_playing(True)
            st.rerun()
        if b.button("Pause replay", disabled=not st.session_state.playing):
            set_playing(False)
            st.rerun()
        if c.button("Return to start"):
            reset_replay()
            st.rerun()
        if st.session_state.playing:
            st.session_state.frame_index = min(st.session_state.frame_index + 1, len(frames)-1)
            if st.session_state.frame_index == len(frames)-1:
                st.session_state.playing = False
                st.rerun()
        st.session_state.frame_index = min(st.session_state.frame_index, len(frames)-1)
        index = st.slider("Replay frame", 0, len(frames)-1, key="frame_index",
                           format="%d", help="Use arrow keys to inspect the replay without animation.")
        st.plotly_chart(pitch_figure(frames[index], run, clip, metadata), width="stretch",
                        config={"displayModeBar": False}, key="pitch-replay")
        current = timeline.iloc[index]
        st.caption(f"{current.elapsed_s:.1f} s into run · estimated free patch {value(current.free_area_m2, ' m²')}")
    replay()
    st.caption("Star: runner · diamond: selected teammate · teal: attacking team · rust: opposition · filled: detected · hollow: extrapolated. Cells: pale teal already free, dark teal newly free, rust no longer free.")
    defender_count = str(int(run.nearby_defender_count)) if pd.notna(run.nearby_defender_count) else "unavailable"
    st.write(f"Selected teammate: **{run.teammate_name if pd.notna(run.teammate_name) else 'unavailable'}**. Fixed-patch change: **{value(run.free_area_delta_m2, ' m²', True)}**. Nearby defenders: **{defender_count}**; mean displacement: **{value(run.defender_displacement_m, ' m')}**.")
    context_visibility = f"{run.context_endpoint_detected_fraction:.0%}" if pd.notna(run.context_endpoint_detected_fraction) else "unavailable"
    st.caption(f"Context players detected at endpoints: {context_visibility}. Runner separation change: {value(run.runner_separation_delta_m, ' m', True)}. Ball detected at both endpoints: {'yes' if run.ball_endpoint_detected else 'no'}.")
    if timeline.free_area_m2.notna().any():
        st.plotly_chart(space_timeline(timeline), width="stretch", config={"displayModeBar": False})
    else:
        st.info("Receiving-space timeline unavailable: incomplete contextual tracking or no eligible teammate.")
    st.caption("Free patch: 1 m² cell centres within 6 m of the selected teammate's starting position, at least 3 m from every opponent. Same cells at every frame; no pass or reachability model.")

    st.subheader("Space change across the selected runs")
    if len(valid):
        chart_rows = valid.copy()
        chart_rows["Runner visibility"] = chart_rows.runner_detected_fraction.eq(1).map({True: "Fully detected", False: "Includes extrapolation"})
        fig = px.scatter(chart_rows, x="distance_m", y="free_area_delta_m2", color="Runner visibility", symbol="Runner visibility",
                         color_discrete_map={"Fully detected": ATTACK, "Includes extrapolation": DEFEND},
                         symbol_map={"Fully detected": "circle", "Includes extrapolation": "x"}, hover_name="player_name",
                         hover_data={"start_clock_s": ":.1f", "context_endpoint_detected_fraction": ":.0%"},
                         labels={"distance_m": "Run distance (m)", "free_area_delta_m2": "Fixed-patch change (m²)",
                                 "start_clock_s": "Match clock (s)", "context_endpoint_detected_fraction": "Context detected"})
        fig.add_hline(y=0, line_color=INK)
        fig.update_layout(paper_bgcolor=PAPER, plot_bgcolor=PAPER, height=350, font=dict(color=INK), margin=dict(t=15),
                           legend=dict(orientation="h", y=1.15, title=""))
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    else:
        st.info("No receiving-space estimates are available under these filters.")
    with st.expander("Inspect exact run records"):
        st.dataframe(filtered[["player_name", "start_clock_s", "distance_m", "behind_line", "wide_channel", "toward_space", "free_area_delta_m2", "runner_detected_fraction", "context_endpoint_detected_fraction"]],
                     column_config={
                         "player_name": "Player", "behind_line": "Behind line", "wide_channel": "Wide channel", "toward_space": "Toward space",
                         "start_clock_s": st.column_config.NumberColumn("Match clock (s)", format="%.1f"),
                         "distance_m": st.column_config.NumberColumn("Distance (m)", format="%.1f"),
                         "free_area_delta_m2": st.column_config.NumberColumn("Patch change (m²)", format="%.1f"),
                         "runner_detected_fraction": st.column_config.NumberColumn("Runner detected (0–1)", format="%.2f"),
                         "context_endpoint_detected_fraction": st.column_config.NumberColumn("Context detected (0–1)", format="%.2f")},
                     width="stretch", hide_index=True)

with st.expander("Methods, data quality and reproducibility"):
    st.write("The defensive line is the second deepest outfield opponent along the attacking direction. A crossing starts at least 0.5 m in front and ends at least 0.5 m beyond that moving line. Wide-channel runs finish in the outer 20% of pitch width on either side and move outward at least 2 m. Toward-space runs gain at least 2 m of nearest-opponent clearance. Categories overlap.")
    st.write("The teammate is chosen using the starting state: nearest outfield teammate, excluding the runner, no more than 10 m behind. Context metrics require matching complete opponent rosters at endpoints, with no tracking segment breaks. Nearby defenders start within 10 m; displacement is measured for the same individuals.")
    st.write("Centred smoothing is retrospective. Missing carrier identities and extrapolated ball positions limit off-ball classification. Space estimates omit offside, pass accessibility and player reactions. No fitted or causal model is used. Future learned models must split by match before fitting preprocessing or tuning.")
    st.json({"scope": manifest["scope"], "audit": manifest["audit"], "provider_overlap_at_published_defaults": manifest["validation"], "speed_sensitivity_at_published_defaults": manifest["sensitivity"]}, expanded=False)
    st.caption("Provider labels are derived from the same source tracking. Overlap is descriptive agreement, not accuracy against human ground truth. Published sensitivity and overlap above do not change when exploratory thresholds change.")
    st.markdown(f"[Source revision](https://github.com/SkillCorner/opendata/tree/{manifest['revision']}) · [Source license](https://github.com/SkillCorner/opendata/blob/{manifest['revision']}/LICENSE)")
    st.download_button("Download source provenance (JSON)", (selected / "provenance.json").read_text(), "provenance.json", mime="application/json")
