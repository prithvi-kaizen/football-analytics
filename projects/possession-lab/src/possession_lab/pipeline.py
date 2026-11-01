from dataclasses import dataclass

import numpy as np

from .features import Features, extract
from .models import ModelConfig, hmm, state_machine
from .schema import LABELS, TrackingAdapter, TrackingBatch


@dataclass(frozen=True)
class InferenceResult:
    labels: np.ndarray
    features: Features
    method: str
    probabilities: object = None


def infer(batch: TrackingBatch, method="state_machine", config=None):
    f = extract(batch)
    probabilities = None
    if method == "state_machine":
        labels = state_machine(f, config or ModelConfig())
    elif method == "hmm":
        labels = hmm(f, config or ModelConfig())
    elif method == "hierarchical":
        from .hierarchical import HierarchicalConfig, hierarchical
        probabilities = hierarchical(f, config or HierarchicalConfig())
        labels = probabilities.labels
    elif method == "nearest":
        labels = f.nearest_team.copy()
        labels[f.period == 0] = "X"
    else:
        raise ValueError(f"unknown inference method {method!r}")
    if labels.shape != batch.frame.shape or not set(labels) <= set(LABELS):
        raise ValueError("inference violated the H/A/D/X contract")
    return InferenceResult(labels, f, method, probabilities)


def run(adapter: TrackingAdapter, method="state_machine", config=None):
    return infer(adapter.load(), method, config)
