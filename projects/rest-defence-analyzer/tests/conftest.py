import pandas as pd
import pytest


@pytest.fixture
def ball_factory():
    def make(possessions, live=None, start=10000, period="firstHalf"):
        n = len(possessions)
        return pd.DataFrame(dict(period=[period]*n, frame=range(start, start+n),
                                 time=[i/25 for i in range(n)], x=[-i*.1 for i in range(n)],
                                 y=[0.]*n, possession=possessions, live=live or [1]*n, valid=[True]*n))
    return make


@pytest.fixture
def empty_events():
    return pd.DataFrame(columns=["period", "kind", "team", "time", "aligned_time", "alignment", "xg", "corrected_frame"])
