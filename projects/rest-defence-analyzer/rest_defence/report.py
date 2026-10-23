"""Reproducible static figure and restrained, source-backed technical readout."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .data import ROOT
from .pipeline import load_result
from .viz import INK,PAPER,RED,TEAL


def summarize(df):
    d=df[df.attacking_scope & ~df.censored & df.vulnerability_score.notna()].copy()
    rho=float(spearmanr(d.vulnerability_score,d.progress_m).statistic) if len(d)>=3 and d.vulnerability_score.nunique()>1 and d.progress_m.nunique()>1 else None
    d["score_bin"]=pd.cut(d.vulnerability_score,[0,100/3,200/3,100],labels=["0–33⅓","33⅓–66⅔","66⅔–100"],include_lowest=True)
    bins=d.groupby("score_bin",observed=False).agg(n=("shot","size"),advanced=("progressed_10m","sum"),shots=("shot","sum")).reset_index()
    teams=d.groupby("team_name").agg(n=("shot","size"),advanced=("progressed_10m","sum"),shots=("shot","sum"),median_behind=("behind_ball","median")).reset_index()
    return d,dict(n=len(d),progressed=int(d.progressed_10m.sum()),shots=int(d.shot.sum()),rho=rho,
                  censored=int(df.censored.sum()),unscored=int(df.vulnerability_score.isna().sum()),
                  corroborated=int(d.event_corroborated.sum()),bins=bins.to_dict("records"),teams=teams.to_dict("records"))


def build(path: Path):
    df,meta,audit=load_result(path)
    d,summary=summarize(df)
    if d.empty:
        raise ValueError("No complete attacking-scope transitions to report")
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":11,"text.color":INK,"axes.labelcolor":INK,"axes.edgecolor":"#b2b7b3","xtick.color":INK,"ytick.color":INK,"svg.hashsalt":"rest-defence-v0.1"})
    fig,axes=plt.subplots(1,2,figsize=(13,6),gridspec_kw={"width_ratios":[1.6,1]})
    fig.patch.set_facecolor(PAPER)
    for ax in axes:
        ax.set_facecolor(PAPER)
        ax.spines[["top","right"]].set_visible(False)
    for (name,group),color in zip(d.groupby("team_name"),[TEAL,RED]):
        axes[0].scatter(group.vulnerability_score,group.progress_m,c=color,s=34,alpha=.7,label=name,edgecolors="none")
    shots=d[d.shot]
    axes[0].scatter(shots.vulnerability_score,shots.progress_m,s=135,facecolors="none",edgecolors=INK,linewidths=1.4,label="Shot followed")
    axes[0].set(xlabel="Pre-loss diagnostic score (0–100)",ylabel="Maximum forward ball displacement (m)",xlim=(0,100),ylim=(0,max(10,float(d.progress_m.max())+4)))
    axes[0].set_title("Every eligible attacking loss",loc="left",fontsize=13,weight="bold")
    axes[0].legend(frameon=False,fontsize=9,loc="upper left")
    bins=summary["bins"]
    rates=[100*b["advanced"]/b["n"] if b["n"] else np.nan for b in bins]
    axes[1].bar(range(3),rates,color=TEAL,width=.55)
    axes[1].set(xticks=range(3),xticklabels=["0–33⅓","33⅓–66⅔","66⅔–100"],ylim=(0,100),ylabel="Ball advanced ≥10 m (%)",xlabel="Fixed score bins")
    axes[1].set_title("Observed outcomes by score bin",loc="left",fontsize=13,weight="bold")
    for i,(b,value) in enumerate(zip(bins,rates)):
        axes[1].text(i,3 if np.isnan(value) else value+3,f"{b['advanced']}/{b['n']}",ha="center",fontsize=11)
    fig.suptitle("Rest defence: a geometric score needs outcome validation",x=.065,y=.97,ha="left",fontsize=20,weight="bold")
    rho=summary["rho"]
    rho_label=f"{rho:+.3f}" if rho is not None else "undefined"
    fig.text(.065,.875,f"{meta['title'].replace(':',' vs ')} · {len(d)} attacking losses · Spearman ρ = {rho_label}",fontsize=11)
    fig.text(.065,.07,"Scope: ≥2 s prior control; ball in opposition half; complete bounded transition. Outcomes stop at first regain/dead ball or 10 s.",fontsize=9)
    fig.text(.065,.035,"DFL / Bassek et al. (2025), CC BY 4.0 · doi:10.1038/s41597-025-04505-y · Fixed heuristic; one match; no causal or league-wide claim.",fontsize=9)
    fig.subplots_adjust(left=.07,right=.97,top=.79,bottom=.2,wspace=.32)
    fig.savefig(path/"score-validation.png",dpi=180,facecolor=PAPER)
    fig.savefig(path/"score-validation.svg",facecolor=PAPER,metadata={"Date":None})
    svg=path/"score-validation.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines())+"\n")
    plt.close(fig)
    (path/"findings.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False))
    shares="; ".join(f"{meta['teams'][key]['name']}: {share:.1%}" for key,share in meta["possession_share"].items())
    lines=["# Possession share does not measure rest defence", "",
           f"A reproducible method demonstration using **{meta['title'].replace(':',' vs ')}**. Source scope: {audit['scope']}. Generated from the pipeline outputs, without invented events or tactical intent labels.","",
           "![Pre-loss score and transition outcomes](score-validation.png)","",
           "## What the tracking shows", "",
           f"The pipeline accepted **{len(df)}** stable live-ball possession switches. **{len(d)}** were uncensored attacking losses with a defined score: at least two seconds of prior control and a pre-loss ball in the opposition half. Of these, **{summary['progressed']}** were followed by at least 10 m of forward ball movement and **{summary['shots']}** by a shot before the bounded window ended.","",
           f"Possession shares of live, valid frames with known control were **{shares}**. These are tracking-frame shares, not provider match-statistics or controlled-attack durations.","",
           "| Losing team | Attacking losses | Ball advanced ≥10 m | Shots | Median outfield behind |","|---|---:|---:|---:|---:|"]
    for t in summary["teams"]:
        lines.append(f"| {t['team_name']} | {t['n']} | {t['advanced']} | {t['shots']} | {t['median_behind']:.0f} |")
    lines += ["", "## Did the score identify more dangerous transitions?", "",
              f"The predeclared equal-weight score had a within-match Spearman rank correlation of **{rho_label}** with maximum forward ball displacement. This readout does not validate the score as a predictor. Shots were too sparse in the attacking-loss subset to support a useful shot-risk conclusion.","",
              "| Fixed score bin | Transitions | Ball advanced ≥10 m | Shots |","|---|---:|---:|---:|"]
    for b in bins:
        lines.append(f"| {b['score_bin']} | {b['n']} | {b['advanced']} | {b['shots']} |")
    # Same-count pair illustrates a measurement distinction, without assigning intent.
    counts=d.groupby("behind_ball").size()
    common=counts.idxmax()
    pair=d[d.behind_ball.eq(common)].sort_values("central_exposed_fraction")
    lo,hi=pair.iloc[0],pair.iloc[-1]
    lines += ["", "## What this adds to a possession statistic", "",
              f"Both snapshot `{lo.transition_id}` and `{hi.transition_id}` had **{int(common)} outfield players behind the ball**. Their central-grid exposed fractions were **{lo.central_exposed_fraction:.1%}** and **{hi.central_exposed_fraction:.1%}**, respectively. These are inspectable geometric measurements under the stated thresholds; equal behind-ball counts can describe different spatial protection.","",
              "This establishes why possession share and a behind-ball headcount cannot substitute for spatial inspection. It does **not** establish that either team deliberately used an unsafe structure or that central exposure caused the next attack. Video review, player motion, pass feasibility and more matches are needed for that explanation.","",
              "## Reliability and limits", "",
              f"{summary['corroborated']}/{len(d)} reported attacking losses have a winning-team action within ±2 s of the tracking anchor. Event timing remains approximate, except for available corrected shot frames. {summary['censored']} accepted windows were censored; {summary['unscored']} snapshot scores were undefined because the clipped central grid had no cells. Neither is silently replaced with zero.","",
              "The chart's bins are fixed in advance, contain unequal sample sizes, and are descriptive counts. Turnovers within one match are dependent. Progression can include a pass in flight. The fixed score ignores speed, orientation, aerial travel, offside and marking assignments. No model was trained, no held-out predictive result is claimed, and no causal or league-wide conclusions follow.","",
              "## Reproduce", "", "```sh", "python -m rest_defence --match J03WPY", "python -m rest_defence.report --result outputs/J03WPY", "```", "",
              "Data: **Deutsche Fußball Liga (DFL)**. Bassek, M., Rein, R., Weber, H. & Memmert, D. (2025). *An integrated dataset of spatiotemporal and event data in elite soccer*. Scientific Data 12, 195. [Paper](https://doi.org/10.1038/s41597-025-04505-y); [original data, version 1](https://doi.org/10.6084/m9.figshare.28196177.v1); [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Coordinates are rotated and metrics derived. [Full methodology](../../docs/methodology.md)."]
    (path/"findings.md").write_text("\n".join(lines)+"\n")
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--result",type=Path,default=ROOT/"outputs/J03WPY")
    args=parser.parse_args()
    print(json.dumps(build(args.result),indent=2,ensure_ascii=False))
