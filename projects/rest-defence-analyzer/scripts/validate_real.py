"""Independent behind-ball count from native XML, without the analysis helpers."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--result",type=Path,default=Path("outputs/J03WPY"))
    parser.add_argument("--tracking",type=Path,default=Path("data/raw/J03WPY_tracking.xml"))
    parser.add_argument("--meta",type=Path,default=Path("data/raw/J03WPY_meta.xml"))
    parser.add_argument("--events",type=Path,default=Path("data/raw/J03WPY_events.xml"))
    args=parser.parse_args()
    records=pd.read_csv(args.result/"transitions.csv")
    roster=ET.parse(args.meta)
    keepers={p.attrib["PersonId"] for p in roster.iter("Player") if p.attrib.get("PlayingPosition")=="TW"}
    directions={n.attrib["GameSection"]:n.attrib["TeamLeft"] for n in ET.parse(args.events).iter("KickOff") if n.attrib.get("GameSection")}
    wanted={(r.period,r.snapshot_frame) for r in records.itertuples()}
    snapshots={key:[] for key in wanted}
    ball={}
    with args.tracking.open("rb") as stream:
        for line in stream:
            if line.startswith(b"<FrameSet "):
                context=ET.fromstring(line.strip()[:-1]+b"/>").attrib
            elif line.startswith(b"<Frame "):
                # Parsing only requested frames keeps the independent audit small.
                frame=int(line.split(b'N="',1)[1].split(b'"',1)[0])
                key=(context["GameSection"],frame)
                if key not in wanted:
                    continue
                a=ET.fromstring(line).attrib
                if context["TeamId"]=="BALL":
                    ball[key]=(float(a["X"]),float(a["Y"]))
                else:
                    snapshots[key].append((context["TeamId"],context["PersonId"],float(a["X"])))
    errors=[]
    for row in records.itertuples():
        key=(row.period,row.snapshot_frame)
        sign=1 if directions[row.period]==row.losing_team else -1
        count=sum(team==row.losing_team and person not in keepers and x*sign<=ball[key][0]*sign for team,person,x in snapshots[key])
        if count!=row.behind_ball or len(snapshots[key])!=22 or abs(ball[key][0]*sign-row.ball_x)>1e-7:
            errors.append(row.transition_id)
    report=dict(check="Independent native-XML behind-ball and snapshot count audit",snapshots_checked=len(records),failures=errors)
    (args.result/"independent-validation.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    if errors:
        raise SystemExit(1)


if __name__=="__main__":
    main()
