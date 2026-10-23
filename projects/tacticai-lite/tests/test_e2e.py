import json
from pathlib import Path

import pandas as pd
import pytest

from tacticai_lite.data import Store, select_matches, download_matches
from tacticai_lite.pipeline import build

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.real_data
def test_real_two_match_pipeline_and_source_reconciliation(tmp_path):
    if not (ROOT/'data/raw/data/events/3930158.json').exists():
        pytest.skip('Run python -m tacticai_lite --sample 1 first')
    corners, info=build(ROOT,sample=1,offline=True,output=str(tmp_path))
    assert len(corners)==16
    assert set(corners.match_id)=={3930158,3998836}
    assert int(corners.has_360.sum())==11
    assert int(corners.shot_created.sum())==6
    assert info['censored']==0
    raw=json.loads((ROOT/'data/raw/data/events/3930158.json').read_text())
    # Source event clocks independently establish the first observed shot delay.
    kick=next(e for e in raw if e['id']=='f86d4d17-19e1-4be9-85b2-8092d39ee871')
    first=corners[corners.corner_id==kick['id']].iloc[0]
    shot=next(e for e in raw if e['id']==first.first_shot_id)
    assert shot['type']['name']=='Shot' and shot['team']['id']==kick['team']['id']
    assert shot['possession']==kick['possession']
    assert (pd.to_timedelta(shot['timestamp'])-pd.to_timedelta(kick['timestamp'])).total_seconds()==pytest.approx(13.216)
    # An offline replay must give identical rows and provenance.
    repeated, info2=build(ROOT,sample=1,offline=True,output=str(tmp_path/'replay'))
    pd.testing.assert_frame_equal(corners,repeated)
    assert info==info2
