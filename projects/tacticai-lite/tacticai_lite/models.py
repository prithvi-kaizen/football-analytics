"""Descriptive clustering and a strictly frame-based match-held-out baseline."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from .analysis import SPATIAL

SEED = 2026


def spatial_matrix(frame):
    return frame[SPATIAL].astype(float)


def usable_frames(frame):
    return (frame.has_360 & frame.visible_players.fillna(0).ge(4)
            & frame.attacker_mean_x.notna() & frame.defender_mean_x.notna())


def cluster_corners(frame, k=4):
    out = frame.copy()
    out['cluster'] = 'No usable frame'
    valid = usable_frames(out)
    if valid.sum() < k:
        return out, {'status': 'insufficient frames', 'features': SPATIAL}, None, None
    x = spatial_matrix(out.loc[valid])
    preprocess = make_pipeline(SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True), StandardScaler())
    z = preprocess.fit_transform(x)
    k = min(k, len(np.unique(z, axis=0)))
    if k < 2:
        return out, {'status': 'insufficient distinct configurations', 'features': SPATIAL}, None, None
    estimator = KMeans(n_clusters=k, random_state=SEED, n_init=20)
    with threadpool_limits(limits=1):
        labels = estimator.fit_predict(z)
    out.loc[valid, 'cluster'] = [f'C{i+1}' for i in labels]
    return out, {'status': 'descriptive only', 'k': k, 'seed': SEED, 'features': SPATIAL,
                 'eligible_corners': int(valid.sum()),
                 'note': 'Fit to all eligible frames, without outcomes. Cluster IDs have no tactical meaning and can change with dataset scope.'}, preprocess, z


def nearest_corners(frame, corner_id, preprocess, z, n=5):
    if preprocess is None or z is None:
        return []
    valid = usable_frames(frame)
    eligible = frame.loc[valid]
    if corner_id not in set(eligible.corner_id):
        return []
    source = preprocess.transform(spatial_matrix(eligible[eligible.corner_id == corner_id]))[0]
    distances = np.linalg.norm(z-source, axis=1)
    return [{'corner_id': eligible.iloc[i].corner_id, 'distance': float(distances[i])}
            for i in np.argsort(distances, kind='stable') if eligible.iloc[i].corner_id != corner_id][:n]


def evaluate(frame):
    eligible = frame.shot_created.notna() & usable_frames(frame)
    if 'delivery' in frame:
        # A direct corner shot makes the target true by definition at the kick.
        eligible &= frame.delivery.ne('Direct shot')
    usable = frame[eligible].copy()
    result = {'seed': SEED, 'features': SPATIAL, 'prediction_time': 'corner-linked frame at kick',
              'excluded_features': ['delivery', 'pass endpoint', 'team/player identity', 'shots', 'xg', 'cluster', 'future events'],
              'status': 'insufficient data', 'scope': 'Pass corners with a usable linked frame and observed outcome; direct shots excluded'}
    if usable.match_id.nunique() < 8 or len(usable) < 50:
        result['reason'] = 'Need at least 8 matches and 50 eligible corners. No model fitted.'
        return result, pd.DataFrame()
    train_idx, test_idx = next(GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=SEED).split(usable, groups=usable.match_id))
    train, test = usable.iloc[train_idx], usable.iloc[test_idx]
    ytrain, ytest = train.shot_created.astype(int), test.shot_created.astype(int)
    result.update(train_matches=sorted(map(int, train.match_id.unique())), test_matches=sorted(map(int, test.match_id.unique())),
                  train_corners=len(train), test_corners=len(test), train_positives=int(ytrain.sum()), test_positives=int(ytest.sum()))
    assert not set(result['train_matches']) & set(result['test_matches'])
    if ytrain.nunique() < 2:
        result['reason'] = 'Training fold has only one outcome class. No classifier fitted.'
        return result, pd.DataFrame()
    models = {'constant': DummyClassifier(strategy='prior'),
              'logistic': make_pipeline(SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True),
                                        StandardScaler(), LogisticRegression(C=1.0, max_iter=2000, random_state=SEED))}
    predictions = test[['corner_id', 'match_id', 'tournament']].copy()
    predictions['actual'] = ytest.to_numpy()
    result['metrics'] = {}
    for label, model in models.items():
        with threadpool_limits(limits=1):
            model.fit(spatial_matrix(train), ytrain)
            prob = model.predict_proba(spatial_matrix(test))[:, 1]
        predictions[label] = prob
        result['metrics'][label] = {
            'brier': float(brier_score_loss(ytest, prob)),
            'log_loss': float(log_loss(ytest, prob, labels=[0, 1])),
            'roc_auc': float(roc_auc_score(ytest, prob)) if ytest.nunique() == 2 else None,
            'average_precision': float(average_precision_score(ytest, prob)) if ytest.nunique() == 2 else None}
    result.update(status='evaluated', note='One fixed whole-match holdout; no tuning on test. Descriptive evidence only, with no claim of transportability.')
    return result, predictions
