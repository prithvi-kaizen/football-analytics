"""Pitch replay and time-resolved fixed-patch space calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .analysis import RunConfig, free_area, receiving_patch
from .data import FPS, attack_sign
from .report import ATTACK, DEFEND, INK, PAPER


def replay_frames(tracking: pd.DataFrame, run: pd.Series, metadata: dict,
                  config: RunConfig) -> tuple[list[dict], pd.DataFrame]:
    clip = tracking[tracking.period.eq(run.period) & tracking.frame.between(run.start_frame, run.end_frame)]
    frame_ids = sorted(set(range(int(run.start_frame), int(run.end_frame) + 1, 5)) | {int(run.end_frame)})
    start = clip[clip.frame.eq(run.start_frame)].dropna(subset=["sx", "sy"])
    teammate = start[start.player_id.eq(run.teammate_id)]
    patch = (receiving_patch(teammate.iloc[0][["sx", "sy"]].to_numpy(dtype=float),
                              metadata["pitch_length"], metadata["pitch_width"], config)
             if len(teammate) else np.empty((0, 2)))
    baseline_opponents = start[start.team_id.ne(run.team_id)].sort_values("player_id")
    baseline_ids = baseline_opponents.player_id.tolist()
    if len(patch) and len(baseline_opponents):
        from scipy.spatial.distance import cdist
        initial_free = cdist(patch, baseline_opponents[["sx", "sy"]]).min(axis=1) >= config.control_radius_m
    else:
        initial_free = np.zeros(len(patch), dtype=bool)
    frames, area_rows = [], []
    for frame_id in frame_ids:
        shot = clip[clip.frame.eq(frame_id)].dropna(subset=["sx", "sy"])
        opp = shot[shot.team_id.ne(run.team_id)].sort_values("player_id")
        valid = (bool(run.context_valid) and len(patch) > 0 and opp.player_id.tolist() == baseline_ids
                 and opp.segment.tolist() == baseline_opponents.segment.tolist())
        if valid:
            current_free = cdist(patch, opp[["sx", "sy"]]).min(axis=1) >= config.control_radius_m
            stable = patch[current_free & initial_free]
            gained = patch[current_free & ~initial_free]
            lost = patch[~current_free & initial_free]
            area = free_area(patch, opp[["sx", "sy"]].to_numpy(), config)
        else:
            stable = gained = lost = np.empty((0, 2))
            area = np.nan
        frames.append(dict(frame=frame_id, shot=shot, stable=stable, gained=gained, lost=lost))
        area_rows.append(dict(frame=frame_id, elapsed_s=(frame_id - run.start_frame) / FPS, free_area_m2=area))
    return frames, pd.DataFrame(area_rows)


def pitch_figure(frame: dict, run: pd.Series, tracking: pd.DataFrame, metadata: dict) -> go.Figure:
    length, width = metadata["pitch_length"], metadata["pitch_width"]
    fig = go.Figure()
    shapes = [dict(type="rect", x0=-length/2, x1=length/2, y0=-width/2, y1=width/2),
              dict(type="line", x0=0, x1=0, y0=-width/2, y1=width/2),
              dict(type="circle", x0=-9.15, x1=9.15, y0=-9.15, y1=9.15)]
    for sign in [-1, 1]:
        for depth, half_width in [(16.5, 20.16), (5.5, 9.16)]:
            shapes.append(dict(type="rect", x0=sign*length/2, x1=sign*(length/2-depth), y0=-half_width, y1=half_width))
    for shape in shapes:
        fig.add_shape(**shape, line=dict(color="#77847d", width=1), layer="below")
    for label, key, color, opacity in [("Already free", "stable", ATTACK, .16),
                                       ("Newly free", "gained", ATTACK, .55),
                                       ("No longer free", "lost", DEFEND, .45)]:
        cells = frame[key]
        fig.add_trace(go.Scatter(x=cells[:, 0], y=cells[:, 1], mode="markers", name=label,
                                 marker=dict(symbol="square", size=7, color=color, opacity=opacity),
                                 hoverinfo="skip", showlegend=False))
    path = tracking[tracking.player_id.eq(run.player_id) & tracking.frame.between(run.start_frame, frame["frame"])]
    fig.add_trace(go.Scatter(x=path.sx, y=path.sy, mode="lines", name="Run path", showlegend=False,
                             line=dict(color=INK, width=3), hoverinfo="skip"))
    shot = frame["shot"]
    for team in [run.team_id, next(t for t in [metadata["home_team"]["id"], metadata["away_team"]["id"]] if t != run.team_id)]:
        for detected in [True, False]:
            group = shot[shot.team_id.eq(team) & shot.detected.eq(detected)]
            color = ATTACK if team == run.team_id else DEFEND
            status = "detected" if detected else "extrapolated"
            fig.add_trace(go.Scatter(x=group.sx, y=group.sy, mode="markers", showlegend=False,
                                     marker=dict(color=color, size=13, symbol="circle" if detected else "circle-open", line=dict(width=2)),
                                     text=group.player_name + ": " + status, hovertemplate="%{text}<extra></extra>"))
    for pid, symbol, label in [(run.player_id, "star", "Runner"), (run.teammate_id, "diamond-open", "Selected teammate")]:
        player = shot[shot.player_id.eq(pid)]
        fig.add_trace(go.Scatter(x=player.sx, y=player.sy, mode="markers", name=label, showlegend=False,
                                 marker=dict(color=INK, symbol=symbol, size=22, line=dict(width=2)),
                                 text=player.player_name, hovertemplate=f"{label}: %{{text}}<extra></extra>"))
    ball = shot.iloc[0] if len(shot) else None
    if ball is not None:
        fig.add_trace(go.Scatter(x=[ball.ball_x], y=[ball.ball_y], mode="markers", name="Ball", showlegend=False,
                                 marker=dict(color=INK, size=8, symbol="circle" if ball.ball_detected else "circle-open"),
                                 hovertemplate="Ball<extra></extra>"))
    direction = "right" if attack_sign(metadata, int(run.team_id), int(run.period)) == 1 else "left"
    fig.update_layout(paper_bgcolor=PAPER, plot_bgcolor=PAPER, font=dict(color=INK, family="Arial"),
                       height=460, margin=dict(l=10, r=10, t=30, b=10),
                       title=dict(text=f"Frame {frame['frame']} · attacking {direction}", font=dict(size=14)),
                       xaxis=dict(range=[-length/2-3, length/2+3], visible=False, fixedrange=True),
                       yaxis=dict(range=[-width/2-3, width/2+3], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1),
                       dragmode=False, uirevision=run.run_id)
    return fig


def space_timeline(rows: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(x=rows.elapsed_s, y=rows.free_area_m2, mode="lines+markers",
                               line=dict(color=ATTACK, width=2), marker=dict(size=5), connectgaps=False,
                               hovertemplate="%{x:.1f} s: %{y:.0f} m²<extra></extra>"))
    fig.update_layout(height=230, paper_bgcolor=PAPER, plot_bgcolor=PAPER,
                       margin=dict(l=30, r=10, t=10, b=40), font=dict(color=INK),
                       xaxis_title="Elapsed run time (s)", yaxis_title="Free patch (m²)",
                       yaxis=dict(rangemode="tozero"))
    return fig
