"""Paired rank associations and clustered uncertainty conditional on selected matches."""
import numpy as np
import pandas as pd


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    valid = np.isfinite(x) & np.isfinite(y)
    if valid.sum() < 3:
        return None
    a, b = pd.Series(x[valid]).rank().to_numpy(), pd.Series(y[valid]).rank().to_numpy()
    if np.std(a) == 0 or np.std(b) == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def association(df, label='ease'):
    d = df.dropna(subset=[label, 'geometry', 'arrival'])
    a, b = spearman(d.geometry, d[label]), spearman(d.arrival, d[label])
    return dict(n=len(d), geometry_rho=a, arrival_rho=b,
                delta_rho=None if a is None or b is None else b-a)


def bootstrap(df, repetitions, seed, cluster='phase', label='ease'):
    d = df.dropna(subset=[label, 'geometry', 'arrival']).reset_index(drop=True)
    point = association(d, label)
    groups = {mid: [np.array(ids) for _, ids in g.groupby(cluster).groups.items()]
              for mid, g in d.groupby('match_id')}
    point.update(clusters=sum(map(len, groups.values())), repetitions=repetitions,
                 method=f'paired {cluster} cluster bootstrap, stratified by match', seed=seed)
    if point['n'] < 3 or point['delta_rho'] is None:
        point['interval_95'] = None
        return point
    rng, draws = np.random.default_rng(seed), []
    for _ in range(repetitions):
        indices = np.concatenate([np.concatenate([gs[i] for i in rng.integers(0, len(gs), len(gs))]) for gs in groups.values()])
        sample = association(d.iloc[indices], label)
        if sample['delta_rho'] is not None:
            draws.append(sample['delta_rho'])
    point['interval_95'] = list(map(float, np.quantile(draws, [.025, .975]))) if draws else None
    point['valid_repetitions'] = len(draws)
    return point
