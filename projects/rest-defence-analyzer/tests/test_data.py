import gzip
from pathlib import Path

import numpy as np
import pytest

from rest_defence.data import ROOT, acquire, attack_sign, metadata, orient, parse_events, parse_tracking, source_files, utc_seconds


def test_timezones_are_same_instant():
    assert utc_seconds("2022-10-15T13:01:28.310+02:00") == utc_seconds("2022-10-15T11:01:28.310Z")
    with pytest.raises(ValueError,match="UTC offset"):
        utc_seconds("2022-10-15T11:01:28")


def test_coordinate_rotation():
    xy = np.array([[52.5,34.],[-52.5,-34.]])
    np.testing.assert_array_equal(orient(orient(xy,-1),-1),xy)
    np.testing.assert_array_equal(orient(xy,1),xy)
    with pytest.raises(ValueError):
        orient(xy,0)


def test_unknown_match():
    with pytest.raises(ValueError,match="Unknown"):
        source_files("invented")


@pytest.mark.real
def test_real_metadata_events_sample(tmp_path):
    paths = acquire(bundled=True, cache=tmp_path)
    m = metadata(paths["meta"])
    e,h = parse_events(paths["events"],m)
    assert m["length"] == 105. and m["width"] == 68.
    assert m["title"] == "Fortuna Düsseldorf:1. FC Nürnberg"
    assert len(e) == 1444 and e.time.is_monotonic_increasing
    for team in m["teams"]:
        assert attack_sign(m,h,team,"firstHalf") == -attack_sign(m,h,team,"secondHalf")
    p,b,a = parse_tracking(paths["tracking"],m)
    assert len(b) == 4501 and b.frame.min() == 10000 and b.frame.max() == 14500
    assert p.groupby("frame").size().eq(22).all()
    assert a["invalid_coordinates"] == a["unknown_entities"] == 0
    assert np.allclose(b.time.diff().dropna(),.04,atol=1e-6)


def test_duplicate_tracking_rejected(tmp_path):
    paths = acquire(bundled=True,cache=tmp_path)
    text = paths["tracking"].read_text()
    first = text[text.index("<Frame "):text.index("/>",text.index("<Frame "))+2]
    paths["tracking"].write_text(text.replace(first,first+"\n"+first,1))
    with pytest.raises(ValueError,match="Duplicate"):
        parse_tracking(paths["tracking"],metadata(paths["meta"]))
