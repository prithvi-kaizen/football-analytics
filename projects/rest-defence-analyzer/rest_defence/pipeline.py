from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .baseline import align_events, detect_turnovers, preloss_snapshot, transition_outcome
from .data import ROOT, FPS, PARSER_VERSION, acquire, analysis_fingerprint, attack_sign, digest, metadata, orient, parse_events, parse_tracking
from .geometry import rest_geometry, vulnerability_score


def clean(paths, meta, stride=5, cache=None):
    key = f"{digest(paths['tracking'])[:16]}-p{PARSER_VERSION}-s{stride}"
    target = Path(cache or ROOT / "data/clean") / key
    receipt = target / "audit.json"
    if receipt.exists():
        info = json.loads(receipt.read_text())
        if info.get("metadata_sha256") == digest(paths["meta"]):
            if all(digest(target / f"{k}.parquet") == info["cache_sha256"][k] for k in ["players","ball"]):
                return pd.read_parquet(target / "players.parquet"), pd.read_parquet(target / "ball.parquet"), info
    players, ball, audit = parse_tracking(paths["tracking"],meta,stride)
    target.mkdir(parents=True,exist_ok=True)
    for k, df in [("players",players),("ball",ball)]:
        df.to_parquet(target / f"{k}.parquet",index=False)
    audit.update(metadata_sha256=digest(paths["meta"]),
                 cache_sha256={k:digest(target / f"{k}.parquet") for k in ["players","ball"]})
    receipt.write_text(json.dumps(audit,indent=2))
    return players,ball,audit


def analyze(players, ball, events, meta, halves, stable_seconds=.4):
    anchors = detect_turnovers(ball,stable_seconds)
    events = align_events(events,ball)
    rows, snapshots, replays, timelines = [],[],[],[]
    rejected = Counter()
    p_groups = {p:g.sort_values("frame").reset_index(drop=True) for p,g in players.groupby("period")}
    b_groups = {p:g.sort_values("frame").reset_index(drop=True) for p,g in ball.groupby("period")}
    for anchor in anchors.itertuples():
        pg,bg = p_groups[anchor.period],b_groups[anchor.period]
        n = anchor.frame
        p0,p1 = np.searchsorted(pg.frame.to_numpy(),[n-5,n],side="left")
        b0,b1 = np.searchsorted(bg.frame.to_numpy(),[n-5,n+252],side="left")
        local_ball = bg.iloc[b0:b1]
        try:
            snap,preball = preloss_snapshot(pg.iloc[p0:p1],local_ball,anchor.period,n)
        except ValueError as exc:
            rejected[str(exc)] += 1
            continue
        losing = meta["possession_map"][anchor.losing]
        winning = meta["possession_map"][anchor.winning]
        sign = attack_sign(meta,halves,losing,anchor.period)
        snap[["x","y"]] = orient(snap[["x","y"]],sign)
        xy_ball = orient([preball.x,preball.y],sign)
        d = snap[(snap.team == losing) & ~snap.is_gk][["x","y"]].to_numpy()
        o = snap[(snap.team == winning) & ~snap.is_gk][["x","y"]].to_numpy()
        metrics = rest_geometry(d,o,xy_ball,meta["length"],meta["width"])
        score = vulnerability_score(metrics)
        # Score is complete before any post-anchor observation is computed.
        outcome = transition_outcome(local_ball,events,anchor.period,n,anchor.winning,winning,sign,length=meta["length"])
        actions = events[(events.period == anchor.period) & (events.team == winning) &
                         events.kind.isin(["Play","OtherBallAction","BallClaiming","TacklingGame","ShotAtGoal"])]
        nearest = actions.iloc[(actions.aligned_time-anchor.time).abs().argsort()[:1]]
        event_delta = float(nearest.iloc[0].aligned_time-anchor.time) if not nearest.empty else np.nan
        identifier = f"{meta['match_id']}-{anchor.period}-{n}"
        row = dict(transition_id=identifier,match_id=meta["match_id"],period=anchor.period,frame=n,
                   time=anchor.time,clock_s=(0 if anchor.period == "firstHalf" else 2700)+anchor.time-halves[anchor.period]["start"],
                   losing_team=losing,winning_team=winning,team_name=meta["teams"][losing]["name"],
                   prior_control_s=anchor.prior_control_s,attacking_scope=bool(xy_ball[0]>=0 and anchor.prior_control_s>=2.),
                   snapshot_frame=int(preball.frame),snapshot_age_s=(n-preball.frame)/FPS,
                   ball_x=float(xy_ball[0]),ball_y=float(xy_ball[1]),
                   goalkeeper_behind=int(((snap.team == losing)&snap.is_gk&(snap.x<=xy_ball[0])).sum()),
                   event_corroborated=abs(event_delta)<=2.,event_delta_s=event_delta,
                   event_id=nearest.iloc[0].event_id if not nearest.empty else None,
                   vulnerability_score=score,**metrics,**outcome)
        rows.append(row)
        snap["transition_id"],snap["side"] = identifier,np.where(snap.team == losing,"Losing team","Counterattacking team")
        snapshots.append(snap)
        r0,r1 = np.searchsorted(pg.frame.to_numpy(),[preball.frame,outcome["end_frame"]+1],side="left")
        replay = pg.iloc[r0:r1].copy()
        replay[["x","y"]] = orient(replay[["x","y"]],sign)
        replay["transition_id"] = identifier
        replay["side"] = np.where(replay.team == losing,"Losing team","Counterattacking team")
        replay["relative_s"] = replay.time-anchor.time
        replays.append(replay)
        timeline = local_ball[local_ball.frame.between(preball.frame,outcome["end_frame"])].copy()
        timeline[["x","y"]] = orient(timeline[["x","y"]],sign)
        timeline["relative_s"] = timeline.time-anchor.time
        timeline["transition_id"] = identifier
        timelines.append(timeline)
    def combine(items):
        return pd.concat(items,ignore_index=True) if items else pd.DataFrame()
    return pd.DataFrame(rows),combine(snapshots),combine(replays),combine(timelines),dict(candidates=len(anchors),accepted=len(rows),rejected=dict(rejected))


def run(match="J03WPY", sample=False, bundled=False, output=None, stable_seconds=.4, paths=None, clean_cache=None):
    paths = paths or acquire(match,sample,bundled)
    meta = metadata(paths["meta"])
    events,halves = parse_events(paths["events"],meta)
    players,ball,parse_audit = clean(paths,meta,cache=clean_cache)
    results,snapshots,replays,timeline,analysis_audit = analyze(players,ball,events,meta,halves,stable_seconds)
    output = Path(output or ROOT / "outputs" / ("sample" if sample or bundled else match))
    output.mkdir(parents=True,exist_ok=True)
    if results.empty:
        raise ValueError(f"No eligible turnovers; audit={analysis_audit}")
    results.to_csv(output / "transitions.csv",index=False,float_format="%.8f")
    for name,df in [("snapshots",snapshots),("replays",replays),("timeline",timeline)]:
        df.to_parquet(output / f"{name}.parquet",index=False)
    known = ball[ball.live.eq(1)&ball.possession.isin([1,2])&ball.valid]
    meta["halves"] = halves
    meta["possession_share"] = {meta["possession_map"][int(k)]:float(v) for k,v in known.possession.value_counts(normalize=True).items()}
    (output / "metadata.json").write_text(json.dumps(meta,indent=2))
    sensitivity=[]
    for seconds in [.4,.8,1.2]:
        t = detect_turnovers(ball,seconds)
        sensitivity.append(dict(persistence_s=seconds,candidates=len(t)))
    audit = dict(match_id=match,analysis_code_sha256=analysis_fingerprint(),scope="first 180 seconds of available tracking" if sample or bundled else "full source match",
                 source={k:dict(file=p.name,sha256=digest(p)) for k,p in paths.items()},
                 parser=parse_audit,analysis=analysis_audit,stable_seconds=stable_seconds,
                 sensitivity=sensitivity,outputs={name:digest(output / name) for name in ["transitions.csv","snapshots.parquet","replays.parquet","timeline.parquet","metadata.json"]})
    (output / "audit.json").write_text(json.dumps(audit,indent=2))
    return results,audit


def load_result(path):
    path=Path(path)
    audit=json.loads((path / "audit.json").read_text())
    if any(digest(path / name)!=sha for name,sha in audit["outputs"].items()):
        raise ValueError("Result integrity check failed; rerun the pipeline")
    df=pd.read_csv(path / "transitions.csv")
    return df,json.loads((path / "metadata.json").read_text()),audit
