"""Field-position-restricted open-play pass benchmark, not a causal control."""
import argparse
import json
import random
from pathlib import Path
from analyse import CACHE, COMPETITIONS, ROOT, cluster_interval, episode, is_corner, name, read_verified, seconds


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--cache",type=Path,default=CACHE)
    p.add_argument("--output",type=Path,default=ROOT/"results/context_control.json")
    args=p.parse_args()
    rng=random.Random(20261113)
    rows=[]
    for cid,sid,label in COMPETITIONS:
        for match in read_verified(args.cache/f"matches/{cid}/{sid}.json"):
            match["tournament"]=label
            events=read_verified(args.cache/f"events/{match['match_id']}.json")
            corners=[(i,seconds(e.get("timestamp")),e.get("period")) for i,e in enumerate(events) if is_corner(e)]
            candidates=[]
            for i,e in enumerate(events):
                if name(e,"type")!="Pass" or (e.get("pass") or {}).get("type") or not e.get("location") or e["location"][0]<80:
                    continue
                t=seconds(e.get("timestamp")); team=(e.get("team") or {}).get("id")
                if t is None or team!=(e.get("possession_team") or {}).get("id"):
                    continue
                if any(period==e.get("period") and ct is not None and abs(t-ct)<=30 for _,ct,period in corners):
                    continue
                candidates.append(i)
            if len(candidates)<len(corners):
                raise ValueError(f"Insufficient open-play pass controls in match {match['match_id']}")
            for i in rng.sample(candidates,len(corners)):
                rows.append(episode(events,i,match,15))
    n=len(rows)
    result={"seed":20261113,"unit":"one final-third open-play pass per corner, sampled within match, >=30s from any corner",
            "n":n,"matches":len(set(r["match_id"] for r in rows)),
            "recovered":{"n":sum(r["recovered"] for r in rows),"match_bootstrap_95":cluster_interval(rows,"recovered")},
            "second_phase_shot":{"n":sum(bool(r["second_shots"]) for r in rows),"match_bootstrap_95":cluster_interval(rows,"second_shots")},
            "limitation":"Final-third open-play passes differ from corners in selection, field position and defensive organization; this is a descriptive context benchmark, not a causal null."}
    args.output.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=="__main__":
    main()
