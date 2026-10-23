from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from mplsoccer import Pitch
import plotly.express as px
import plotly.graph_objects as go

from .geometry import central_grid, clear_lane

RED="#9f2936"
TEAL="#086b67"
INK="#202c2b"
PAPER="#faf9f5"


def pitch_figure(snapshot, ball_xy, losing_team, length=105., width=68., title="Pre-loss structure", overlays=True):
    pitch=Pitch(pitch_type="custom",pitch_length=length,pitch_width=width,pitch_color=PAPER,line_color="#667571",linewidth=1)
    fig,ax=pitch.draw(figsize=(11,7))
    fig.set_facecolor(PAPER)
    shift=np.array([length/2,width/2])
    ball=np.asarray(ball_xy)
    rest=snapshot[(snapshot.team==losing_team)&~snapshot.is_gk&(snapshot.x<=ball[0])]
    if overlays:
        ax.axvline(ball[0]+length/2,color=INK,linestyle="--",linewidth=1,alpha=.65)
        grid=central_grid(ball,length,width)
        if len(grid):
            from scipy.spatial.distance import cdist
            exposed=cdist(grid,rest[["x","y"]]).min(axis=1)>5 if len(rest) else np.ones(len(grid),dtype=bool)
            ax.scatter(*(grid[exposed]+shift).T,s=12,marker="x",color="#6b6152",alpha=.55)
        opponents=snapshot[(snapshot.team!=losing_team)&~snapshot.is_gk]
        opponents=opponents[(opponents.x<=ball[0]-3)&(np.linalg.norm(opponents[["x","y"]].to_numpy()-ball,axis=1)<=40)]
        defenders=snapshot[(snapshot.team==losing_team)&~snapshot.is_gk][["x","y"]].to_numpy()
        for target in opponents[["x","y"]].to_numpy():
            if clear_lane(ball,target,defenders):
                pitch.lines(ball[0]+length/2,ball[1]+width/2,target[0]+length/2,target[1]+width/2,
                            color=TEAL,linestyle=":",linewidth=1.7,alpha=.7,ax=ax)
    for losing,color,marker in [(True,RED,"o"),(False,TEAL,"^")]:
        group=snapshot[snapshot.team.eq(losing_team)==losing]
        pitch.scatter(group.x+length/2,group.y+width/2,s=260,marker=marker,color=color,edgecolor="white",linewidth=1.2,ax=ax,zorder=5)
        for r in group.itertuples():
            pitch.annotate(str(r.number),xy=(r.x+length/2,r.y+width/2),ha="center",va="center",fontsize=8,color="white",weight="bold",ax=ax,zorder=6)
        keepers=group[group.is_gk]
        pitch.scatter(keepers.x+length/2,keepers.y+width/2,s=350,marker="s",facecolors="none",edgecolors=color,linewidth=1.3,ax=ax,zorder=7)
    pitch.scatter(ball[0]+length/2,ball[1]+width/2,s=90,color=INK,edgecolors="white",linewidths=1.4,ax=ax,zorder=8)
    ax.set_title(title,loc="left",fontsize=16,color=INK,pad=16,weight="bold")
    ax.text(0,-5,"Losing team attacked right →   |   Own goal on the left",fontsize=10,color=INK)
    legend=[Line2D([0],[0],marker="o",color="w",markerfacecolor=RED,markersize=10,label="Losing team"),
            Line2D([0],[0],marker="^",color="w",markerfacecolor=TEAL,markersize=10,label="Counterattacking team"),
            Line2D([0],[0],marker="s",color=INK,markerfacecolor="none",linestyle="none",label="Goalkeeper ring"),
            Line2D([0],[0],marker="x",color="#6b6152",linestyle="none",label="Central cell >5 m from rest defence")]
    ax.legend(handles=legend,loc="upper center",bbox_to_anchor=(.5,-.07),ncol=2,frameon=False,fontsize=9)
    fig.subplots_adjust(bottom=.17)
    return fig


def scatter_figure(df):
    fig=px.scatter(df,x="vulnerability_score",y="progress_m",color="team_name",symbol="shot",
                   color_discrete_sequence=[RED,TEAL],hover_data=["transition_id","behind_ball","open_lanes","observed_seconds"],
                   labels={"vulnerability_score":"Pre-loss diagnostic score (0–100)","progress_m":"Maximum forward ball displacement (m)","team_name":"Losing team","shot":"Shot within bounded window"})
    fig.update_layout(template="plotly_white",height=400,margin=dict(l=15,r=15,t=10,b=10),legend=dict(orientation="h",y=-.25),font=dict(color=INK,size=13))
    fig.update_xaxes(range=[0,100])
    fig.update_yaxes(rangemode="tozero")
    return fig


def timeline_figure(timeline):
    data=timeline[timeline.relative_s>=0].copy()
    fig=go.Figure()
    if len(data):
        fig.add_scatter(x=data.relative_s,y=-(data.x-data.x.iloc[0]),mode="lines",line=dict(color=TEAL,width=2),name="Ball displacement")
    fig.update_layout(template="plotly_white",height=260,margin=dict(l=10,r=15,t=5,b=10),
                      xaxis_title="Seconds since turnover",yaxis_title="Forward ball displacement (m)",font=dict(color=INK,size=13))
    fig.add_hline(y=10,line_dash="dot",line_color=INK)
    fig.update_xaxes(range=[0,10])
    return fig
