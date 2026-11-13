"""Reconstruct post-corner event sequences from a pinned local StatsBomb cache."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb"
CACHE = ROOT / "data/raw/data" if (ROOT / "data/raw/data/competitions.json").exists() else ROOT.parent / "tacticai-lite/data/raw/data"
COMPETITIONS = [(55, 282, "Men's Euro 2024"), (53, 315, "Women's Euro 2025")]
CONTACT = {"Clearance", "Block", "Interception", "Duel", "50/50", "Goal Keeper", "Ball Recovery"}
CONTROL = {"Pass", "Carry", "Shot", "Dribble"}
STOP = {"Half End", "Offside", "Injury Stoppage", "Referee Ball-Drop"}


def name(event, key):
    return (event.get(key) or {}).get("name")


def read_verified(path):
    receipt = path.with_suffix(".receipt.json")
    if not receipt.exists():
        raise ValueError(f"Missing SHA-256 source receipt: {receipt}")
    info = json.loads(receipt.read_text())
    content = path.read_bytes()
    if info.get("revision") != REVISION or info.get("sha256") != hashlib.sha256(content).hexdigest():
        raise ValueError(f"Source integrity failure: {path}")
    return json.loads(content)


def seconds(timestamp):
    try:
        h, m, s = timestamp.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except (ValueError, AttributeError):
        return None


def is_corner(e):
    return e.get("period") in (1, 2, 3, 4) and (
        (name(e, "type") == "Pass" and name(e.get("pass", {}), "type") == "Corner")
        or (name(e, "type") == "Shot" and name(e.get("shot", {}), "type") == "Corner")
    )


def box_entry(e):
    if name(e, "type") not in ("Pass", "Carry"):
        return False
    start = e.get("location") or []
    end = (e.get("pass") or {}).get("end_location") if name(e, "type") == "Pass" else (e.get("carry") or {}).get("end_location")
    return bool(len(start) >= 2 and end and len(end) >= 2 and
                not (start[0] >= 102 and 18 <= start[1] <= 62) and
                end[0] >= 102 and 18 <= end[1] <= 62)


def validate(events):
    ids = [e.get("id") for e in events]
    indexes = [e.get("index") for e in events]
    if len(ids) != len(set(ids)) or None in ids or len(indexes) != len(set(indexes)) or None in indexes:
        raise ValueError("Duplicate/missing event ID or index")
    if indexes != sorted(indexes):
        raise ValueError("Events not in provider index order")
    anomalies = Counter()
    previous = {}
    for e in events:
        t = seconds(e.get("timestamp"))
        p = e.get("period")
        if t is None:
            anomalies["missing_clock"] += 1
        elif p in previous and t < previous[p] - .001:
            anomalies["clock_reversal"] += 1
        if t is not None:
            previous[p] = t
        if e.get("possession") is None or not e.get("possession_team"):
            anomalies["missing_possession"] += 1
    return anomalies


def episode(events, i, match, horizon=30):
    corner = events[i]
    t0 = seconds(corner.get("timestamp"))
    attack = (corner.get("team") or {}).get("id")
    defense = (match.get("away_team") or {}).get("away_team_id") if attack == (match.get("home_team") or {}).get("home_team_id") else (match.get("home_team") or {}).get("home_team_id")
    row = dict(id=corner["id"], match_id=match["match_id"], tournament=match["tournament"],
               match=f"{match['home_team']['home_team_name']} v {match['away_team']['away_team_name']}",
               date=match["match_date"], attack=(corner.get("team") or {}).get("name"),
               minute=corner.get("minute"), period=corner["period"], direct_shot=name(corner, "type") == "Shot",
               delivery="direct_shot" if name(corner, "type") == "Shot" else "other",
               contact=False, clearance=False, recovered=False, confirmed_defense=False,
               continuation=False, immediate_shots=0, second_shots=0, continuation_shots=0,
               ambiguous_shots=0, immediate_xg=0.0, continuation_xg=0.0,
               second_xg=0.0, second_box_entries=0, counter_shots=0, counter_xg=0.0,
               first_shot_s=None, possession_end_s=None, recovery_s=None, state="unknown", complete=False,
               events=[])
    if t0 is None or attack not in (match["home_team"]["home_team_id"], match["away_team"]["away_team_id"]):
        return row
    if (corner.get("possession_team") or {}).get("id") != attack:
        row["state"] = "ambiguous_possession"
        return row
    if row["direct_shot"]:
        row["immediate_shots"] = 1
        row["first_shot_s"] = 0.0
        row["immediate_xg"] = (corner.get("shot") or {}).get("statsbomb_xg")
    else:
        length = (corner.get("pass") or {}).get("length")
        recipient = (corner.get("pass") or {}).get("recipient")
        if isinstance(length, (float, int)) and recipient and length <= 15:
            row["delivery"] = "short_verified"
        elif isinstance(length, (float, int)) and length > 15:
            row["delivery"] = "direct_delivery"
    row["events"].append(dict(t=0.0, phase="Corner", label="Corner shot" if row["direct_shot"] else "Delivery"))
    stop_index = None
    last_contact_s = None
    for j in range(i + 1, len(events)):
        e = events[j]
        if e.get("period") != corner["period"]:
            row["state"], row["complete"], row["possession_end_s"] = "period_end", True, row["possession_end_s"]
            stop_index = j
            break
        t = seconds(e.get("timestamp"))
        if t is None or t < t0 - .001:
            row["state"] = "ambiguous_clock"
            stop_index = j
            break
        dt = t - t0
        if dt > horizon:
            row["state"], row["complete"] = ("attacking_recovery" if row["recovered"] else "attacking_continuation" if row["continuation"] else "contact_unresolved" if row["contact"] else "no_observed_action"), True
            stop_index = j
            break
        typ = name(e, "type")
        if is_corner(e) or (typ == "Pass" and name(e.get("pass", {}), "type") in {"Free Kick", "Throw-in", "Goal Kick", "Kick Off"}):
            row["state"], row["complete"], row["possession_end_s"] = "restart", True, dt
            stop_index = j
            break
        team = (e.get("team") or {}).get("id")
        poss_team = (e.get("possession_team") or {}).get("id")
        if team == defense and typ in CONTACT:
            row["contact"] = True
            last_contact_s = dt
            if typ == "Clearance":
                row["clearance"] = True
            row["events"].append(dict(t=round(dt, 2), phase="Defensive contact", label=typ))
        if typ in STOP or (typ == "Foul Committed" and not e.get("foul_committed", {}).get("advantage")) or (typ == "Foul Won" and not e.get("foul_won", {}).get("advantage")) or e.get("out"):
            row["state"], row["complete"], row["possession_end_s"] = "stoppage", True, dt
            stop_index = j
            break
        if team == defense and typ in CONTROL and poss_team == defense:
            row["confirmed_defense"] = True
            row["possession_end_s"] = dt
            row["state"], row["complete"] = "defending_possession", True
            row["events"].append(dict(t=round(dt, 2), phase="Turnover", label=typ))
            stop_index = j
            break
        if team == attack and typ in CONTROL | {"Ball Recovery"}:
            if poss_team != attack:
                row["events"].append(dict(t=round(dt, 2), phase="Unresolved", label="Attacking action with conflicting possession tag"))
                continue
            simultaneous = row["contact"] and not row["recovered"] and last_contact_s is not None and dt <= last_contact_s + .001
            if simultaneous:
                if typ == "Shot":
                    row["ambiguous_shots"] += 1
                    if row["first_shot_s"] is None:
                        row["first_shot_s"] = dt
                row["events"].append(dict(t=round(dt, 2), phase="Unresolved", label=typ + " simultaneous with contact"))
                continue
            first_ball_shot = typ == "Shot" and not row["contact"] and not row["continuation"]
            if row["contact"]:
                if not row["recovered"]:
                    row["recovery_s"] = dt
                row["recovered"] = True
                phase = "Second ball"
            else:
                row["continuation"] = True
                phase = "Continuation"
            if typ == "Shot":
                if row["first_shot_s"] is None:
                    row["first_shot_s"] = dt
                if row["recovered"]:
                    row["second_shots"] += 1
                    xg = (e.get("shot") or {}).get("statsbomb_xg")
                    row["second_xg"] = row["second_xg"] + xg if isinstance(xg, (float, int)) else None
                elif first_ball_shot:
                    row["immediate_shots"] += 1
                    xg = (e.get("shot") or {}).get("statsbomb_xg")
                    row["immediate_xg"] = row["immediate_xg"] + xg if isinstance(xg, (float, int)) else None
                else:
                    row["continuation_shots"] += 1
                    xg = (e.get("shot") or {}).get("statsbomb_xg")
                    row["continuation_xg"] = row["continuation_xg"] + xg if isinstance(xg, (float, int)) else None
            if row["recovered"] and box_entry(e):
                row["second_box_entries"] += 1
            if typ in {"Pass", "Carry", "Shot", "Ball Recovery"}:
                row["events"].append(dict(t=round(dt, 2), phase=phase, label=typ + (" into box" if box_entry(e) else "")))
            if typ == "Shot" and name(e.get("shot", {}), "outcome") == "Goal":
                row["state"], row["complete"], row["possession_end_s"] = "goal", True, dt
                stop_index = j + 1
                break
    if stop_index is None:
        row["state"] = "recording_end"
    # A counter is evaluated only after confirmed defensive control, not after a touch.
    if row["confirmed_defense"] and stop_index is not None:
        control_time = t0 + row["possession_end_s"]
        for e in events[stop_index + 1:]:
            if e.get("period") != corner["period"]:
                break
            t = seconds(e.get("timestamp"))
            if t is None or t < control_time or t > control_time + 15 or is_corner(e):
                break
            if name(e, "type") in STOP or e.get("out"):
                break
            if (e.get("team") or {}).get("id") == defense and name(e, "type") == "Shot":
                row["counter_shots"] += 1
                row["events"].append(dict(t=round(t-t0, 2), phase="Counterattack", label="Opposition shot"))
                xg = (e.get("shot") or {}).get("statsbomb_xg")
                row["counter_xg"] = row["counter_xg"] + xg if isinstance(xg, (int, float)) else None
            if (e.get("possession_team") or {}).get("id") == attack and name(e, "type") in CONTROL:
                break
    return row


def cluster_interval(rows, key, repeats=2000, seed=13):
    groups = defaultdict(list)
    for r in rows:
        groups[r["match_id"]].append(r)
    ids = list(groups)
    if not ids or not rows:
        return [None, None]
    rng = random.Random(seed)
    values = []
    for _ in range(repeats):
        sample = [r for mid in rng.choices(ids, k=len(ids)) for r in groups[mid]]
        values.append(sum(bool(r[key]) for r in sample) / len(sample))
    values.sort()
    return [round(values[int(.025 * repeats)], 4), round(values[int(.975 * repeats)], 4)]


def exact_binomial_interval(k, n, alpha=.05):
    """Clopper-Pearson interval from finite binomial tails."""
    def cdf(kmax, p):
        if p >= 1:
            return 0.0 if kmax < n else 1.0
        if p <= 0:
            return 1.0
        term = (1-p)**n
        total = term
        for j in range(1, kmax+1):
            term *= (n-j+1)*p/(j*(1-p))
            total += term
        return total
    if not n:
        return [None, None]
    if k == 0:
        low = 0.0
    else:
        a,b=0.0,k/n
        for _ in range(70):
            m=(a+b)/2
            if 1-cdf(k-1,m) < alpha/2: a=m
            else: b=m
        low=(a+b)/2
    if k == n:
        high=1.0
    else:
        a,b=k/n,1.0
        for _ in range(70):
            m=(a+b)/2
            if cdf(k,m) > alpha/2: a=m
            else: b=m
        high=(a+b)/2
    return [round(low,4),round(high,4)]


def quantiles(values):
    values=sorted(values)
    if not values:
        return {"n":0,"q25":None,"median":None,"q75":None}
    def q(p):
        x=(len(values)-1)*p; lo=int(x); hi=min(lo+1,len(values)-1)
        return round(values[lo]*(hi-x)+values[hi]*(x-lo),2)
    return {"n":len(values),"q25":q(.25),"median":q(.5),"q75":q(.75)}


def summarize(rows):
    result = {}
    for tournament in sorted(set(r["tournament"] for r in rows)) + ["Combined (descriptive)"]:
        subset = rows if tournament.startswith("Combined") else [r for r in rows if r["tournament"] == tournament]
        n = len(subset)
        keys = ["contact", "clearance", "recovered", "confirmed_defense", "continuation", "second_shots", "second_box_entries", "counter_shots"]
        result[tournament] = {"corners": n, "matches": len(set(r["match_id"] for r in subset)),
            "states": dict(Counter(r["state"] for r in subset)),
            "outcomes": {k: {"count": sum(bool(r[k]) for r in subset), "rate": round(sum(bool(r[k]) for r in subset)/n, 4),
                              "match_bootstrap_95": cluster_interval(subset, k)} for k in keys},
            "shots": {"immediate": sum(r["immediate_shots"] for r in subset),
                      "unopposed_continuation": sum(r["continuation_shots"] for r in subset),
                      "recovered_second_phase": sum(r["second_shots"] for r in subset),
                      "ambiguous_phase": sum(r["ambiguous_shots"] for r in subset)},
            "shot_xg": {k: round(sum(r[k] or 0 for r in subset), 4) for k in ("immediate_xg", "continuation_xg", "second_xg")},
            "second_xg": round(sum(r["second_xg"] or 0 for r in subset), 4),
            "second_box_entries": sum(r["second_box_entries"] for r in subset),
            "time_to_first_shot_s": quantiles([r["first_shot_s"] for r in subset if r["first_shot_s"] is not None]),
            "time_to_possession_end_s": quantiles([r["possession_end_s"] for r in subset if r["possession_end_s"] is not None]),
            "counter_after_confirmed_control": {"shots": sum(bool(r["counter_shots"]) for r in subset),
                "controls": sum(r["confirmed_defense"] for r in subset),
                "exact_95": exact_binomial_interval(sum(bool(r["counter_shots"]) for r in subset), sum(r["confirmed_defense"] for r in subset))}}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    all_rows, audit = {}, {}
    for comp, season, label in COMPETITIONS:
        matches = read_verified(args.cache / f"matches/{comp}/{season}.json")
        for m in matches:
            m["tournament"] = label
            path = args.cache / f"events/{m['match_id']}.json"
            if not path.exists():
                raise FileNotFoundError(path)
            events = read_verified(path)
            audit[m["match_id"]] = dict(validate(events))
            for i, e in enumerate(events):
                if is_corner(e):
                    all_rows[e["id"]] = {str(h): episode(events, i, m, h) for h in (10, 15, 20, 30)}
    (args.output / "audit.json").write_text(json.dumps({"revision": "4b73468fc5b0f1950f9f66fada70ad3a4f9327cb", "matches": len(audit), "anomalies": dict(sum((Counter(v) for v in audit.values()), Counter())), "match_anomalies": {str(k): v for k,v in audit.items() if v}}, indent=2))
    summaries = {h: summarize([v[str(h)] for v in all_rows.values()]) for h in (10, 15, 20, 30)}
    (args.output / "summary.json").write_text(json.dumps(summaries, indent=2))
    # Local event-derived records stay outside public web artifacts.
    (args.output / "episodes.local.json").write_text(json.dumps(all_rows))
    print(json.dumps({h: {t: {"n": s["corners"], "states": s["states"], "shots": s["shots"], "recovered": s["outcomes"]["recovered"]["rate"]} for t,s in summaries[h].items()} for h in (10,15,20,30)}, indent=2))


if __name__ == "__main__":
    main()
