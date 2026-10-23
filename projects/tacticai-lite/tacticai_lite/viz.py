"""Evidence-first pitch and rate visualizations."""
from __future__ import annotations

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from mplsoccer import VerticalPitch
import plotly.graph_objects as go

from .analysis import canonical, xy

PAPER = '#FCFBF7'
INK = '#202A26'
GREEN = '#176044'
OCHRE = '#915C12'


def pitch_figure(detail, show_delivery=True):
    event, frame = detail['event'], detail['frame']
    origin = xy(event.get('location'))
    pitch = VerticalPitch(pitch_type='statsbomb', half=True, pitch_color=PAPER, line_color='#67736C', linewidth=1.0)
    fig, ax = pitch.draw(figsize=(9,6))
    fig.set_facecolor(PAPER)
    ax.set_ylim(75,124)
    if origin is None:
        ax.text(40,100,'Corner location unavailable',ha='center',color=INK)
        return fig
    if frame:
        raw = frame.get('visible_area', [])
        if len(raw) >= 6 and len(raw) % 2 == 0:
            poly = [canonical((raw[i],raw[i+1]),origin) for i in range(0,len(raw),2)]
            ax.add_patch(Polygon([(y,x) for x,y in poly],facecolor=GREEN,alpha=.08,edgecolor=GREEN,linestyle='--',zorder=1))
        for teammate, marker, label in [(True,'o','Visible attacker'),(False,'s','Visible defender')]:
            points = [canonical(xy(p['location']),origin) for p in frame.get('freeze_frame',[])
                      if p.get('teammate') is teammate and xy(p.get('location')) and not p.get('actor')]
            if points:
                ax.scatter(*zip(*[(y,x) for x,y in points]),s=95,marker=marker,c=GREEN if teammate else PAPER,
                           edgecolors=GREEN if teammate else OCHRE,linewidths=2,label=label,zorder=3)
        keepers = [canonical(xy(p['location']),origin) for p in frame.get('freeze_frame',[])
                   if p.get('keeper') and xy(p.get('location'))]
        for x,y in keepers:
            ax.text(y,x,'K',ha='center',va='center',fontsize=7,color=INK,zorder=4)
    else:
        ax.text(40,99,'No linked 360 frame\nPlayer positions unavailable',ha='center',va='center',color=INK)
    a = canonical(origin,origin)
    ax.scatter(a[1],a[0],s=95,marker='D',color=INK,label='Corner taker',zorder=4)
    b = xy(event.get('pass',{}).get('end_location'))
    if show_delivery and b:
        b = canonical(b,origin)
        ax.annotate('',xy=(b[1],b[0]),xytext=(a[1],a[0]),arrowprops={'arrowstyle':'->','color':INK,'lw':1.5,'linestyle':':'})
    ax.legend(loc='lower left',bbox_to_anchor=(0,-.04),frameon=False,ncol=2,fontsize=9,labelcolor=INK)
    fig.tight_layout()
    return fig


def rate_plot(table, group='delivery'):
    fig = go.Figure()
    palette = [GREEN,OCHRE]
    for i, (tournament, rows) in enumerate(table.groupby('tournament', sort=True)):
        fig.add_trace(go.Scatter(x=rows.rate, y=rows[group], mode='markers', name=tournament,
            marker={'size':11,'color':palette[i%2],'symbol':'circle' if i%2==0 else 'diamond'},
            error_x={'type':'data','symmetric':False,'array':rows.high-rows.rate,'arrayminus':rows.rate-rows.low,'thickness':1.5},
            customdata=rows[['corners','shots_created','low','high']].to_numpy(),
            hovertemplate='%{y}<br>%{x:.1%} (%{customdata[1]:.0f}/%{customdata[0]:.0f})<br>95% Wilson interval: %{customdata[2]:.1%} to %{customdata[3]:.1%}<extra>%{fullData.name}</extra>'))
    fig.update_layout(height=max(300,100+60*table[group].nunique()), paper_bgcolor=PAPER,plot_bgcolor=PAPER,
        font={'color':INK,'family':'sans-serif','size':14},margin={'l':10,'r':20,'t':30,'b':20},
        xaxis={'title':'Corners producing a shot','tickformat':'.0%','range':[0,1],'gridcolor':'#DDDED6'},
        yaxis={'title':None},legend={'orientation':'h','y':1.22},hovermode='closest')
    return fig
