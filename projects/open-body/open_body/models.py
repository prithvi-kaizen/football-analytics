"""Fixed regularized baselines, held-out predictions and conditional uncertainty."""

import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, brier_score_loss, roc_auc_score


def fit_predict(train, test, features, cfg):
    if train.target.nunique() != 2:
        raise ValueError("Training needs both outcome classes")
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            C=1 / cfg["ridge_lambda"], solver="lbfgs", max_iter=2000, tol=1e-9
        ),
    )
    model.fit(train[features].to_numpy(float), train.target.to_numpy(int))
    return model.predict_proba(test[features].to_numpy(float))[:, 1], model


def losses(y, p):
    p = np.clip(np.asarray(p), 1e-12, 1 - 1e-12)
    y = np.asarray(y)
    return -(y * np.log(p) + (1 - y) * np.log1p(-p))


def metrics(y, p):
    y = np.asarray(y)
    p = np.asarray(p)
    bins = []
    for lo, hi in zip(np.arange(0, 1, 0.2), np.arange(0.2, 1.01, 0.2)):
        mask = (p >= lo) & (p < (hi if hi < 0.99 else 1.000001))
        bins.append(
            {
                "lower": float(lo),
                "upper": float(hi),
                "n": int(mask.sum()),
                "predicted": float(p[mask].mean()) if mask.any() else None,
                "observed": float(y[mask].mean()) if mask.any() else None,
            }
        )
    return {
        "n": len(y),
        "positives": int(y.sum()),
        "prevalence": float(y.mean()),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "auroc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        "calibration": bins,
    }


def block_interval(difference, blocks, cfg):
    """Paired non-overlapping temporal-block bootstrap, conditional on this match."""
    difference = np.asarray(difference)
    blocks = np.asarray(blocks)
    keys = np.unique(blocks)
    if len(keys) < 2:
        return {"low": None, "high": None, "blocks": len(keys)}
    chunks = [difference[blocks == k] for k in keys]
    rng = np.random.default_rng(cfg["seed"])
    sums = np.array([x.sum() for x in chunks])
    counts = np.array([len(x) for x in chunks])
    draws = rng.integers(0, len(keys), (cfg["bootstrap_repetitions"], len(keys)))
    samples = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)
    low, high = np.quantile(samples, [0.025, 0.975])
    return {
        "low": float(low),
        "high": float(high),
        "blocks": len(keys),
        "repetitions": cfg["bootstrap_repetitions"],
        "conditional_on": "one held-out match and fitted training model; not a new-match confidence interval",
    }


def compare(train, test, cfg):
    base = cfg["baseline_features"]
    orient = cfg["orientation_features"]
    pb, mb = fit_predict(train, test, base, cfg)
    po, mo = fit_predict(train, test, base + orient, cfg)
    constant = np.full(len(test), train.target.mean())
    d = losses(test.target, po) - losses(test.target, pb)
    summary = {
        "train_match": int(train.match_id.iloc[0]),
        "test_match": int(test.match_id.iloc[0]),
        "train_n": len(train),
        "constant": metrics(test.target, constant),
        "baseline": metrics(test.target, pb),
        "orientation": metrics(test.target, po),
        "delta_log_loss": float(d.mean()),
        "delta_brier": float(
            np.mean((po - test.target) ** 2 - (pb - test.target) ** 2)
        ),
        "delta_log_loss_95ci": block_interval(
            d, np.floor(test.frame / 10 / cfg["bootstrap_block_seconds"]), cfg
        ),
    }
    pred = test[
        ["match_id", "event_id", "frame", "period", "phase_index", "target"]
    ].copy()
    pred["p_baseline"] = pb
    pred["p_orientation"] = po
    pred["loss_difference"] = d
    summary["coefficients"] = {
        name: float(v) for name, v in zip(base + orient, mo[-1].coef_[0])
    }
    return summary, pred
