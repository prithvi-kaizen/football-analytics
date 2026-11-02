"""New motion/public-intervention interface; the historical explorer API stays intact."""
from dataclasses import replace
import json

import numpy as np

from .event_worlds import ActionCue, PrivateAction, rule_labels
from .explorer_api import describe_batch, metric_module
from .motion_v2 import generate, observe
from .schema import TrackingBatch
from .synthetic_tags import observe_actions, uninformative_tags


def _request(request, public=False):
    allowed={'source','seed','mechanism','noise','loss','gap_start','gap_duration'}
    if not isinstance(request,dict) or set(request)-allowed:
        raise ValueError('unsupported request')
    cfg={'source':'public1' if public else 'synthetic_v2','seed':101,'mechanism':'ordinary',
         'noise':.12,'loss':.05,'gap_start':12.,'gap_duration':6.,**request}
    if not isinstance(cfg['seed'],int) or isinstance(cfg['seed'],bool) or not 1<=cfg['seed']<=99999:
        raise ValueError('seed must be an integer in 1..99999')
    for name,(lo,hi) in {'noise':(0,.5),'loss':(0,.7),'gap_start':(0,110),'gap_duration':(0,15)}.items():
        if isinstance(cfg[name],bool) or not isinstance(cfg[name],(int,float)) or not np.isfinite(cfg[name]) or not lo<=cfg[name]<=hi:
            raise ValueError('invalid '+name)
    if cfg['mechanism'] not in ('ordinary','stationary_live','contested','player_gaps','identity_switches'):
        raise ValueError('unknown mechanism')
    if cfg['source'] not in (('public1','public2') if public else ('synthetic_v2',)):
        raise ValueError('unknown source')
    if public and cfg['mechanism']!='ordinary':
        raise ValueError('public demonstrations accept observation loss/noise only')
    return cfg


def scenario(request=None):
    cfg=_request({} if request is None else request)
    match=generate(cfg['seed'],cfg['mechanism'])
    batch=observe(match,**{name:cfg[name] for name in ('seed','noise','loss','gap_start','gap_duration','mechanism')})
    output=describe_batch(batch,match.truth,'Continuous role-based synthetic passage',cfg)
    output['motion_validation']=match.diagnostics
    return output


def _full(values):
    values=np.asarray(values)
    if np.issubdtype(values.dtype,np.floating):
        result=values.astype(object);result[~np.isfinite(values)]=None
        return result.tolist()
    return values.tolist()


def public_payload(batch,game):
    """Exact canonical public positions preserve zero-intervention inference parity."""
    if batch.provenance.get('kind')!='public_sample' or game not in (1,2):
        raise ValueError('known public sample required')
    return {'sample_game':game,'fps':batch.fps,'pitch':batch.pitch,'provenance':batch.provenance,
            **{name:_full(getattr(batch,name)) for name in ('frame','time_s','period','ball','home','away')}}


def public_demo(request,payload):
    cfg=_request(request,public=True)
    if (not isinstance(payload,dict) or payload.get('sample_game') not in (1,2)
            or cfg['source']!='public'+str(payload['sample_game'])
            or payload.get('provenance',{}).get('kind')!='public_sample'):
        raise ValueError('public sample identity mismatch')
    n=len(payload['frame'])
    if not 1<=n<=1000 or payload['fps']!=25 or tuple(payload['pitch'])!=(105.,68.):
        raise ValueError('only the released bounded public excerpts are accepted')
    batch=TrackingBatch(np.asarray(payload['frame'],int),np.asarray(payload['time_s'],float),
                        np.asarray(payload['period'],int),np.asarray(payload['ball'],float),
                        np.asarray(payload['home'],float),np.asarray(payload['away'],float),
                        tuple(payload['pitch']),payload['fps'],payload['provenance'])
    if cfg['gap_start']*batch.fps>=n:
        raise ValueError('gap start must be inside the public excerpt')
    # A wrapper provides observations to the common measurement corruption layer.
    from .motion_v2 import MotionMatch
    batch=observe(MotionMatch(batch,np.array([],dtype='<U1'),(),{}),**{name:cfg[name] for name in ('seed','noise','loss','gap_start','gap_duration','mechanism')})
    batch.provenance.update({'intervention_scope':'Simulated measurement loss/noise applied to public tracking; no synthetic ground truth',
                             'underlying_movement':'Public Metrica observations, not simulated player motion'})
    return describe_batch(batch,None,f'Public Metrica sample {payload["sample_game"]} with observation failures',cfg)


def observability(request=None):
    request={} if request is None else request
    if not isinstance(request,dict) or set(request)-{'seed','kind','evidence'}:
        raise ValueError('unsupported observability settings')
    seed=request.get('seed',22001);evidence=request.get('evidence','none')
    if (not isinstance(seed,int) or isinstance(seed,bool) or not 1<=seed<=99999
            or request.get('kind','moving')!='moving' or evidence not in ('none','independent','null')):
        raise ValueError('invalid moving-pair request')
    original=generate(seed).tracking
    a,b=125,575
    batch=TrackingBatch(np.arange(b-a),np.arange(b-a)/25,np.ones(b-a,int),
                        original.ball[a:b].copy(),original.home[a:b].copy(),original.away[a:b].copy(),
                        provenance={**original.provenance,'generator':'role_motion_v2_counterexample',
                                    'scope':'Identical synthetic movement under two private referee rulings'})
    target=(150,300)
    common=(PrivateAction(ActionCue(400,'controlled_touch','A',1),True),)
    actions=(
        (PrivateAction(ActionCue(target[0],'advisory_gesture','H',1),False),
         PrivateAction(ActionCue(target[1],'pass','H',1),True),*common),
        (PrivateAction(ActionCue(target[0],'stop_gesture','H',1),True),
         PrivateAction(ActionCue(target[1],'restart_attempt','H',1),True),*common))
    worlds=[]
    for latent in actions:
        truth=rule_labels(batch.period,latent,'H')
        tags=()
        if evidence=='independent':
            # Annotator sees public cues only, never the private ruling or truth.
            tags=observe_actions(tuple(action.cue for action in latent),batch.period,seed+900000)
        elif evidence=='null':tags=uninformative_tags(batch.period,seed+5)
        data=describe_batch(batch,truth,'Moving exact-observation counterexample',tags=tags)
        data['target']=list(target)
        data['tags']=[{'start':e.start,'stop':e.stop,'code':e.code,'team':e.team_hint} for e in tags]
        worlds.append(data)
    pm=metric_module();summary=[]
    for model in worlds[0]['models']:
        accuracies=[]
        for world in worlds:
            labels=next(m['labels'] for m in world['models'] if m['id']==model['id'])
            gt=pm.label_codes(world['truth']);filled=pm.fill_abstentions(pm.label_codes(labels),pm.valid_runs(gt))
            accuracies.append(float((filled[target[0]:target[1]]==gt[target[0]:target[1]]).mean()))
        summary.append({'id':model['id'],'balanced_target_accuracy':sum(accuracies)/2})
    return {'worlds':worlds,'identical_tracking':worlds[0]['tracking']==worlds[1]['tracking'],
            'seed':seed,'kind':'moving','evidence':evidence,'summary':summary,
            'scope':'One constructed synthetic pair, not a realistic match or performance estimate'}


def run_json(mode,request_json='{}',public_json=None):
    request=json.loads(request_json)
    if mode=='scenario_v2':output=scenario(request)
    elif mode=='observability_v2':output=observability(request)
    elif mode=='public_demo' and public_json is not None:output=public_demo(request,json.loads(public_json))
    else:raise ValueError('unsupported v2 operation')
    return json.dumps(output,allow_nan=False,separators=(',',':'))
