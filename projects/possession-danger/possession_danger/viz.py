from __future__ import annotations

import os
from pathlib import Path
import tempfile
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "possession-danger-mpl"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

TEAL, RUST, PAPER, INK = "#006B68", "#A34526", "#FAF8F3", "#252A28"


def style(fig, height=420):
    fig.update_layout(template="plotly_white", paper_bgcolor=PAPER, plot_bgcolor=PAPER,
                      font=dict(color=INK, size=14), margin=dict(l=20, r=25, t=30, b=40),
                      height=height, legend_title_text="", hovermode="closest")
    return fig


def scatter(totals, focus, metric="threat_share"):
    data = totals.copy()
    data["group"] = np.where(data.team.eq(focus), focus, "Other teams")
    fig = px.scatter(data, x="possession_pct", y=metric, color="group", symbol="group",
                     symbol_map={focus: "diamond", "Other teams": "circle"},
                     color_discrete_map={focus: TEAL, "Other teams": RUST},
                     hover_name="team", hover_data={"date": True, "match_id": True, "xt_per_100": ":.2f", "group": False},
                     labels={"possession_pct": "Active possession-time share (%)", "threat_share": "Positive move xT share (%)", "field_tilt": "Final-third completed-pass share (%)"})
    fig.update_traces(marker=dict(size=10, opacity=.7, line=dict(width=.5, color=INK)))
    fig.add_shape(type="line", x0=0, x1=100, y0=0, y1=100, line=dict(color="#777A73", dash="dash", width=1))
    fig.update_xaxes(range=[0, 100])
    fig.update_yaxes(range=[0, 100])
    return style(fig, 500)


def timeline(seq, teams, minute_range):
    fig = go.Figure()
    for team, color in zip(teams, [TEAL, RUST]):
        group = seq.loc[seq.team.eq(team)].sort_values("clock")
        fig.add_trace(go.Scatter(x=group.clock / 60, y=group.positive_xt.cumsum(), name=team,
                                mode="lines+markers", line=dict(color=color, shape="hv"),
                                customdata=group[["possession", "period", "passes", "positive_xt", "score_state"]].to_numpy(),
                                hovertemplate="%{fullData.name}<br>Period %{customdata[1]}, possession %{customdata[0]}<br>%{customdata[2]} passes; +xT %{customdata[3]:.3f}<br>Started %{customdata[4]}<extra></extra>"))
    fig.update_xaxes(title="Elapsed playing clock (minutes, includes stoppage time)", range=minute_range)
    fig.update_yaxes(title="Cumulative positive move xT", rangemode="tozero")
    return style(fig)


def pitch_sequence(actions, title):
    pitch = Pitch(pitch_type="statsbomb", pitch_color=PAPER, line_color="#6C746D", linewidth=1)
    fig, ax = pitch.draw(figsize=(10, 6))
    fig.set_facecolor(PAPER)
    moves = actions.loc[actions.type.isin(["Pass", "Carry"]) & actions.end_x.notna()]
    for number, (_, row) in enumerate(moves.iterrows(), 1):
        color = TEAL if row.complete else RUST
        pitch.arrows(row.x, row.y, row.end_x, row.end_y, ax=ax, color=color, width=1.5,
                     linestyle="--" if row.type == "Carry" else "-", alpha=.8)
        pitch.annotate(str(number), xy=(row.x, row.y), ax=ax, fontsize=8, color=INK)
    shots = actions.loc[actions.type.eq("Shot")]
    if len(shots):
        pitch.scatter(shots.x, shots.y, s=120, marker="*", color=RUST, ax=ax, label="Shot")
    ax.set_title(title, loc="left", color=INK, fontsize=12)
    fig.text(.06, .025, "Attacking right | solid: pass; dashed: carry; rust: failed move or shot; numbers: move order", fontsize=9, color=INK)
    return fig


def pitch_model(model):
    pitch = Pitch(pitch_type="statsbomb", pitch_color=PAPER, line_color=INK, line_zorder=2)
    fig, ax = pitch.draw(figsize=(10, 5.5))
    fig.set_facecolor(PAPER)
    grid = np.array(model["value"])
    mesh = ax.pcolormesh(np.linspace(0, 120, model["nx"] + 1), np.linspace(0, 80, model["ny"] + 1), grid,
                         cmap="YlGnBu", vmin=0, vmax=max(.01, grid.max()), shading="flat")
    fig.colorbar(mesh, ax=ax, shrink=.7, label="Fitted xT probability")
    ax.set_title("Location-only xT, fitted on training matches", loc="left", fontsize=12)
    return fig
