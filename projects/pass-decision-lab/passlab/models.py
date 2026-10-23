"""Fixed baselines, match-separated evaluation and transparent JSON inference."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .features import EVENT_FEATURES, ORIGIN_360, TARGET_360, TARGET_GEOMETRY

SEED = 2026
FEATURE_SETS = {
    "event": EVENT_FEATURES,
    "360": EVENT_FEATURES + ORIGIN_360,
    "target_geometry": EVENT_FEATURES + TARGET_GEOMETRY,
    "target_360": EVENT_FEATURES + TARGET_GEOMETRY + ORIGIN_360 + TARGET_360,
}


def split_matches(df: pd.DataFrame) -> dict:
    """Same fixed tournament-stratified match partition for every experiment."""
    rng = np.random.default_rng(SEED)
    train, test = [], []
    for _, group in df[["tournament", "match_id"]].drop_duplicates().groupby("tournament", sort=True):
        ids = np.sort(group.match_id.to_numpy())
        if len(ids) < 2:
            raise ValueError("Need at least two matches per tournament: use --sample 2 or --full")
        rng.shuffle(ids)
        n = max(1, math.ceil(len(ids) * 0.25))
        test.extend(int(x) for x in ids[:n])
        train.extend(int(x) for x in ids[n:])
    assert not set(train) & set(test)
    return {
        "train": sorted(train),
        "test": sorted(test),
        "seed": SEED,
        "method": "25% of matches per tournament, shuffled once with numpy default_rng",
    }


def make_estimator(kind: str):
    if kind == "logistic":
        return make_pipeline(
            SimpleImputer(strategy="median", keep_empty_features=True),
            StandardScaler(),
            LogisticRegression(C=1.0, max_iter=2000, random_state=SEED),
        )
    if kind == "boosted":
        # Early stopping would randomly split event rows, violating match isolation.
        return make_pipeline(
            SimpleImputer(strategy="median", keep_empty_features=True),
            HistGradientBoostingClassifier(
                max_iter=100,
                learning_rate=0.05,
                max_leaf_nodes=7,
                min_samples_leaf=30,
                l2_regularization=2,
                early_stopping=False,
                random_state=SEED,
            ),
        )
    raise ValueError(kind)


def scores(y, p) -> dict:
    p = np.clip(np.asarray(p, dtype=float), 1e-8, 1 - 1e-8)
    return {
        "n": len(y),
        "completion_rate": float(np.mean(y)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "roc_auc": float(roc_auc_score(y, p)) if len(set(y)) == 2 else None,
    }


def cluster_interval(df: pd.DataFrame, repeats: int = 400):
    work = df.copy()
    p = np.clip(work.probability.to_numpy(), 1e-8, 1 - 1e-8)
    y = work.complete.to_numpy()
    work["loss"] = -(y * np.log(p) + (1 - y) * np.log1p(-p))
    groups = work.groupby("match_id").agg(loss_sum=("loss", "sum"), n=("loss", "size"))
    if len(groups) < 4:
        return None, None
    rng = np.random.default_rng(SEED)
    indices = rng.integers(len(groups), size=(repeats, len(groups)))
    losses = groups.loss_sum.to_numpy()[indices].sum(axis=1) / groups.n.to_numpy()[indices].sum(axis=1)
    return tuple(float(x) for x in np.quantile(losses, [0.025, 0.975]))


def calibration_table(df: pd.DataFrame):
    work = df.copy()
    work["bin"] = pd.cut(work.probability, np.linspace(0, 1, 11), include_lowest=True)
    return (
        work.groupby("bin", observed=True)
        .agg(predicted=("probability", "mean"), observed=("complete", "mean"), n=("complete", "size"))
        .reset_index()
    )


def logistic_bundle(model, columns: list[str], training: pd.DataFrame) -> dict:
    imputer, scaler, clf = model.steps[0][1], model.steps[1][1], model.steps[2][1]
    bounds = {}
    for col in columns:
        data = training[col].dropna()
        if len(data):
            bounds[col] = [float(data.quantile(0.01)), float(data.quantile(0.99))]
    return {
        "features": columns,
        "imputer": imputer.statistics_.tolist(),
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "coef": clf.coef_[0].tolist(),
        "intercept": float(clf.intercept_[0]),
        "bounds": bounds,
        "training_rows": len(training),
        "model": "fixed logistic C=1",
        "training_matches": sorted(int(x) for x in training.match_id.unique()),
    }


def predict_bundle(bundle: dict, rows: pd.DataFrame) -> np.ndarray:
    values = rows.reindex(columns=bundle["features"]).to_numpy(dtype=float)
    values = np.where(np.isnan(values), np.asarray(bundle["imputer"]), values)
    z = ((values - bundle["mean"]) / bundle["scale"]) @ np.asarray(bundle["coef"]) + bundle["intercept"]
    return 1 / (1 + np.exp(-np.clip(z, -700, 700)))


def support_flags(bundle: dict, row: dict) -> list[str]:
    # Marginal guards are deliberately limited: joint support is not established.
    flags = []
    for col in bundle["features"]:
        value = row.get(col, np.nan)
        if value is None or not np.isfinite(value):
            flags.append(f"{col}: unobserved")
        elif col in bundle["bounds"]:
            lo, hi = bundle["bounds"][col]
            if value < lo - 1e-6 or value > hi + 1e-6:
                flags.append(f"{col}: outside training 1-99% range")
    return flags


def fit_evaluate(df: pd.DataFrame, split: dict, kinds=("logistic", "boosted")):
    paired = df[df.has_frame & df.has_opponents.fillna(False)].copy()
    targets = paired[paired.has_target].copy()
    metrics, predictions, bundles, omissions = [], [], {}, []
    for population, cohort, feature_names in [
        ("context", paired, ["event", "360"]),
        ("recipient_proxy", targets, ["target_geometry", "target_360"]),
    ]:
        training = cohort[cohort.match_id.isin(split["train"])]
        testing = cohort[cohort.match_id.isin(split["test"])]
        if (
            len(training) < 100
            or training.complete.value_counts().min() < 5
            or training.complete.nunique() < 2
            or testing.complete.nunique() < 2
        ):
            omissions.append(f"{population}: insufficient training rows/classes or holdout classes")
            continue
        baseline = float(training.complete.mean())
        for features in ["mean"] + feature_names:
            for kind in ["constant"] if features == "mean" else kinds:
                model_id = f"{population}/{kind}/{features}"
                if features == "mean":
                    p = np.repeat(baseline, len(testing))
                else:
                    cols = FEATURE_SETS[features]
                    estimator = make_estimator(kind)
                    estimator.fit(training[cols], training.complete)
                    p = estimator.predict_proba(testing[cols])[:, 1]
                    if kind == "logistic":
                        bundles[features] = logistic_bundle(estimator, cols, training)
                pred = testing[["event_id", "match_id", "tournament", "complete"]].copy()
                pred["probability"], pred["model_id"], pred["population"] = p, model_id, population
                lower, upper = cluster_interval(pred)
                metrics.append(
                    {
                        "model_id": model_id,
                        "population": population,
                        "estimator": kind,
                        "features": features,
                        "train_n": len(training),
                        "train_matches": training.match_id.nunique(),
                        "test_matches": testing.match_id.nunique(),
                        **scores(testing.complete, p),
                        "log_loss_ci_low": lower,
                        "log_loss_ci_high": upper,
                    }
                )
                predictions.append(pred)
    if not predictions:
        raise ValueError("Not enough observations to fit even a context model; download more matches")
    return pd.DataFrame(metrics), pd.concat(predictions, ignore_index=True), bundles, omissions
