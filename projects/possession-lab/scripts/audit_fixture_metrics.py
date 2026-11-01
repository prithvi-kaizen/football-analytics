"""Independent calculations on the bytes actually served by the public demo."""
import argparse
import json
from pathlib import Path
import numpy as np

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data', type=Path, required=True, help='Explicit directory containing the public/synthetic release JSON fixtures')
parser.add_argument('--output', type=Path)
args=parser.parse_args()
DATA=args.data

def runs_of_truth(truth):
    runs=[]
    start=None
    for i,v in enumerate(truth+'X'):
        if v!='X' and start is None:start=i
        elif v=='X' and start is not None:runs.append((start,i));start=None
    return runs

def filled(prediction,runs):
    values=list(prediction)
    for a,b in runs:
        seen=[i for i in range(a,b) if values[i]!='X']
        if not seen:continue
        last=values[seen[0]]
        for i in range(a,b):
            if values[i]!='X':last=values[i]
            else:values[i]=last
    return ''.join(values)

def spells(values,runs):
    result=[]
    for a,b in runs:
        start=a
        for i in range(a+1,b+1):
            if i==b or values[i]!=values[start]:
                if values[start] in 'HA':result.append((start,i,values[start]))
                start=i
    return result

def independent(truth,prediction):
    g=np.array(list(truth));p=np.array(list(prediction));valid=g!='X'
    gs,ps=g[valid],p[valid]
    f1=[]
    for c in 'HAD':
        denom=int((gs==c).sum()+(ps==c).sum())
        f1.append(2*int(((gs==c)&(ps==c)).sum())/denom if denom else 0)
    tp=int(((gs=='D')&(ps=='D')).sum());npred=int((ps=='D').sum());ntrue=int((gs=='D').sum())
    runs=runs_of_truth(truth);prediction=filled(prediction,runs)
    gt_spells,pred_spells=spells(truth,runs),spells(prediction,runs)
    candidates=[]
    for i,(a,b,c) in enumerate(gt_spells):
        for j,(x,y,k) in enumerate(pred_spells):
            overlap=max(0,min(b,y)-max(a,x))
            if c==k and overlap:candidates.append((-overlap/(max(b,y)-min(a,x)),i,j))
    scores=[]
    for threshold in [.3,.4,.5,.6,.7]:
        used_g,used_p=set(),set()
        for negative,i,j in sorted(candidates):
            if -negative>=threshold and i not in used_g and j not in used_p:used_g.add(i);used_p.add(j)
        denom=len(gt_spells)+len(pred_spells)
        scores.append(2*len(used_g)/denom if denom else 0)
    return {'macro_f1':sum(f1)/3,'spell_f1':sum(scores)/5,'D_precision':tp/npred if npred else None,'D_recall':tp/ntrue if ntrue else None,'possessions':len(pred_spells),'true_possessions':len(gt_spells),'graded_frames':int(valid.sum()),'abstained_frames':int((ps=='X').sum())}

def close(a,b,tol=1e-12):
    return a is None and b is None or a is not None and b is not None and abs(a-b)<=tol

def check_features(data):
    t=data['tracking'];ball=np.asarray(t['ball'],float);period=np.asarray(t['period']);n=len(ball)
    largest=0
    for side,key in [('home','home_distance'),('away','away_distance')]:
        team=np.asarray(t[side],float)
        distance=np.linalg.norm(team-ball[:,None],axis=2)
        distance[~np.isfinite(distance)]=np.inf
        nearest=distance.min(axis=1);nearest[~np.isfinite(nearest)]=np.nan
        exported=np.asarray(t[key],float)
        assert np.array_equal(np.isnan(nearest),np.isnan(exported)),key
        error=np.nanmax(abs(nearest-exported))
        assert error<=.002,(key,error)
        largest=max(largest,float(error))
    return largest

rows=[];feature_errors=[];public=[];null_pairs=[]
for path in sorted(DATA.glob('*.json')):
    data=json.loads(path.read_text());worlds=data.get('worlds',[data])
    if 'worlds' in data:
        assert data['identical_tracking'] and worlds[0]['tracking']==worlds[1]['tracking']
        if data['evidence']!='independent':
            assert worlds[0]['tags']==worlds[1]['tags']
            assert all(s['balanced_target_accuracy']<=.5 for s in data['summary'])
            null_pairs.append(path.name)
        for summary in data['summary']:
            accuracies=[]
            for world in worlds:
                pred=next(m['labels'] for m in world['models'] if m['id']==summary['id'])
                pred=filled(pred,runs_of_truth(world['truth']));a,b=world['target']
                accuracies.append(sum(pred[i]==world['truth'][i] for i in range(a,b))/(b-a))
            assert close(sum(accuracies)/2,summary['balanced_target_accuracy'])
    for index,world in enumerate(worlds):
        n=world['frames'];assert all(len(m['labels'])==n and set(m['labels'])<=set('HADX') for m in world['models'])
        feature_errors.append(check_features(world))
        if world['truth'] is None:
            assert path.name.startswith('public')
            assert all(m['metrics'] is None for m in world['models'])
            public.append({'fixture':path.name,'models_withheld':len(world['models']),'frames':n})
            continue
        for m in world['models']:
            independent_metrics=independent(world['truth'],m['labels'])
            for key,value in independent_metrics.items():
                assert close(value,m['metrics'][key]),(path.name,index,m['id'],key,value,m['metrics'][key])
            rows.append({'fixture':path.name,'world':index,'model':m['id'],'passed':True})
report={'synthetic_model_outputs_independently_scored':len(rows),'metric_fields_checked_per_output':8,'public_samples':public,'null_pair_cases':null_pairs,'nearest_distance_max_error_metres_after_coordinate_rounding':max(feature_errors),'all_checks_passed':True}
if args.output:
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
