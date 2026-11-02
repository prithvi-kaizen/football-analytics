"""Fixed, small v2 evaluation; no model or threshold selection. Public data unscored."""
import csv
import json
from pathlib import Path
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import numpy as np
from possession_lab.explorer_v2 import scenario,observability
from possession_lab.motion_v2 import generate
from possession_lab.synthetic import generate as legacy_generate,SyntheticConfig
from possession_lab.phase2_experiments import verify_phase1_freeze
from possession_lab.official import verify

OUT=ROOT/'reports/motion-v2'
SEEDS=[301,302,303,304,305]
MECHANISMS=['ordinary','stationary_live','contested','player_gaps','identity_switches']
METHODS=['nearest','state_machine','hmm','hierarchical']
METRICS=['spell_f1','macro_f1','D_precision','D_recall','boundary_mae_frames','boundary_missed','boundary_spurious']


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[];kinematics=[]
    for mechanism in MECHANISMS:
        for seed in SEEDS:
            start=perf_counter()
            result=scenario({'seed':seed,'mechanism':mechanism,'noise':.1,'loss':.08,'gap_start':19,'gap_duration':6})
            elapsed=(perf_counter()-start)*1000
            kinematics.append({'seed':seed,'mechanism':mechanism,**{k:v for k,v in result['motion_validation'].items() if k!='limits'}})
            for model in result['models']:
                if model['id'] in METHODS:
                    rows.append({'seed':seed,'mechanism':mechanism,'method':model['id'],'full_pipeline_14_models_ms':elapsed,**{key:model['metrics'][key] for key in METRICS}})
    for name,values in [('trials.csv',rows),('kinematics.csv',kinematics)]:
        with (OUT/name).open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(values[0]));writer.writeheader();writer.writerows(values)
    rng=np.random.default_rng(20261101);summaries=[]
    for mechanism in MECHANISMS:
        for method in METHODS:
            selected=[row for row in rows if row['mechanism']==mechanism and row['method']==method]
            for metric in METRICS:
                values=np.array([np.nan if row[metric] is None else row[metric] for row in selected],float)
                defined=values[np.isfinite(values)]
                if len(defined):
                    means=np.mean(defined[rng.integers(0,len(defined),(2000,len(defined)))],axis=1)
                    mean=float(defined.mean());lo,hi=map(float,np.percentile(means,[2.5,97.5]))
                else:mean=lo=hi=None
                summaries.append({'mechanism':mechanism,'method':method,'metric':metric,'mean':mean,'low':lo,'high':hi,'defined_trials':len(defined),'trials':len(selected)})
    (OUT/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    old=legacy_generate(SyntheticConfig(noise_m=0,occlusion_rate=0,player_gap_rate=0),101)
    maximum=lambda team:float(np.nanmax(np.linalg.norm(np.diff(team,axis=0),axis=-1)))
    comparison={'legacy_clean_max_step_m':max(maximum(old.tracking.home),maximum(old.tracking.away)),
                'v2_worst_max_step_m':max(row['max_player_step_m'] for row in kinematics),
                'frozen_files_unchanged':verify_phase1_freeze(),'official_files_unchanged':len(verify()['files']),
                'scenario_trials':len(kinematics),'reported_method_runs':len(rows),
                'full_pipeline_median_ms':float(np.median([row['full_pipeline_14_models_ms'] for row in rows]))}
    (OUT/'validation.json').write_text(json.dumps(comparison,indent=2)+'\n')
    lines=['# Motion v2: exploratory diagnostics','','Fixed seeds 301–305; 5 mechanisms; unchanged models. Five trials per case are too few for robust generalization claims. Intervals resample whole trials. Undefined D precision is omitted, never scored as perfect.','','| Mechanism | Method | SpellF1 mean [95% trial interval] | MacroF1 | D recall |','| --- | --- | --- | --- | --- |']
    for mechanism in MECHANISMS:
        for method in METHODS:
            group={row['metric']:row for row in summaries if row['mechanism']==mechanism and row['method']==method}
            a=group['spell_f1'];b=group['macro_f1'];c=group['D_recall']
            lines.append(f"| {mechanism} | {method} | {a['mean']:.3f} [{a['low']:.3f}, {a['high']:.3f}] | {b['mean']:.3f} | {c['mean']:.3f} |")
    lines+=['','These scores must not be pooled with the historical Phase 1/2 benchmarks. The new generator changes the data-generating process. No public Metrica or competition labels enter this evaluation.','',f"Largest noise-free player step: legacy {comparison['legacy_clean_max_step_m']:.3f} m versus v2 {comparison['v2_worst_max_step_m']:.3f} m at 25 fps. This checks kinematic continuity, not realism or tactical validity."]
    (OUT/'comparison.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure,axes=plt.subplots(1,2,figsize=(11,4),facecolor='#f8f6f0')
    batch=generate(101).tracking
    for ax in axes:ax.set_facecolor('#f8f6f0')
    for side,color in [(batch.home,'#2456a6'),(batch.away,'#ae4b16')]:
        for slot in range(11):
            axes[0].plot(side[:500,slot,0],side[:500,slot,1],color=color,lw=.8,alpha=.8)
            axes[0].scatter(*side[0,slot],color=color,s=12)
    axes[0].set(xlim=(0,105),ylim=(0,68),aspect='equal',title='V2 latent player paths: first 20 s',xlabel='Metres',ylabel='Metres')
    axes[1].bar(['Legacy fixture','Continuous v2'],[comparison['legacy_clean_max_step_m'],comparison['v2_worst_max_step_m']],color=['#626568','#245742'])
    axes[1].set(title='Largest player step in 0.04 s',ylabel='Metres')
    axes[1].text(1,comparison['v2_worst_max_step_m']+1,f"{comparison['v2_worst_max_step_m']:.3f} m",ha='center')
    figure.tight_layout();figure.savefig(OUT/'motion-validation.png',dpi=160);plt.close(figure)
    print(json.dumps(comparison))

if __name__=='__main__':main()
