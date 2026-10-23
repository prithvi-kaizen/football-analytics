from pathlib import Path
import pandas as pd
import pytest

from rest_defence.pipeline import load_result
from rest_defence.report import summarize


def test_summary_denominators_and_fixed_bins():
    path=Path(__file__).resolve().parents[1]/"outputs/J03WPY"
    df,_,_=load_result(path)
    selected,s=summarize(df)
    assert s["n"]==168 and s["progressed"]==94 and s["shots"]==1
    assert sum(b["n"] for b in s["bins"])==s["n"]
    assert sum(b["advanced"] for b in s["bins"])==s["progressed"]
    assert abs(s["rho"])<.001
    df.loc[df.attacking_scope,"censored"]=True
    _,empty=summarize(df)
    assert empty["n"]==0 and empty["rho"] is None
