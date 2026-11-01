import numpy as np
import pytest

from possession_lab.schema import TrackingBatch


@pytest.fixture
def controlled_batch():
    n = 300
    t = np.arange(n) / 25
    ball = np.c_[40 + 1.5 * t, np.full(n, 30.0)]
    home = np.tile([20.0, 10.0], (n, 2, 1))
    away = np.tile([80.0, 50.0], (n, 2, 1))
    home[:100, 0] = ball[:100] + [0.5, 0]
    away[100:200, 0] = ball[100:200] + [0.5, 0]
    for value in (ball, home, away):
        value[200:] = value[200]
    return TrackingBatch(np.arange(n), t, np.ones(n, int), ball, home, away,
                         provenance={"kind": "synthetic"})
