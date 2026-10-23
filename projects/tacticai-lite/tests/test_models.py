import numpy as np
import pandas as pd

from tacticai_lite.analysis import SPATIAL
from tacticai_lite.models import cluster_corners, evaluate


def data():
    # Synthetic fixtures test model invariants only; never used for findings.
    rng=np.random.default_rng(1)
    d=pd.DataFrame(rng.normal(size=(120,len(SPATIAL))),columns=SPATIAL)
    d['corner_id']=[str(i) for i in range(120)]
    d['match_id']=np.repeat(np.arange(12),10)
    d['has_360']=True;d['visible_players']=12
    d['tournament']='Test fixture';d['shot_created']=np.arange(120)%3==0
    return d


def test_match_separation_and_forbidden_features():
    d=data();result,pred=evaluate(d)
    assert result['status']=='evaluated'
    assert not set(result['train_matches']) & set(result['test_matches'])
    assert set(result['features'])==set(SPATIAL)
    assert {'delivery','shots','xg','cluster'}.isdisjoint(result['features'])
    assert len(pred)==result['test_corners']
    # Altering test outcomes cannot change a fitted model's probabilities.
    d.loc[d.match_id.isin(result['test_matches']),'shot_created']=False
    result2,pred2=evaluate(d)
    np.testing.assert_allclose(pred.logistic,pred2.logistic)


def test_clusters_do_not_use_outcomes_and_missing_frames_stay_missing():
    d=data();d.loc[0,'has_360']=False
    a,*_=cluster_corners(d)
    d['shot_created']=~d.shot_created
    b,*_=cluster_corners(d)
    assert a.cluster.tolist()==b.cluster.tolist()
    assert a.iloc[0].cluster=='No usable frame'
    result,_=evaluate(d.iloc[:5])
    assert result['status']=='insufficient data'


def test_no_attacking_outfielder_is_not_a_usable_shape():
    from tacticai_lite.models import usable_frames
    d=data();d.loc[0,'attacker_mean_x']=np.nan
    assert not usable_frames(d).iloc[0]


def test_direct_shots_are_excluded_from_predictive_task():
    d=data();d['delivery']='Inswinging';d.loc[0:9,'delivery']='Direct shot'
    result,pred=evaluate(d)
    assert 0 not in result['train_matches']+result['test_matches']
    assert len(pred)>0
