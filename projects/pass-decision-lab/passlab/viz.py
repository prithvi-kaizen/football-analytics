"""Pitch and diagnostic figures with observation/estimate distinctions."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import plotly.graph_objects as go
from matplotlib.lines import Line2D
from mplsoccer import Pitch

from .models import calibration_table
from .report import INK, PAPER, RUST, TEAL


def pitch_figure(scene: dict, highlight: str | None = None):
    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color=PAPER,
        line_color="#7d8989",
        linewidth=0.8,
        pad_top=3,
        pad_bottom=3,
        pad_left=3,
        pad_right=3,
    )
    fig, ax = pitch.draw(figsize=(11, 7.4), tight_layout=False)
    fig.set_facecolor(PAPER)
    area = scene.get("visible_area", [])
    if area and len(area) >= 6 and len(area) % 2 == 0:
        polygon = np.array(area).reshape(-1, 2)
        ax.fill(polygon[:, 0], polygon[:, 1], color=TEAL, alpha=0.065, zorder=1)
    origin = scene["origin"]
    for teammate in scene["teammates"]:
        target = teammate["location"]
        selected = teammate["candidate_id"] == highlight
        ax.plot(
            [origin[0], target[0]],
            [origin[1], target[1]],
            "--",
            color=TEAL,
            lw=2.7 if selected else 0.9,
            alpha=1 if selected else 0.35,
            zorder=2,
        )
        pitch.scatter(
            *target,
            s=140 if selected else 95,
            marker="o",
            facecolor=PAPER,
            edgecolor=TEAL,
            linewidth=2,
            ax=ax,
            zorder=5,
        )
        ax.annotate(
            teammate["candidate_id"],
            target,
            xytext=(0, -13),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color=INK,
            bbox={"facecolor": PAPER, "edgecolor": "none", "pad": 0.5},
            zorder=6,
        )
    if scene["opponents"]:
        opponents = np.asarray(scene["opponents"])
        pitch.scatter(
            opponents[:, 0],
            opponents[:, 1],
            s=65,
            marker="s",
            facecolor=RUST,
            edgecolor=PAPER,
            linewidth=0.7,
            ax=ax,
            zorder=4,
        )
    endpoint = scene.get("actual_end")
    if endpoint and len(endpoint) >= 2 and np.isfinite(endpoint[:2]).all():
        pitch.arrows(*origin, *endpoint[:2], width=2, headwidth=4, headlength=4, color=RUST, ax=ax, zorder=4)
    pitch.scatter(*origin, s=150, marker="o", facecolor=INK, edgecolor=PAPER, linewidth=1.5, ax=ax, zorder=7)
    ax.set_title(
        "The pass played. The teammates visible.",
        fontfamily="DejaVu Serif",
        fontsize=20,
        color=INK,
        loc="left",
        pad=20,
    )
    legend = [
        Line2D([0], [0], color=RUST, lw=2, label="Recorded pass end"),
        Line2D([0], [0], color=TEAL, ls="--", label="Hypothetical ground pass"),
        Line2D([0], [0], marker="s", color=RUST, ls="", label="Visible opponent"),
        Line2D([0], [0], marker="o", color=INK, ls="", label="Passer"),
    ]
    fig.legend(
        handles=legend,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.05),
        ncol=2,
        frameon=False,
        fontsize=10,
        labelcolor=INK,
    )
    fig.text(
        0.1,
        0.012,
        "Attack direction: left to right. Shading: known camera area. T labels are anonymous, local to this frame.",
        fontsize=9,
        color=INK,
    )
    fig.subplots_adjust(bottom=0.19, top=0.91)
    return fig


def calibration_plot(predictions):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfect calibration",
            line={"dash": "dash", "color": "#69757a"},
        )
    )
    for i, (model_id, group) in enumerate(predictions.groupby("model_id", sort=True)):
        c = calibration_table(group)
        fig.add_trace(
            go.Scatter(
                x=c.predicted,
                y=c.observed,
                mode="lines+markers",
                name=model_id,
                customdata=c[["n"]].to_numpy(),
                line={"color": TEAL if i % 2 else RUST, "dash": "solid" if i < 2 else "dot"},
                marker={"symbol": ["circle", "square", "diamond", "cross", "triangle-up"][i % 5]},
                hovertemplate="Mean xPass %{x:.3f}<br>Observed %{y:.3f}<br>Passes %{customdata[0]}<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_layout(
        xaxis_title="Mean predicted completion",
        yaxis_title="Observed completion",
        xaxis_range=[0, 1],
        yaxis_range=[0, 1],
        paper_bgcolor=PAPER,
        plot_bgcolor=PAPER,
        font={"color": INK},
        height=480,
        margin={"t": 20, "b": 50, "l": 50, "r": 20},
        legend={"orientation": "h", "y": -0.25},
        hovermode="closest",
    )
    return fig
