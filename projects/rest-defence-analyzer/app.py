"""Run with: streamlit run app.py"""
from pathlib import Path
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from rest_defence.data import ROOT
from rest_defence.pipeline import load_result
from rest_defence.viz import pitch_figure, scatter_figure, timeline_figure

st.set_page_config(page_title="Rest Defence Analyzer",layout="wide",initial_sidebar_state="expanded")
st.markdown("""<style>
.block-container {max-width:1400px;padding-top:3.75rem;}
h1 {letter-spacing:-0.035em;font-size:clamp(2rem,4vw,3.25rem)!important;}
h2 {letter-spacing:-0.02em;}
button:focus-visible,a:focus-visible,input:focus-visible {outline:3px solid #086b67!important;outline-offset:3px;}
@media(max-width:700px){.block-container{padding:1rem;}h1{font-size:2rem!important;}}
</style>""",unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading verified tracking analysis…")
def read_result(path, audit_stamp):
    path=Path(path)
    df,meta,audit=load_result(path)
    return df,meta,audit,pd.read_parquet(path/"snapshots.parquet"),pd.read_parquet(path/"replays.parquet"),pd.read_parquet(path/"timeline.parquet")


def clock(value):
    return f"{int(value)//60:02d}:{int(value)%60:02d}"


def score_label(value):
    return f"{value:.1f}" if pd.notna(value) else "unavailable"


st.caption("DFL OPEN TRACKING / 2022–23 / METHODS WORKBENCH")
st.title("Who protects the attack?")
st.write("Inspect the structure a team leaves behind when it loses possession, then follow the next ten seconds.")

folders=sorted([p for p in (ROOT/"outputs").glob("*") if p.is_dir() and (p/"audit.json").exists() and p.name != "download-smoke"],key=lambda p:(p.name=="sample",p.name))
if not folders:
    st.info("No analysis yet. Run `python -m rest_defence --bundled` for a small real-data sample.")
    st.stop()
with st.sidebar:
    st.header("Match & scope")
    selected=st.selectbox("Analysis",folders,format_func=lambda p:"Three-minute smoke sample" if p.name=="sample" else p.name)
try:
    df,meta,audit,snapshots,replays,timelines=read_result(str(selected),(selected/"audit.json").stat().st_mtime_ns)
except (ValueError,OSError,KeyError) as exc:
    st.error(f"Could not load the analysis: {exc}. Rerun `python -m rest_defence --bundled` or the full-match pipeline.")
    st.stop()
with st.sidebar:
    st.caption(meta["title"].replace(":"," vs "))
    team=st.selectbox("Losing team",["Both teams"]+sorted(df.team_name.unique()))
    period=st.radio("Half",["Both halves","First half","Second half"])
    attack_only=st.checkbox("Attacking losses only",value=True,help="At least two seconds of continuous control, with the pre-loss ball in the opposition half.")
    corroborated=st.checkbox("Require event corroboration",value=False,help="Winning-team action within ±2 s. Event timing remains approximate.")
    score_range=st.slider("Diagnostic score range",0,100,(0,100),help="Fixed heuristic, not a probability. Unscored rows are included when the full range is selected.")
    st.caption("25 Hz turnover detection · 5 Hz player snapshots")
filtered=df.copy()
if team!="Both teams": filtered=filtered[filtered.team_name==team]
if period!="Both halves": filtered=filtered[filtered.period==("firstHalf" if period=="First half" else "secondHalf")]
if attack_only: filtered=filtered[filtered.attacking_scope]
if corroborated: filtered=filtered[filtered.event_corroborated]
score_mask=filtered.vulnerability_score.between(*score_range)
if score_range==(0,100): score_mask|=filtered.vulnerability_score.isna()
filtered=filtered[score_mask]
st.subheader(meta["title"].replace(":"," vs "))
st.caption(f"{audit['scope']} · {audit['analysis']['accepted']} usable turnovers before filters · DFL / Bassek et al. (2025), CC BY 4.0")
if selected.name=="sample": st.warning("This is a three-minute smoke sample. Use a complete match for substantive case analysis.")
if filtered.empty:
    st.info("No turnovers match these filters. Broaden the half, team, score or attacking-loss selection.")
    st.stop()
complete=filtered[~filtered.censored]
cols=st.columns(4)
cols[0].metric("Selected turnovers",len(filtered))
cols[1].metric("Median outfield players behind",f"{filtered.behind_ball.median():.0f}")
cols[2].metric("Ball advanced ≥10 m",f"{int(complete.progressed_10m.sum())} / {len(complete)}")
cols[3].metric("Transition shots",f"{int(complete.shot.sum())} / {len(complete)}")
st.caption(f"Outcome denominators exclude {int(filtered.censored.sum())} censored transitions. Each window ends at the first regain, dead ball, gap, half end or ten seconds. Ball advancement can include a pass in flight.")
options=filtered.sort_values(["vulnerability_score","frame"],ascending=[False,True]).transition_id.tolist()
indexed=filtered.set_index("transition_id")
chosen=st.selectbox("Turnover to inspect",options,format_func=lambda key:f"{clock(indexed.loc[key,'clock_s'])} · {indexed.loc[key,'team_name']} · score {score_label(indexed.loc[key,'vulnerability_score'])} · {int(indexed.loc[key,'behind_ball'])} behind")
row=indexed.loc[chosen]
snap=snapshots[snapshots.transition_id==chosen]
replay=replays[replays.transition_id==chosen]
timeline=timelines[timelines.transition_id==chosen]
tab_structure,tab_evidence,tab_methods=st.tabs(["Structure & transition","Match evidence","Definitions & sources"])
with tab_structure:
    st.subheader(f"{clock(row.clock_s)} · {row.team_name} lose control")
    view=st.radio("Pitch view",["Pre-loss snapshot","Recorded transition frames"],horizontal=True)
    overlays=st.checkbox("Show central space and clear corridors",value=True,disabled=view!="Pre-loss snapshot")
    if view=="Pre-loss snapshot":
        fig=pitch_figure(snap,[row.ball_x,row.ball_y],row.losing_team,meta["length"],meta["width"],
                         f"Structure {row.snapshot_age_s:.2f} s before the turnover",overlays)
    else:
        frames=sorted(set(replay.frame)&set(timeline.frame))
        if not frames:
            st.info("No synchronized replay frames for this transition.")
            st.stop()
        frame=st.select_slider("Recorded frame",options=frames,format_func=lambda n:f"{float(timeline[timeline.frame==n].iloc[0].relative_s):+.2f} s")
        b=timeline[timeline.frame==frame].iloc[0]
        fig=pitch_figure(replay[replay.frame==frame],[b.x,b.y],row.losing_team,meta["length"],meta["width"],f"Recorded positions at {b.relative_s:+.2f} s",False)
    st.pyplot(fig,width="stretch")
    plt.close(fig)
    st.caption("Circles: losing team. Triangles: opposition. Shirt numbers identify players; square rings identify goalkeepers. All views rotate with the losing team's attacking direction. Dotted corridors are geometric candidates; they do not establish pass feasibility.")
    st.caption("The measurements below always describe the pre-loss snapshot, including while scrubbing recorded transition frames.")
    values=st.columns(4)
    values[0].metric("Outfield behind ball",int(row.behind_ball),help="Goalkeeper excluded; at or goal-side of the ball.")
    values[1].metric("Rest structure RMS",f"{row.compactness_rms_m:.1f} m" if pd.notna(row.compactness_rms_m) else "Undefined",help="Root-mean-square distance to centroid. Undefined with fewer than two players.")
    values[2].metric("Central cells exposed",f"{row.central_exposed_fraction:.0%}" if pd.notna(row.central_exposed_fraction) else "No in-pitch cells")
    values[3].metric("Clear forward corridors",f"{int(row.open_lanes)} / {int(row.counter_options)}")
    st.write(f"**Coverage margin:** {int(row.coverage_margin):+d} outfield players. **Goalkeeper behind ball:** {int(row.goalkeeper_behind)}. **Diagnostic score:** {score_label(row.vulnerability_score)} / 100 (fixed heuristic).")
    with st.expander("All snapshot measurements"):
        st.dataframe(pd.DataFrame({"Measurement":["Rest width (m)","Rest depth (m)","Convex hull area (m²)","Mean nearest-defender distance to options (m)","Maximum nearest-defender distance to options (m)"],
                                   "Value":[row.rest_width_m,row.rest_depth_m,row.hull_area_m2,row.nearest_option_mean_m,row.nearest_option_max_m]}),hide_index=True,width="stretch")
        st.caption("Blank distances mean there are no counter options or no behind-ball defenders. Undefined values are never substituted with zero.")
    st.write(f"**Observed outcome:** {row.observed_seconds:.2f} s, ending at `{row.stop_reason}`. Maximum forward ball displacement: {row.progress_m:.1f} m. Shot: {'yes' if row.shot else 'no'}.")
    if row.censored: st.warning("Incomplete observation: this outcome is excluded from summary rates and association charts.")
    st.plotly_chart(timeline_figure(timeline),width="stretch")
    st.caption("This is recorded ball movement at native 25 Hz, anchored to the first new-control frame. The 10 m reference line is a descriptive threshold. Player replay frames are sampled at 5 Hz.")
    st.write(f"**Event corroboration:** {'within ±2 seconds' if row.event_corroborated else 'no action within ±2 seconds'}. Nearest winning-team event: `{row.event_id}`, offset {row.event_delta_s:+.2f} s. Approximate UTC shot alignments in this window: {int(row.approx_shots)}.")
with tab_evidence:
    st.subheader("Pre-loss score and subsequent ball movement")
    st.plotly_chart(scatter_figure(complete),width="stretch")
    st.caption("Each mark is one uncensored selected turnover. Symbol distinguishes whether a shot followed. Association is descriptive within the displayed match; no model was fitted.")
    display=["clock_s","team_name","behind_ball","compactness_rms_m","central_exposed_fraction","open_lanes","vulnerability_score","progress_m","shot","censored","event_corroborated"]
    st.dataframe(filtered[display],hide_index=True,width="stretch")
    st.download_button("Download selected turnovers (CSV)",filtered.to_csv(index=False),file_name="rest-defence-selected.csv",mime="text/csv")
    st.subheader("Tracking possession share")
    st.write({meta["teams"][key]["name"]:f"{value:.1%}" for key,value in meta["possession_share"].items()})
    st.caption("Share of live, valid ball frames with known possession in the loaded source scope. Filters above do not change this match-level denominator.")
with tab_methods:
    st.markdown((ROOT/"docs/methodology.md").read_text())
    st.subheader("Source and processing receipt")
    st.json(audit,expanded=False)
    st.link_button("Original dataset and licence","https://doi.org/10.6084/m9.figshare.28196177.v1")
    st.link_button("Read the data paper","https://doi.org/10.1038/s41597-025-04505-y")
st.divider()
st.caption("Data: Deutsche Fußball Liga (DFL), Bassek, Rein, Weber & Memmert (2025). CC BY 4.0. Coordinates have been rotated and metrics derived. Seven selected matches support method development and match case studies, not league-wide conclusions.")
