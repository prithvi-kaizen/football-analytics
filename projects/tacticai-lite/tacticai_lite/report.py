"""Rebuild a public aggregate chart and findings from local pipeline outputs."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
import pandas as pd

from .analysis import summary
from .viz import GREEN, INK, PAPER

ROOT = Path(__file__).resolve().parents[1]


def main():
    corners = pd.read_csv(ROOT/'outputs/corners.csv')
    info = json.loads((ROOT/'outputs/manifest.json').read_text())
    model = json.loads((ROOT/'outputs/model.json').read_text())
    table = summary(corners[corners.delivery.ne('Direct shot')])
    destination = ROOT/'reports'
    destination.mkdir(exist_ok=True)
    table.to_csv(destination/'delivery_summary.csv',index=False)
    tournaments = sorted(corners.tournament.unique())
    order = ['Inswinging','Outswinging','Short','Straight','Other / unknown']
    fig, axes = plt.subplots(1,len(tournaments),figsize=(12,6),squeeze=False,sharex=True,sharey=True)
    fig.set_facecolor(PAPER)
    for ax, tournament in zip(axes[0],tournaments):
        ax.set_facecolor(PAPER)
        rows = table[table.tournament==tournament].set_index('delivery')
        for i, category in enumerate(order):
            if category not in rows.index:
                continue
            r=rows.loc[category]
            ax.errorbar(r.rate,i,xerr=[[r.rate-r.low],[r.high-r.rate]],fmt='o',markersize=7,
                        color=GREEN,ecolor=GREEN,elinewidth=1.7,capsize=3)
            ax.text(.98,i,f'{int(r.shots_created)}/{int(r.corners)}',ha='right',va='center',fontsize=10,color=INK)
        ax.set_title(tournament,loc='left',fontsize=13,fontweight='bold',color=INK,pad=18)
        ax.set_yticks(range(len(order)),order)
        ax.set_xlim(0,1)
        ax.set_xticks([0,.25,.5,.75,1],['0%','25%','50%','75%','100%'])
        ax.set_xlabel('Corners producing a shot',color=INK,labelpad=10)
        ax.grid(axis='x',alpha=.18)
        ax.spines[['top','right']].set_visible(False)
        ax.spines[['bottom','left']].set_color('#67736C')
        ax.tick_params(colors=INK)
    axes[0,0].invert_yaxis()
    fig.suptitle(f'Shot creation after corners: {info["horizon_seconds"]:g}-second window',x=.16,y=.98,ha='left',fontsize=18,fontweight='bold',color=INK)
    fig.text(.16,.035,'Same possession and period; stops at restart/stoppage. Points: observed rates; bars: 95% Wilson intervals.\n'
             'Labels: shot-producing corners / observed pass-corners. Direct shots excluded; intervals assume independent corners.\n'
             f'Data: StatsBomb Open Data | {len(info["matches"])} matches | revision {info["revision"][:12]}',fontsize=9,color=INK,linespacing=1.6)
    logo=plt.imread(ROOT/'assets/SB - Icon Lockup - Colour positive.png')
    logo_ax=fig.add_axes([.80,.015,.17,.10]);logo_ax.imshow(logo);logo_ax.axis('off')
    fig.subplots_adjust(left=.16,right=.98,top=.84,bottom=.24,wspace=.14)
    fig.savefig(destination/'corner-shot-creation.png',dpi=180,facecolor=PAPER)
    plt.close(fig)
    lines=['# TacticAI Lite: what public corner data can tell us','',
        'I built a simplified, open-data corner-kick intelligence tool inspired by TacticAI. It links event sequences to partial 360 snapshots, groups visible configurations and checks a simple shot-creation baseline. It does not reproduce TacticAI’s proprietary data, model or counterfactual suggestions.','',
        '## Data and scope','',
        f"The pinned StatsBomb revision `{info['revision']}` contains the selected {len(info['matches'])} matches. The pipeline extracted {len(corners)} corners; {int(corners.has_360.sum())} ({corners.has_360.mean():.1%}) have a linked frame. {info['censored']} outcomes were censored. {info['invalid_players']} off-pitch or otherwise invalid player entries were excluded from the corner frames, rather than clipped into the pitch.", '',
        '## Observed results','',
        '| Tournament | Corners | Shot-producing corners | Rate | Linked frames |','|---|---:|---:|---:|---:|']
    for tournament,rows in corners.groupby('tournament'):
        observed=rows[rows.shot_created.notna()]
        lines.append(f"| {tournament} | {len(rows)} | {int(observed.shot_created.sum())} / {len(observed)} | {observed.shot_created.mean():.1%} | {int(rows.has_360.sum())} |")
    lines += ['', '![Shot creation by delivery](corner-shot-creation.png)', '',
        '| Tournament | Delivery | Shots / corners | Rate | 95% Wilson interval |','|---|---|---:|---:|---:|']
    for r in table.itertuples():
        lines.append(f'| {r.tournament} | {r.delivery} | {r.shots_created}/{r.corners} | {r.rate:.1%} | {r.low:.1%} to {r.high:.1%} |')
    if (destination/'window_sensitivity.csv').exists():
        sensitivity=pd.read_csv(destination/'window_sensitivity.csv')
        lines += ['', 'The shot-window threshold changes the measured rate. Keeping possession/stoppage rules fixed:', '',
                  '| Tournament | Window | Shots / corners | Rate |','|---|---:|---:|---:|']
        for r in sensitivity.itertuples():
            lines.append(f'| {r.tournament} | {r.horizon_seconds} s | {r.shot_created}/{r.corners} | {r.rate:.1%} |')
    lines += ['', f"The {int(corners.delivery.eq('Direct shot').sum())} directly shot corners are included in the overall counts but excluded from this delivery chart/table and the classifier. They make the shot outcome positive by definition, so their 100% shot rate cannot be compared as evidence of a better delivery tactic.", '',
        'These are associations under a declared event definition. They do not establish that changing delivery would change shot probability. Small categories and within-match dependence make tactical rankings unreliable. Wilson intervals describe per-corner uncertainty and do not account for that dependence. The two tournaments remain separate because their player populations and years differ.', '',
        '## A modest model check','']
    if model['status']=='evaluated':
        lines += [f"The fixed whole-match holdout used {len(model['train_matches'])} training matches ({model['train_corners']} frame-eligible corners) and {len(model['test_matches'])} held-out matches ({model['test_corners']} corners). There is no match overlap. Median imputation, missingness indicators and scaling were fitted on training data only. Logistic regression uses only spatial/visibility features from the kick’s own frame; it excludes delivery, pass endpoints, identities, future events and outcomes.",'',
            '| Model | Brier score (lower is better) | Log loss (lower is better) | ROC AUC | Average precision |','|---|---:|---:|---:|---:|']
        for label,metrics in model['metrics'].items():
            vals=[f'{metrics[k]:.4f}' if metrics[k] is not None else 'Unavailable' for k in ['brier','log_loss','roc_auc','average_precision']]
            lines.append('| '+label+' | '+' | '.join(vals)+' |')
        delta=model['metrics']['constant']['brier']-model['metrics']['logistic']['brier']
        lines += ['',f"Logistic regression {'improved' if delta>0 else 'did not improve'} Brier score relative to the constant training-rate baseline on this split (difference: {delta:+.4f}, positive favours logistic). One split is an exploratory check, not evidence of robust superiority. No hyperparameters were tuned on the holdout. Team overlap across different matches and frame-availability selection remain limitations."]
    else:
        lines += [model.get('reason','Insufficient data for the classifier.')]
    lines += ['', '## Configuration search','',
        'K-means groups eligible corners using visible attacking/defending counts, centroids, lateral spread, nearest-defender distances and camera coverage. It does not use outcomes. The cluster fit describes this dataset, including its visibility patterns; cluster IDs are not tactical labels or inferred routines. The app lets a reader inspect each linked frame and its subsequent event sequence before making any interpretation.', '',
        '## Method, assumptions and limits','',
        f"A corner is a Pass or direct Shot with type Corner, in periods 1–4. Shot creation means at least one same-team shot at elapsed time 0 to {info['horizon_seconds']:g} seconds, within the same period and possession, before a restart, ball-out event or stoppage. Advantage fouls continue. A goal terminates the sequence. Multiple shots count once. A recording ending early without a terminal event remains unknown, rather than negative.", '',
        f"Inswinging, outswinging and straight labels come from the recorded technique. Short means a pass length ≤{info['short_threshold_units']:g} standardized units, using Euclidean endpoint distance if length is missing. Unknown technique remains unknown. Endpoint geometry and technique are retrospective descriptions, so they are not classifier inputs.", '',
        'Coordinates span 120×80 standardized units. The actor’s team already attacks toward x=120; only width is reflected for bottom-side corners. Visible attacking outfield counts exclude actor and keeper; defenders include the keeper. The penalty area is x=102–120, y=18–62. Near and far refer to y<36 and y>44 inside that area. Density divides defenders inside both box and camera polygon by the visible intersection area, multiplied by 100. Missing polygons leave density unknown. Missing players are never treated as absent defenders.', '',
        '360 provides event-linked broadcast snapshots, not complete tracking. It cannot establish run trajectories, player identities, marking roles or intent. Some keeper/actor flags have documented provider caveats. Observational event labels, arbitrary time/short thresholds and excluded second phases affect the results. This system offers evidence to inspect, not recommendations for optimal player positioning.', '',
        '## Reproduce','',
        '```bash\npython -m tacticai_lite --all\npython -m pytest -q\npython -m tacticai_lite.report\nstreamlit run app.py\n```', '',
        'Source: [StatsBomb Open Data](https://github.com/statsbomb/open-data), including its event and 360 specifications and public-data agreement. Data is freely accessible for research under provider terms, not an unrestricted open-source licence; raw data and per-corner/player records are excluded from publication. Source attribution uses the official StatsBomb logo. Code uses open-source dependencies and requires no paid API.', '',
        'Research inspiration: Wang et al. (2024), [TacticAI: an AI assistant for football tactics](https://doi.org/10.1038/s41467-024-45965-x), Nature Communications 15, 1906.', '',
        '![StatsBomb attribution](../assets/SB%20-%20Icon%20Lockup%20-%20Colour%20positive.png)', '']
    (destination/'findings.md').write_text('\n'.join(lines))
    print(f'Wrote {destination / "corner-shot-creation.png"} and findings.md')


if __name__ == '__main__':
    main()
